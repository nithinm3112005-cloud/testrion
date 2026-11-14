"""Test generators shared by classification and regression suites.

Implements the functional requirements from the project specification:
  FR-1.1 edge-case generation      FR-1.2 adversarial test generation
  FR-1.3 data-slice testing        FR-1.5 fairness (demographic parity)
  FR-1.4 accuracy threshold -> deployment gate
"""
import re

import numpy as np
import pandas as pd

from .testing import SEED, _grade_hi, _grade_lo, _pct, _test

PROTECTED_TOKENS = {
    "gender", "sex", "age", "region", "race", "ethnicity", "ethnic", "religion", "caste", "marital",
    "nationality", "disability", "location", "zone", "state", "city", "district", "area",
}
ROB = "Robustness"
FS = "Fairness & Slices"
GATE_THRESHOLD = 0.85
PARITY_LIMIT = 0.10


# --------------------------------------------------------------------------
# FR-1.1  edge-case generation
# --------------------------------------------------------------------------
def edge_cases(model, Xte, Xtr, task, y_all):
    num = [c for c in Xte.columns if pd.api.types.is_numeric_dtype(Xte[c])]
    cat = [c for c in Xte.columns if c not in num]
    base = Xte.head(5)
    by_kind = {}

    def add(kind, col, val):
        df = base.copy()
        if col in num:
            df[col] = df[col].astype(float)
        else:
            df[col] = df[col].astype(object)
        df[col] = val
        by_kind.setdefault(kind, []).append(df)

    for c in num[:8]:
        lo, hi = float(Xtr[c].min()), float(Xtr[c].max())
        span = (hi - lo) or 1.0
        add("minimum value", c, lo)
        add("maximum value", c, hi)
        add("zero", c, 0.0)
        add("out-of-distribution (10x range)", c, hi + 10 * span)
        add("null / NaN", c, np.nan)
    for c in cat[:4]:
        add("unseen category", c, "ZZZ_unseen")
        add("special characters", c, "!@#$%^&*()'\";--<script>")
        add("empty string", c, "")
        add("null / NaN", c, np.nan)

    ymin, ymax = float(np.min(y_all)), float(np.max(y_all))
    yspan = (ymax - ymin) or 1.0
    total = bad = 0
    detail = {}
    for kind, frames in by_kind.items():
        X = pd.concat(frames)
        n = len(X)
        total += n
        try:
            p = np.asarray(model.predict(X))
            if task == "regression":
                p = p.astype(float)
                invalid = int((~np.isfinite(p) | (p < ymin - 5 * yspan) | (p > ymax + 5 * yspan)).sum())
            else:
                invalid = 0
            failed = invalid
        except Exception:
            failed = n
        bad += failed
        detail[kind] = {"cases": n, "failed": int(failed)}
    ok = 1 - bad / max(total, 1)
    worst = [f"{k}: {v['failed']}/{v['cases']}" for k, v in detail.items() if v["failed"]]
    status = _grade_hi(ok, 0.99, 0.90)
    return _test(
        "edge_cases", ROB, "Edge-case inputs (generated)",
        "Auto-generates min/max, zero, out-of-distribution, null, unseen-category and special-character inputs.",
        status, _pct(ok), "≥ 99% handled",
        f"{total} edge cases generated, {bad} crashed or produced invalid output"
        + (f" ({'; '.join(worst)})." if worst else "."),
        "Add imputation, and make sure the model is stable outside the training range.", {"by_kind": detail},
    )


