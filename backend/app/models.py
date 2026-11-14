"""Model registry, default hyper-parameters and tuning grids."""
from sklearn.ensemble import (
    GradientBoostingClassifier, GradientBoostingRegressor, RandomForestClassifier, RandomForestRegressor,
)
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

SEED = 42

REGISTRY = {
    "logistic_regression": {
        "label": "Logistic Regression",
        "description": "Linear model; fast and interpretable but sensitive to feature scale.",
        "cls": LogisticRegression,
        "defaults": {"max_iter": 300},
        "seed": True,
        "class_weight": True,
        "grid": {"C": [0.01, 0.1, 1, 10]},
    },
    "random_forest": {
        "label": "Random Forest",
        "description": "Ensemble of decision trees; robust, handles non-linear patterns.",
        "cls": RandomForestClassifier,
        "defaults": {"n_estimators": 120},
        "seed": True,
        "class_weight": True,
        "grid": {"n_estimators": [100, 200], "max_depth": [4, 8, None], "min_samples_leaf": [1, 3, 5]},
    },
    "decision_tree": {
        "label": "Decision Tree",
        "description": "Single tree; interpretable but prone to overfitting.",
        "cls": DecisionTreeClassifier,
        "defaults": {},
        "seed": True,
        "class_weight": True,
        "grid": {"max_depth": [3, 5, 8], "min_samples_leaf": [1, 5, 10]},
    },
    "knn": {
        "label": "K-Nearest Neighbours",
        "description": "Distance based; very sensitive to feature scaling.",
        "cls": KNeighborsClassifier,
        "defaults": {"n_neighbors": 5},
        "seed": False,
        "class_weight": False,
        "grid": {"n_neighbors": [5, 9, 15, 25]},
    },
    "svm": {
        "label": "Support Vector Machine",
        "description": "Margin-based classifier; needs scaled inputs.",
        "cls": SVC,
        "defaults": {"probability": False},
        "seed": True,
        "class_weight": True,
        "grid": {"C": [0.5, 1, 5], "gamma": ["scale", "auto"]},
    },
    "gradient_boosting": {
        "label": "Gradient Boosting",
        "description": "Boosted trees; strong accuracy, can overfit without tuning.",
        "cls": GradientBoostingClassifier,
        "defaults": {"n_estimators": 100},
        "seed": True,
        "class_weight": False,
        "grid": {"n_estimators": [80, 150], "max_depth": [2, 3], "learning_rate": [0.05, 0.1]},
    },
}


REG_REGISTRY = {
    "linear_regression": {
        "label": "Linear Regression",
        "description": "Baseline linear model; fast and interpretable, cannot capture non-linear effects.",
        "cls": LinearRegression, "defaults": {}, "seed": False, "class_weight": False,
        "grid": {"positive": [False, True]},
    },
    "ridge": {
        "label": "Ridge Regression",
        "description": "Linear model with L2 regularisation; stable when features are correlated.",
        "cls": Ridge, "defaults": {}, "seed": False, "class_weight": False,
        "grid": {"alpha": [0.01, 0.1, 1, 10, 100]},
    },
    "decision_tree_reg": {
        "label": "Decision Tree Regressor",
        "description": "Single tree; interpretable but prone to overfitting.",
        "cls": DecisionTreeRegressor, "defaults": {}, "seed": True, "class_weight": False,
        "grid": {"max_depth": [4, 6, 10], "min_samples_leaf": [1, 5, 10]},
    },
    "random_forest_reg": {
        "label": "Random Forest Regressor",
        "description": "Ensemble of trees; strong default for tabular price prediction.",
        "cls": RandomForestRegressor, "defaults": {"n_estimators": 120}, "seed": True, "class_weight": False,
        "grid": {"n_estimators": [100, 200], "max_depth": [6, 12, None], "min_samples_leaf": [1, 3, 5]},
    },
    "gradient_boosting_reg": {
        "label": "Gradient Boosting Regressor",
        "description": "Boosted trees; very accurate, can overfit without tuning.",
        "cls": GradientBoostingRegressor, "defaults": {"n_estimators": 150}, "seed": True, "class_weight": False,
        "grid": {"n_estimators": [100, 200], "max_depth": [2, 3, 4], "learning_rate": [0.05, 0.1]},
    },
    "knn_reg": {
        "label": "K-Nearest Neighbours Regressor",
        "description": "Distance based; very sensitive to feature scaling.",
        "cls": KNeighborsRegressor, "defaults": {"n_neighbors": 5}, "seed": False, "class_weight": False,
        "grid": {"n_neighbors": [5, 9, 15, 25]},
    },
}
for _v in REGISTRY.values():
    _v["task"] = "classification"
for _v in REG_REGISTRY.values():
    _v["task"] = "regression"
REGISTRY.update(REG_REGISTRY)


def model_list():
    return [
        {"id": k, "label": v["label"], "description": v["description"], "task": v["task"]}
        for k, v in REGISTRY.items()
    ]


def make_estimator(model_id, params=None, class_weight=None):
    spec = REGISTRY[model_id]
    kwargs = dict(spec["defaults"])
    if params:
        kwargs.update(params)
    if spec["seed"]:
        kwargs["random_state"] = SEED
    if class_weight and spec["class_weight"]:
        kwargs["class_weight"] = class_weight
    return spec["cls"](**kwargs)
