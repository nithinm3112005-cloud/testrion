"""Problem-solving engine: diagnoses failed tests and automatically applies fixes.

Strategy (each stage is re-validated with the full test-suite):
  1. Data / pipeline repairs  - imputation, de-duplication, constant & leaking feature
     removal, scaling, class balancing, log-transform of skewed targets, removal of
     protected attributes that cause unfair predictions.
  2. Hyper-parameter tuning   - randomised cross-validated search.
  3. Model search             - tries alternative algorithms, keeps the best.
Stages 2-3 are only kept if they improve the overall quality score.
"""
import copy
import warnings

from sklearn.model_selection import (
    KFold, ParameterGrid, RandomizedSearchCV, StratifiedKFold, cross_val_score,
)

from . import testing
from .models import REGISTRY, SEED

MODEL_TESTS = {
    "holdout_f1", "cv_f1", "cv_stability", "overfitting", "noise", "min_recall", "order_invariance",
    "holdout_r2", "cv_r2", "mape", "valid_range", "adversarial", "slices",
}
QUALITY_TESTS = ("holdout_f1", "cv_f1", "holdout_r2", "cv_r2")
CANDIDATES = {
    "classification": ["logistic_regression", "random_forest", "gradient_boosting"],
    "regression": ["ridge", "random_forest_reg", "gradient_boosting_reg"],
}


def _not_worse(new, old):
    """A tuning / model-switch is kept only if it does not add failures or lower the overall score."""
    a, b = new["summary"], old["summary"]
    return a["failed"] <= b["failed"] and a["score"] >= b["score"] - 1e-9


def _issues(result):
    return {t["id"]: t for t in result["tests"] if t["status"] in ("warn", "fail")}


def _repair_pipeline(result, model_id, cfg):
    """Stage 1: derive config changes from failing data / pipeline tests."""
    issues = _issues(result)
    steps = []
    cfg = copy.deepcopy(cfg)
    task = REGISTRY[model_id]["task"]

    def step(title, why, change):
        steps.append({"title": title, "why": why, "change": change})

    if "leakage" in issues and issues["leakage"]["data"].get("columns"):
        cols = issues["leakage"]["data"]["columns"]
        cfg["drop_columns"] = sorted(set(cfg["drop_columns"]) | set(cols))
        step("Removed leaking features", f"{', '.join(cols)} almost perfectly reveal the target and will not "
             "be available in production.", f"drop_columns = {cols}")
    if ({"missing_values", "missing_inputs", "edge_cases"} & set(issues)) and not cfg["impute"]:
        cfg["impute"] = True
        step("Added missing-value imputation", ("Rows with gaps were being discarded. " if "missing_values" in issues else "")
             + "The model crashed on incomplete or edge-case inputs at prediction time.", "median imputation for numeric, most-frequent for categorical")
    if "duplicates" in issues and not cfg["dedupe"]:
        cfg["dedupe"] = True
        step("Removed duplicate rows", "Duplicates leak between train and test and inflate scores.",
             "drop_duplicates()")
    if "constant_features" in issues and not cfg["drop_constant"]:
        cfg["drop_constant"] = True
        step("Dropped constant features", "They carry no information.", "drop_constant = true")
    if task == "classification" and ("imbalance" in issues or "min_recall" in issues) and cfg["balance"] is None:
        cfg["balance"] = "class_weight" if REGISTRY[model_id]["class_weight"] else "oversample"
        step("Rebalanced the classes", "Minority classes were under-represented, hurting their recall.",
             "class_weight = balanced" if cfg["balance"] == "class_weight" else "random oversampling")
    if task == "regression" and ({"target_distribution", "valid_range"} & set(issues)) and not cfg["log_target"]:
        nonneg = issues.get("target_distribution", {}).get("data", {}).get("nonneg", True)
        if nonneg:
            cfg["log_target"] = True
            step("Log-transformed the target", "A skewed target lets a few extreme values dominate and allows "
                 "negative predictions; training on log(1+y) fixes both.", "log_target = true (expm1 on output)")
    if "outliers" in issues and cfg["scale"] == "none":
        cfg["scale"] = "robust"
        step("Applied robust scaling", "Extreme values distort the model; median/IQR scaling is resistant.",
             "RobustScaler")
    scale_sensitive = model_id not in testing.TREE_MODELS
    if cfg["scale"] == "none" and ("scale_invariance" in issues or scale_sensitive):
        cfg["scale"] = "standard"
        step("Applied feature standardisation",
             "Predictions changed when feature units changed." if "scale_invariance" in issues
             else f"{REGISTRY[model_id]['label']} is sensitive to feature scale.", "StandardScaler")
    if "fairness" in issues and issues["fairness"]["status"] == "fail":
        cols = [c for c in issues["fairness"]["data"].get("columns", []) if c not in cfg["drop_columns"]]
        if cols:
            cfg["drop_columns"] = sorted(set(cfg["drop_columns"]) | set(cols))
            step("Removed protected attributes from the features",
                 f"Predictions differed by more than 10% between groups of {', '.join(cols)}. The attributes are "
                 "still audited, but no longer used by the model.", f"drop_columns += {cols}")
    return cfg, steps


def _cv(task):
    return KFold(3, shuffle=True, random_state=SEED) if task == "regression" else \
        StratifiedKFold(3, shuffle=True, random_state=SEED)


