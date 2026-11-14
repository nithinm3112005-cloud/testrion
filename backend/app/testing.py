"""Automated test suite for machine learning models.

The suite validates the *data*, the *model's quality*, its *robustness* (noise,
missing inputs, metamorphic relations) and its *reliability* (determinism,
drift, latency) and returns a structured, explainable report.
"""
import time
import warnings

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin, clone
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, RobustScaler, StandardScaler
from sklearn.tree import DecisionTreeClassifier

from .models import REGISTRY, SEED, make_estimator

import os

MAX_ROWS = int(os.environ.get("MLTESTLAB_MAX_ROWS", 6000))
TREE_MODELS = {"random_forest", "decision_tree", "gradient_boosting", "decision_tree_reg",
               "random_forest_reg", "gradient_boosting_reg"}

DEFAULT_CONFIG = {
    "impute": False,
    "scale": "none",  # none | standard | robust
    "balance": None,  # None | class_weight | oversample
    "dedupe": False,
    "drop_constant": False,
    "drop_columns": [],
    "params": {},
    "protected": [],  # columns audited for fairness (auto-detected when empty)
    "log_target": False,  # regression only
}

CATEGORY_WEIGHT = {
    "Data Quality": 1.0,
    "Model Performance": 2.0,
    "Robustness": 1.5,
    "Reliability": 1.0,
    "Fairness & Slices": 1.5,
}


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
class OversampleClassifier(ClassifierMixin, BaseEstimator):
    """Wraps a pipeline and randomly oversamples minority classes while fitting."""

    def __init__(self, pipe=None, seed=SEED):
        self.pipe = pipe
        self.seed = seed

    def fit(self, X, y):
        y = np.asarray(y)
        classes, counts = np.unique(y, return_counts=True)
        rng = np.random.RandomState(self.seed)
        idx = []
        for c, n in zip(classes, counts):
            ci = np.where(y == c)[0]
            idx.extend(ci)
            if n < counts.max():
                idx.extend(rng.choice(ci, counts.max() - n, replace=True))
        idx = np.array(idx)
        self.pipe_ = clone(self.pipe).fit(X.iloc[idx], y[idx])
        self.classes_ = self.pipe_.classes_
        return self

    def predict(self, X):
        return self.pipe_.predict(X)

    def predict_proba(self, X):
        return self.pipe_.predict_proba(X)


def _effective_balance(model_id, config):
    b = config.get("balance")
    if b == "class_weight" and not REGISTRY[model_id]["class_weight"]:
        return "oversample"
    return b


def build_model(model_id, config, X):
    num_cols = [c for c in X.columns if pd.api.types.is_numeric_dtype(X[c])]
    cat_cols = [c for c in X.columns if c not in num_cols]

    num_steps = []
    if config.get("impute"):
        num_steps.append(("imp", SimpleImputer(strategy="median")))
    if config.get("scale") == "standard":
        num_steps.append(("sc", StandardScaler()))
    elif config.get("scale") == "robust":
        num_steps.append(("sc", RobustScaler()))
    cat_steps = []
    if config.get("impute"):
        cat_steps.append(("imp", SimpleImputer(strategy="most_frequent")))
    cat_steps.append(("oh", OneHotEncoder(handle_unknown="ignore", sparse_output=False)))

    transformers = []
    if num_cols:
        transformers.append(("num", Pipeline(num_steps) if num_steps else "passthrough", num_cols))
    if cat_cols:
        transformers.append(("cat", Pipeline(cat_steps), cat_cols))
    pre = ColumnTransformer(transformers)

    balance = _effective_balance(model_id, config)
    est = make_estimator(
        model_id, config.get("params"), "balanced" if balance == "class_weight" else None
    )
    pipe = Pipeline([("pre", pre), ("model", est)])
    if config.get("log_target") and REGISTRY[model_id]["task"] == "regression":
        from sklearn.compose import TransformedTargetRegressor
        return TransformedTargetRegressor(regressor=pipe, func=np.log1p, inverse_func=np.expm1)
    return OversampleClassifier(pipe) if balance == "oversample" else pipe


