def build(B, D):
    B.h1("MACHINE LEARNING MODELS")
    B.p("This chapter describes the models that Testrion trains and tests and the metrics used to judge them. Testrion does not propose a new learning algorithm; its contribution is the testing and repair of models. It therefore uses well-known, interpretable scikit-learn models [17] so that the behaviour of the tests can be studied on algorithms with different strengths and weaknesses: linear and non-linear, scale-sensitive and scale-insensitive, high-bias and high-variance.")
    B.h2("4.1 Task Detection and Model Registry")
    B.p("The task is detected from the target column. A numeric target with more than 20 distinct values is a regression target; any other target with 2 to 30 distinct values is a classification target. A model whose task does not match the target is rejected with a clear message. The registry holds six classifiers and six regressors, shown in {T:registry}. Every model uses a fixed random seed of 42 so that results are reproducible, and the test suite verifies this explicitly.")
    reg = [
        ["Logistic Regression", "Classification", "Linear, scale-sensitive; probabilistic", "max_iter = 300"],
        ["Decision Tree", "Classification", "Non-linear, interpretable, prone to overfitting", "default depth"],
        ["Random Forest", "Classification", "Ensemble of trees; robust", "n_estimators = 120"],
        ["K-Nearest Neighbours", "Classification", "Distance based, scale-sensitive", "k = 5"],
        ["Support Vector Machine", "Classification", "Margin based, needs scaled inputs", "RBF kernel, C = 1"],
        ["Gradient Boosting", "Classification", "Boosted trees; accurate, can overfit", "n_estimators = 100"],
        ["Linear Regression", "Regression", "Baseline linear model", "–"],
        ["Ridge Regression", "Regression", "Linear with L2 penalty", "alpha = 1"],
        ["Decision Tree Regressor", "Regression", "Single tree", "default depth"],
        ["Random Forest Regressor", "Regression", "Ensemble of trees", "n_estimators = 120"],
        ["Gradient Boosting Regressor", "Regression", "Boosted trees", "n_estimators = 150"],
        ["KNN Regressor", "Regression", "Distance based", "k = 5"],
    ]
    B.table("registry", "Models available in Testrion", ["Model", "Task", "Character", "Default setting"], reg, [1.9, 1.1, 2.7, 1.3], 9.5)
    B.h2("4.2 Logistic Regression")
    B.p("Logistic regression models the probability that an input belongs to the positive class as the logistic function of a linear combination of the features [17]. For a feature vector x with weights w and bias b,")
    B.eq("p(y = 1 | x) = σ(wᵀx + b),   σ(z) = 1 / (1 + e⁻ᶻ)", "(4.1)")
    B.p("The weights are found by minimising the regularised binary cross-entropy (log) loss,")
    B.eq("L(w) = −(1/n) Σ [ yᵢ log pᵢ + (1 − yᵢ) log(1 − pᵢ) ] + (1 / 2C)‖w‖²", "(4.2)")
    B.p("where C controls the strength of regularisation. Multi-class problems are handled by the multinomial extension. Because the penalty and the optimiser treat all weights alike, logistic regression is sensitive to feature scale, which the unit-change test reveals and the standardisation repair removes. It is used in the demonstration as a fast, stable baseline and, after Auto-fix, as the chosen model for the churn, credit-default and loan-approval datasets.")
    B.h2("4.3 Decision Trees")
    B.p("A decision tree splits the feature space recursively with axis-aligned thresholds, choosing at each node the split that most reduces impurity [22]. For classification the Gini impurity of a node with class proportions p_k is")
    B.eq("G = 1 − Σₖ pₖ²", "(4.3)")
    B.p("and for regression the splits reduce the mean squared error. Trees need no feature scaling and handle mixed data naturally, but an unconstrained tree memorises the training data, which appears in the overfitting-gap test as a training score near 1.0 and a much lower test score. Limiting `max_depth` and `min_samples_leaf`, as the tuning stage does, regularises the tree.")
    B.h2("4.4 Random Forest")
    B.p("A random forest averages many decision trees, each trained on a bootstrap sample of the rows and a random subset of features at every split [20]. Averaging reduces variance, so forests are accurate and robust on tabular data. For regression the prediction is the mean of the trees, for classification the majority vote. The platform uses forests of 120 trees by default and searches 100 or 200 trees, depths of 4, 8 or unlimited (6, 12 or unlimited for regression) and leaf sizes of 1, 3 or 5 during tuning.")
    B.h2("4.5 Gradient Boosting")
    B.p("Gradient boosting builds trees sequentially, each new tree fitted to the negative gradient of the loss with respect to the current predictions [21]:")
    B.eq("Fₘ(x) = Fₘ₋₁(x) + ν · hₘ(x)", "(4.4)")
    B.p("where hₘ is the m-th shallow tree and ν the learning rate. Boosting often gives the highest accuracy on structured data, but without regularisation (a small depth, a modest learning rate and a limited number of trees) it can overfit. In the house-price experiment the Auto-fix model search selected gradient boosting for the regression problem.")
    B.h2("4.6 K-Nearest Neighbours")
    B.p("The k-nearest-neighbours rule predicts the majority class (or the mean value) of the k training points closest to the query point [24], using Euclidean distance on the encoded features:")
    B.eq("d(x, x′) = √ Σⱼ (xⱼ − x′ⱼ)²", "(4.5)")
    B.p("Since the distance is dominated by features with large numeric ranges, KNN is the most scale-sensitive model in the registry. It fails the unit-change test unless the features are standardised and is therefore a useful demonstration of the metamorphic test.")
    B.h2("4.7 Support Vector Machine")
    B.p("A support-vector machine finds the decision boundary that maximises the margin between classes, and with the radial-basis-function kernel it can represent non-linear boundaries [23]:")
    B.eq("K(x, x′) = exp( −γ ‖x − x′‖² )", "(4.6)")
    B.p("The kernel depends on distances, so the SVM requires standardised inputs. On the unscaled Wine dataset it classifies only 71% of the test wines correctly, and after standardisation 98%, which is the clearest single example of a repair in the experiments (Chapter 7).")
    B.h2("4.8 Linear and Ridge Regression")
    B.p("Linear regression predicts a number as a weighted sum of the features and minimises the squared error. Ridge regression adds an L2 penalty on the weights, which stabilises the solution when features are correlated [25]:")
    B.eq("ŵ = argmin_w  ‖y − Xw‖² + α‖w‖²", "(4.7)")
    B.p("Linear models are the natural baseline for the house-price problem. They cannot represent the multiplicative effect of region and property type on price, so their hold-out R² is limited, and they can predict negative prices for small houses, which the valid-predictions test detects. Training on log(1 + price), one of the Auto-fix repairs, converts these multiplicative effects into additive ones and guarantees non-negative predictions.")
    B.h2("4.9 Hyper-parameter Search Spaces")
    B.p("Stage 2 of the Auto-fix engine searches the grids in {T:grids} with a randomised search of at most eight candidates and three-fold cross-validation on the training portion [18], [19]. The grids are deliberately small and regularisation-oriented, so that the search finishes in seconds and favours simpler models.")
    grids = [
        ["Logistic Regression", "C ∈ {0.01, 0.1, 1, 10}"], ["Decision Tree", "max_depth ∈ {3, 5, 8}; min_samples_leaf ∈ {1, 5, 10}"],
        ["Random Forest", "n_estimators ∈ {100, 200}; max_depth ∈ {4, 8, None}; min_samples_leaf ∈ {1, 3, 5}"], ["K-Nearest Neighbours", "n_neighbors ∈ {5, 9, 15, 25}"],
        ["Support Vector Machine", "C ∈ {0.5, 1, 5}; gamma ∈ {scale, auto}"], ["Gradient Boosting", "n_estimators ∈ {80, 150}; max_depth ∈ {2, 3}; learning_rate ∈ {0.05, 0.1}"],
        ["Linear Regression", "fit_intercept ∈ {True, False}"], ["Ridge Regression", "alpha ∈ {0.01, 0.1, 1, 10, 100}"],
        ["Decision Tree Regressor", "max_depth ∈ {4, 6, 10}; min_samples_leaf ∈ {1, 5, 10}"],
        ["Random Forest Regressor", "n_estimators ∈ {100, 200}; max_depth ∈ {6, 12, None}; min_samples_leaf ∈ {1, 3, 5}"],
        ["Gradient Boosting Regressor", "n_estimators ∈ {100, 200}; max_depth ∈ {2, 3, 4}; learning_rate ∈ {0.05, 0.1}"], ["KNN Regressor", "n_neighbors ∈ {5, 9, 15, 25}"],
    ]
    B.table("grids", "Hyper-parameter search spaces used by the tuning stage", ["Model", "Search space"], grids, [2.2, 4.8], 9.5)
    B.h2("4.10 Evaluation Metrics")
    B.p("Let TP, TN, FP and FN denote true positives, true negatives, false positives and false negatives of a binary problem. The metrics used for classification are")
    B.eq("Accuracy = (TP + TN) / (TP + TN + FP + FN)", "(4.8)")
    B.eq("Precision = TP / (TP + FP)", "(4.9)")
    B.eq("Recall = TP / (TP + FN)", "(4.10)")
    B.eq("F1 = 2 · Precision · Recall / (Precision + Recall)", "(4.11)")
    B.p("For problems with more than two classes the precision, recall and F1-score are computed per class and averaged. The *macro* average treats every class equally and is the quantity used by the F1 test; the *weighted* average weights each class by its number of test rows. The worst-class recall, the smallest recall over all classes, protects against a model that ignores a rare class. For regression the metrics are")
    B.eq("R² = 1 − Σ(yᵢ − ŷᵢ)² / Σ(yᵢ − ȳ)²", "(4.12)")
    B.eq("RMSE = √[ (1/n) Σ(yᵢ − ŷᵢ)² ],   MAE = (1/n) Σ|yᵢ − ŷᵢ|", "(4.13)")
    B.eq("MAPE = (1/n) Σ |yᵢ − ŷᵢ| / |yᵢ|", "(4.14)")
    B.p("Reliability and fairness use two further quantities. The Population Stability Index between a reference distribution with bin shares eᵢ and a current distribution with shares aᵢ is")
    B.eq("PSI = Σᵢ (aᵢ − eᵢ) · ln(aᵢ / eᵢ)", "(4.15)")
    B.p("and the demographic parity difference of a protected attribute with groups g is")
    B.eq("DPD = maxₖ ( max_g P(ŷ = k | g) − min_g P(ŷ = k | g) )", "(4.16)")
    B.p("where P(ŷ = k | g) is the rate at which class k is predicted within group g. These definitions are used consistently by the testing engine, the web interface and the Streamlit application.")
