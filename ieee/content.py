"""IEEE paper content (single source for the PDF and the Word file)."""
import json, re
D = json.load(open("../report/build/report_data.json"))
R = D["runs"]
ORDER = ["house_price", "iris", "wine", "churn", "credit", "used_car_prices", "energy_consumption", "loan_approval", "student_grades", "fraud_transactions", "quick_small_test"]
SHORT = {"house_price": "House price", "iris": "Iris", "wine": "Wine", "churn": "Customer churn", "credit": "Credit default", "used_car_prices": "Used-car prices",
         "energy_consumption": "Energy consumption", "loan_approval": "Loan approval", "student_grades": "Student grades", "fraud_transactions": "Fraud transactions", "quick_small_test": "Quick small test"}
MODEL = {"linear_regression": "Linear Reg.", "gradient_boosting_reg": "Grad. Boosting", "decision_tree": "Decision Tree", "svm": "SVM", "random_forest": "Random Forest",
         "logistic_regression": "Logistic Reg.", "knn": "KNN", "gradient_boosting": "Grad. Boosting"}
mb = sum(R[k]["before"]["score"] for k in ORDER) / 11; ma = sum(R[k]["after"]["score"] for k in ORDER) / 11
blocked_b = [k for k in ORDER if R[k]["before"]["gate"]["status"] == "BLOCKED"]; blocked_a = [k for k in ORDER if R[k]["after"]["gate"]["status"] == "BLOCKED"]
improved = [k for k in ORDER if R[k]["after"]["score"] > R[k]["before"]["score"]]
maxdur = max(R[k][s]["duration"] for k in ORDER for s in ("before", "after"))
def prim(k, s):
    m = R[k][s]["metrics"]; return m["r2"] if m["task"] == "regression" else m["accuracy"]

