def fmt(v):
    if abs(v) >= 1000: return f"{v:,.0f}"
    if abs(v) >= 100: return f"{v:.1f}"
    return f"{v:.2f}".rstrip("0").rstrip(".") if v != int(v) else str(int(v))

def colrows(D, key, docs=True, compact=False):
    ds = D["datasets"][key]; cd = D.get("column_docs", {}).get(key, {}); rows = []
    for c in ds["columns"]:
        if c["type"] == "numeric": rng = f'{fmt(c["min"])} – {fmt(c["max"])} (mean {fmt(c["mean"])})'
        else: rng = ", ".join(c["top"].keys()) + (", …" if c["unique"] > len(c["top"]) else "")
        row = [c["name"] + (" (target)" if c["target"] else ""), c["type"]] + ([] if compact else [str(c["missing"]) if c["missing"] else "–", str(c["unique"])]) + [rng]
        if docs: row.append(cd.get(c["name"], ""))
        rows.append(row)
    return rows

def build(B, D):
    ds = D["datasets"]
    B.h1("METHODOLOGY AND PROPOSED SYSTEM")
    B.p("This chapter explains the workflow implemented in Testrion. The pipeline starts with a dataset, validates it and detects the task, prepares the data with a protected hold-out split, trains the chosen model, executes the automated test suite, converts the outcomes into a score and a deployment decision, and, when requested, diagnoses and repairs the problems before re-testing. A separate monitoring component watches live predictions after release. The chapter also describes in detail every dataset used in the project.")
    B.h2("3.1 System Workflow")
    B.p("The workflow of a single run is shown in {F:workflow}. The user supplies a CSV file or selects a built-in sample, chooses the target column and the model, and optionally switches on pipeline options such as imputation, scaling or class balancing. The server validates the request, detects the task, prepares the data and trains the model. The test suite then evaluates data quality, model performance, robustness, reliability and fairness. The results are stored in the database, shown in the web interface and used to compute the deployment decision. If problems exist, the Auto-fix engine produces a second run in which the repairs were applied, and both runs are kept so they can be compared.")
    B.fig("workflow", "fig_workflow.png", "End-to-end Testrion workflow", 5.5)
    B.h2("3.2 Datasets Used")
    B.p("The project uses eleven datasets: five built into the application and six demonstration CSV files that are uploaded through the interface. Two of them (Iris and Wine) are real public datasets distributed with scikit-learn [17], [27], [28]; the other nine are synthetic datasets produced by seeded generators in the project code, so every run is reproducible. Synthetic data was chosen deliberately: it allows realistic problems (missing values, duplicates, outliers, class imbalance, leakage, biased groups) to be injected in known amounts, so that the platform's ability to find and repair them can be demonstrated and verified. This also means that the accuracy figures reported in this document describe the behaviour of the platform on these datasets and must not be read as the expected accuracy of a real application. {T:ds_overview} summarises all eleven datasets.")
    rows = []
    desc = {"house_price": "Regression; the project's demonstration dataset; missing values, duplicates, outliers", "iris": "Clean three-class benchmark", "wine": "Three classes, unscaled features",
            "churn": "Missing values, duplicates, imbalance, constant column", "credit": "Imbalance, missing income, leakage column, protected attributes",
            "used_car_prices": "Regression; missing values, duplicates, outliers", "energy_consumption": "Clean regression", "loan_approval": "Fairness: gender, age, region; biased outcomes",
            "student_grades": "Hard, noisy three-class problem", "fraud_transactions": "Leakage, severe imbalance, duplicates", "quick_small_test": "Tiny file for a quick smoke test"}
    for k, d in ds.items():
        rows.append([d["name"], "Real" if "real" in d["source"] else "Synthetic", d["task"].capitalize(), f'{d["rows"]:,}', str(d["cols"]), d["target"], desc[k]])
    B.table("ds_overview", "Overview of the eleven datasets used in the project", ["Dataset", "Origin", "Task", "Rows", "Cols", "Target", "Purpose / built-in problems"], rows, [1.55, 0.7, 0.85, 0.55, 0.4, 0.95, 2.1], 9)

    h = ds["house_price"]
    B.h3("3.2.1 House Price Prediction (primary dataset)")
    B.p(f"The house-price dataset is the demonstration dataset named in the project specification. It is a synthetic regression dataset of {h['rows']:,} rows and {h['cols']} columns in which the price of a house, in lakhs of rupees, is predicted from its area, the number of bedrooms and bathrooms, the year of construction, the distance to the city centre, the number of garage spaces, the region of the city and the property type. The price is generated from a base value that grows with area, rooms, garage spaces and newness and falls with distance from the city, multiplied by a regional factor (the West and Central regions are more expensive) and a property-type factor (villas cost more than apartments), and then a small log-normal noise term is applied. The target has a mean of {h['target_stats']['mean']:.1f} lakhs, a median of {h['target_stats']['median']:.1f}, a range of {h['target_stats']['min']:.1f} to {h['target_stats']['max']:.1f} and a skewness of {h['target_stats']['skew']:.2f}.")
    B.p(f"The generator injects realistic data problems on purpose: missing values in the area (5%), distance (6%) and region (3%) columns, which gives {h['missing_cells']} missing cells in total ({h['missing_pct']:.1f}% of all cells); twelve data-entry outliers in which the area is several times too large; and {h['duplicates']} duplicated rows. These are exactly the problems that the automated tests detect and the Auto-fix engine repairs. {{T:ds_house}} is the data dictionary.")
    B.table("ds_house", "Data dictionary of the House Price Prediction dataset", ["Column", "Type", "Range / values", "Meaning"], colrows(D, "house_price", True, True), [1.3, 0.8, 1.75, 3.15], 8.5)
    B.h3("3.2.2 Iris Flowers")
    B.p(f"Iris is the classic multi-class benchmark introduced by Fisher in 1936 [27] and distributed through the UCI repository [28] and scikit-learn. It contains {ds['iris']['rows']} flowers, four numeric measurements (sepal length and width, petal length and width) and a balanced three-class target (setosa, versicolor, virginica; 50 flowers each). It contains one duplicated row and no missing values. In this project it serves as a clean, small, real dataset on which the platform is expected to report few problems, and it shows that Auto-fix does not invent improvements where none are needed.")
    B.h3("3.2.3 Wine Cultivars")
    B.p(f"The Wine dataset records 13 chemical measurements (for example alcohol, malic acid, flavanoids, colour intensity and proline) for {ds['wine']['rows']} wines grown by three cultivars [28]. The classes are moderately imbalanced (71, 59 and 48 wines). The features are measured on very different scales (proline is in the hundreds while hue is near one), which makes the dataset a good test of scale sensitivity: distance-based and kernel models such as support-vector machines perform poorly on the raw values and well after standardisation.")
    B.h3("3.2.4 Customer Churn")
    c = ds["churn"]
    B.p(f"The customer-churn dataset is a synthetic binary classification problem with {c['rows']:,} rows and {c['cols']} columns in which the target says whether a telecom customer leaves (Yes) or stays (No). Churn probability rises for month-to-month contracts, short tenure, high monthly charges, many support calls and fibre internet service. The dataset is imbalanced (about {c['classes']['Yes'] / c['rows'] * 100:.0f}% churners), contains {c['missing_cells']} missing cells, {c['duplicates']} duplicated rows, a constant column (`country_code`) and a feature on a very large scale (`total_charges`). It is therefore a compact example of a messy business dataset ({{T:ds_churn}}).")
    B.table("ds_churn", "Data dictionary of the Customer Churn dataset", ["Column", "Type", "Range / values", "Meaning"], colrows(D, "churn", True, True), [1.3, 0.8, 1.75, 3.15], 8.5)
    B.h3("3.2.5 Credit Default")
    cr = ds["credit"]
    B.p(f"The credit-default dataset has {cr['rows']:,} rows and {cr['cols']} columns and predicts whether a borrower defaults (about {cr['classes']['Default'] / cr['rows'] * 100:.0f}% do). Default probability depends on the debt ratio, the number of late payments, income and age. Two features are deliberately problematic. The column `collections_flag` is set after a customer has defaulted and therefore reveals the answer: it is a textbook case of target leakage [9]. The columns `gender`, `region` and `age` are personal attributes, which the platform treats as protected attributes and audits for fairness ({{T:ds_credit}}).")
    B.table("ds_credit", "Data dictionary of the Credit Default dataset", ["Column", "Type", "Range / values", "Meaning"], colrows(D, "credit", True, True), [1.3, 0.8, 1.75, 3.15], 8.5)
    B.fig("classdist", "fig_classdist.png", "Class distribution of the three imbalanced classification datasets", 5.4)
    B.h3("3.2.6 Demonstration CSV Files")
    B.p("Six additional CSV files, stored in the `demo_csv` folder of the project and regenerated by the script `make_demo_csv.py`, are provided for uploading through the interface. They differ in task, size and built-in problems so that every part of the platform can be exercised ({T:ds_demo}).")
    demo = [
        ["used_car_prices.csv", "1,535 × 9", "Regression", "price_lakhs", "Brand, fuel, transmission, year, kilometres, owners, engine size, region. Missing values, duplicates, outliers, skewed price."],
        ["energy_consumption.csv", "1,200 × 7", "Regression", "energy_kwh", "Temperature, humidity, occupancy, hour, weekend, floor area. Clean data with a nearly linear relationship."],
        ["loan_approval.csv", "2,200 × 9", "Classification", "approved", "Age, gender, region, income, loan amount, credit score, employment years, existing loans. Deliberate bias against rural applicants and one gender; missing income."],
        ["student_grades.csv", "900 × 8", "Classification (3 classes)", "grade_band", "Study hours, attendance, previous score, sleep, internet access, parental support, gender. Noisy; no model reaches 85% accuracy."],
        ["fraud_transactions.csv", "3,060 × 9", "Classification", "is_fraud", "Amount, hour, distance from home, merchant category, channel, account age, currency. Leaking `chargeback_flag`, about 7% fraud, duplicates, a constant column."],
        ["quick_small_test.csv", "120 × 4", "Classification", "label", "Two numeric features and one colour column; a five-second smoke test."],
    ]
    B.table("ds_demo", "The six demonstration CSV files", ["File", "Size", "Task", "Target", "Content and built-in problems"], demo, [1.5, 0.75, 0.95, 0.85, 2.9], 9)
    B.h3("3.2.7 Dataset Handling in the Application")
    B.ul(["The Datasets page lists every dataset with its origin (real, synthetic or uploaded), size and tags, and offers a preview with a data dictionary and a CSV download.",
          "Uploaded files must be CSV, at most 10 MB, with at least 20 rows and 2 columns. Each uploaded file belongs to one user and is never shown to others.",
          "The target selector marks which columns are valid targets: a column with 2 to 30 categories is a classification target, and a numeric column with more than 20 distinct values is a regression target; other columns are disabled.",
          "Columns that look like identifiers (text columns with more than 50 distinct values that are also more than 30% of the rows) are dropped automatically and reported.",
          "Interactive runs use at most 6,000 randomly sampled rows so that results appear within seconds; the limit can be raised for benchmarking."])
    B.h2("3.3 Data Preprocessing")
    B.p("Preprocessing is implemented as a scikit-learn `ColumnTransformer` placed in front of the model, so that exactly the same transformation is applied during training, testing, prediction and export. Numeric columns can pass through an optional median imputer and an optional scaler (standardisation or a robust median/IQR scaler). Categorical columns can pass through an optional most-frequent imputer and are always one-hot encoded, with unseen categories ignored at prediction time. When imputation is switched off, rows containing missing values are dropped before training, which is the naive behaviour that the tests are designed to expose. All preprocessing statistics are learned on the training portion only.")
    B.p("Additional data-preparation options, which the Auto-fix engine can switch on, are removal of duplicate rows, removal of constant columns, removal of named columns (for example a leaking or protected column, which is still kept aside so it can be audited), balancing of classes by class weights or random oversampling, and a log(1+y) transformation of a skewed non-negative regression target.")
    B.h2("3.4 Data Splitting and Validation Protocol")
    B.p("Every model is evaluated with a strict three-part protocol, shown in {F:split}. The prepared rows are divided into a 75% training portion and a 25% hold-out test portion with a fixed random seed (stratified by class for classification). The test portion is never used to fit a model, to tune a hyper-parameter or to choose between algorithms. The *validation* score is obtained by k-fold cross-validation inside the training portion only [19], and it is the only score the Auto-fix engine uses to decide whether a tuning or model change is kept. The test portion is used for the final report and for the tests that need unseen data. After evaluation, the exported model (`model.pkl`) and the playground model are re-trained on all rows, as is standard practice before deployment.")
    B.fig("split", "fig_split.png", "Data-splitting and validation protocol", 5.2)
    B.p("One detail deserves mention. The diagnosis of problems (which tests failed) is read from the test results, which include test-set measurements such as the overfitting gap. The selection of hyper-parameters and algorithms, however, depends on validation scores only, so the hold-out set cannot be overfitted through model selection.")
    B.h2("3.5 Feature Representation")
    B.p("Features are the columns of the CSV file other than the target. Numeric features are used as they are (optionally imputed and scaled); categorical features are expanded into binary indicator columns. The number of encoded features therefore depends on the cardinality of the categorical columns. Protected attributes such as gender, age and region are detected from column names: a column whose name contains a token such as `gender`, `sex`, `age`, `region`, `race`, `religion`, `caste` or `marital` is audited, except where the name shows that it describes an object or a duration (for example `account_age_days` or `floor_area_sqft`). The user can mark any other column as protected in the advanced options. Numeric protected attributes such as age are divided into three quantile bands for slicing.")
    B.h2("3.6 Proposed System Architecture")
    B.p("The system consists of a React web application, a FastAPI server, a testing engine, an Auto-fix engine, a model registry and a SQLite database, with an optional Streamlit interface and a GitHub Actions workflow around them. The detailed architecture, the modules, the database schema and the API are described in Chapter 5, and the architecture is shown in {F:architecture}. The important design decision is that the testing engine and the Auto-fix engine are ordinary Python modules that do not depend on the web server, so the same code runs in the web application, in the command-line gate, in the pytest suite and in the Streamlit interface.")
    B.h2("3.7 Automated Test Suite")
    B.p("The suite contains 23 tests for classification and 24 for regression, organised in five categories. Each test returns a status (passed, warning, failed or skipped), the measured value, the threshold, an evidence-based explanation and a recommended fix. {T:suite} lists the tests and their thresholds; tests that exist only for one task are marked.")
    suite = [
        ["Data Quality", "Missing values handled", "Pass if no gaps or imputation is on; warning up to 5% missing; otherwise fail"],
        ["Data Quality", "Duplicate rows", "Pass ≤ 0.5%; warning ≤ 3%"],
        ["Data Quality", "Class balance (classification) / Target distribution skew (regression)", "Minority/majority ratio ≥ 0.5 (pass), ≥ 0.2 (warning), or mitigated by balancing; |skewness| ≤ 1 (pass), ≤ 2.5 (warning)"],
        ["Data Quality", "Constant features", "Warning if any column has one value"],
        ["Data Quality", "Outlier exposure", "Share of values with |z| > 4: pass ≤ 1%, warning ≤ 4%; tree models and robust scaling are insensitive"],
        ["Data Quality", "Target leakage", "Fail if one feature alone gives balanced accuracy ≥ 0.96 (regression: |r| ≥ 0.98)"],
        ["Data Quality", "Sufficient sample size", "Fail below 50 rows; pass ≥ 10 rows per feature; warning ≥ 5"],
        ["Model Performance", "Hold-out macro F1 (classification) / Hold-out R² (regression)", "Pass ≥ 0.85; warning ≥ 0.70"],
        ["Model Performance", "Mean absolute % error (regression)", "Pass ≤ 15%; warning ≤ 25%"],
        ["Model Performance", "k-fold cross-validation", "Validation score on training data: pass ≥ 0.85; warning ≥ 0.70"],
        ["Model Performance", "Cross-validation stability", "Standard deviation across folds: pass ≤ 0.03; warning ≤ 0.07"],
        ["Model Performance", "Overfitting gap", "Train score − test score: pass ≤ 0.05; warning ≤ 0.12"],
        ["Model Performance", "Worst-class recall (classification) / Valid predictions (regression)", "Recall: pass ≥ 70%, warning ≥ 50%; predictions must be finite and non-negative for a non-negative target"],
        ["Robustness", "Gaussian noise", "10% of each feature's standard deviation added; score drop ≤ 0.05 (pass), ≤ 0.10 (warning)"],
        ["Robustness", "Missing values at inference", "10% of numeric cells blanked; a crash fails; drop ≤ 0.08 (pass), ≤ 0.20 (warning)"],
        ["Robustness", "Unit-change invariance (metamorphic)", "Features rescaled by factors 1000, 0.001, 10, 100 and model re-trained; agreement ≥ 97% (pass), ≥ 90% (warning)"],
        ["Robustness", "Training-order invariance (metamorphic)", "Training rows shuffled and model re-trained; agreement ≥ 97% (pass), ≥ 90% (warning)"],
        ["Robustness", "Edge-case inputs (generated)", "Minimum, maximum, zero, 10× range, null, unseen category, special characters, empty string; handled ≥ 99% (pass), ≥ 90% (warning)"],
        ["Robustness", "Adversarial perturbation", "Eight random-sign perturbations of ±15% std (±10% for regression); stable rows ≥ 90% (pass), ≥ 75% (warning)"],
        ["Reliability", "Reproducibility", "Two trainings with the same seed must give identical predictions"],
        ["Reliability", "Train/test drift (PSI)", "Largest PSI ≤ max(0.10, 3× expected noise); warning up to max(0.25, 6× expected noise)"],
        ["Reliability", "Prediction latency", "Time for 1,000 predictions: pass ≤ 150 ms; warning ≤ 600 ms"],
        ["Fairness & Slices", "Data-slice performance", "Accuracy gap between slices ≤ 10 points (pass), ≤ 20 (warning); regression: extra % error ≤ 8 / 15 points"],
        ["Fairness & Slices", "Demographic parity difference", "Gap in predicted-outcome rate between groups < 10% (pass); otherwise fail"],
    ]
    B.table("suite", "The automated tests, their categories and thresholds", ["Category", "Test", "Pass / warning / fail rule"], suite, [1.2, 2.3, 3.5], 9)
    B.p("Four of these tests implement requirements named in the project specification and are described in more detail below.")
    B.p("**Edge-case generation.** For up to eight numeric columns the test builds copies of five test rows in which one column at a time is replaced by its training minimum, its maximum, zero, a value ten ranges beyond the maximum, or a null value; for up to four categorical columns it substitutes an unseen category, a string of special characters (including quotes and markup), an empty string or a null. The model is asked to predict all of these rows; a crash, a non-finite value or a regression value far outside the plausible range counts as a failure.")
    B.p("**Adversarial perturbation.** A random sample of up to 250 test rows is perturbed eight times; in each perturbation every numeric feature moves up or down by a random sign times a fixed fraction of that feature's training standard deviation. A row is stable if its prediction (class, or value within 20% for regression) never changes. The fraction of stable rows is the score.")
    B.p("**Data-slice testing.** The test set is split by each protected attribute (or, when none is found, by up to two low-cardinality categorical columns), the accuracy or the percentage error is computed per slice with at least 15 rows, and the spread between slices is compared with the threshold.")
    B.p("**Demographic parity.** For classification the parity difference of a protected attribute is the largest, over predicted classes, of the gap between the highest and lowest rate at which the class is predicted in a group. For regression, where outcomes are numbers, the corresponding measure is the group bias, |mean prediction − mean actual| divided by the mean actual value, taken per group. The attribute with the worst value is reported.")
    B.h2("3.8 Scoring and Deployment Gate")
    B.p("Each test contributes one point when passed, half a point as a warning and none when failed; skipped tests are ignored. The category scores are combined with weights of 2.0 for Model Performance, 1.5 for Robustness and for Fairness & Slices, and 1.0 for Data Quality and for Reliability, giving a quality score from 0 to 100 and a grade (A ≥ 90, B ≥ 80, C ≥ 70, D ≥ 55, otherwise F). The score is a convenient summary; the release decision is made by the **deployment gate**, which is independent of the score ({F:gate}).")
    B.fig("gate", "fig_gate.png", "Logic of the deployment gate", 5.0)
    B.p("The gate requires: (1) hold-out accuracy of at least 85% for classification or hold-out R² of at least 0.85 for regression, because accuracy is not a regression metric and R² is its natural equivalent; (2) a demographic parity difference below 10% whenever a protected attribute is present and large enough to evaluate; (3) for classification, a worst-class recall that is not a failure, so that a model cannot be approved merely because it predicts the majority class; (4) no target leakage; and (5) reproducible predictions. If any check fails, the gate reports BLOCKED and names the check; otherwise it reports APPROVED.")
    B.h2("3.9 Auto-Fix Engine")
    B.p("The Auto-fix engine is the problem-solving part of the platform. It reads the failed and warning tests of a run, applies the matching repairs, re-runs the full suite and reports exactly what changed ({F:autofix}). It works in three stages. **Stage 1** repairs the data pipeline and is always kept, because it removes real defects: {T:repairs} lists the mapping from failed tests to repairs. **Stage 2** tunes hyper-parameters with a randomised search over a small regularisation-friendly grid, using at most eight candidates and three-fold cross-validation on the training portion only [18]; the result is kept only if the validation score does not decrease. **Stage 3** compares alternative algorithms by cross-validated score on the training portion (logistic regression, random forest and gradient boosting, plus a support-vector machine for small data, for classification; ridge regression, random forest and gradient boosting for regression) and switches only if a candidate is clearly better and the validation score of the new run improves.")
    B.fig("autofix", "fig_autofix.png", "Stages of the Auto-fix problem-solving engine", 5.3)
    rep = [
        ["Target leakage", "Remove the leaking column(s) from the features"],
        ["Missing values, missing inputs, edge cases", "Median imputation for numeric and most-frequent imputation for categorical columns"],
        ["Duplicate rows", "Drop duplicate rows before splitting"],
        ["Constant features", "Drop constant columns"],
        ["Class imbalance, weak class recall", "Class weights, or random oversampling for models without class weights"],
        ["Target skew, invalid (negative) predictions", "Train on log(1 + y) and map predictions back (non-negative targets only)"],
        ["Outliers", "Robust (median/IQR) scaling"],
        ["Unit-change sensitivity, scale-sensitive model", "Standardisation (z-score scaling) for non-tree models"],
        ["Failed fairness test", "Remove protected attributes from the features (they are still audited)"],
        ["Overfitting, instability, weak quality", "Randomised hyper-parameter search, then algorithm search"],
    ]
    B.table("repairs", "Mapping from failed tests to automatic repairs", ["Failed or warned test", "Automatic repair"], rep, [2.7, 4.3], 9.5)
    B.h2("3.10 Live Monitoring")
    B.p("After a model is accepted, it can be used through the prediction playground or the API. Every prediction is logged with its inputs, output and latency. The monitoring service compares the logged inputs with a reference sample of the training data using the Population Stability Index for each feature [15], [16]. A feature with PSI below 0.10 is stable, between 0.10 and 0.25 is a warning and above 0.25 indicates drift; the overall status becomes DRIFT DETECTED when any feature exceeds 0.25 and at least 30 predictions have been logged. For demonstration the service can replay training-like traffic, normal or deliberately shifted, through the live model. The monitoring page also reports the average and 95th-percentile prediction latency and the time taken to compute the drift verdict.")
    B.h2("3.11 CI/CD Integration")
    B.p("The repository contains a GitHub Actions workflow that is triggered on every push and pull request [34]. It installs the dependencies on Ubuntu 22.04 with Python 3.10, runs the 11 pytest tests, runs the command-line deployment gate on the house-price model with imputation and de-duplication enabled, and uploads the JSON test report as an artefact. The gate script exits with status 1 when the gate is blocked, which makes the workflow fail, so that a model or a code change that breaks the acceptance conditions cannot pass unnoticed. Chapter 12 lists the automated tests that protect the platform itself.")
