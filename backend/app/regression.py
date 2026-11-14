"""Automated test suite for regression models (e.g. house-price prediction)."""
import time

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_score

from . import extras
from .models import SEED
from .testing import (
    TREE_MODELS, _grade_hi, _grade_lo, _pct, _psi, _test, build_model, prepare, split_ready, summarize,
)

DQ, MP, RB, RL = "Data Quality", "Model Performance", "Robustness", "Reliability"


def _mape(y, p):
    return float(np.mean(np.abs(y - p) / np.maximum(np.abs(y), np.abs(y).max() * 1e-3 + 1e-9)))


def run_regression(raw_df, target, model_id, cfg, t0):
    df, raw_rows, notes, audit = prepare(raw_df, target, cfg, "regression")
    ctx = split_ready(df, target, cfg, "regression")
    X, y, Xtr, Xte, ytr, yte = (ctx[k] for k in ("X", "y", "Xtr", "Xte", "ytr", "yte"))
    feats = [c for c in df.columns if c != target]
    num_cols = [c for c in feats if pd.api.types.is_numeric_dtype(df[c])]
    rng = np.random.RandomState(SEED)
    tests = []

    # ============================ DATA QUALITY ============================
    miss_frac = float(df[feats].isna().sum().sum() / max(1, df[feats].size))
    worst_col = df[feats].isna().mean().sort_values(ascending=False)
    if cfg["impute"]:
        st, det = "pass", (f"{_pct(miss_frac)} of cells are missing and are filled by imputation."
                           if miss_frac else "No missing values found.")
    else:
        st = _grade_lo(miss_frac, 0.0, 0.05) if miss_frac else "pass"
        det = (f"{_pct(miss_frac)} of cells are missing (worst: '{worst_col.index[0]}' at "
               f"{_pct(worst_col.iloc[0])}). Without imputation {ctx['dropped_rows']} rows are discarded."
               if miss_frac else "No missing values found.")
    tests.append(_test("missing_values", DQ, "Missing values handled",
        "Checks that missing cells are either absent or handled by the pipeline.", st, _pct(miss_frac),
        "0% or imputed", det, "Enable median / most-frequent imputation instead of dropping rows."))

    dup_frac = float(df.duplicated().mean())
    tests.append(_test("duplicates", DQ, "Duplicate rows",
        "Duplicates inflate test scores because identical rows leak between train and test.",
        _grade_lo(dup_frac, 0.005, 0.03), _pct(dup_frac), "< 0.5%",
        f"{int(df.duplicated().sum())} duplicate rows found." if dup_frac else "No duplicate rows.",
        "Remove duplicate rows before splitting the data."))

    skew = float(pd.Series(y).skew())
    nonneg = bool(np.min(y) >= 0)
    tests.append(_test("target_distribution", DQ, "Target distribution (skew)",
        "A heavily skewed target (like prices) lets a few expensive rows dominate the error.",
        _grade_lo(abs(skew), 1.0, 2.5), f"{skew:+.2f}", "|skew| ≤ 1.0",
        f"Skewness of '{target}' is {skew:+.2f}.", "Log-transform the target before training.",
        {"nonneg": nonneg}))

    const = [c for c in feats if df[c].nunique(dropna=False) <= 1]
    tests.append(_test("constant_features", DQ, "Constant features",
        "Features with a single value carry no information and add noise.",
        "pass" if not const else "warn", str(len(const)), "0",
        f"Constant columns: {', '.join(const)}." if const else "All features vary.",
        "Drop constant columns.", {"columns": const}))

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
        "Extreme values can dominate distance- and gradient-based models.", st, _pct(out_frac), "< 1%", det,
        "Use a robust scaler (median / IQR) or a tree-based model."))

    leaks = []
    if num_cols:
        yy = df[target].astype(float)
        for c in num_cols[:40]:
            col = df[c].astype(float)
            if col.nunique() > 1:
                r = abs(float(col.fillna(col.median()).corr(yy)))
                if r >= 0.98:
                    leaks.append((c, r))
    tests.append(_test("leakage", DQ, "Target leakage",
        "A feature that is almost perfectly correlated with the target usually leaks the label.",
        "pass" if not leaks else "fail", str(len(leaks)), "0",
        ("Suspicious features: " + ", ".join(f"{c} (|r| = {r:.3f})" for c, r in leaks) + ".") if leaks
        else "No feature is suspiciously correlated with the target.",
        "Remove the leaking feature(s) - they will not exist at prediction time.",
        {"columns": [c for c, _ in leaks]}))

    rows_per_feat = len(X) / max(1, len(feats))
    tests.append(_test("sample_size", DQ, "Sufficient sample size",
        "Too few rows per feature leads to unstable, overfitted models.",
        "fail" if len(X) < 50 else _grade_hi(rows_per_feat, 10, 5), f"{len(X)} rows", "≥ 10 rows / feature",
        f"{len(X)} usable rows for {len(feats)} features ({rows_per_feat:.1f} rows per feature).",
        "Collect more data or reduce the number of features."))

    # ========================= MODEL PERFORMANCE ==========================
    t_fit = time.time()
    model = build_model(model_id, cfg, X)
    model.fit(Xtr, ytr)
    fit_time = time.time() - t_fit
    pred, train_pred = model.predict(Xte), model.predict(Xtr)
    r2_te, r2_tr = float(r2_score(yte, pred)), float(r2_score(ytr, train_pred))
    rmse = float(np.sqrt(mean_squared_error(yte, pred)))
    mae = float(mean_absolute_error(yte, pred))
    mape = _mape(yte, pred)

    tests.append(_test("holdout_r2", MP, "Hold-out R² (accuracy)",
        "Share of variance explained on unseen data - the regression equivalent of accuracy.",
        _grade_hi(r2_te, 0.85, 0.70), f"{r2_te:.3f}", "≥ 0.85",
        f"R² {r2_te:.3f}, RMSE {rmse:,.2f}, MAE {mae:,.2f} on {len(yte)} unseen rows.",
        "Tune hyper-parameters, add features or try a non-linear model."))
    tests.append(_test("mape", MP, "Mean absolute % error",
        "Average relative error of the predictions.", _grade_lo(mape, 0.15, 0.25), _pct(mape), "≤ 15%",
        f"Predictions are off by {_pct(mape)} on average.", "Tune the model or log-transform the target."))

    # validation = cross-validation INSIDE the training portion; the hold-out test rows are never touched
    cv = KFold(5, shuffle=True, random_state=SEED)
    cv_scores = cross_val_score(build_model(model_id, cfg, Xtr), Xtr, ytr, cv=cv, scoring="r2")
    cv_mean, cv_std = float(cv_scores.mean()), float(cv_scores.std())
    tests.append(_test("cv_r2", MP, "5-fold cross-validation",
        "Validation score: k-fold cross-validation inside the training data (the test set is never used).",
        _grade_hi(cv_mean, 0.85, 0.70), f"{cv_mean:.3f}", "≥ 0.85",
        "Fold R²: " + ", ".join(f"{s:.3f}" for s in cv_scores) + ".", "Tune hyper-parameters or switch model."))
    tests.append(_test("cv_stability", MP, "Cross-validation stability",
        "Large variance between folds means the model is unstable.",
        _grade_lo(cv_std, 0.03, 0.07), f"±{cv_std:.3f}", "std ≤ 0.03",
        f"Standard deviation across folds is {cv_std:.3f}.", "Use stronger regularisation / more data."))
    gap = r2_tr - r2_te
    tests.append(_test("overfitting", MP, "Overfitting gap",
        "Compares training and test R²; a large gap means memorisation.",
        _grade_lo(gap, 0.05, 0.12), f"{gap:+.3f}", "gap ≤ 0.05",
        f"Train R² {r2_tr:.3f} vs test R² {r2_te:.3f}.", "Increase regularisation (max_depth, min_samples_leaf)."))

    pred_all = np.asarray(model.predict(X), dtype=float)
    bad = (~np.isfinite(pred_all)) | ((pred_all < 0) if nonneg else False)
    bad_frac = float(np.mean(bad))
    tests.append(_test("valid_range", MP, "Valid predictions (non-negative)" if nonneg else "Valid predictions (finite)",
        "Predictions must be finite" + (" and positive (a price can never be negative)." if nonneg else "."),
        "pass" if bad_frac == 0 else "warn" if bad_frac <= 0.02 else "fail", _pct(bad_frac) + " invalid", "0%",
        f"{int(bad.sum())} of {len(pred_all)} predictions are invalid." if bad_frac else
        "All predictions are valid" + (" and positive." if nonneg else "."),
        "Log-transform the target so predictions can never go negative."))

    # ============================ ROBUSTNESS ==============================
    if num_cols:
        Xn = Xte.copy()
        for c in num_cols:
            sd = float(Xtr[c].std()) if Xtr[c].notna().any() else 0.0
            Xn[c] = Xn[c].astype(float) + rng.normal(0, 0.1 * (sd or 0), len(Xn))
        drop_n = r2_te - float(r2_score(yte, model.predict(Xn)))
        tests.append(_test("noise", RB, "Gaussian noise robustness",
            "Adds noise (10% of each feature's std) to test inputs and measures the R² drop.",
            _grade_lo(drop_n, 0.05, 0.10), f"{drop_n:+.3f}", "drop ≤ 0.05",
            f"R² changes by {-drop_n:+.3f} under noise.", "Regularise the model or use smoother models."))
        Xm = Xte.copy()
        for c in num_cols:
            Xm[c] = Xm[c].astype(float)
            Xm.loc[rng.rand(len(Xm)) < 0.10, c] = np.nan
        try:
            drop_m = r2_te - float(r2_score(yte, model.predict(Xm)))
            st, det, val = _grade_lo(drop_m, 0.08, 0.20), \
                f"With 10% of numeric cells blanked, R² changes by {-drop_m:+.3f}.", f"{drop_m:+.3f}"
        except Exception as e:
            st, val, det = "fail", "crash", f"Model crashes when inputs contain missing values ({type(e).__name__})."
        tests.append(_test("missing_inputs", RB, "Missing values at inference",
            "Production data is rarely complete - the model must not crash or collapse.", st, val,
            "no crash, drop ≤ 0.08", det, "Add an imputation step to the pipeline."))

        factors = [1000, 0.001, 10, 100]
        Xtr_s, Xte_s = Xtr.copy(), Xte.copy()
        for i, c in enumerate(num_cols):
            Xtr_s[c] = Xtr_s[c].astype(float) * factors[i % 4]
            Xte_s[c] = Xte_s[c].astype(float) * factors[i % 4]
        p2 = build_model(model_id, cfg, Xtr_s).fit(Xtr_s, ytr).predict(Xte_s)
        agree = float((np.abs(p2 - pred) / np.maximum(np.abs(pred), 1e-9) <= 0.02).mean())
        tests.append(_test("scale_invariance", RB, "Unit-change invariance (metamorphic)",
            "Changing units of a feature (e.g. metres → millimetres) must not change predictions.",
            _grade_hi(agree, 0.97, 0.90), _pct(agree), "≥ 97% within 2%",
            f"{_pct(agree)} of predictions stay within 2% after rescaling features and retraining.",
            "Add feature scaling to the pipeline."))
    else:
        for tid, nm in (("noise", "Gaussian noise robustness"), ("missing_inputs", "Missing values at inference"),
                        ("scale_invariance", "Unit-change invariance (metamorphic)")):
            tests.append(_test(tid, RB, nm, nm, "skip", "n/a", "-", "No numeric features.", None))

    perm = rng.permutation(len(Xtr))
    p3 = build_model(model_id, cfg, Xtr).fit(Xtr.iloc[perm], ytr[perm]).predict(Xte)
    agree_o = float((np.abs(p3 - pred) / np.maximum(np.abs(pred), 1e-9) <= 0.05).mean())
    tests.append(_test("order_invariance", RB, "Training-order invariance (metamorphic)",
        "Shuffling the order of training rows must not change what the model learns.",
        _grade_hi(agree_o, 0.97, 0.90), _pct(agree_o), "≥ 97% within 5%",
        f"{_pct(agree_o)} of predictions stay within 5% after shuffling training data.",
        "Use more data, more trees or a more stable model."))
    tests.append(extras.edge_cases(model, Xte, Xtr, "regression", y))
    tests.append(extras.adversarial(model, Xte, Xtr, "regression"))

    # ============================ RELIABILITY =============================
    same = bool(np.allclose(build_model(model_id, cfg, Xtr).fit(Xtr, ytr).predict(Xte), pred))
    tests.append(_test("determinism", RL, "Reproducibility",
        "Training twice with the same seed must give identical predictions.",
        "pass" if same else "fail", "identical" if same else "differs", "identical",
        "Two independent trainings produced identical predictions." if same
        else "Two trainings with the same seed produced different predictions.",
        "Fix random seeds for all stochastic components."))

    bins = int(min(10, max(3, len(Xte) // 10)))
    psis = {c: _psi(Xtr[c].astype(float).values, Xte[c].astype(float).values, bins) for c in num_cols}
    max_psi = max(psis.values()) if psis else 0.0
    worst_psi = max(psis, key=psis.get) if psis else "-"
    expected = (bins - 1) * (1 / max(1, len(Xtr)) + 1 / max(1, len(Xte)))
    ok_t, warn_t = max(0.10, 3 * expected), max(0.25, 6 * expected)
    tests.append(_test("drift", RL, "Train/test drift (PSI)",
        "Population Stability Index flags features whose distribution shifted between train and test.",
        _grade_lo(max_psi, ok_t, warn_t) if psis else "skip", f"{max_psi:.3f}" if psis else "n/a",
        f"PSI ≤ {ok_t:.2f}", f"Largest shift is '{worst_psi}' with PSI {max_psi:.3f}." if psis else "No numeric features.",
        "Re-split the data or investigate distribution shift."))

    t_p = time.time()
    for _ in range(3):
        model.predict(Xte)
    ms = (time.time() - t_p) / 3 / max(1, len(Xte)) * 1_000_000
    tests.append(_test("latency", RL, "Prediction latency", "Time needed to score 1,000 rows.",
        _grade_lo(ms, 150, 600), f"{ms:.0f} ms", "≤ 150 ms / 1k rows",
        f"{ms:.0f} ms per 1,000 predictions (training took {fit_time:.2f}s).",
        "Use a lighter model for low-latency serving."))

    t_slice, t_fair, slice_rows = extras.slices_and_fairness("regression", Xte, yte, pred, audit, cfg.get("protected"))
    tests += [t_slice, t_fair]

    # ============================== METRICS ===============================
    try:
        sub = Xte.sample(min(len(Xte), 800), random_state=SEED)
        yy = yte[[Xte.index.get_loc(i) for i in sub.index]]
        pi = permutation_importance(model, sub, yy, scoring="r2", n_repeats=3, random_state=SEED)
        imp = sorted([{"feature": c, "importance": float(v)} for c, v in zip(Xte.columns, pi.importances_mean)],
                     key=lambda d: -d["importance"])[:10]
    except Exception:
        imp = []
    resid = yte - pred
    cnt, edges = np.histogram(resid, bins=14)
    sc = rng.choice(len(yte), min(220, len(yte)), replace=False)
    table = [{"actual": float(a), "predicted": float(p), "error": float(p - a),
              "error_pct": float(abs(p - a) / max(abs(a), 1e-9))} for a, p in zip(yte[:20], pred[:20])]
    metrics = {
        "task": "regression", "accuracy": r2_te, "r2": r2_te, "train_r2": r2_tr, "rmse": rmse, "mae": mae,
        "mape": mape, "cv_mean": cv_mean, "cv_std": cv_std, "fit_time": fit_time,
        "comparison_table": table,
        "scatter": [{"actual": float(yte[i]), "predicted": float(pred[i])} for i in sc],
        "residual_hist": [{"bin": f"{(edges[i] + edges[i + 1]) / 2:.3g}", "count": int(cnt[i])} for i in range(len(cnt))],
        "feature_importance": imp, "slices": slice_rows,
    }
    tcnt, tedges = np.histogram(y, bins=14)
    profile = {
        "rows": raw_rows, "usable_rows": int(len(X)), "features": len(feats), "numeric_features": len(num_cols),
        "categorical_features": len(feats) - len(num_cols), "missing_pct": miss_frac,
        "target_stats": {"mean": float(np.mean(y)), "median": float(np.median(y)), "min": float(np.min(y)),
                         "max": float(np.max(y)), "skew": skew},
        "target_histogram": [{"bin": f"{(tedges[i] + tedges[i + 1]) / 2:.3g}", "count": int(tcnt[i])}
                             for i in range(len(tcnt))],
        "notes": notes,
    }
    return {
        "task": "regression",
        "config": {"model": model_id, "target": target, **cfg},
        "summary": summarize(tests, r2_te), "tests": tests, "metrics": metrics, "profile": profile,
        "duration_sec": round(time.time() - t0, 2),
    }