def _psi(a, b, bins=10):
    a, b = a[~np.isnan(a)], b[~np.isnan(b)]
    if len(a) < 20 or len(b) < 20:
        return 0.0
    edges = np.unique(np.quantile(a, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    pa = np.clip(np.histogram(a, edges)[0] / len(a), 1e-4, None)
    pb = np.clip(np.histogram(b, edges)[0] / len(b), 1e-4, None)
    return float(np.sum((pb - pa) * np.log(pb / pa)))


def _grade_hi(v, ok, warn):
    return "pass" if v >= ok else "warn" if v >= warn else "fail"


def _grade_lo(v, ok, warn):
    return "pass" if v <= ok else "warn" if v <= warn else "fail"


def _pct(x):
    return f"{x * 100:.1f}%"


def _test(tid, category, name, desc, status, value, threshold, details, fix=None, data=None):
    return {
        "id": tid,
        "category": category,
        "name": name,
        "description": desc,
        "status": status,
        "value": value,
        "threshold": threshold,
        "details": details,
        "fix": fix if status in ("warn", "fail") else None,
        "data": data or {},
    }


# --------------------------------------------------------------------------
# data preparation
# --------------------------------------------------------------------------
def prepare(df, target, config, task="classification"):
    if target not in df.columns:
        raise ValueError(f"Target column '{target}' not found in dataset")
    df = df.copy()
    df = df.dropna(subset=[target])
    if len(df) > MAX_ROWS:
        df = df.sample(MAX_ROWS, random_state=SEED)
    notes = []
    raw_rows = len(df)

    drop = [c for c in config.get("drop_columns", []) if c in df.columns and c != target]
    audit = df[drop].copy() if drop else pd.DataFrame(index=df.index)  # kept for fairness auditing
    if drop:
        df = df.drop(columns=drop)

    # identifier-like text columns are never useful features
    for c in list(df.columns):
        if c == target or pd.api.types.is_numeric_dtype(df[c]):
            continue
        if df[c].nunique() > 50 and df[c].nunique() > 0.3 * len(df):
            df = df.drop(columns=[c])
            notes.append(f"Dropped identifier-like column '{c}'")

    if config.get("dedupe"):
        df = df.drop_duplicates()
    if config.get("drop_constant"):
        const = [c for c in df.columns if c != target and df[c].nunique(dropna=False) <= 1]
        if const:
            df = df.drop(columns=const)

    if task == "regression":
        if not pd.api.types.is_numeric_dtype(df[target]):
            raise ValueError(f"'{target}' is not numeric, so it cannot be used as a regression target.")
        if len(df) < 30:
            raise ValueError("Dataset has too few rows (need at least 30)")
        if df.shape[1] < 2:
            raise ValueError("Dataset needs at least one feature column besides the target")
        return df, raw_rows, notes, audit
    y_raw = df[target].astype(str)
    n_classes = y_raw.nunique()
    if n_classes < 2:
        raise ValueError("Target column has fewer than 2 classes")
    if n_classes > 30:
        raise ValueError(
            f"'{target}' has {n_classes} distinct values, so it is not a classification target. "
            "Choose a label column with 2-30 categories (for example a class or Yes/No column)."
        )
    if len(df) < 20:
        raise ValueError("Dataset has too few rows (need at least 20)")
    if df.shape[1] < 2:
        raise ValueError("Dataset needs at least one feature column besides the target")
    return df, raw_rows, notes, audit


def detect_task(df, target):
    s = df[target]
    return "regression" if pd.api.types.is_numeric_dtype(s) and s.nunique() > 20 else "classification"


def split_ready(df, target, config, task="classification"):
    work = df if config.get("impute") else df.dropna()
    dropped_rows = len(df) - len(work)
    if len(work) < 20:
        raise ValueError("Too few rows remain after removing rows with missing values - enable imputation")
    X = work.drop(columns=[target])
    for c in X.columns:
        if not pd.api.types.is_numeric_dtype(X[c]):
            X[c] = X[c].astype(object).where(X[c].notna(), np.nan)
    if task == "regression":
        y = work[target].astype(float).values
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=SEED)
        return {"X": X, "y": y, "Xtr": Xtr, "Xte": Xte, "ytr": ytr, "yte": yte, "classes": [],
                "dropped_rows": dropped_rows}
    le = LabelEncoder()
    y = le.fit_transform(work[target].astype(str))
    counts = np.bincount(y)
    strat = y if counts.min() >= 2 else None
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=SEED, stratify=strat)
    return {
        "X": X, "y": y, "Xtr": Xtr, "Xte": Xte, "ytr": ytr, "yte": yte,
        "classes": list(le.classes_), "dropped_rows": dropped_rows,
    }


