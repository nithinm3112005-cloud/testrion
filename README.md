# Testrion
### Automated Software Testing and Problem Solving of Machine Learning Models

Testrion is a full-stack web application that **automatically tests a machine-learning model like software**,
**diagnoses the problems it finds**, and **fixes them with one click** — then re-runs every test to prove the improvement.

## Quick start

```bash
./run.sh            # then open http://127.0.0.1:8000
```

Development mode (hot reload): run `uvicorn app.main:app --reload` in `backend/` and `npm run dev` in `frontend/` (http://localhost:5173).

## Accounts
Landing page at `/`, sign up / log in, per-user data isolation (PBKDF2-hashed passwords, expiring bearer-token sessions).
Demo account: **demo@mltestlab.com / demo1234** (also a one-click button on the login page).

## Extra features
Model playground (predict live with probabilities) · download the trained model (.joblib) · compare any two runs ·
advanced pipeline options · target-column validation.

## Architecture

| Layer     | Technology                                   | Role |
|-----------|----------------------------------------------|------|
| Frontend  | React 18, Vite, React Router, Recharts       | Dashboard, test wizard, reports, auto-fix view |
| Backend   | FastAPI, scikit-learn, pandas, NumPy         | REST API, test engine, problem-solving engine |
| Storage   | SQLite (+ CSV uploads on disk)               | Runs, results and datasets |

```
backend/app/
  main.py      REST API + serves the built frontend
  testing.py   classification test suite, shared scoring + deployment gate
  regression.py regression test suite (house prices)
  extras.py    edge-case, adversarial, slice and fairness tests
  fixer.py     diagnosis + automatic repair engine
  models.py    model registry (6 algorithms) and tuning grids
  datasets.py  5 built-in datasets (2 deliberately broken) + CSV loading
  db.py        SQLite persistence
frontend/src/pages/  Dashboard · NewTest · Report · Datasets · History · HowItWorks
```

## Alignment with the Stage-1 project presentation
The in-app page **Requirements** (`/app/requirements`) maps every slide to its implementation. Summary:

| Slide requirement | Where it lives |
|---|---|
| House-price prediction, actual vs predicted table | Built-in *House Price Prediction* dataset, regression models, comparison table + scatter |
| FR-1.1 Edge-case generation | Test *Edge-case inputs (generated)* – min/max, zero, out-of-distribution, null, special characters |
| FR-1.2 Adversarial tests | Test *Adversarial perturbation* – worst-case search |
| FR-1.3 Slice testing (gender / age / region) | Test *Data-slice performance* + slice charts |
| FR-1.4 Accuracy < 85% ⇒ deployment fails | **Deployment gate** banner on every report; `ci_check.py` exits 1 |
| FR-1.5 Demographic parity difference < 10% | Test *Fairness: demographic parity difference* (part of the gate) |
| Drift detection < 5 s on live predictions | **Live monitoring** tab (logs predictions, PSI drift, latency) |
| Dashboard < 3 s | Load time measured and shown on the Dashboard |
| Many models in parallel | **Benchmark all models** → leaderboard with measured speed-up |
| Save `MODEL.PKL` | *Model* button downloads `model-run<N>.pkl` (standard Python pickle) |
| CI/CD with GitHub Actions | `.github/workflows/ml-tests.yml` → pytest + deployment gate on every push |
| Streamlit GUI | `backend/streamlit_app.py` (`streamlit run streamlit_app.py`) in addition to the React app |

Performance targets were **measured** (see `backend/EVIDENCE.md`, regenerate with `python evidence.py`):
1,000,000 records in 22 s (Ridge), 100 models in parallel in 41 s (9.6× speed-up), drift verdict in 11 ms, dashboard load 13 ms.
They come from one 10-core Mac; the interactive app still caps a run at 6,000 rows. The Dockerfile has not been built
on this machine (Docker not installed). Healthcare etc. are potential applications only - nothing health-specific is implemented.
The test split is never used to fit, tune or select a model; validation is cross-validation inside the training data.

## The automated tests (24 for regression, 23 for classification)

| Category | Tests |
|----------|-------|
| **Data Quality** | Missing values · Duplicates · Class balance *(or target skew)* · Constant features · Outliers · Target leakage · Sample size |
| **Model Performance** | Hold-out macro F1 *(or R²)* · Cross-validation · CV stability · Overfitting gap · Worst-class recall *(or MAPE + valid/positive predictions)* |
| **Robustness** | Gaussian noise · Missing values at inference · Unit-change invariance *(metamorphic)* · Training-order invariance *(metamorphic)* · **Edge-case inputs** · **Adversarial perturbation** |
| **Reliability** | Reproducibility · Train/test drift (PSI) · Prediction latency |
| **Fairness & Slices** | **Data-slice performance** · **Demographic parity difference** |

Each test returns **pass / warn / fail**, the measured value, the threshold, an evidence-based explanation and a recommended fix.
Results combine into a weighted 0–100 quality score, an A–F grade and the **deployment gate**
(accuracy/R² ≥ 85%, parity < 10%, every class detected, no leakage, reproducible).

## CI/CD
```bash
cd backend
python -m pytest tests -q                                   # automated test cases
python ci_check.py --dataset house_price --model gradient_boosting_reg --impute   # exit 1 = deployment blocked
```
GitHub Actions runs both on every push / pull request (`.github/workflows/ml-tests.yml`).

## Problem-solving (Auto-Fix) engine

1. **Pipeline repair** – imputation, de-duplication, constant & leaking feature removal, robust/standard scaling, class weights or oversampling, log-transform of skewed targets, removal of protected attributes that cause unfair predictions.
2. **Hyper-parameter tuning** – cross-validated randomised search with regularisation-friendly grids.
3. **Model search** – compares alternative algorithms by CV macro-F1 and switches if clearly better.

Stages 2–3 are kept only if the full test-suite score improves. The report shows a before/after comparison and a timeline of every change.

## Suggested demo flow for the presentation

1. **Dashboard** → click *House Price Prediction* (the project dataset); use Linear Regression → score ≈ 78, gate **BLOCKED**.
2. Open the failed tests (missing-value crash, edge cases) and the actual-vs-predicted table.
3. Open failed tests → show evidence & recommended fixes.
4. Click **Auto-fix** → score ≈ 85 (B); show the fix timeline and before/after table.
5. Repeat with *Credit Default* (leakage detection) and *Wine* (unscaled SVM: 61 → 98).
6. Upload your own CSV, show **History**, **Print** the report, and finish on **How it works**.

## API summary

`GET /api/datasets` · `POST /api/datasets` (CSV upload) · `GET /api/datasets/{id}/preview` · `GET /api/models` ·
`POST /api/runs` · `GET /api/runs` · `GET /api/runs/{id}` · `POST /api/runs/{id}/autofix` · `DELETE /api/runs/{id}` · `GET /api/stats`
(interactive docs at `/docs`).
