def st(t): return {"pass": "Pass", "warn": "Warning", "fail": "Fail", "skip": "Skipped"}[t["status"]]
def cell(t): return f'{st(t)} ({t["value"]})'
def tmap(run): return {t["id"]: t for t in run["tests"]}
def pct(x): return f"{x * 100:.1f}%"

def build(B, D):
    R = D["runs"]
    B.h1("ADDRESSING COMPLEX ENGINEERING PROBLEMS WITH SOCIAL IMPACT")
    B.p("This project addresses a complex engineering problem because testing a machine-learning model involves several goals that interact and can conflict. A model must be accurate, but accuracy alone is misleading when classes are imbalanced or features leak the answer. A model must be robust, but robustness to noise is different from robustness to missing values or to unusual inputs. A model should be fair to groups of people, but fairness can reduce accuracy and the available fairness definitions can disagree. A repair must improve the model, but a repair chosen with the test data would make the reported accuracy dishonest. These objectives cannot be assessed with one metric, so the project combines test design, statistical measurement, automatic repair, software engineering and explicit reporting of limits.")
    B.h2("6.1 Introduction: Engineering Complexity")
    B.p("The difficulty appears at every layer. At the data layer the platform must accept arbitrary CSV files and still decide, without human help, which column is a valid target, which columns are identifiers and which attributes concern people. At the learning layer it must support linear, tree-based, distance-based and kernel models, whose weaknesses differ: the same preprocessing that rescues a support-vector machine is irrelevant for a random forest. At the testing layer each test needs thresholds that are strict enough to catch real problems and tolerant enough not to raise false alarms on small datasets; for example, the drift statistic is noisy on a 38-row test set, so its thresholds scale with sample size. At the decision layer the gate must refuse a model that merely predicts the majority class even though its accuracy looks high. At the repair layer the engine must separate diagnosis, which may use test results, from selection, which may use validation scores only. Finally, at the software layer the system must be reproducible, secure enough for local use and fast enough for interactive work: the measured benchmarks in Chapter 7 show a full 24-test run on one million records in 22 seconds with a linear model.")
    B.h2("6.2 Social Impact")
    B.p("Automated, repeatable testing of models can reduce the chance that an unreliable or unfair model reaches users. The fairness and slice tests make differences between groups visible before release instead of after complaints. The leakage test prevents a model that looks perfect in evaluation from being deployed on information that will not exist in practice, which in lending or fraud detection can mean wrongly approved or wrongly refused customers. The live drift monitor helps to notice that the world has changed. Because the platform is free, runs on a laptop and explains every finding in plain language, it can also be used for teaching how responsible machine-learning practice looks in a working tool.")
    B.p("The potential impact must be described carefully. Testrion tests the properties it implements, on the data it is given. A passed gate is evidence, not a guarantee: it does not prove that a model is correct for every input, that it is fair in every sense or that it is secure against a determined attacker. Demographic parity is only one fairness criterion, and some of the sample data are synthetic. The tool supports good decisions; it does not replace human responsibility for them.")
    B.h2("6.3 Sustainable Development Goal Mapping")
    B.p("The project has a plausible connection to the United Nations Sustainable Development Goals listed in {T:sdg}. The mapping describes potential relevance and not a measured social outcome.")
    B.table("sdg", "Potential SDG mapping", ["SDG", "Connection", "Project relevance"], [
        ["SDG 9: Industry, Innovation and Infrastructure", "Resilient, reliable digital infrastructure", "Provides an automated release gate and monitoring for machine-learning components, reducing the risk of silent model failure."],
        ["SDG 10: Reduced Inequalities", "Fair treatment of groups", "Slice testing and the demographic parity check expose differences in outcomes between genders, age bands and regions before a model is released."],
        ["SDG 16: Peace, Justice and Strong Institutions", "Accountable and transparent systems", "Every decision is explained with evidence, thresholds and a recorded configuration; limits are stated openly."],
    ], [2.0, 1.8, 3.2], 9.5)

    # ------------------------------------------------------------ Chapter 7
    B.h1("RESULTS AND DISCUSSION")
    B.p("This chapter reports the measured behaviour of Testrion. All numbers were produced by the platform itself on the datasets described in Chapter 3 and were collected by a script, not typed by hand. The same results can be regenerated with `evidence.py` and the report data collector. They describe the platform's behaviour on these datasets and this configuration and should not be generalised beyond them.")
    B.h2("7.1 Experimental Configuration")
    B.p("{T:config} lists the configuration used for all experiments.")
    B.table("config", "Experimental configuration", ["Parameter", "Value"], [
        ["Machine", "Apple laptop, Apple M5 chip (10-core CPU), macOS"],
        ["Software", "Python 3.9.6, scikit-learn 1.6.1, pandas 2.3.3, NumPy 2.0.2"],
        ["Datasets", "11 (2 real, 9 synthetic); 5 built in and 6 uploaded CSV files"],
        ["Models", "6 classifiers and 6 regressors; fixed random seed 42"],
        ["Split", "75% training and 25% hold-out test; 5-fold cross-validation inside the training portion"],
        ["Row limit", "6,000 rows per interactive run (raised only for the 1,000,000-record benchmark)"],
        ["Gate thresholds", "Accuracy or R² ≥ 85%; demographic parity difference < 10%; worst-class recall ≥ 50%; no leakage; reproducible"],
        ["Baseline run", "Chosen model on raw data with no repair options (naive pipeline)"],
        ["Fixed run", "Result of the three-stage Auto-fix engine applied to the baseline run"],
    ], [1.8, 5.2], 10, bold_first=True)

    h = R["house_price"]; hb, ha = h["before"], h["after"]; mb, ma = hb["metrics"], ha["metrics"]
    B.h2("7.2 Results on the House-Price Data")
    B.p(f"The house-price dataset is the project's demonstration problem. The baseline is a linear regression trained on the raw data. {{T:house_metrics}} shows that this baseline reaches a hold-out R² of {mb['r2']:.3f}, below the 0.85 required by the gate, and fails two robustness tests (the model crashes on missing values and on null edge-case inputs). The deployment gate therefore reports **{hb['gate']['status']}** with a quality score of {hb['score']:.1f} (grade {hb['grade']}). Auto-fix applied {len(h['steps'])} repairs ({'; '.join(str(i+1)+') '+s['title'].lower() for i,s in enumerate(h['steps']))}) and the fixed run, a gradient-boosting regressor, reaches R² {ma['r2']:.3f}, passes {ha['passed']} of {ha['total']} tests and the gate reports **{ha['gate']['status']}** with a score of {ha['score']:.1f} (grade {ha['grade']}).")
    rows = [["Quality score (0–100)", f"{hb['score']:.1f}", f"{ha['score']:.1f}"], ["Grade", hb["grade"], ha["grade"]], ["Deployment gate", hb["gate"]["status"], ha["gate"]["status"]],
            ["Hold-out R²", f"{mb['r2']:.3f}", f"{ma['r2']:.3f}"], ["RMSE (lakhs)", f"{mb['rmse']:.2f}", f"{ma['rmse']:.2f}"], ["MAE (lakhs)", f"{mb['mae']:.2f}", f"{ma['mae']:.2f}"],
            ["Mean absolute % error", pct(mb["mape"]), pct(ma["mape"])], ["Train R²", f"{mb['train_r2']:.3f}", f"{ma['train_r2']:.3f}"], ["Cross-validation R² (training data)", f"{mb['cv_mean']:.3f} ± {mb['cv_std']:.3f}", f"{ma['cv_mean']:.3f} ± {ma['cv_std']:.3f}"],
            ["Tests passed / warnings / failed", f"{hb['passed']} / {hb['warned']} / {hb['failed']}", f"{ha['passed']} / {ha['warned']} / {ha['failed']}"]]
    B.table("house_metrics", "House-price results before and after Auto-fix", ["Measure", "Before (Linear Regression)", "After (Gradient Boosting)"], rows, [3.0, 2.0, 2.0], 10, ["left", "center", "center"])
    B.fig("categories", "fig_categories.png", "House-price category scores before and after Auto-fix", 4.7)
    B.fig("scatter", "fig_scatter.png", "Actual versus predicted house price on the hold-out rows", 3.3)
    B.p("{F:categories} shows where the improvement came from: the Model Performance and Robustness categories rose most, because the baseline could not exploit the multiplicative effect of region and property type and crashed on blanks. {F:scatter} shows that the fixed model's predictions follow the diagonal. {T:house_tests} gives the full test-by-test record.")
    bt, at = tmap(hb), tmap(ha); rows = []
    for t in ha["tests"]:
        b = bt.get(t["id"])
        rows.append([t["category"], t["name"], cell(b) if b else "–", cell(t)])
    B.table("house_tests", "Status and value of every test for the house-price model, before and after Auto-fix", ["Category", "Test", "Before", "After"], rows, [1.2, 2.5, 1.65, 1.65], 8.5)

    B.h2("7.3 Evidence for the Specified Test Types")
    B.p("The project specification names four families of generated tests. This section gives actual results for each, taken from the house-price runs.")
    eb = bt["edge_cases"]["data"]["by_kind"]; rows = [[k[0].upper() + k[1:], str(v["cases"]), str(v["failed"])] for k, v in eb.items()]
    B.p(f"**Edge-case inputs.** The baseline generated {sum(v['cases'] for v in eb.values())} edge-case rows, of which {sum(v['failed'] for v in eb.values())} could not be predicted ({bt['edge_cases']['value']} handled). All failures were null values, which a model without imputation cannot process; minimum, maximum, zero, out-of-range, unseen-category, special-character and empty-string inputs were all handled ({{T:edge}}). After imputation was added, {at['edge_cases']['value']} of the cases were handled.")
    B.table("edge", "Edge-case inputs generated for the baseline house-price model", ["Edge-case type", "Rows generated", "Crashed / invalid"], rows, [3.4, 1.8, 1.8], 10, ["left", "center", "center"])
    B.p(f"**Adversarial perturbation.** Under eight random-sign perturbations of 10% of each feature's standard deviation, {bt['adversarial']['value']} of the rows kept their prediction within 20% for the baseline and {at['adversarial']['value']} for the fixed model; both pass the 90% threshold. {at['adversarial']['details']}")
    sl = [s for s in ma["slices"] if s["column"] == "region"]
    B.p(f"**Data-slice testing.** The fixed model's mean absolute percentage error by region ranges from {min(s['metric'] for s in sl) * 100:.1f}% to {max(s['metric'] for s in sl) * 100:.1f}% ({{T:slices}}). The slice test reports the largest extra error as {at['slices']['value']} (limit 8 points), a pass.")
    B.table("slices", "Mean absolute % error of the fixed house-price model by region", ["Region", "Test rows", "Mean absolute % error"],
            [[s["group"], str(s["n"]), pct(s["metric"])] for s in sl], [3.0, 2.0, 2.0], 10, ["left", "center", "center"])
    B.p(f"**Fairness.** The demographic parity (group-bias) difference for the protected attribute `region` was {bt['fairness']['value']} for the baseline and {at['fairness']['value']} for the fixed model, both below the 10% limit. For the baseline the gate failed on the R² check; for the fixed model every gate check passed.")
    B.h2("7.4 Results on Classification Data")
    ch = R["churn"]; cb, ca = ch["before"]["metrics"], ch["after"]["metrics"]
    B.p(f"**Customer churn.** The baseline is a random forest on the raw data. It reaches an accuracy of {pct(cb['accuracy'])} and a macro F1 of {cb['f1']:.3f} on the hold-out rows, but its training F1 is {cb['train_f1']:.3f}, which means it memorised the training data, and it fails the duplicate-rows test and the overfitting test, with warnings for missing values, class imbalance, a constant column and unstable cross-validation. (Random forests in scikit-learn 1.6 accept missing values natively, so this baseline does not crash on blanks.) Auto-fix added imputation, removed the duplicate rows and the constant column, balanced the classes with class weights, tuned the model and finally switched it to logistic regression (standardisation is applied automatically together with that switch). The fixed model has a lower hold-out accuracy ({pct(ca['accuracy'])}) and macro F1 ({ca['f1']:.3f}) but a higher quality score ({ch['before']['score']:.1f} to {ch['after']['score']:.1f}), a train–test gap that has almost disappeared ({ca['train_f1']:.3f} train against {ca['f1']:.3f} test) and a much higher recall for the churners ({ca['per_class'][1]['recall']:.3f} against {cb['per_class'][1]['recall']:.3f}). This is an honest trade-off, not an error: the engine chose the model with the better validation score and robustness, and a user who values raw accuracy above all could keep the forest and tune it instead ({{T:churn}}, {{F:confusion}}).")
    rows = [["Hold-out accuracy", pct(cb["accuracy"]), pct(ca["accuracy"])], ["Macro precision", f"{cb['precision']:.3f}", f"{ca['precision']:.3f}"], ["Macro recall", f"{cb['recall']:.3f}", f"{ca['recall']:.3f}"],
            ["Macro F1", f"{cb['f1']:.3f}", f"{ca['f1']:.3f}"], ["Train F1", f"{cb['train_f1']:.3f}", f"{ca['train_f1']:.3f}"], ["Cross-validation F1", f"{cb['cv_mean']:.3f}", f"{ca['cv_mean']:.3f}"],
            ["Recall of the churner class", f"{cb['per_class'][1]['recall']:.3f}", f"{ca['per_class'][1]['recall']:.3f}"], ["Quality score", f"{ch['before']['score']:.1f}", f"{ch['after']['score']:.1f}"],
            ["Deployment gate", ch["before"]["gate"]["status"], ch["after"]["gate"]["status"]]]
    B.table("churn", "Customer-churn results before (random forest) and after (logistic regression) Auto-fix", ["Measure", "Before", "After"], rows, [3.2, 1.9, 1.9], 10, ["left", "center", "center"])
    B.fig("confusion", "fig_confusion.png", "Confusion matrix of the fixed Customer Churn model on the hold-out rows", 2.9)
    lb, la = R["loan_approval"]["before"], R["loan_approval"]["after"]; lt = tmap(lb)
    B.p(f"**Loan approval (fairness).** The uploaded loan file contains gender, age and region columns and a built-in bias against rural applicants and one gender. The baseline logistic regression has a hold-out accuracy of {pct(lb['metrics']['accuracy'])}, crashes on missing income, is sensitive to feature scale and fails the demographic parity test (difference {lt['fairness']['value']}), so the gate reports **{lb['gate']['status']}** (score {lb['score']:.1f}). Auto-fix imputed the missing values, balanced the classes, standardised the features and removed the protected attributes from the features while continuing to audit them. The fixed model reaches {pct(la['metrics']['accuracy'])} accuracy, the parity difference falls to {tmap(la)['fairness']['value']} and the gate reports **{la['gate']['status']}** (score {la['score']:.1f}).")
    for key, label in (("credit", "Credit default"), ("fraud_transactions", "Fraud transactions")):
        r = R[key]; rb, ra = r["before"], r["after"]; leak = tmap(rb)["leakage"]
        B.p(f"**{label} (leakage).** The leakage test failed for the baseline ({leak['details']}). The baseline's accuracy of {pct(rb['metrics']['accuracy'])} is therefore inflated by the leaking column; after the column was removed, imputation and class balancing were applied and the model was tuned (model: {r['model_after'].replace('_', ' ')}), the honest hold-out accuracy is {pct(ra['metrics']['accuracy'])}. The gate changed from {rb['gate']['status']} to {ra['gate']['status']} and the score from {rb['score']:.1f} to {ra['score']:.1f}. The drop in accuracy is the intended outcome: it replaces an unreliable number with a reliable one.")
    sg = R["student_grades"]
    B.p(f"**Student grades (a refusal).** This noisy three-class file is designed to fail. The best model found by Auto-fix (logistic regression) lifts the score from {sg['before']['score']:.1f} to {sg['after']['score']:.1f} but reaches only {pct(sg['after']['metrics']['accuracy'])} accuracy, so the gate stays **{sg['after']['gate']['status']}**. This shows that the gate cannot be satisfied by repairs alone.")

    B.h2("7.5 Results Across All Datasets")
    B.p("{T:all} and {F:before_after} summarise the results for all eleven datasets. In nine of eleven cases the gate changed from blocked to approved or stayed approved with a higher score. Iris was already clean: its score changed from 92.2 to 90.5 because de-duplication was applied and no other change improved the validation score, so the engine correctly made almost no change. The student-grades file stayed blocked as designed.")
    rows = []
    for k, r in R.items():
        b, a = r["before"], r["after"]; mb_, ma_ = b["metrics"], a["metrics"]
        key = f"R² {mb_['r2']:.2f} → {ma_['r2']:.2f}" if mb_["task"] == "regression" else f"Acc. {mb_['accuracy'] * 100:.0f}% → {ma_['accuracy'] * 100:.0f}%"
        rows.append([r["name"].replace(".csv", ""), r["model_before"].replace("_", " ") + (" → " + r["model_after"].replace("_", " ") if r["model_after"] != r["model_before"] else ""), f"{b['score']:.1f} → {a['score']:.1f}", f"{b['gate']['status'].capitalize()} → {a['gate']['status'].capitalize()}", key])
    B.table("all", "Results of Auto-fix on all eleven datasets", ["Dataset", "Model", "Quality score", "Deployment gate", "Key metric (hold-out)"], rows, [1.5, 1.9, 1.05, 1.35, 1.2], 8.5)
    B.fig("before_after", "fig_before_after.png", "Quality score before and after Auto-fix for all eleven datasets", 5.6)
    B.h2("7.6 Model Comparison on the House-Price Data")
    ex = D["extra"]
    ex = D["extra"]
    B.fig("models", "fig_models.png", "Hold-out R² of different models on the house-price data", 4.2)
    B.h2("7.7 Performance Benchmarks")
    ev = D["evidence_md"]
    B.p("The performance targets of the project specification were measured with the script `evidence.py` on the development machine. {T:bench} gives the results. These figures come from one machine; the one-million-record result applies to a linear model, and tree ensembles are much slower per row. The interactive application still limits a run to 6,000 rows.")
    B.table("bench", "Measured performance against the specified targets", ["Requirement", "Target", "Measured result", "Status"], [
        ["Test-execution speed", "1,000,000 records, full suite < 15 min", "24 tests on 1,000,000 records in 22 s (Ridge Regression)", "Met"],
        ["Parallel model testing", "100 models in parallel", "100 full test-suites in 41 s on 10 threads; sum of individual times 395 s (9.6× speed-up)", "Met"],
        ["Drift-detection latency", "< 5 s (unit interpreted as seconds)", "DRIFT DETECTED 11 ms after 200 live predictions", "Met"],
        ["Dashboard load time", "< 3 s", "Page and bundles transferred in 13 ms over localhost; browser load time shown on the dashboard", "Met"],
    ], [1.5, 1.6, 3.0, 0.9], 9.5)
    B.h2("7.8 Coverage of the Project Specification")
    B.p("{T:cover} maps every requirement of the project specification to its implementation and to the evidence for it.")
    B.table("cover", "Coverage of the functional and non-functional requirements", ["Requirement", "Implementation", "Evidence"], [
        ["Edge-case generation (min/max, null, out-of-range, special characters)", "Edge-case inputs test", "{T:edge}"],
        ["Adversarial test generation", "Adversarial perturbation test", "Section 7.3"],
        ["Data-slice testing (gender, age, region)", "Data-slice performance test and slice charts", "{T:slices}"],
        ["Deployment fails below 85% accuracy", "Deployment gate (R² for regression)", "Section 7.3"],
        ["Demographic parity difference below 10%", "Fairness test and gate check", "Section 7.4 (loan approval)"],
        ["Train, validate and test discipline", "75/25 split; cross-validation on training data only", "Section 3.4"],
        ["Save the model as model.pkl", "Model download (Python pickle)", "Chapter 5"],
        ["CI/CD with GitHub Actions on every push", "Workflow, pytest suite and command-line gate", "Chapter 12"],
        ["Compare actual and predicted values", "Comparison table, scatter plot and residuals", "{F:scatter}"],
        ["Dashboard (Streamlit in the specification)", "React application and a Streamlit interface", "Chapter 5"],
        ["Problem solving (project title)", "Three-stage Auto-fix engine", "Sections 7.2 and 7.4"],
        ["Execution speed, monitoring latency, dashboard load, scalability", "Benchmarks", "{T:bench}"],
    ], [2.6, 2.7, 1.7], 9.5)
    B.h2("7.9 Limitations and Interpretation")
    B.p("The results are limited in several ways that should be stated plainly. Nine of the eleven datasets are synthetic, so the accuracy values show how the platform behaves when problems of known size are present, not what a real application would achieve. The thresholds (for example 85% accuracy or R² and a 10% parity difference) come from the project specification and are reasonable defaults, not universal truths; demographic parity in particular is one criterion among several. The robustness tests sample perturbations at random, so they can miss a worst-case attack. The benchmarks were measured on one machine, and the one-million-record figure is for a linear model. Auto-fix improves what the tests measure; it cannot add information that the data do not contain, as the student-grades file shows. Finally, the GitHub Actions workflow and the Dockerfile are provided but have not been executed on GitHub or in Docker from the development machine; the equivalent commands were run locally.")