def f1m(y, p):
    return float(f1_score(y, p, average="macro", zero_division=0))


def summarize(tests, accuracy):
    """Weighted score, grade and the deployment gate (accuracy >= 85% and fairness < 10%)."""
    scored = [t for t in tests if t["status"] != "skip"]
    wsum = sum(CATEGORY_WEIGHT[t["category"]] for t in scored)
    pts = {"pass": 1.0, "warn": 0.5, "fail": 0.0}
    score = 100 * sum(CATEGORY_WEIGHT[t["category"]] * pts[t["status"]] for t in scored) / max(wsum, 1e-9)
    cats = []
    for name in CATEGORY_WEIGHT:
        ct = [t for t in scored if t["category"] == name]
        if ct:
            cats.append({"name": name, "score": 100 * sum(pts[t["status"]] for t in ct) / len(ct),
                         "passed": sum(t["status"] == "pass" for t in ct), "total": len(ct)})
    grade = "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D" if score >= 55 else "F"
    verdict = {
        "A": "Excellent - ready for deployment",
        "B": "Good - minor issues to review",
        "C": "Fair - several problems need attention",
        "D": "Poor - significant problems found",
        "F": "Critical - not safe to deploy",
    }[grade]
    by_id = {t["id"]: t for t in tests}
    if "holdout_r2" in by_id:  # regression: accuracy is not a regression metric, so R² >= 0.85 is used
        checks = [{"name": "Hold-out R² ≥ 0.85 (regression equivalent of 85% accuracy)", "value": f"{accuracy:.3f}",
                   "passed": accuracy >= 0.85}]
    else:
        checks = [{"name": "Hold-out accuracy ≥ 85%", "value": f"{accuracy * 100:.1f}%", "passed": accuracy >= 0.85}]
    fair = by_id.get("fairness")
    if fair and fair["status"] != "skip":
        checks.append({"name": "Demographic parity difference < 10%", "value": fair["value"],
                       "passed": fair["status"] == "pass"})
    else:
        checks.append({"name": "Demographic parity difference < 10%", "value": "not evaluated", "passed": None})
    if "min_recall" in by_id:
        checks.append({"name": "Every class detected (worst-class recall ≥ 50%)", "value": by_id["min_recall"]["value"],
                       "passed": by_id["min_recall"]["status"] != "fail"})
    for tid, label in (("leakage", "No target leakage"), ("determinism", "Reproducible predictions")):
        if tid in by_id:
            checks.append({"name": label, "value": by_id[tid]["value"], "passed": by_id[tid]["status"] == "pass"})
    blocked = any(c["passed"] is False for c in checks)
    return {
        "score": round(score, 1), "grade": grade, "verdict": verdict,
        "passed": sum(t["status"] == "pass" for t in tests),
        "warned": sum(t["status"] == "warn" for t in tests),
        "failed": sum(t["status"] == "fail" for t in tests),
        "skipped": sum(t["status"] == "skip" for t in tests),
        "total": len(tests), "categories": cats,
        "gate": {"status": "BLOCKED" if blocked else "APPROVED", "checks": checks},
    }


