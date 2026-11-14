import c2

def pct(x): return f"{x * 100:.1f}%"

def build(B, D):
    R = D["runs"]; h = R["house_price"]; l = R["loan_approval"]
    B.h1("CONCLUSION AND FUTURE WORK")
    B.h2("8.1 Conclusion")
    B.p(f"This project designed, implemented and evaluated **Testrion**, a platform for automated software testing and problem solving of machine-learning models. The platform accepts any tabular CSV dataset, detects the task, trains one of twelve scikit-learn models and runs up to 24 automated tests in five categories. A deployment gate converts the results into an explicit decision, and a three-stage Auto-fix engine repairs the data pipeline, tunes the model and searches for a better algorithm, always verifying the result by re-running the full suite. A strict protocol keeps the hold-out test set out of every training, tuning and selection decision.")
    B.p(f"On the house-price dataset, the baseline linear regression scored {h['before']['score']:.1f} and was blocked by the gate; after Auto-fix the gradient-boosting model scored {h['after']['score']:.1f}, reached a hold-out R² of {h['after']['metrics']['r2']:.3f} and was approved. On the loan-approval file, removing protected attributes that caused a parity gap moved the score from {l['before']['score']:.1f} to {l['after']['score']:.1f}. On the Credit and Fraud files the platform detected target leakage and replaced an inflated accuracy with an honest one, and on the student-grades file it correctly refused to approve a model that could not reach the threshold. Measured on one Apple M5 laptop, the full suite processed one million records in 22 seconds with a linear model, one hundred models were tested concurrently in 41 seconds, and drift was detected on live predictions in 11 milliseconds.")
    B.p("These results indicate that integrating data validation, behavioural testing, fairness checks, a release gate, automatic repair and monitoring in one reproducible workflow is practical and fast enough for interactive use. They do not show that a passed gate guarantees correct behaviour in production, that demographic parity alone makes a model fair, or that the platform would give the same results on real datasets, since nine of the eleven datasets are synthetic. The GitHub Actions workflow and the Dockerfile are provided but were not executed on GitHub or in Docker from the development machine.")
    B.h2("8.2 Future Work")
    B.p("Several extensions would strengthen the work:")
    B.ol(["Evaluate the platform on real, publicly available datasets such as a real house-price or credit dataset, and report results with confidence intervals over repeated splits.",
          "Add further fairness definitions, such as equality of opportunity (equal true-positive rates) and calibration within groups, and let the user choose the criterion of the gate.",
          "Add more robustness tests, including distribution-shift scenarios, label noise and gradient-based adversarial attacks for models that expose gradients.",
          "Extend support to deep-learning, image, text and time-series models with suitable adapters and tests.",
          "Add explanation methods, such as SHAP values, to the report to help diagnose why a test failed.",
          "Harden the platform for multi-user deployment: password reset and e-mail verification, login rate limiting, a production web server and database, and sandboxing of uploaded models.",
          "Run the benchmark suite on larger machines and with tree ensembles at one million rows, and publish the measurements together with the hardware.",
          "Integrate the monitoring service with an alerting channel and with automatic retraining pipelines."])
    B.h1("REFERENCES", number=False)
    B.refs(c2.REFS)

    B.h1("DETAILED RESEARCH WORKFLOW")
    B.h2("9.1 Purpose of the Workflow")
    B.p("The workflow is organised so that data preparation, training, testing, scoring, repair and monitoring can be inspected independently. This matters because a change in preprocessing alters the model inputs, a change in the model alters every test, and a change in the thresholds alters the decision even when the model is unchanged. Reproducible experimentation therefore requires a stable configuration, a fixed random seed and a record of the artefacts produced at each stage. In Testrion each run stores its complete configuration (model, target, pipeline options, hyper-parameters, seed) inside the result, so any run can be repeated and any two runs can be compared.")
    B.p("A run starts with a validated dataset. The training portion is used to learn preprocessing statistics, which are then applied unchanged to the test portion. The model is trained, the tests are executed and the results are scored. If the user starts Auto-fix, the engine reads the failed tests of the stored run, creates a new configuration, trains and tests again and stores a second run that points to the first through its parent identifier, so the history shows exactly what was changed and why.")
    B.h2("9.2 Stage-by-Stage Processing")
    B.table("stages", "Stages of the Testrion processing workflow", ["Stage", "Input", "Purpose and output"], [
        ["1", "Uploaded or built-in dataset", "Validate the file, detect the task and check that the target is usable."],
        ["2", "Dataset table", "Drop rows with a missing target; sample at most 6,000 rows; drop identifier-like columns; apply repair options (de-duplication, constant and named columns)."],
        ["3", "Prepared table", "Split 75% / 25% with a fixed seed (stratified for classification)."],
        ["4", "Training portion", "Build the preprocessing pipeline and train the chosen model."],
        ["5", "Prepared table and model", "Run the data-quality tests on the cleaned data."],
        ["6", "Model and test portion", "Run model-performance tests (hold-out score, cross-validation inside the training portion, overfitting gap, worst-class recall or valid predictions)."],
        ["7", "Model and perturbed inputs", "Run robustness tests: noise, missing values, unit change, training order, edge cases, adversarial search."],
        ["8", "Model, repeat training", "Run reliability tests: reproducibility, train/test drift, latency."],
        ["9", "Predictions and protected attributes", "Run slice and fairness tests."],
        ["10", "All test results", "Compute the score, the grade and the deployment gate; compute metrics, feature importance and profile."],
        ["11", "Failed tests", "Auto-fix: repair, tune, search, re-run; store the fixed run and its comparison."],
        ["12", "Accepted model and live inputs", "Playground, logging and drift monitoring; model download."],
    ], [0.55, 2.0, 4.45], 9.5)
    B.h2("9.3 Reproducibility Principles")
    B.p("A reproduction should use the same project version, the same configuration stored in the run, the same dataset (the built-in datasets are generated by seeded code, and uploaded files are stored unchanged) and the same library versions listed in Chapter 5. All stochastic components use the fixed seed 42, and the reproducibility test verifies that two trainings give identical predictions. Timings and some floating-point details may differ between machines; the benchmark chapter therefore states the hardware.")
    B.p("This document separates three kinds of information. *Measured results* come from running the platform and are reproduced by the scripts described in Chapter 14. *Design statements* describe how the platform is built. *Interpretations and future work* are discussions that are not established by the measurements and are labelled as such.")

    B.h1("ALGORITHMIC DESCRIPTION AND PSEUDOCODE")
    B.h2("10.1 Sequence of a Test Run and of Auto-Fix")
    B.p("{F:sequence} shows the interaction between the browser, the server, the engines and the database when a test run is requested and then repaired. The browser sends the dataset identifier, the target and the model; the server checks ownership and task, calls the testing engine, stores the result and returns it. When the user presses Auto-fix, the server loads the stored run, calls the Auto-fix engine, which in turn calls the testing engine for every stage, and stores the fixed run.")
    B.fig("sequence", "fig_sequence.png", "Sequence of a test run followed by Auto-fix", 5.2)
    B.h2("10.2 Algorithm 1: Running the Test Suite")
    B.code("""run_suite(data, target, model, config):
    task <- detect_task(data, target); check model.task == task
    df, audit <- prepare(data, target, config)          # cap rows, drop ids, repair options
    train, test <- split(df, 75% / 25%, seed = 42)
    pipeline <- build_model(model, config)               # impute / scale / encode + estimator
    fit pipeline on train
    tests <- []
    tests += data_quality_tests(df)                      # missing, duplicates, balance/skew,
                                                         # constants, outliers, leakage, size
    tests += performance_tests(pipeline, train, test)    # hold-out, CV on train, gap, recall
    tests += robustness_tests(pipeline, train, test)     # noise, blanks, unit change, order,
                                                         # edge cases, adversarial
    tests += reliability_tests(pipeline, train, test)    # reproducibility, PSI, latency
    tests += slice_and_fairness_tests(test, audit)       # slices, demographic parity
    score <- weighted_score(tests); gate <- deployment_gate(tests)
    return {tests, score, grade, gate, metrics, profile, config}""")
    B.h2("10.3 Algorithm 2: Auto-Fix")
    B.code("""autofix(data, target, model, original):
    cfg <- original.config
    # Stage 1 - pipeline repair (always kept)
    for each failed or warned test in original.tests:
        apply the matching repair to cfg          # see the repair table in Chapter 3
    result <- run_suite(data, target, model, cfg)
    # Stage 2 - hyper-parameter search (kept only if validation score does not drop)
    if model-level tests still fail:
        params <- randomised_search(grid[model], cv = 3, on = train only, n_iter <= 8)
        candidate <- run_suite(data, target, model, cfg + params)
        if candidate.cv_score >= result.cv_score: result <- candidate
    # Stage 3 - algorithm search (kept only if validation score improves)
    if quality tests still fail:
        scores <- {m: cv_score(m, train only) for m in candidates[task]}
        best <- argmax(scores)
        if scores[best] > scores[model] + 0.01:
            candidate <- run_suite(data, target, best, cfg)
            if candidate.cv_score > result.cv_score: result, model <- candidate, best
    return result, steps, before_after_comparison""")
    B.h2("10.4 Algorithm 3: Edge-Case and Adversarial Tests")
    B.p("Five test rows are copied many times; in each copy one numeric column is set to its training minimum, maximum, zero, maximum plus ten ranges, or null, or one categorical column is set to an unseen category, special characters, an empty string or null. Rows that make the model raise an error or return a non-finite or implausible value count as failures. For the adversarial test, up to 250 test rows are perturbed eight times by adding to every numeric feature a random sign times ε times its training standard deviation (ε = 0.15, or 0.10 for regression); a row is stable if its class never changes (regression: never changes by more than 20%), and the fraction of stable rows is reported.")
    B.h2("10.5 Algorithm 4: Live Drift Monitoring")
    B.p("Every prediction is logged with its inputs and latency. A reference sample of up to 2,000 training rows is drawn; for each numeric feature eight quantile bins are formed from the reference data and the shares of reference and live values in each bin are compared (for categorical features, the category shares). The PSI of each feature (Equation 4.15) is compared with 0.10 and 0.25, and DRIFT DETECTED is reported when any feature exceeds 0.25 and at least 30 predictions are logged, together with the time taken to compute the verdict.")

    B.h1("METRIC DEFINITIONS AND NUMERICAL INTERPRETATION")
    B.h2("11.1 Confusion-Matrix Terms")
    B.p("The confusion matrix separates correct and incorrect predictions by class. For a binary problem, one class is chosen as positive. A true positive is a positive record predicted as positive, a false negative is a positive record predicted as negative, a true negative is a negative record predicted as negative, and a false positive is a negative record predicted as positive. In the customer-churn example below, \"Yes\" (the customer leaves) is the positive class ({T:cmterms}).")
    B.table("cmterms", "Interpretation of confusion-matrix outcomes for the churn model", ["Outcome", "Meaning", "Interpretation for churn"], [
        ["TP", "Churner predicted as churner", "A customer who would leave is identified and can be approached."],
        ["TN", "Stayer predicted as stayer", "A loyal customer is correctly left alone."],
        ["FP", "Stayer predicted as churner", "A retention offer is wasted on a loyal customer."],
        ["FN", "Churner predicted as stayer", "A customer who leaves is missed."],
    ], [0.9, 2.5, 3.6], 10)
    cm = R["churn"]["after"]["metrics"]["confusion_matrix"]; tn, fp, fn, tp = cm[0][0], cm[0][1], cm[1][0], cm[1][1]; n = tn + fp + fn + tp
    B.h2("11.2 Metric Calculation from the Recorded Counts")
    B.p(f"The recorded confusion matrix of the fixed churn model contains TN = {tn}, FP = {fp}, FN = {fn} and TP = {tp}, a total of {tn} + {fp} + {fn} + {tp} = {n} hold-out rows. The metrics follow directly:")
    B.eq(f"Accuracy = (TP + TN) / total = ({tp} + {tn}) / {n} = {(tp + tn) / n:.4f}", "(11.1)")
    B.eq(f"Precision = TP / (TP + FP) = {tp} / {tp + fp} = {tp / (tp + fp):.4f}", "(11.2)")
    B.eq(f"Recall = TP / (TP + FN) = {tp} / {tp + fn} = {tp / (tp + fn):.4f}", "(11.3)")
    B.eq(f"F1 = 2 · P · R / (P + R) = {2 * (tp / (tp + fp)) * (tp / (tp + fn)) / ((tp / (tp + fp)) + (tp / (tp + fn))):.4f}", "(11.4)")
    B.eq(f"False-positive rate = FP / (FP + TN) = {fp} / {fp + tn} = {fp / (fp + tn):.4f}", "(11.5)")
    B.p(f"The miss rate of the churner class is FN / (TP + FN) = {fn / (tp + fn) * 100:.1f}%. These values agree with the figures reported in Chapter 7 for the positive class. For regression the same principle applies: the hold-out errors of the house-price model are summarised by the RMSE, the MAE and the mean absolute percentage error, and the comparison table in the report lists actual and predicted prices row by row.")
    B.h2("11.3 Interpreting Metrics Together")
    B.p("No single metric captures the behaviour of a model. Accuracy is influenced by the class distribution: in the fraud file only about 7% of the transactions are fraudulent, so a model that never predicts fraud would be about 93% accurate, which is why the gate also checks the worst-class recall. Precision tells how reliable a positive prediction is, and recall tells how many of the real positives are found; a conservative model can have high precision and low recall. For regression, R² says how much of the variance is explained but not how large the errors are in real units, so the RMSE, the MAE and the percentage error are reported as well. The cross-validation score and the gap between training and test scores show whether the model is stable and whether it overfits.")
    B.h2("11.4 Limits of the Drift Statistic and of the Quality Score")
    B.p("The Population Stability Index is sensitive to the number of bins and to the sample size: on small samples it is noisy even without any real shift, which is why the thresholds of the train/test drift test grow with the expected noise level. It examines each feature separately and cannot detect a change in the relationship between the features and the target. The quality score is a convenient weighted summary, but it depends on the chosen weights; two models with the same score can have different weaknesses, and the deployment gate, not the score, makes the release decision.")
