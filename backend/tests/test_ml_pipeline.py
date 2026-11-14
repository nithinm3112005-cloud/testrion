"""Automated tests for the ML testing platform itself and for the project's house-price model.

These run on every push through GitHub Actions (see .github/workflows/ml-tests.yml):
if the model or the testing engine regresses, the pipeline fails *before deployment*.
"""
import pytest

from app import datasets, fixer, testing


def load(name):
    return datasets.load_df(f"builtin:{name}"), datasets.BUILTIN[name]["target"]


def by_id(result):
    return {t["id"]: t for t in result["tests"]}


# ---------------------------------------------------------------- deployment gate
def test_house_price_model_passes_deployment_gate():
    """The production configuration of the house-price model must be deployable."""
    df, target = load("house_price")
    cfg = {"impute": True, "dedupe": True, "log_target": True, "scale": "standard",
           "protected": ["region"], "params": {"n_estimators": 200, "max_depth": 3, "learning_rate": 0.1}}
    res = testing.run_suite(df, target, "gradient_boosting_reg", cfg)
    gate = res["summary"]["gate"]
    assert gate["status"] == "APPROVED", gate["checks"]
    assert res["metrics"]["r2"] >= 0.85
    assert res["summary"]["score"] >= 85


def test_predictions_are_positive_for_house_prices():
    df, target = load("house_price")
    res = testing.run_suite(df, target, "random_forest_reg", {"impute": True})
    assert by_id(res)["valid_range"]["status"] == "pass"


def test_actual_vs_predicted_comparison_table_is_produced():
    df, target = load("house_price")
    res = testing.run_suite(df, target, "random_forest_reg", {"impute": True})
    row = res["metrics"]["comparison_table"][0]
    assert {"actual", "predicted", "error", "error_pct"} <= set(row)


# ---------------------------------------------------------------- test engine behaviour
def test_engine_has_all_specified_test_types():
    df, target = load("churn")
    ids = set(by_id(testing.run_suite(df, target, "random_forest")))
    assert {"edge_cases", "adversarial", "slices", "fairness", "leakage", "scale_invariance"} <= ids


def test_leakage_is_detected():
    df, target = load("credit")
    res = testing.run_suite(df, target, "random_forest")
    assert by_id(res)["leakage"]["status"] == "fail"
    assert "collections_flag" in by_id(res)["leakage"]["data"]["columns"]


def test_edge_cases_expose_missing_value_crashes():
    df, target = load("churn")
    bad = testing.run_suite(df, target, "logistic_regression")
    good = testing.run_suite(df, target, "logistic_regression", {"impute": True})
    assert by_id(bad)["edge_cases"]["status"] == "fail"
    assert by_id(good)["edge_cases"]["status"] != "fail"


def test_fairness_detects_protected_attributes():
    df, target = load("credit")
    res = testing.run_suite(df, target, "random_forest", {"impute": True})
    fair = by_id(res)["fairness"]
    assert fair["status"] in ("pass", "fail")  # evaluated, not skipped
    assert {"gender", "region", "age"} <= set(fair["data"]["columns"])


def test_task_mismatch_is_rejected():
    df, target = load("house_price")
    with pytest.raises(ValueError):
        testing.run_suite(df, target, "knn")


# ---------------------------------------------------------------- problem solving
@pytest.mark.parametrize("name,model", [("churn", "logistic_regression"), ("house_price", "linear_regression")])
def test_autofix_improves_quality(name, model):
    df, target = load(name)
    before = testing.run_suite(df, target, model)
    after, _, steps, _ = fixer.autofix(df, target, model, before)
    assert steps
    assert after["summary"]["score"] > before["summary"]["score"]


# ---------------------------------------------------------------- API security
def test_api_requires_login_and_isolates_users():
    from fastapi.testclient import TestClient
    from app.main import app

    c = TestClient(app)
    assert c.get("/api/runs").status_code == 401
    a = c.post("/api/auth/signup", json={"name": "Ann", "email": "ann@x.com", "password": "secret1"}).json()
    b = c.post("/api/auth/signup", json={"name": "Bob", "email": "bob@x.com", "password": "secret2"}).json()
    ha, hb = ({"Authorization": f"Bearer {t['token']}"} for t in (a, b))
    run = c.post("/api/runs", headers=ha, json={"dataset_id": "builtin:iris", "target": "species",
                                                 "model": "decision_tree"}).json()
    assert c.get(f"/api/runs/{run['id']}", headers=hb).status_code == 404
    assert c.get("/api/runs", headers=hb).json() == []