REFS = {  # key -> IEEE reference text (<i> for italics); numbered by first citation
 "breck": "E. Breck, S. Cai, E. Nielsen, M. Salib, and D. Sculley, “The ML test score: A rubric for ML production readiness and technical debt reduction,” in <i>Proc. IEEE Int. Conf. Big Data</i>, 2017, pp. 1123–1132.",
 "sculley": "D. Sculley <i>et al.</i>, “Hidden technical debt in machine learning systems,” in <i>Proc. Adv. Neural Inf. Process. Syst. (NIPS)</i>, vol. 28, 2015, pp. 2503–2511.",
 "amershi": "S. Amershi <i>et al.</i>, “Software engineering for machine learning: A case study,” in <i>Proc. IEEE/ACM 41st Int. Conf. Softw. Eng.: Softw. Eng. Pract. (ICSE-SEIP)</i>, 2019, pp. 291–300.",
 "zhang": "J. M. Zhang, M. Harman, L. Ma, and Y. Liu, “Machine learning testing: Survey, landscapes and horizons,” <i>IEEE Trans. Softw. Eng.</i>, vol. 48, no. 1, pp. 1–36, 2022.",
 "chen": "T. Y. Chen <i>et al.</i>, “Metamorphic testing: A review of challenges and opportunities,” <i>ACM Comput. Surv.</i>, vol. 51, no. 1, Art. 4, 2018.",
 "xie": "X. Xie, J. W. K. Ho, C. Murphy, G. Kaiser, B. Xu, and T. Y. Chen, “Testing and validating machine learning classifiers by metamorphic testing,” <i>J. Syst. Softw.</i>, vol. 84, no. 4, pp. 544–558, 2011.",
 "ribeiro": "M. T. Ribeiro, T. Wu, C. Guestrin, and S. Singh, “Beyond accuracy: Behavioral testing of NLP models with CheckList,” in <i>Proc. 58th Annu. Meeting Assoc. Comput. Linguistics</i>, 2020, pp. 4902–4912.",
 "breckdata": "E. Breck, N. Polyzotis, S. Roy, S. E. Whang, and M. Zinkevich, “Data validation for machine learning,” in <i>Proc. Conf. Syst. Mach. Learn. (SysML)</i>, 2019.",
 "kaufman": "S. Kaufman, S. Rosset, C. Perlich, and O. Stitelman, “Leakage in data mining: Formulation, detection, and avoidance,” <i>ACM Trans. Knowl. Discov. Data</i>, vol. 6, no. 4, Art. 15, 2012.",
 "goodfellow": "I. J. Goodfellow, J. Shlens, and C. Szegedy, “Explaining and harnessing adversarial examples,” in <i>Proc. Int. Conf. Learn. Represent. (ICLR)</i>, 2015.",
 "hardt": "M. Hardt, E. Price, and N. Srebro, “Equality of opportunity in supervised learning,” in <i>Proc. Adv. Neural Inf. Process. Syst. (NIPS)</i>, vol. 29, 2016.",
 "dwork": "C. Dwork, M. Hardt, T. Pitassi, O. Reingold, and R. Zemel, “Fairness through awareness,” in <i>Proc. 3rd Innov. Theor. Comput. Sci. Conf. (ITCS)</i>, 2012, pp. 214–226.",
 "feldman": "M. Feldman, S. A. Friedler, J. Moeller, C. Scheidegger, and S. Venkatasubramanian, “Certifying and removing disparate impact,” in <i>Proc. 21st ACM SIGKDD Int. Conf. Knowl. Discov. Data Mining</i>, 2015, pp. 259–268.",
 "mehrabi": "N. Mehrabi, F. Morstatter, N. Saxena, K. Lerman, and A. Galstyan, “A survey on bias and fairness in machine learning,” <i>ACM Comput. Surv.</i>, vol. 54, no. 6, Art. 115, 2021.",
 "gama": "J. Gama, I. Žliobaitė, A. Bifet, M. Pechenizkiy, and A. Bouchachia, “A survey on concept drift adaptation,” <i>ACM Comput. Surv.</i>, vol. 46, no. 4, Art. 44, 2014.",
 "siddiqi": "N. Siddiqi, <i>Credit Risk Scorecards: Developing and Implementing Intelligent Credit Scoring</i>. Hoboken, NJ, USA: Wiley, 2006.",
 "pedregosa": "F. Pedregosa <i>et al.</i>, “Scikit-learn: Machine learning in Python,” <i>J. Mach. Learn. Res.</i>, vol. 12, pp. 2825–2830, 2011.",
 "bergstra": "J. Bergstra and Y. Bengio, “Random search for hyper-parameter optimization,” <i>J. Mach. Learn. Res.</i>, vol. 13, pp. 281–305, 2012.",
 "kohavi": "R. Kohavi, “A study of cross-validation and bootstrap for accuracy estimation and model selection,” in <i>Proc. 14th Int. Joint Conf. Artif. Intell. (IJCAI)</i>, 1995, pp. 1137–1143.",
 "breiman": "L. Breiman, “Random forests,” <i>Mach. Learn.</i>, vol. 45, no. 1, pp. 5–32, 2001.",
 "friedman": "J. H. Friedman, “Greedy function approximation: A gradient boosting machine,” <i>Ann. Statist.</i>, vol. 29, no. 5, pp. 1189–1232, 2001.",
 "cart": "L. Breiman, J. H. Friedman, R. A. Olshen, and C. J. Stone, <i>Classification and Regression Trees</i>. Belmont, CA, USA: Wadsworth, 1984.",
 "svm": "C. Cortes and V. Vapnik, “Support-vector networks,” <i>Mach. Learn.</i>, vol. 20, no. 3, pp. 273–297, 1995.",
 "knn": "T. Cover and P. Hart, “Nearest neighbor pattern classification,” <i>IEEE Trans. Inf. Theory</i>, vol. 13, no. 1, pp. 21–27, 1967.",
 "ridge": "A. E. Hoerl and R. W. Kennard, “Ridge regression: Biased estimation for nonorthogonal problems,” <i>Technometrics</i>, vol. 12, no. 1, pp. 55–67, 1970.",
 "he": "H. He and E. A. Garcia, “Learning from imbalanced data,” <i>IEEE Trans. Knowl. Data Eng.</i>, vol. 21, no. 9, pp. 1263–1284, 2009.",
 "fisher": "R. A. Fisher, “The use of multiple measurements in taxonomic problems,” <i>Ann. Eugenics</i>, vol. 7, no. 2, pp. 179–188, 1936.",
 "uci": "D. Dua and C. Graff, “UCI machine learning repository,” Univ. California, Irvine, CA, USA, 2019. [Online]. Available: https://archive.ics.uci.edu/",
 "pbkdf": "K. Moriarty, B. Kaliski, and A. Rusch, “PKCS #5: Password-based cryptography specification version 2.1,” IETF RFC 8018, Jan. 2017.",
 "fastapi": "S. Ramírez, “FastAPI,” FastAPI documentation. [Online]. Available: https://fastapi.tiangolo.com/",
 "react": "Meta Open Source, “React,” React documentation. [Online]. Available: https://react.dev/",
}