def _tune(raw_df, target, model_id, cfg):
    """Stage 2: randomised CV search over a small, regularisation-friendly grid."""
    task = REGISTRY[model_id]["task"]
    df, _, _, _ = testing.prepare(raw_df, target, cfg, task)
    ctx = testing.split_ready(df, target, cfg, task)
    grid = REGISTRY[model_id]["grid"]
    base = testing.build_model(model_id, {**cfg, "balance": cfg["balance"] if cfg["balance"] != "oversample" else None},
                               ctx["X"])
    prefix = "regressor__model__" if cfg.get("log_target") and task == "regression" else "model__"
    param_grid = {f"{prefix}{k}": v for k, v in grid.items()}
    n_iter = min(8, len(ParameterGrid(param_grid)))
    search = RandomizedSearchCV(base, param_grid, n_iter=n_iter, cv=_cv(task),
                                scoring="r2" if task == "regression" else "f1_macro",
                                random_state=SEED, n_jobs=1, error_score=0)
    search.fit(ctx["Xtr"], ctx["ytr"])
    return {k.replace(prefix, ""): v for k, v in search.best_params_.items()}, float(search.best_score_)


def _search_models(raw_df, target, current, cfg):
    """Stage 3: compare candidate algorithms by cross-validated score."""
    task = REGISTRY[current]["task"]
    df, _, _, _ = testing.prepare(raw_df, target, cfg, task)
    ctx = testing.split_ready(df, target, cfg, task)
    Xtr, ytr = ctx["Xtr"], ctx["ytr"]  # never the held-out test rows
    candidates = list(CANDIDATES[task])
    if task == "classification" and len(Xtr) <= 3000:
        candidates.append("svm")
    scores = {}
    for m in candidates:
        c = {**cfg, "params": {}, "scale": cfg["scale"] if cfg["scale"] != "none" else "standard"}
        try:
            scores[m] = float(cross_val_score(testing.build_model(m, c, Xtr), Xtr, ytr,
                                              cv=_cv(task), scoring="r2" if task == "regression" else "f1_macro").mean())
        except Exception:
            scores[m] = 0.0
    return scores


def autofix(raw_df, target, model_id, original):
    """Returns (final_result, model_id, steps, comparison)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return _autofix(raw_df, target, model_id, original)


def _autofix(raw_df, target, model_id, original):
    base_cfg = {k: original["config"].get(k, v) for k, v in testing.DEFAULT_CONFIG.items()}
    steps = []
    best, best_model, best_cfg = original, model_id, base_cfg

    # ---- stage 1: repair the data pipeline
    cfg, s1 = _repair_pipeline(original, model_id, base_cfg)
    if s1:
        res = testing.run_suite(raw_df, target, model_id, cfg)
        steps += s1
        best, best_cfg = res, cfg

    # ---- stage 2: hyper-parameter tuning if model-level problems remain
    if set(_issues(best)) & MODEL_TESTS:
        try:
            params, cv_best = _tune(raw_df, target, best_model, best_cfg)
            cfg2 = {**best_cfg, "params": params}
            res = testing.run_suite(raw_df, target, best_model, cfg2)
            # keep only if the VALIDATION score (cross-validation on training data) did not get worse
            if (res["metrics"]["cv_mean"] >= best["metrics"]["cv_mean"] - 1e-9 and params != best_cfg.get("params")
                    and _not_worse(res, best)):
                steps.append({"title": "Tuned hyper-parameters",
                              "why": f"Cross-validated search (score {cv_best:.3f}) to reduce overfitting and "
                                     "improve generalisation.",
                              "change": ", ".join(f"{k}={v}" for k, v in params.items())})
                best, best_cfg = res, cfg2
        except Exception:
            pass

    # ---- stage 3: switch algorithm if quality is still lacking
    still = _issues(best)
    if any(k in still for k in QUALITY_TESTS):
        try:
            scores = _search_models(raw_df, target, best_model, best_cfg)
            cand = max(scores, key=scores.get)
            if cand != best_model and scores[cand] > scores.get(best_model, 0) + 0.01:
                cfg3 = {**best_cfg, "params": {}}
                if cfg3["scale"] == "none":
                    cfg3["scale"] = "standard"
                res = testing.run_suite(raw_df, target, cand, cfg3)
                if res["metrics"]["cv_mean"] > best["metrics"]["cv_mean"] and _not_worse(res, best):
                    steps.append({"title": f"Switched model to {REGISTRY[cand]['label']}",
                                  "why": "Model search over " + ", ".join(
                                      f"{REGISTRY[m]['label']} ({s:.3f})" for m, s in scores.items()) + " (CV score).",
                                  "change": f"{REGISTRY[best_model]['label']} → {REGISTRY[cand]['label']}"})
                    best, best_model, best_cfg = res, cand, cfg3
        except Exception:
            pass

    gate = best["summary"].get("gate", {})
    if gate.get("status") == "BLOCKED":
        bad = [c["name"] for c in gate.get("checks", []) if c.get("passed") is False]
        steps.append({"title": "Release gate still blocked - limit of the data, not the pipeline",
                      "why": "Auto-fix repairs pipeline problems and searches models, but cannot add information "
                             "the data does not contain. Still failing: " + "; ".join(bad) + ". Pick a target that "
                             "the other columns actually explain, add more rows / informative features, or use a "
                             "different dataset.",
                      "change": "no automatic fix available"})

    before = {t["id"]: t for t in original["tests"]}
    comparison = [
        {"id": t["id"], "name": t["name"], "category": t["category"],
         "before": before[t["id"]]["status"] if t["id"] in before else None, "after": t["status"],
         "before_value": before[t["id"]]["value"] if t["id"] in before else None, "after_value": t["value"]}
        for t in best["tests"]
    ]
    return best, best_model, steps, comparison
