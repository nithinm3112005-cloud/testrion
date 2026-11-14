import re, json

def pct(x): return f"{x * 100:.1f}%"

def build(B, D):
    R = D["runs"]; ev = D["evidence_md"]
    B.h1("TESTING STRATEGY AND VALIDATION RECORD")
    B.h2("12.1 Testing Goals")
    B.p("Two kinds of testing apply to this project. The first is the testing that Testrion performs on other people's models, described in Chapter 3. The second is the testing of Testrion itself: the platform must behave correctly, otherwise its verdicts cannot be trusted. This chapter records the second kind. It covers numerical correctness (scores, gates, parity and slice calculations), behavioural correctness of the repair engine, and the security properties of the interface. Passing these tests shows that the platform works as designed; it does not by itself show that every model verdict is right, which is why the evidence chapter reports measurements on datasets with known, injected problems.")
    B.h2("12.2 Automated Test Cases of the Platform")
    B.p("The repository contains an automated suite of eleven pytest tests in `backend/tests/test_ml_pipeline.py`, executed locally and, through the workflow, on every push. {T:pytests} lists them. All eleven tests passed on the development machine in about 27 seconds.")
    B.table("pytests", "Automated tests of the Testrion platform", ["Test", "What it verifies", "Status"], [
        ["test_house_price_model_passes_deployment_gate", "The production configuration of the house-price model is approved: gate APPROVED, R² ≥ 0.85, score ≥ 85.", "Passed"],
        ["test_predictions_are_positive_for_house_prices", "No predicted price is negative (valid-predictions test passes).", "Passed"],
        ["test_actual_vs_predicted_comparison_table_is_produced", "The report contains the actual, predicted, error and error-percentage columns.", "Passed"],
        ["test_engine_has_all_specified_test_types", "Edge-case, adversarial, slice, fairness, leakage and unit-change tests are present.", "Passed"],
        ["test_leakage_is_detected", "The leaking column of the credit data is flagged and named.", "Passed"],
        ["test_edge_cases_expose_missing_value_crashes", "The edge-case test fails without imputation and no longer fails with it.", "Passed"],
        ["test_fairness_detects_protected_attributes", "Gender, region and age are detected and evaluated, not skipped.", "Passed"],
        ["test_task_mismatch_is_rejected", "A classification model on a regression target is refused with an error.", "Passed"],
        ["test_autofix_improves_quality [churn]", "Auto-fix gives a higher score than the baseline on the churn data.", "Passed"],
        ["test_autofix_improves_quality [house price]", "Auto-fix gives a higher score than the baseline on the house-price data.", "Passed"],
        ["test_api_requires_login_and_isolates_users", "Unauthenticated calls are rejected; user B cannot read user A's runs.", "Passed"],
    ], [2.9, 3.4, 0.7], 9)
    B.h2("12.3 Metric Consistency Check")
    cm = R["churn"]["after"]["metrics"]["confusion_matrix"]
    B.p(f"The counts of the recorded confusion matrix of the fixed churn model ({cm[0][0]}, {cm[0][1]}, {cm[1][0]}, {cm[1][1]}) sum to the number of hold-out rows, and recalculating accuracy, precision, recall, F1 and the false-positive rate from them (Chapter 11) reproduces the values shown in the report to rounding. This is a consistency check of the recorded result, not an independent rerun of the training pipeline.")
    B.h2("12.4 Deployment-Gate Record in CI")
    g = json.load(open(__import__("os").path.dirname(__file__) + "/ci_good.json"))["summary"]; bd = json.load(open(__import__("os").path.dirname(__file__) + "/ci_bad.json"))["summary"]
    r2 = [c for c in g["gate"]["checks"] if "R²" in c["name"]][0]["value"]; dp = [c for c in g["gate"]["checks"] if "parity" in c["name"]][0]["value"]
    B.p(f"The command-line gate (`ci_check.py`) was run locally with the two configurations that matter for the workflow. For the house-price data with a gradient-boosting regressor and imputation and de-duplication switched on (the configuration used in the workflow) the gate reported {g['gate']['status']}: hold-out R² {r2}, demographic parity difference {dp}, no leakage and reproducible predictions, with a quality score of {g['score']} (grade {g['grade']}). For the raw linear-regression baseline the gate reported {bd['gate']['status']}, because the model crashes on blank values and on null edge-case inputs and its R² is below 0.85. The script exits with status 0 for an approved model and 1 for a blocked model, which is the behaviour the GitHub Actions workflow relies on: a blocked model makes the step, and therefore the workflow, fail. The workflow file itself has not been executed on GitHub from the development machine.")
    B.h2("12.5 Recommended Acceptance Criteria")
    B.p("A final validation record should identify the exact project version, the configuration and the dataset version, and should distinguish passed, failed, skipped and not-implemented checks. A check that has not been run must not be labelled as passed. Items not covered in this record are: the first execution of the workflow on GitHub, building and running the Docker image, tests on operating systems other than macOS, load tests with many simultaneous users, and a security review of a public deployment.")

    B.h1("THREAT MODEL AND SECURITY DISCUSSION")
    B.h2("13.1 Assets and Adversaries")
    B.p("Two sets of assets must be considered. For the platform, the assets are the user accounts, the uploaded datasets, the stored runs and trained models, and the integrity of the verdicts. For the models under test, the assets are the correctness, fairness and availability of their predictions. The adversaries considered are an unauthorised user trying to read another user's data, a user who uploads a malformed or hostile file, a data provider whose data contain leakage or bias, and a deployer whose model drifts away from the data it was trained on.")
    B.h2("13.2 Threats Considered")
    B.table("threats", "Threats and the current evidence", ["Threat", "Potential effect", "Mitigation and limitation"], [
        ["Unauthorised access to data", "One user reads or deletes another user's runs or datasets", "Token authentication and per-user filtering on every query; verified by an automated test. No rate limiting."],
        ["Credential theft or guessing", "Account takeover", "Salted PBKDF2 hashes (200,000 iterations), constant-time comparison, token expiry. No password policy beyond length, no lockout."],
        ["Malformed or oversized upload", "Crash or resource exhaustion", "CSV only, 10 MB limit, minimum size, parse errors reported; row cap per run."],
        ["Hostile model file", "Code execution when loading a pickle", "Models are produced by the platform itself; the documentation warns to load pickle files only from trusted sources. Uploaded models are not supported."],
        ["Target leakage in data", "Inflated accuracy, model fails in use", "Leakage test and repair; limited to single-feature leakage."],
        ["Biased outcomes", "Unequal treatment of groups", "Slice and demographic-parity tests; protected attributes removed by Auto-fix. Only one fairness criterion."],
        ["Data drift after release", "Silent degradation of predictions", "Live PSI monitoring with alerting status; no automatic retraining."],
        ["Adversarial inputs", "Prediction flips from small perturbations", "Random perturbation search; does not search worst-case perturbations."],
        ["Selection on the test set", "Over-optimistic reported accuracy", "Tuning and model choice use training-data cross-validation only; the test set is used for reporting."],
    ], [1.5, 2.1, 3.4], 9)
    B.h2("13.3 Testing Is Not a Complete Guarantee")
    B.p("A passed test shows the absence of one specific problem under one specific stress; it does not prove the absence of other problems. The thresholds are defaults from the specification. Random perturbation can miss rare worst cases, the leakage detector looks at one feature at a time and cannot find leakage that needs a combination of features, and demographic parity can be satisfied by a model that is unfair in another sense. The deployment gate should therefore be read as a necessary check before release and not as a certificate of correctness.")
    B.h2("13.4 Privacy and Integrity Are Different Goals")
    B.p("Testrion focuses on integrity and quality of models. It does not provide differential privacy or secure aggregation, and it does not claim to. Datasets uploaded by a user are stored unencrypted in the local project folder, so the machine that runs the platform must be protected like any other place that holds the data. Passwords are the only secrets stored, and they are stored as salted hashes.")
    B.h2("13.5 Deployment Boundary")
    B.p("The application was developed and tested locally on macOS and is designed for single-organisation use. It should not be described as a hardened public service without further work on rate limiting, password recovery, transport security (HTTPS termination), a production database and web server, resource limits, logging and monitoring of the platform itself, and a security review. The trust boundary lies between the browser, the API server, the Python engines, the dataset files and the exported model files.")

    B.h1("REPRODUCIBILITY, ARTIFACTS, AND VERSION CONTROL")
    B.h2("14.1 Project Artifacts")
    B.p("{T:artifacts} lists the files that allow the measurements in this document to be reproduced.")
    B.table("artifacts", "Project artifacts and their role in verification", ["Artifact", "Role"], [
        ["backend/app/*", "Source code of the engines, API and database layer."],
        ["backend/tests/test_ml_pipeline.py", "The eleven automated tests of the platform."],
        ["backend/ci_check.py", "Command-line deployment gate; exit code 0 (approved) or 1 (blocked); writes a JSON report."],
        ["backend/evidence.py and EVIDENCE.md", "Generator and output of the evidence tables and the performance benchmarks."],
        ["backend/streamlit_app.py", "Streamlit interface using the same engines."],
        ["demo_csv/make_demo_csv.py and the six CSV files", "Seeded generator and the demonstration datasets."],
        [".github/workflows/ml-tests.yml", "CI workflow run on every push and pull request."],
        ["Dockerfile, run.sh, README.md", "Container build (not executed on the development machine), one-command launcher and documentation."],
        ["SLIDE_CORRECTIONS.md", "Corrections for the earlier presentation slides."],
        ["report/", "The data collector, figure scripts, screenshots and the generator of this document."],
    ], [2.6, 4.4], 9.5)
    B.h2("14.2 Versioning Recommendations")
    B.p("The project folder contains a `.gitignore` that excludes virtual environments, node modules, compiled front-end files, the database and uploads. At the time of writing the folder has not been initialised as a Git repository, so the first step before submission is to initialise one, commit the current state and tag the version used for this report; the GitHub Actions workflow only becomes active after the repository is pushed to GitHub. The report should always refer to the tagged version, and a re-run of the benchmarks should write new files rather than overwrite the earlier evidence.")
    B.h2("14.3 Configuration Record")
    B.p("The configuration of the experiments is: random seed 42; 75% training and 25% hold-out split; 5-fold cross-validation for the cross-validation test and 3-fold cross-validation for tuning and model search; at most eight randomised-search candidates; 6,000-row cap per interactive run (2,000,000 for the benchmark); scoring weights 2.0, 1.5, 1.0, 1.0 and 1.5 for model performance, robustness, data quality, reliability and fairness; and the gate thresholds of 85% accuracy or R², 10% parity difference and 50% worst-class recall. These values are stored in the code and, for each run, in the run's configuration record.")
    B.h2("14.4 Reporting Changes")
    B.p("If a threshold, a test or a repair rule is changed, the change should be recorded together with its reason, and earlier results should not be overwritten. During this project, for example, the model-search stage was changed to use training-data cross-validation only, after a review showed that the earlier version had included the hold-out rows; the experiments reported here use the corrected version.")

    B.h1("ADDITIONAL RESULT TABLES")
    B.h2("15.1 Dataset Statistics")
    rows = []
    for k, d in D["datasets"].items():
        cls = ", ".join(f"{a}: {b}" for a, b in d["classes"].items()) if d.get("classes") else f"mean {d['target_stats']['mean']:.1f}, range {d['target_stats']['min']:.1f}–{d['target_stats']['max']:.1f}"
        rows.append([d["name"].replace(".csv", ""), f'{d["rows"]:,}', f'{d["missing_pct"]:.1f}%', str(d["duplicates"]), cls])
    B.table("dsstats", "Rows, missing cells, duplicate rows and target distribution of every dataset", ["Dataset", "Rows", "Missing cells", "Duplicates", "Target distribution"], rows, [1.7, 0.6, 0.85, 0.8, 3.05], 9)
    B.h2("15.2 Per-Class Metrics of Fixed Classification Runs")
    B.p("{T:perclass} lists precision, recall and F1-score of each class for the fixed runs of the classification datasets on their hold-out rows.")
    rows = []
    for key in ("iris", "wine", "churn", "credit", "loan_approval", "fraud_transactions", "student_grades", "quick_small_test"):
        r = R[key]; m = r["after"]["metrics"]
        for p in m["per_class"]:
            rows.append([r["name"].replace(".csv", ""), str(p["class"]), f'{p["precision"]:.3f}', f'{p["recall"]:.3f}', f'{p["f1"]:.3f}', str(p["support"])])
    B.table("perclass", "Per-class precision, recall and F1-score of the fixed classification runs", ["Dataset", "Class", "Precision", "Recall", "F1-score", "Rows"], rows, [1.9, 1.3, 0.9, 0.9, 0.9, 0.6], 8.5, ["left", "left", "center", "center", "center", "center"])
    B.h2("15.3 Repairs Applied to Every Dataset")
    rows = []
    for key, r in R.items():
        rows.append([r["name"].replace(".csv", ""), "; ".join(s["title"].replace("Switched model to ", "Model → ") for s in r["steps"]) or "none"])
    B.table("allsteps", "Automatic repairs applied by the Auto-fix engine to each dataset", ["Dataset", "Repairs"], rows, [1.7, 5.3], 8.5)
    B.h2("15.4 Comparison Caveats")
    B.p("The tables in this document compare a baseline run with a repaired run of the same dataset. Both are measured on the same hold-out rows, so the comparison is fair for that dataset, but the numbers are not comparable across datasets: the synthetic datasets differ in noise, size and injected problems. The accuracy of a fixed run can be lower than that of its baseline when the baseline benefited from leakage or overfitting (the churn, credit and fraud files); the quality score and the gate, not the accuracy alone, describe whether the model became better.")