# --------------------------------------------------------------------------
# main entry
# --------------------------------------------------------------------------
def run_suite(raw_df, target, model_id, config=None):
    t0 = time.time()
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    if model_id not in REGISTRY:
        raise ValueError(f"Unknown model '{model_id}'")
    if target in raw_df.columns:
        want, have = detect_task(raw_df, target), REGISTRY[model_id]["task"]
        if want != have:
            raise ValueError(
                f"'{REGISTRY[model_id]['label']}' is a {have} model but '{target}' is a {want} target. "
                f"Choose a {want} model.")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if REGISTRY[model_id]["task"] == "regression":
            from .regression import run_regression
            return run_regression(raw_df, target, model_id, cfg, t0)
        return _run(raw_df, target, model_id, cfg, t0)


def _run(raw_df, target, model_id, cfg, t0):
    df, raw_rows, notes, audit = prepare(raw_df, target, cfg)
    ctx = split_ready(df, target, cfg)
    X, y, Xtr, Xte, ytr, yte = (ctx[k] for k in ("X", "y", "Xtr", "Xte", "ytr", "yte"))
    classes = ctx["classes"]
    n_classes = len(classes)
    feats = [c for c in df.columns if c != target]
    num_cols = [c for c in feats if pd.api.types.is_numeric_dtype(df[c])]
    tests = []
    rng = np.random.RandomState(SEED)
    class_counts = np.bincount(y)

    # ============================ DATA QUALITY ============================
    DQ = "Data Quality"
    # 1. missing values
    miss_frac = float(df[feats].isna().sum().sum() / max(1, df[feats].size))
    worst_col = df[feats].isna().mean().sort_values(ascending=False)
    if cfg["impute"]:
        st, det = "pass", (
            f"{_pct(miss_frac)} of cells are missing and are filled by imputation (median / most-frequent)."
            if miss_frac else "No missing values found."
        )
    else:
        st = _grade_lo(miss_frac, 0.0, 0.05) if miss_frac else "pass"
        det = (
            f"{_pct(miss_frac)} of cells are missing (worst: '{worst_col.index[0]}' at "
            f"{_pct(worst_col.iloc[0])}). Without imputation {ctx['dropped_rows']} rows are discarded."
            if miss_frac else "No missing values found."
        )
    tests.append(_test("missing_values", DQ, "Missing values handled",
        "Checks that missing cells are either absent or handled by the pipeline.",
        st, _pct(miss_frac), "0% or imputed", det,
        "Enable median / most-frequent imputation instead of dropping rows."))

    # 2. duplicates
    dup_frac = float(df.duplicated().mean())
    st = _grade_lo(dup_frac, 0.005, 0.03)
    tests.append(_test("duplicates", DQ, "Duplicate rows",
        "Duplicates inflate test scores because identical rows leak between train and test.",
        st, _pct(dup_frac), "< 0.5%",
        f"{int(df.duplicated().sum())} duplicate rows found." if dup_frac else "No duplicate rows.",
        "Remove duplicate rows before splitting the data."))

    # 3. class imbalance
    ratio = float(class_counts.min() / class_counts.max())
    dist = ", ".join(f"{c}: {n}" for c, n in zip(classes, class_counts))
    mitigated = cfg["balance"] is not None
    if ratio >= 0.5:
        st, det = "pass", f"Classes are reasonably balanced ({dist})."
    elif mitigated:
        st, det = "pass", f"Imbalance ratio {ratio:.2f} is mitigated using {_effective_balance(model_id, cfg)} ({dist})."
    else:
        st, det = _grade_hi(ratio, 0.5, 0.2), f"Minority/majority ratio is {ratio:.2f} ({dist})."
    tests.append(_test("imbalance", DQ, "Class balance",
        "Severe imbalance makes accuracy misleading and hides poor minority-class recall.",
        st, f"{ratio:.2f}", "ratio ≥ 0.50 or mitigated", det,
        "Use class weights (or random oversampling for models without weights)."))

    # 4. constant features
    const = [c for c in feats if df[c].nunique(dropna=False) <= 1]
    tests.append(_test("constant_features", DQ, "Constant features",
        "Features with a single value carry no information and add noise.",
        "pass" if not const else "warn", str(len(const)), "0",
        f"Constant columns: {', '.join(const)}." if const else "All features vary.",
        "Drop constant columns.", {"columns": const}))

    # 5. outliers
    if num_cols:
        nd = df[num_cols].astype(float)
        z = ((nd - nd.mean()) / nd.std(ddof=0).replace(0, np.nan)).abs()
        out_frac = float((z > 4).sum().sum() / max(1, z.notna().sum().sum()))
    else:
        out_frac = 0.0
    insensitive = model_id in TREE_MODELS or cfg["scale"] == "robust"
    if out_frac <= 0.01 or not num_cols:
        st, det = "pass", f"{_pct(out_frac)} of numeric values are extreme outliers (|z| > 4)."
    elif insensitive:
        st, det = "pass", f"{_pct(out_frac)} outliers, but the pipeline is insensitive to them."
    else:
        st, det = _grade_lo(out_frac, 0.01, 0.04), f"{_pct(out_frac)} of numeric values have |z| > 4."
    tests.append(_test("outliers", DQ, "Outlier exposure",
        "Extreme values can dominate distance- and gradient-based models.",
        st, _pct(out_frac), "< 1%", det, "Use a robust scaler (median / IQR) or a tree-based model."))

    # 6. leakage
    leaks = []
    if len(df) >= 100:
        ytmp = LabelEncoder().fit_transform(df[target].astype(str))
        cv3 = StratifiedKFold(3, shuffle=True, random_state=SEED) if np.bincount(ytmp).min() >= 3 else 3
        for c in feats[:30]:
            col = df[c]
            vals = (col.fillna(col.median()) if c in num_cols else col.astype("category").cat.codes).astype(float)
            try:
                s = cross_val_score(DecisionTreeClassifier(max_depth=2, random_state=SEED),
                                    vals.values.reshape(-1, 1), ytmp, cv=cv3,
                                    scoring="balanced_accuracy").mean()
            except Exception:
                continue
            if s >= 0.96:
                leaks.append((c, float(s)))
    tests.append(_test("leakage", DQ, "Target leakage",
        "A single feature that almost perfectly predicts the target usually leaks the label.",
        "pass" if not leaks else "fail", str(len(leaks)), "0",
        ("Suspicious features: " + ", ".join(f"{c} ({s:.2f} balanced accuracy alone)" for c, s in leaks) + ".")
        if leaks else "No single feature predicts the target suspiciously well.",
        "Remove the leaking feature(s) - they will not exist at prediction time.",
        {"columns": [c for c, _ in leaks]}))

    # 7. sample size
    rows_per_feat = len(X) / max(1, len(feats))
    st = "fail" if len(X) < 50 else _grade_hi(rows_per_feat, 10, 5)
    tests.append(_test("sample_size", DQ, "Sufficient sample size",
        "Too few rows per feature leads to unstable, overfitted models.",
        st, f"{len(X)} rows", "≥ 10 rows / feature",
        f"{len(X)} usable rows for {len(feats)} features ({rows_per_feat:.1f} rows per feature).",
        "Collect more data or reduce the number of features."))

    # ========================= MODEL PERFORMANCE ==========================
    MP = "Model Performance"
    t_fit = time.time()
    model = build_model(model_id, cfg, X)
    model.fit(Xtr, ytr)
    fit_time = time.time() - t_fit
    pred = model.predict(Xte)
    train_pred = model.predict(Xtr)
    f1_te, f1_tr = f1m(yte, pred), f1m(ytr, train_pred)
    acc = float(accuracy_score(yte, pred))

    tests.append(_test("holdout_f1", MP, "Hold-out macro F1",
        "Macro F1 treats every class equally, so it is robust to class imbalance.",
        _grade_hi(f1_te, 0.85, 0.70), f"{f1_te:.3f}", "≥ 0.85",
        f"Macro F1 {f1_te:.3f}, accuracy {acc:.3f} on {len(yte)} unseen rows.",
        "Tune hyper-parameters, improve features or try a stronger model."))

    # validation = cross-validation INSIDE the training portion; the hold-out test rows are never touched
    n_splits = int(max(2, min(5, np.bincount(ytr).min())))
    cv = StratifiedKFold(n_splits, shuffle=True, random_state=SEED)
    cv_scores = cross_val_score(build_model(model_id, cfg, Xtr), Xtr, ytr, cv=cv, scoring="f1_macro")
    cv_mean, cv_std = float(cv_scores.mean()), float(cv_scores.std())
    tests.append(_test("cv_f1", MP, f"{n_splits}-fold cross-validation",
        "Validation score: k-fold cross-validation inside the training data (the test set is never used).",
        _grade_hi(cv_mean, 0.85, 0.70), f"{cv_mean:.3f}", "≥ 0.85",
        "Fold scores: " + ", ".join(f"{s:.3f}" for s in cv_scores) + ".",
        "Tune hyper-parameters or switch model."))
    tests.append(_test("cv_stability", MP, "Cross-validation stability",
        "Large variance between folds means the model is unstable.",
        _grade_lo(cv_std, 0.03, 0.07), f"±{cv_std:.3f}", "std ≤ 0.03",
        f"Standard deviation across folds is {cv_std:.3f}.",
        "Use stronger regularisation / more data to stabilise the model."))

    gap = f1_tr - f1_te
    tests.append(_test("overfitting", MP, "Overfitting gap",
        "Compares training and test F1; a large gap means memorisation.",
        _grade_lo(gap, 0.05, 0.12), f"{gap:+.3f}", "gap ≤ 0.05",
        f"Train F1 {f1_tr:.3f} vs test F1 {f1_te:.3f}.",
        "Increase regularisation (max_depth, min_samples_leaf, C) via tuning."))

    prec, rec, f1c, sup = precision_recall_fscore_support(yte, pred, labels=range(n_classes), zero_division=0)
    worst = int(np.argmin(rec))
    min_rec = float(rec[worst])
    tests.append(_test("min_recall", MP, "Worst-class recall",
        "Even the weakest class should be detected reliably (slice / fairness test).",
        _grade_hi(min_rec, 0.70, 0.50), _pct(min_rec), "≥ 70%",
        f"Class '{classes[worst]}' has the lowest recall ({_pct(min_rec)}).",
        "Rebalance classes with class weights or oversampling."))

    # ============================ ROBUSTNESS ==============================
    RB = "Robustness"
    # noise
    if num_cols:
        Xn = Xte.copy()
        for c in num_cols:
            sd = float(Xtr[c].std()) if Xtr[c].notna().any() else 0.0
            Xn[c] = Xn[c].astype(float) + rng.normal(0, 0.1 * (sd or 0), len(Xn))
        try:
            drop_n = f1_te - f1m(yte, model.predict(Xn))
            tests.append(_test("noise", RB, "Gaussian noise robustness",
                "Adds noise (10% of each feature's std) to test inputs and measures the F1 drop.",
                _grade_lo(drop_n, 0.05, 0.10), f"{drop_n:+.3f}", "drop ≤ 0.05",
                f"Macro F1 changes by {-drop_n:+.3f} under noise.",
                "Regularise the model or use smoother models / scaling."))
        except Exception as e:
            tests.append(_test("noise", RB, "Gaussian noise robustness", "Adds noise to test inputs.",
                               "fail", "error", "-", f"Model failed on noisy input: {e}", "Enable imputation."))
    else:
        tests.append(_test("noise", RB, "Gaussian noise robustness", "Adds noise to test inputs.",
                           "skip", "n/a", "-", "No numeric features to perturb.", None))

    # missing at inference
    if num_cols:
        Xm = Xte.copy()
        for c in num_cols:
            Xm[c] = Xm[c].astype(float)
            Xm.loc[rng.rand(len(Xm)) < 0.10, c] = np.nan
        try:
            drop_m = f1_te - f1m(yte, model.predict(Xm))
            st = _grade_lo(drop_m, 0.08, 0.20)
            det = f"With 10% of numeric cells blanked, macro F1 changes by {-drop_m:+.3f}."
            val = f"{drop_m:+.3f}"
        except Exception as e:
            st, val = "fail", "crash"
            det = f"Model crashes when inputs contain missing values ({type(e).__name__})."
        tests.append(_test("missing_inputs", RB, "Missing values at inference",
            "Production data is rarely complete - the model must not crash or collapse.",
            st, val, "no crash, drop ≤ 0.08", det, "Add an imputation step to the pipeline."))
    else:
        tests.append(_test("missing_inputs", RB, "Missing values at inference",
                           "Blank inputs at prediction time.", "skip", "n/a", "-", "No numeric features.", None))

    # metamorphic: feature rescaling
    if num_cols:
        factors = [1000, 0.001, 10, 100]
        Xtr_s, Xte_s = Xtr.copy(), Xte.copy()
        for i, c in enumerate(num_cols):
            f = factors[i % len(factors)]
            Xtr_s[c] = Xtr_s[c].astype(float) * f
            Xte_s[c] = Xte_s[c].astype(float) * f
        m2 = build_model(model_id, cfg, Xtr_s).fit(Xtr_s, ytr)
        agree = float((m2.predict(Xte_s) == pred).mean())
        tests.append(_test("scale_invariance", RB, "Unit-change invariance (metamorphic)",
            "Changing units of a feature (e.g. metres → millimetres) must not change predictions.",
            _grade_hi(agree, 0.97, 0.90), _pct(agree), "≥ 97% agreement",
            f"Predictions agree on {_pct(agree)} of test rows after rescaling features and retraining.",
            "Add feature scaling to the pipeline."))
    else:
        tests.append(_test("scale_invariance", RB, "Unit-change invariance (metamorphic)",
                           "Unit changes must not change predictions.", "skip", "n/a", "-", "No numeric features.", None))

    # metamorphic: training order
    perm = rng.permutation(len(Xtr))
    m3 = build_model(model_id, cfg, Xtr).fit(Xtr.iloc[perm], ytr[perm])
    agree_o = float((m3.predict(Xte) == pred).mean())
    tests.append(_test("order_invariance", RB, "Training-order invariance (metamorphic)",
        "Shuffling the order of training rows must not change what the model learns.",
        _grade_hi(agree_o, 0.97, 0.90), _pct(agree_o), "≥ 97% agreement",
        f"Predictions agree on {_pct(agree_o)} of test rows after shuffling training data.",
        "Use more data, more trees or a more stable model."))

    from . import extras
    tests.append(extras.edge_cases(model, Xte, Xtr, "classification", y))
    tests.append(extras.adversarial(model, Xte, Xtr, "classification"))

    # ============================ RELIABILITY =============================
    RL = "Reliability"
    m4 = build_model(model_id, cfg, Xtr).fit(Xtr, ytr)
    same = bool(np.array_equal(m4.predict(Xte), pred))
    tests.append(_test("determinism", RL, "Reproducibility",
        "Training twice with the same seed must give identical predictions.",
        "pass" if same else "fail", "identical" if same else "differs", "identical",
        "Two independent trainings produced identical predictions." if same
        else "Two trainings with the same seed produced different predictions.",
        "Fix random seeds for all stochastic components."))

    psi_bins = int(min(10, max(3, len(Xte) // 10)))
    psis = {c: _psi(Xtr[c].astype(float).values, Xte[c].astype(float).values, psi_bins) for c in num_cols}
    max_psi = max(psis.values()) if psis else 0.0
    worst_psi = max(psis, key=psis.get) if psis else "-"
    # PSI is noisy on small samples: scale thresholds by its expected value under no shift
    expected = (psi_bins - 1) * (1 / max(1, len(Xtr)) + 1 / max(1, len(Xte)))
    psi_ok, psi_warn = max(0.10, 3 * expected), max(0.25, 6 * expected)
    tests.append(_test("drift", RL, "Train/test drift (PSI)",
        "Population Stability Index flags features whose distribution shifted between train and test.",
        _grade_lo(max_psi, psi_ok, psi_warn) if psis else "skip", f"{max_psi:.3f}" if psis else "n/a",
        f"PSI ≤ {psi_ok:.2f}",
        f"Largest shift is '{worst_psi}' with PSI {max_psi:.3f}." if psis else "No numeric features.",
        "Re-split the data or investigate distribution shift."))

    t_p = time.time()
    for _ in range(3):
        model.predict(Xte)
    ms = (time.time() - t_p) / 3 / max(1, len(Xte)) * 1000 * 1000
    tests.append(_test("latency", RL, "Prediction latency",
        "Time needed to score 1,000 rows.",
        _grade_lo(ms, 150, 600), f"{ms:.0f} ms", "≤ 150 ms / 1k rows",
        f"{ms:.0f} ms per 1,000 predictions (training took {fit_time:.2f}s).",
        "Use a lighter model for low-latency serving."))

    t_slice, t_fair, slice_rows = extras.slices_and_fairness("classification", Xte, yte, pred, audit,
                                                              cfg.get("protected"))
    tests += [t_slice, t_fair]

    # ============================== METRICS ===============================
    cm = confusion_matrix(yte, pred, labels=range(n_classes))
    try:
        sub = Xte.sample(min(len(Xte), 1200), random_state=SEED)
        pi = permutation_importance(model, sub, yte[[Xte.index.get_loc(i) for i in sub.index]],
                                    scoring="f1_macro", n_repeats=3, random_state=SEED)
        imp = sorted(
            [{"feature": c, "importance": float(v)} for c, v in zip(Xte.columns, pi.importances_mean)],
            key=lambda d: -d["importance"],
        )[:10]
    except Exception:
        imp = []

    metrics = {
        "task": "classification",
        "slices": slice_rows,
        "accuracy": acc,
        "precision": float(np.mean(prec)),
        "recall": float(np.mean(rec)),
        "f1": f1_te,
        "train_f1": f1_tr,
        "cv_mean": cv_mean,
        "cv_std": cv_std,
        "classes": classes,
        "confusion_matrix": cm.tolist(),
        "per_class": [
            {"class": classes[i], "precision": float(prec[i]), "recall": float(rec[i]),
             "f1": float(f1c[i]), "support": int(sup[i])} for i in range(n_classes)
        ],
        "feature_importance": imp,
        "fit_time": fit_time,
    }
    profile = {
        "rows": raw_rows,
        "usable_rows": int(len(X)),
        "features": len(feats),
        "numeric_features": len(num_cols),
        "categorical_features": len(feats) - len(num_cols),
        "missing_pct": miss_frac,
        "class_distribution": [{"class": c, "count": int(n)} for c, n in zip(classes, class_counts)],
        "notes": notes,
    }

    summary = summarize(tests, acc)
    return {
        "task": "classification",
        "config": {"model": model_id, "target": target, **cfg},
        "summary": summary,
        "tests": tests,
        "metrics": metrics,
        "profile": profile,
        "duration_sec": round(time.time() - t0, 2),
    }


def fit_final(raw_df, target, model_id, config):
    """Train the run's pipeline on ALL usable data (for the playground / model export / monitoring)."""
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    task = REGISTRY[model_id]["task"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df, _, _, _ = prepare(raw_df, target, cfg, task)
        work = df if cfg["impute"] else df.dropna()
        X = work.drop(columns=[target])
        for c in X.columns:
            if not pd.api.types.is_numeric_dtype(X[c]):
                X[c] = X[c].astype(object).where(X[c].notna(), np.nan)
        if task == "regression":
            y, classes = work[target].astype(float).values, None
        else:
            le = LabelEncoder()
            y = le.fit_transform(work[target].astype(str))
            classes = list(le.classes_)
        model = build_model(model_id, cfg, X).fit(X, y)
    features = []
    for c in X.columns:
        if pd.api.types.is_numeric_dtype(X[c]):
            features.append({"name": c, "type": "numeric", "min": float(X[c].min()), "max": float(X[c].max()),
                             "median": float(X[c].median())})
        else:
            vc = X[c].dropna().astype(str).value_counts()
            features.append({"name": c, "type": "categorical", "options": list(vc.index[:30]),
                             "default": vc.index[0] if len(vc) else ""})
    ref = X.sample(min(len(X), 2000), random_state=SEED)
    return model, classes, features, ref
