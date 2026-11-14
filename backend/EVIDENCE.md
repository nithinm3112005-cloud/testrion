# Testrion - evidence and benchmarks

Generated 2026-11-13 15:33 on macOS-27.0.1-arm64-arm-64bit · Python 3.9.6 · 10 CPU cores.

## 1. Evidence for each test type (house-price dataset)

*Before* = Linear Regression, raw data. *After* = Gradient Boosting with the repaired pipeline (imputation, de-duplication, log-target, scaling).

| Test | Before | After | Target |
|---|---|---|---|
| Edge-case inputs | 78.9% (fail) | 100.0% (pass) | ≥ 99% handled |
| Adversarial perturbation | 100.0% (pass) | 99.2% (pass) | ≥ 90% stable |
| Data-slice performance | 6.4 pts (pass) | 4.0 pts (pass) | extra % error ≤ 8 pts |
| Demographic parity difference | 9.9% (pass) | 6.7% (pass) | < 10% |
| Hold-out R² | 0.753 (warn) | 0.864 (pass) | ≥ 0.85 |
| Positive predictions | 0.0% invalid (pass) | 0.0% invalid (pass) | 0% |

**Edge cases generated (before):**

| Edge-case type | Cases | Crashed / invalid |
|---|---|---|
| minimum value | 30 | 0 |
| maximum value | 30 | 0 |
| zero | 30 | 0 |
| out-of-distribution (10x range) | 30 | 0 |
| null / NaN | 40 | 40 |
| unseen category | 10 | 0 |
| special characters | 10 | 0 |
| empty string | 10 | 0 |

**Data slices by region (after):**

| Region | Test rows | Mean abs. % error |
|---|---|---|
| West | 85 | 11.2% |
| South | 94 | 11.1% |
| Central | 84 | 10.4% |
| North | 86 | 11.0% |
| East | 38 | 10.5% |

**Deployment gate - Before: BLOCKED** (score 75.0, grade C)

| Check | Value | Result |
|---|---|---|
| Hold-out R² ≥ 0.85 (regression equivalent of 85% accuracy) | 0.753 | FAIL |
| Demographic parity difference < 10% | 9.9% | pass |
| No target leakage | 0 | pass |
| Reproducible predictions | identical | pass |

**Deployment gate - After: APPROVED** (score 94.1, grade A)

| Check | Value | Result |
|---|---|---|
| Hold-out R² ≥ 0.85 (regression equivalent of 85% accuracy) | 0.864 | pass |
| Demographic parity difference < 10% | 6.7% | pass |
| No target leakage | 0 | pass |
| Reproducible predictions | identical | pass |

**Regression metrics (after):** R² 0.864 · RMSE 18.65 · MAE 13.66 · MAPE 11.0% (price in lakhs)

**Actual vs predicted (first 8 test rows, after):**

| Actual | Predicted | Error % |
|---|---|---|
| 117.2 | 124.5 | 6.2% |
| 67.7 | 78.7 | 16.1% |
| 134.4 | 155.8 | 15.9% |
| 82.9 | 79.9 | 3.6% |
| 108.0 | 99.7 | 7.6% |
| 118.3 | 125.2 | 5.8% |
| 49.9 | 74.4 | 49.1% |
| 95.2 | 109.2 | 14.8% |

**Automatic problem solving:** score 75.0 → 97.1, gate BLOCKED → APPROVED after these automatic steps:

- Added missing-value imputation — `median imputation for numeric, most-frequent for categorical`
- Removed duplicate rows — `drop_duplicates()`
- Log-transformed the target — `log_target = true (expm1 on output)`
- Applied feature standardisation — `StandardScaler`
- Tuned hyper-parameters — `fit_intercept=True`
- Switched model to Gradient Boosting Regressor — `Linear Regression → Gradient Boosting Regressor`

## 2. Benchmark: test execution speed (target: 1M records, full suite < 15 min)

| Dataset rows | Model | Tests executed | Wall-clock | Target | Result |
|---|---|---|---|---|---|
| 1,025,000 (1,000,000 usable) | Ridge Regression | 24 | 22 s (0.4 min) | < 15 min | MET |

*(Synthetic data generation took 1s and is not included.)* Tree ensembles are much slower per row; this result applies to the linear model tested.

## 3. Benchmark: parallel model testing (target: 100 models)

| Models tested | Worker threads | Wall-clock | Sum of individual run times | Speed-up | Target | Result |
|---|---|---|---|---|---|---|
| 100 | 10 | 41 s | 395 s | 9.59× | 100 models | MET |

## 4. Benchmark: drift-detection latency (target: < 5 s) and dashboard load (target: < 3 s)

| Measurement | Result | Target | Status |
|---|---|---|---|
| Drift verdict after 200 live (drifted) predictions | 11 ms (server-side compute 8.1 ms) | < 5 s | MET |
| Verdict returned | DRIFT DETECTED | DRIFT DETECTED | MET |
| Mean single-prediction latency | 7.86 ms (p95 8.09 ms) | - | - |
| Dashboard page + JS/CSS bundles over localhost (excludes browser render) | 13 ms | < 3 s | MET |

*Interpretation of the slide: "under 5 delay" is taken to mean 5 seconds.* In the app the browser-measured dashboard load time is also displayed live on the Dashboard page.

## Validation discipline

Every model is evaluated on a 25% hold-out test split that is never used to fit, tune or select a model. Cross-validation (the *validation* score) runs only inside the remaining 75%, and the auto-fix engine keeps a tuning or model change only if that validation score does not get worse. The final deployed/exported model (`model.pkl`) is re-trained on all rows after evaluation.