# --------------------------------------------------------------------------
# FR-1.2  adversarial test generation
# --------------------------------------------------------------------------
def adversarial(model, Xte, Xtr, task, eps=None, k=8, n=250):
    eps = eps or (0.10 if task == "regression" else 0.15)
    tol = 0.20
    num = [c for c in Xte.columns if pd.api.types.is_numeric_dtype(Xte[c])]
    name = "Adversarial perturbation (worst-case search)"
    desc = f"Searches {k} adversarial perturbations of ±{int(eps * 100)}% std per row for prediction flips."
    if not num:
        return _test("adversarial", ROB, name, desc, "skip", "n/a", "-", "No numeric features.", None)
    rng = np.random.RandomState(SEED)
    sub = Xte.sample(min(n, len(Xte)), random_state=SEED)
    sd = Xtr[num].astype(float).std().fillna(0).values
    try:
        base = np.asarray(model.predict(sub))
        stable = np.ones(len(sub), dtype=bool)
        for _ in range(k):
            P = sub.copy()
            signs = rng.choice([-1.0, 1.0], size=(len(sub), len(num)))
            P[num] = sub[num].astype(float).values + signs * eps * sd
            p = np.asarray(model.predict(P))
            if task == "regression":
                stable &= np.abs(p - base) / np.maximum(np.abs(base), 1e-9) <= tol
            else:
                stable &= p == base
    except Exception as e:
        return _test("adversarial", ROB, name, desc, "fail", "crash", "no crash", f"Model failed: {e}",
                     "Enable imputation.")
    rate = float(stable.mean())
    what = "stay within 20%" if task == "regression" else "keep their label"
    return _test("adversarial", ROB, name, desc, _grade_hi(rate, 0.90, 0.75), _pct(rate), "≥ 90% stable",
                 f"{_pct(rate)} of rows {what} under every adversarial perturbation.",
                 "Regularise or tune the model; smoother decision boundaries are harder to attack.")


# --------------------------------------------------------------------------
# FR-1.3 / FR-1.5  slices + fairness
# --------------------------------------------------------------------------
# "age" / "area" / "state" ... in these contexts describe an object or a duration, not a person's attribute
NOT_PERSON_TOKENS = {"account", "house", "building", "vehicle", "car", "property", "device", "file", "product", "asset", "machine",
                     "tenure", "days", "months", "weeks", "hours", "sqft", "square", "floor", "plot", "land", "engine", "battery"}


def find_protected(frame, user_cols):
    out = []
    for c in frame.columns:
        toks = set(re.split(r"[^a-z0-9]+", str(c).lower()))
        hit = toks & PROTECTED_TOKENS
        if hit and (toks & NOT_PERSON_TOKENS):
            hit = set()  # e.g. account_age_days, floor_area_sqft
        geo = {"area", "zone", "state", "city", "district", "location", "region"}
        if hit and hit <= geo and pd.api.types.is_numeric_dtype(frame[c]) and frame[c].nunique() > 8:
            hit = set()  # continuous measurement (e.g. tumour "mean area"), not a geographic group
        if c in user_cols or hit:
            out.append(c)
    return out


def _groups(s):
    """Turn a column into readable group labels (numeric -> 3 quantile bands)."""
    if pd.api.types.is_numeric_dtype(s) and s.nunique() > 8:
        edges = np.unique(np.quantile(s.dropna(), [0, 1 / 3, 2 / 3, 1]))
        if len(edges) >= 3:
            bins = [-np.inf] + list(edges[1:-1]) + [np.inf]
            lbl = [f"≤{edges[1]:.3g}"] + [f"{edges[i]:.3g}–{edges[i + 1]:.3g}" for i in range(1, len(edges) - 2)] \
                  + [f">{edges[-2]:.3g}"]
            return pd.cut(s, bins=bins, labels=lbl).astype(str)
    return s.astype(object).where(s.notna(), "missing").astype(str)