def blocks():
    B = []
    h1 = lambda t: B.append(("h1", t)); h2 = lambda t: B.append(("h2", t)); p = lambda t: B.append(("p", t))
    eq = lambda t, n: B.append(("eq", t, n))
    fig = lambda src, cap, span=False, w=3.35: B.append(("fig", src, cap, span, w))
    tab = lambda cap, head, rows, widths, span=False, fs=7: B.append(("table", cap, head, rows, widths, span, fs))
    abstract = (f"Machine learning models are usually judged by a single accuracy figure, which hides defective data, target leakage, fragile behaviour and unfair predictions. "
        f"This paper presents Testrion, a full-stack platform that automatically tests a model with 24 tests in five categories (data quality, model performance, robustness, reliability, and fairness and slices), "
        f"summarises the outcome as a weighted 0–100 quality score and an independent deployment gate, and then solves the problems it finds with a three-stage Auto-fix engine "
        f"(pipeline repair, randomised hyper-parameter search and model search) that re-runs every test after each change. "
        f"The platform combines a React web interface, a FastAPI back end with per-user accounts, 12 scikit-learn models, live drift monitoring, a parallel batch benchmark and a continuous-integration gate. "
        f"On 11 datasets, Auto-fix raised the mean quality score from {mb:.1f} to {ma:.1f}, improved {len(improved)} of 11 runs and released {len(blocked_b) - len(blocked_a)} of the {len(blocked_b)} runs that the gate had blocked. "
        f"On the Wine data the hold-out accuracy rose from 71.1% to 97.8% (macro F1 0.609 to 0.976) and on the house-price data R² rose from 0.753 to 0.862. "
        f"The gate also exposed target leakage in two datasets whose apparent accuracy was 98.7% and 99.5%. "
        f"A 24-test suite finishes in under {max(1, round(maxdur))} s on every dataset used here, 1,000,000 rows are tested in 22 s, 100 models are tested in 41 s on 10 threads (9.6× speed-up), and a drift verdict is returned in 11 ms. "
        f"Most datasets are synthetic, so the figures show that the method works rather than predict performance on production data.")
    B.append(("abstract", abstract))
    B.append(("keywords", "machine learning testing, automated testing, deployment gate, auto-fix, data leakage, fairness, drift detection, metamorphic testing, scikit-learn"))

    h1("Introduction")
    p("Machine learning models now support decisions on credit, hiring, health and education, yet they are usually released after a single check: the accuracy on one held-out set. "
      "That number says nothing about duplicated or leaking rows, missing values at prediction time, sensitivity to units and noise, weak performance on a minority class or a region, or a data distribution that changes after release. "
      "Practitioners therefore carry a large and often invisible testing and maintenance burden {R:sculley}, {R:amershi}, and rubrics for production readiness exist but are checked by hand {R:breck}.")
    p("Existing work covers pieces of this problem. Surveys catalogue machine learning testing techniques {R:zhang}; metamorphic relations test classifiers without an oracle {R:chen}, {R:xie}; behavioural test suites check language models {R:ribeiro}; data validators check the inputs {R:breckdata}; and fairness criteria measure group-level harm {R:hardt}, {R:dwork}. "
      "What is rarely offered is one workflow that runs all of these checks automatically on any tabular dataset, turns them into a clear release decision, and then repairs what failed and proves the repair by re-testing.")
    p("This paper presents Testrion, a web platform for automated software testing and problem solving of machine learning models. The contributions are: "
      "(i) a layered architecture that connects a React interface, a FastAPI service, a test engine, a model registry and SQLite persistence behind per-user accounts; "
      "(ii) a suite of 24 automatic tests in five categories whose results are combined into a weighted quality score and, separately, a five-condition deployment gate; "
      "(iii) an Auto-fix engine that diagnoses failures, applies pipeline repairs, a randomised search and a model search, keeps a change only if validation does not get worse, and re-runs every test; "
      "(iv) live drift monitoring, a parallel batch benchmark, a Streamlit application and a continuous-integration gate that fails a build when a model is blocked; and "
      "(v) an evaluation on 11 datasets, with scalability and system tests, that separates what was measured from what was only designed.")

    h1("Related Work")
    p("*A. Testing and validating machine learning.* Breck et al. proposed the ML Test Score, a rubric of tests for data, model, infrastructure and monitoring {R:breck}, and Sculley et al. described the technical debt that untested machine learning systems accumulate {R:sculley}. "
      "Amershi et al. reported the engineering difficulties of machine learning at scale {R:amershi}, and Zhang et al. surveyed machine learning testing, including its properties, components and open problems {R:zhang}. "
      "These works motivate what to test, but leave the execution to the engineer.")
    p("*B. Metamorphic and behavioural testing.* Metamorphic testing checks a relation between outputs for related inputs when the correct output is unknown {R:chen}; Xie et al. applied it to classifiers {R:xie}. "
      "CheckList extends the idea to behavioural tests of language models {R:ribeiro}. Testrion uses the same principle for tabular data: a change of units or a reordering of the training rows must not change predictions. "
      "Adversarial examples show that small input changes can flip predictions {R:goodfellow}, which motivates its worst-case perturbation search.")
    p("*C. Data validation, leakage and drift.* Data validation catches schema and distribution errors before training {R:breckdata}. Leakage, in which a feature carries information that will not exist at prediction time, inflates accuracy and is hard to see {R:kaufman}. "
      "Concept drift degrades models after release and must be monitored {R:gama}; the Population Stability Index is a standard measure in credit scoring {R:siddiqi}.")
    p("*D. Fairness.* Equality of opportunity {R:hardt}, fairness through awareness {R:dwork} and disparate-impact analysis {R:feldman} define group fairness; Mehrabi et al. survey sources of bias {R:mehrabi}. Testrion reports the demographic parity difference of declared protected attributes and the error on every data slice.")
    p("Table VIII compares the approaches. The works above address one aspect each and rely on the engineer to run and fix; Testrion adds automatic execution, a release decision and automatic repair on top of these ideas.")

    h1("System Architecture")
    p("*A. Layered design.* Testrion has four loosely coupled layers (Fig. 1). The presentation layer is a React 18 application built with Vite {R:react} and Recharts, with a landing page, sign-in and 12 pages: dashboard, new test, datasets, test history, compare runs, leaderboard, report, requirements, viva guide and how-it-works. "
      "The application layer is a FastAPI service {R:fastapi} that exposes authentication, dataset, run, auto-fix, monitoring and batch routes. The testing engine holds task detection, the 24 tests, scoring, the deployment gate, the Auto-fix engine and a registry of 12 scikit-learn models {R:pedregosa}. "
      "SQLite stores users, uploaded datasets, runs and fix reports. A Streamlit application exposes the same engine for notebook-style use.")
    fig("assets/f1_arch.png", "Layered architecture of Testrion.", True, 7.0)
    p("*B. Accounts and isolation.* Passwords are stored as salted PBKDF2-HMAC-SHA256 hashes with 200,000 iterations {R:pbkdf}. Sign-in issues a token that is valid for seven days and is required for the data routes; a missing or invalid token is rejected. "
      "Every dataset, run and monitor belongs to one user, and another user's identifier returns HTTP 404 (not found), so results are isolated per account.")
    p("*C. Data and model flow.* A user selects one of five built-in datasets or uploads a CSV file of at most 10 MB. The platform previews the columns, suggests a target, lets the user choose a model and optional preparation steps, and runs the suite. "
      "The report page shows the score, the gate, every test with its evidence, the metrics, a prediction playground, live drift monitoring and the exported model. The final model is re-trained on all rows and exported as a pickle file for deployment.")

    h1("Methodology")
    p("*A. Task detection and validation protocol.* A numeric target with more than 20 distinct values is treated as regression and a target with 2 to 30 distinct values as classification; anything else is rejected with a message. "
      "Each run uses a 75/25 train/test split (stratified for classification) with a fixed seed of 42. The 25% test portion is never used to fit, tune or select a model. Cross-validation {R:kohavi} runs only inside the 75% training portion and is the validation score used by the Auto-fix engine. "
      "The registry offers six classifiers (logistic regression, decision tree, random forest {R:breiman}, k-nearest neighbours {R:knn}, support-vector machine {R:svm} and gradient boosting {R:friedman}) and six regressors (linear, ridge {R:ridge}, decision tree {R:cart}, random forest, gradient boosting and KNN).")
    p("*B. The 24 tests.* The suite has 24 tests for regression and 23 for classification, because the non-negative-prediction test applies only to regression. Table I lists the categories and Table II the operating thresholds. "
      "Each test returns pass, warning, fail or skipped, with its measured value, threshold and a suggested fix. The edge-case test generates minimum, maximum, zero, ten-times-range, null, unseen-category, special-character and empty-string inputs. "
      "The leakage test trains a one-feature model for every column and flags a column that alone reaches a balanced accuracy of 0.96 or more. Class imbalance is reported because it distorts accuracy {R:he}.")
    tab("Test categories, number of tests and score weights", ["Category", "Tests", "Weight", "Checks"], [
        ["Data Quality", "7", "1.0", "Missing values, duplicates, target skew or class balance, constant features, outliers, leakage, sample size"],
        ["Model Performance", "6", "2.0", "Hold-out accuracy or R², F1 or MAPE, 5-fold CV, CV stability, overfitting gap, valid predictions"],
        ["Robustness", "6", "1.5", "Gaussian noise, missing values at inference, unit-change and training-order invariance, edge cases, adversarial search"],
        ["Reliability", "3", "1.0", "Reproducibility, train/test drift (PSI), prediction latency"],
        ["Fairness & Slices", "2", "1.5", "Data-slice performance, demographic parity difference"]], [0.85, 0.35, 0.42, 1.8], False, 7)
    tab("Key operating parameters", ["Component", "Setting"], [
        ["Split / seed", "75% train, 25% test; seed 42"],
        ["Validation", "5-fold CV in tests; 3-fold CV in tuning"],
        ["Gate: performance", "accuracy ≥ 85% (R² ≥ 0.85)"],
        ["Gate: fairness", "demographic parity < 10%"],
        ["Gate: classes", "worst-class recall ≥ 50%"],
        ["Gate: integrity", "no leakage; identical predictions"],
        ["Leakage flag", "single-feature balanced acc. ≥ 0.96"],
        ["Invariance tests", "prediction agreement ≥ 97%"],
        ["Edge / adversarial", "≥ 99% handled / ≥ 90% stable"],
        ["Slice error", "extra error ≤ 8 points"],
        ["Drift (PSI)", "≤ 0.10 pass; ≤ 0.25 warning"],
        ["Auto-fix search", "≤ 8 random candidates"],
        ["Accounts", "PBKDF2, 200k iterations; 7-day token"]], [1.15, 2.3], False, 7)
    p("*C. Metrics.* For a binary problem with true and false positives and negatives (TP, FP, TN, FN), the classification metrics are")
    eq("Accuracy = (TP + TN) / (TP + TN + FP + FN)", "(1)")
    eq("Precision = TP / (TP + FP),   Recall = TP / (TP + FN)", "(2)")
    eq("F1 = 2 · Precision · Recall / (Precision + Recall)", "(3)")
    p("For more than two classes, precision, recall and F1 are averaged over classes (macro average), and the worst-class recall protects against a model that ignores a rare class. For regression,")
    eq("R² = 1 − Σ(yᵢ − ŷᵢ)² / Σ(yᵢ − ȳ)²", "(4)")
    p("with the root mean squared error RMSE = √[(1/n) Σ(yᵢ − ŷᵢ)²], the mean absolute error and the mean absolute percentage error reported alongside. Drift between the training distribution (bin shares eᵢ) and the test or live distribution (shares aᵢ) is measured by the Population Stability Index {R:siddiqi}, and fairness by the demographic parity difference over groups g:")
    eq("PSI = Σᵢ (aᵢ − eᵢ) · ln(aᵢ / eᵢ)", "(5)")
    eq("DPD = maxₖ [ max_g P(ŷ=k|g) − min_g P(ŷ=k|g) ]", "(6)")
    p("*D. Quality score.* A passed test earns one point, a warning half a point and a failure none; skipped tests are ignored. With P_c, W_c and F_c the passed, warned and failed tests of category c, the category score and the overall quality score are")
    eq("s_c = 100 · (P_c + 0.5 W_c) / (P_c + W_c + F_c)", "(7)")
    eq("Q = Σ_c w_c s_c / Σ_c w_c", "(8)")
    p("where the weights w_c are those of Table I. The grade is A for Q ≥ 90, B for Q ≥ 80, C for Q ≥ 70, D for Q ≥ 55 and F otherwise.")
    p("*E. Deployment gate.* The score is a summary; the release decision is made by an independent gate. A model is approved only if all five conditions of (9) hold: G_1, accuracy ≥ 85% (R² ≥ 0.85 for regression); G_2, DPD < 10%; G_3, worst-class recall ≥ 50%; G_4, no leaking feature; and G_5, identical predictions when the model is run twice,")
    eq("Gate = G_1 ∧ G_2 ∧ G_3 ∧ G_4 ∧ G_5", "(9)")
    p("so a high score cannot hide a failed condition. The parity condition is evaluated only when a protected attribute (such as gender, age or region) is present, and is reported as “not evaluated” otherwise.")
    fig("assets/f2_flow.png", "Testing pipeline and the three-stage Auto-fix loop.", True, 7.0)
    p("*F. Auto-fix engine.* When a run is weak or blocked, the engine works in three stages (Fig. 2). Stage 1 repairs the pipeline from the failed tests: median and most-frequent imputation, removal of duplicate rows, dropping a leaking column, standardisation, class weights or oversampling, and a log(1 + y) transform of a skewed regression target. "
      "Stage 2 runs a randomised search {R:bergstra} of at most eight candidates with three-fold cross-validation. Stage 3 cross-validates every model of the same task and switches only if another model is clearly better. "
      "A change is kept only if the validation score does not get worse. The full suite is then re-run, and the report lists every step, its reason, the tests whose status changed and the before and after scores.")
    p("*G. Drift monitoring and batch benchmark.* After a model is trained, live predictions are posted to a monitor that compares each numeric feature with the training reference by PSI and returns a drift verdict. "
      "A batch route tests many models in parallel on a thread pool and ranks them on a leaderboard.")

    h1("Implementation and Experimental Setup")
    p("The back end is Python with FastAPI, scikit-learn 1.6.1, pandas and NumPy; the front end uses React, Vite and Recharts; and storage is SQLite. All measurements were made on an Apple M5 laptop (10 CPU cores, macOS 27.0.1, Python 3.9.6), with the server and the browser on the same machine. "
      "Eleven automated tests of the engine run under pytest and a GitHub Actions workflow calls a command-line gate that exits with an error when a model is blocked.")
    p("*Datasets.* Table III lists the 11 datasets. Two are real public datasets: Iris {R:fisher} and Wine from the UCI repository {R:uci}. Three are synthetic datasets generated by Testrion with deliberate defects: house price (missing values, duplicates, outliers, regional effects), customer churn (missing values, duplicates, imbalance, a constant column) and credit default (severe imbalance, missing income and a leaking feature). "
      "Six more synthetic CSV files, supplied with the application for testing uploads, cover used-car prices, energy consumption, loan approval, student grades, fraud detection and a 120-row sample. Because most data are synthetic, the defects are known in advance, which makes it possible to check that the tests find them.")
    rows = []
    for k in ORDER:
        d = D["datasets"][k]
        rows.append([SHORT[k], f"{d['rows']:,}", str(d["cols"]), "Reg." if d["task"] == "regression" else "Class.", d["target"], "R" if "real" in d["source"] else "S"])
    tab("Datasets used in the evaluation (R: real, S: synthetic)", ["Dataset", "Rows", "Cols", "Task", "Target", "Src"], rows, [1.05, 0.42, 0.33, 0.42, 1.0, 0.28], False, 7)
    p("*Protocol.* For each dataset the default model is tested on the raw data (before), then the Auto-fix engine is run (after). The before models were chosen to show typical weaknesses: Linear Regression and an unscaled SVM and KNN, an unpruned Decision Tree and a Random Forest. All numbers are hold-out values on the 25% test split.")

    h1("Results")
    p("*A. Quality score and gate.* Table IV and Fig. 3 show the effect of Auto-fix. "
      f"The mean quality score rose from {mb:.1f} to {ma:.1f}. The score improved on {len(improved)} of 11 datasets; the gate had blocked {len(blocked_b)} runs before the repair and blocked {len(blocked_a)} afterwards (student grades). "
      "Gains were largest where the defect was clearest: Wine from 61.2 to 98.3 (SVM on unscaled features), loan approval from 64.8 to 97.7 (accuracy 72.5% to 89.3% and a parity difference of 47.3% reduced to 5.6%) and house price from 75.0 to 97.1.")
    rows = []
    for k in ORDER:
        b, a = R[k]["before"], R[k]["after"]; m = "R²" if b["metrics"]["task"] == "regression" else "Acc."
        rows.append([SHORT[k], MODEL[R[k]["model_before"]], MODEL[R[k]["model_after"]], f"{b['score']:.1f} ({b['grade']})", f"{a['score']:.1f} ({a['grade']})", b["gate"]["status"].title(), a["gate"]["status"].title(), m, f"{prim(k,'before'):.3f}", f"{prim(k,'after'):.3f}"])
    tab("Quality score, grade, gate and primary metric before and after Auto-fix", ["Dataset", "Model before", "Model after", "Score before", "Score after", "Gate before", "Gate after", "Metric", "Before", "After"], rows,
        [1.0, 0.85, 0.85, 0.7, 0.7, 0.65, 0.65, 0.4, 0.5, 0.5], True, 7)
    fig("assets/f3_scores.png", "Quality score before and after Auto-fix on 11 datasets.", False, 3.3)
    p("Two results need an honest reading. On Iris the score fell slightly (92.2 to 90.5) because the data were already clean: the engine only removed the one duplicate row, no other change improved the validation score, and the gate stayed approved. "
      "On customer churn the hold-out accuracy fell from 90.4% to 85.3% while the score rose from 76.2 to 88.5: the unpruned Random Forest had memorised the training data (failing the overfitting test), and the simpler logistic regression is more trustworthy even though its raw accuracy is lower. "
      "Student grades remained blocked (accuracy 67.1% to 79.6%) because the data carry too little signal for the 85% condition; the engine reports this rather than forcing a pass.")
    p("*B. Precision, recall and F1.* Table V gives the classification metrics. The largest change is on Wine, where macro precision rose from 0.651 to 0.982, recall from 0.650 to 0.972 and F1 from 0.609 to 0.976. Without scaling, the RBF kernel is dominated by the features with large numeric ranges and class 2 is almost never predicted (recall 8.3%); after standardisation only one of 45 test wines is misclassified (Fig. 4).")
    rows = []
    for k in ORDER:
        b, a = R[k]["before"]["metrics"], R[k]["after"]["metrics"]
        if b["task"] != "classification": continue
        f = lambda key: f"{b[key]:.3f} → {a[key]:.3f}"
        rows.append([SHORT[k], f("accuracy"), f("precision"), f("recall"), f("f1")])
    tab("Hold-out classification metrics before → after Auto-fix (macro average)", ["Dataset", "Accuracy", "Precision", "Recall", "F1-score"], rows, [1.5, 1.5, 1.5, 1.5, 1.5], True, 7.2)
    fig("assets/f4_conf.png", "Wine confusion matrices (45 test rows) before and after standardisation.", False, 3.3)
    p("*C. Regression.* Table VI shows the regression datasets. On house prices, R² rose from 0.753 to 0.862, RMSE fell from 22.9 to 18.7 lakhs and the mean absolute percentage error from 15.8% to 11.0%. The repair applied imputation, de-duplication, a log-transformed target, standardisation and a switch from Linear Regression to Gradient Boosting. "
      "The edge-case test shows why imputation matters: all 40 null inputs crashed the raw pipeline (78.9% of generated cases handled) and none crashed after the repair. Used-car prices reached the maximum score of 100, and energy consumption, already linear, improved from 90.8 to 97.7 once imputation removed its two failed tests (missing values at inference and generated edge cases).")
    rows = []
    for k in ORDER:
        b, a = R[k]["before"]["metrics"], R[k]["after"]["metrics"]
        if b["task"] != "regression": continue
        rows.append([SHORT[k], f"{b['r2']:.3f} → {a['r2']:.3f}", f"{b['rmse']:.2f} → {a['rmse']:.2f}", f"{b['mae']:.2f} → {a['mae']:.2f}", f"{b['mape']*100:.1f}% → {a['mape']*100:.1f}%"])
    tab("Hold-out regression metrics before → after Auto-fix", ["Dataset", "R²", "RMSE", "MAE", "MAPE"], rows, [1.1, 0.8, 0.8, 0.8, 0.9], False, 6.8)
    p("*D. Leakage and fairness.* The leakage test flagged one leaking feature in the credit-default and in the fraud datasets. The apparent hold-out accuracy was 98.7% and 99.5%, yet the gate blocked both; after the leaking column was removed the honest accuracies were 91.2% and 92.0% and both were approved. "
      "This is the clearest case where a single accuracy number would have approved a model that fails in production. In the loan data the parity difference fell from 47.3% to 5.6%, and in the credit data from 16.7% to 7.6%, both below the 10% limit.")
    fig("assets/f5_cats.png", "Category scores before and after Auto-fix (DQ: data quality, MP: model performance, RB: robustness, RL: reliability, FS: fairness and slices).", False, 3.3)
    p("*E. Category analysis.* Fig. 5 shows that the repair acts on different categories in different datasets. For house prices the gains are in data quality (78.6 to 100), model performance (66.7 to 91.7) and robustness (66.7 to 100); for loan approval the largest gains are in robustness (41.7 to 91.7), model performance (60.0 to 100) and fairness (50.0 to 100). "
      "Reliability (reproducibility, drift and latency) is high in most runs because the seed is fixed and the random split introduces little drift.")
    tab("Scalability and responsiveness benchmarks", ["Measurement", "Result", "Target"], [
        ["1,000,000 rows, 24 tests, Ridge", "22 s", "< 15 min"],
        ["100 models, 10 threads", "41 s (9.6× speed-up)", "100 models"],
        ["Sum of 100 sequential runs", "395 s", "–"],
        ["Drift verdict, 200 live predictions", "11 ms", "< 5 s"],
        ["Mean single prediction", "7.9 ms (p95 8.1 ms)", "–"],
        ["Dashboard bundle over localhost", "13 ms", "< 3 s"],
        [f"Full suite, largest dataset here", f"≤ {max(1, round(maxdur))} s", "–"]], [1.75, 1.15, 0.6], False, 7)
    p("*F. Scalability.* Table VII lists the benchmarks. With S = T_seq / T_par,")
    eq("S = 395 s / 41 s = 9.6", "(10)")
    p("so ten threads give an almost linear speed-up on 100 models. The 1,000,000-row run used a linear model; tree ensembles are much slower per row and were not benchmarked at this size. The server-side drift verdict and the dashboard figure exclude browser rendering.")
    p("*G. System verification.* The 11 automated tests pass. They check that the house-price model passes the gate, that predictions are positive, that the actual-versus-predicted table is produced, that all specified test types are present, that a leaking feature is detected, that null inputs expose crashes, that protected attributes are found, that a task mismatch is rejected, that Auto-fix improves the quality score, and that the API requires login and isolates users. "
      "The command-line gate approved the repaired house-price model (score 97.1, R² 0.858, parity 4.4%) and blocked an unrepaired one (score 75.0), returning a non-zero exit code that fails the build. GitHub Actions and Docker files are included but were not executed for this paper.")
    tab("Comparison with representative approaches", ["Approach", "Scope", "Auto-run", "Repair"], [
        ["ML Test Score {R:breck}", "Production-readiness rubric", "No", "No"],
        ["Metamorphic testing {R:xie}", "Classifier relations", "Partly", "No"],
        ["CheckList {R:ribeiro}", "Behavioural tests (NLP)", "Partly", "No"],
        ["Data validation {R:breckdata}", "Input data only", "Yes", "No"],
        ["Testrion", "Data, model, robustness, drift, fairness, gate", "Yes", "Yes"]], [1.15, 1.45, 0.45, 0.4], False, 7)

    h1("Limitations")
    p("Nine of the 11 datasets are synthetic, so defects are known and results should not be read as field accuracy; a real production dataset may behave differently. Each result comes from a single 75/25 split with seed 42 and carries no confidence interval. "
      "The platform covers tabular data and scikit-learn models only, the demographic parity check needs a declared protected attribute, and the thresholds (85%, 10%, 0.96) are defaults that a domain may need to change. The Auto-fix search is deliberately small to finish in seconds and is not exhaustive. "
      "Authentication is suitable for a single-server deployment and was not penetration-tested. The 1,000,000-row benchmark used one linear model.")

    h1("Conclusion")
    p(f"Testrion turns the testing of a machine learning model into one automatic workflow: 24 tests, an independent release gate, a three-stage repair engine and a re-test that proves the repair. Across 11 datasets the mean quality score rose from {mb:.1f} to {ma:.1f}, "
      f"Wine accuracy rose from 71.1% to 97.8%, house-price R² from 0.753 to 0.862, and two cases of target leakage that a plain accuracy check would have approved were blocked. A full suite runs in under 4 s on every dataset used here, 100 models are tested in 41 s, and a drift verdict takes 11 ms. "
      "Future work includes real-world datasets with confidence intervals, tests for deep-learning and time-series models, explainability-based checks and multi-user team workspaces.")
    return B