def slices_and_fairness(task, Xte, yte, pred, audit, user_protected):
    """Returns (slice_test, fairness_test, slice_rows)."""
    frame = Xte.copy()
    if audit is not None and len(audit.columns):
        extra = audit.loc[audit.index.intersection(Xte.index)]
        for c in extra.columns:
            if c not in frame.columns:
                frame[c] = extra[c].reindex(Xte.index)
    protected = find_protected(frame, set(user_protected or []))
    slice_cols = list(protected)
    auto = False
    if not slice_cols:
        auto = True
        for c in Xte.columns:
            if not pd.api.types.is_numeric_dtype(Xte[c]) and 2 <= Xte[c].nunique() <= 8:
                slice_cols.append(c)
            if len(slice_cols) == 2:
                break

    y = np.asarray(yte, dtype=float)
    p = np.asarray(pred, dtype=float)
    if task == "regression":
        err = np.abs(y - p) / np.maximum(np.abs(y), np.abs(y).max() * 1e-3 + 1e-9)
        overall = float(err.mean())
    else:
        err = (y == p).astype(float)
        overall = float(err.mean())

    rows, worst_gap, worst_desc = [], 0.0, ""
    for c in slice_cols:
        g = _groups(frame[c]).values
        metrics = []
        for lab in pd.unique(g):
            m = g == lab
            if m.sum() < 15:
                continue
            val = float(err[m].mean())
            metrics.append(val)
            rows.append({"column": c, "group": str(lab), "n": int(m.sum()), "metric": val,
                         "protected": c in protected})
        if len(metrics) >= 2:
            gap = (max(metrics) - min(metrics)) if task == "classification" else (max(metrics) - overall)
            if gap >= worst_gap:
                worst_gap, worst_desc = gap, c

    nm = "Data-slice performance"
    desc = "Compares accuracy (or % error) across slices such as gender, age and region."
    if not rows:
        t_slice = _test("slices", FS, nm, desc, "skip", "n/a", "-",
                        "No sliceable columns (need a categorical / protected column with ≥15 test rows per group).", None)
    else:
        label = "accuracy gap" if task == "classification" else "extra % error"
        ok, wn = (0.10, 0.20) if task == "classification" else (0.08, 0.15)
        t_slice = _test("slices", FS, nm, desc, _grade_lo(worst_gap, ok, wn), f"{worst_gap * 100:.1f} pts",
                        f"{label} ≤ {int(ok * 100)} pts",
                        f"Largest {label} is {worst_gap * 100:.1f} points on '{worst_desc}'"
                        + (" (auto-selected slice column)." if auto else "."),
                        "Collect more data for weak slices or tune / rebalance the model.")

    # ---- fairness: demographic parity difference
    fname = "Fairness: demographic parity difference"
    fdesc = ("Difference in predicted-outcome rate between groups of a protected attribute must stay below 10%. "
             "Demographic parity is one criterion and does not by itself prove a model is fair.")
    if not protected:
        t_fair = _test("fairness", FS, fname, fdesc, "skip", "n/a", "< 10%",
                       "No protected attribute (gender, age, region, race …) found. "
                       "Mark columns as protected under Advanced options.", None)
    else:
        worst_dpd, worst_col = 0.0, ""
        for c in protected:
            g = _groups(frame[c]).values
            rates = []
            for lab in pd.unique(g):
                m = g == lab
                if m.sum() < 15:
                    continue
                if task == "classification":
                    rates.append({k: float((p[m] == k).mean()) for k in np.unique(p)})
                else:  # regression: group bias = |mean prediction - mean actual| / mean |actual|
                    rates.append({"bias": abs(float(p[m].mean() - y[m].mean())) / (np.abs(y).mean() + 1e-9)})
            if len(rates) < 2:
                continue
            if task == "classification":
                keys = set().union(*[set(r) for r in rates])
                d = max(max(r.get(k, 0.0) for r in rates) - min(r.get(k, 0.0) for r in rates) for k in keys)
            else:
                d = max(r["bias"] for r in rates)
            if d >= worst_dpd:
                worst_dpd, worst_col = d, c
        if not worst_col:
            t_fair = _test("fairness", FS, fname, fdesc, "skip", "n/a", "< 10%",
                           "Protected groups were too small (<15 test rows) to evaluate.", None)
        else:
            t_fair = _test("fairness", FS, fname, fdesc, "pass" if worst_dpd < PARITY_LIMIT else "fail",
                           f"{worst_dpd * 100:.1f}%", "< 10%",
                           f"Largest parity difference is {worst_dpd * 100:.1f}% on protected attribute '{worst_col}'."
                           + (" (group bias for regression: |mean prediction − mean actual| per group.)"
                              if task == "regression" else ""),
                           "Remove the protected attribute from the features and rebalance the training data.",
                           {"columns": protected})
    t_fair["data"].setdefault("columns", protected)
    return t_slice, t_fair, rows
