"""Streamlit front-end (as named in the project methodology).

Run:  streamlit run streamlit_app.py
Shows: data entry -> prediction, actual-vs-predicted comparison table, automated test results
and the deployment gate. It uses exactly the same testing engine as the web app.
"""
import pandas as pd
import streamlit as st

from app import datasets, fixer, testing
from app.models import REGISTRY

st.set_page_config(page_title="Testrion · Streamlit", page_icon="✅", layout="wide")
st.title("✅ Automated Testing & Problem Solving of ML Models")
st.caption("House-price prediction · automated test cases · deployment gate")

names = {k: v["name"] for k, v in datasets.BUILTIN.items()}
with st.sidebar:
    st.header("Configuration")
    ds = st.selectbox("Dataset", list(names), format_func=names.get, index=0)
    df = datasets.load_df(f"builtin:{ds}")
    target = datasets.BUILTIN[ds]["target"]
    task = testing.detect_task(df, target)
    options = [k for k, v in REGISTRY.items() if v["task"] == task]
    model_id = st.selectbox("Model", options, format_func=lambda k: REGISTRY[k]["label"],
                            index=options.index("random_forest_reg") if "random_forest_reg" in options else 0)
    autofix = st.checkbox("Apply Auto-fix (repair data, tune, search models)", value=False)
    run = st.button("Run automated tests", type="primary", use_container_width=True)


@st.cache_data(show_spinner="Running automated tests…")
def run_tests(ds_, model_, fix_):
    d = datasets.load_df(f"builtin:{ds_}")
    t = datasets.BUILTIN[ds_]["target"]
    res = testing.run_suite(d, t, model_)
    final_model = model_
    if fix_:
        res, final_model, _, _ = fixer.autofix(d, t, model_, res)
    return res, final_model


if run or "res" in st.session_state:
    if run:
        st.session_state.res, st.session_state.model = run_tests(ds, model_id, autofix)
    res, final_model = st.session_state.res, st.session_state.model
    s = res["summary"]
    gate = s["gate"]

    (st.success if gate["status"] == "APPROVED" else st.error)(
        f"Deployment {gate['status']} — quality score {s['score']} (grade {s['grade']}): "
        f"{s['passed']} passed · {s['warned']} warnings · {s['failed']} failed")

    t_pred, t_cmp, t_tests, t_gate = st.tabs(["🔮 Prediction", "📊 Actual vs predicted", "🧪 Test results", "🚦 Deployment gate"])

    with t_pred:
        model, classes, features, _ = testing.fit_final(df, target, final_model, res["config"])
        st.write("Enter values and get a prediction from the tested model.")
        cols = st.columns(3)
        row = {}
        for i, f in enumerate(features):
            with cols[i % 3]:
                if f["type"] == "numeric":
                    row[f["name"]] = st.number_input(f["name"], value=float(f["median"]))
                else:
                    row[f["name"]] = st.selectbox(f["name"], f["options"])
        if st.button("Predict"):
            X = pd.DataFrame([row])
            p = model.predict(X)[0]
            st.metric(f"Predicted {target}", f"{p:,.2f}" if classes is None else classes[int(p)])

    with t_cmp:
        m = res["metrics"]
        if m["task"] == "regression":
            st.dataframe(pd.DataFrame(m["comparison_table"]).rename(columns={
                "actual": "Actual", "predicted": "Predicted", "error": "Error", "error_pct": "Error %"}),
                use_container_width=True)
            st.scatter_chart(pd.DataFrame(m["scatter"]), x="actual", y="predicted")
            c = st.columns(4)
            c[0].metric("R²", f"{m['r2']:.3f}"); c[1].metric("RMSE", f"{m['rmse']:.2f}")
            c[2].metric("MAE", f"{m['mae']:.2f}"); c[3].metric("MAPE", f"{m['mape'] * 100:.1f}%")
        else:
            st.dataframe(pd.DataFrame(m["per_class"]), use_container_width=True)
            st.write("Confusion matrix", pd.DataFrame(m["confusion_matrix"], index=m["classes"], columns=m["classes"]))

    with t_tests:
        icon = {"pass": "✅", "warn": "⚠️", "fail": "❌", "skip": "➖"}
        st.dataframe(pd.DataFrame([{"": icon[t["status"]], "Category": t["category"], "Test": t["name"],
                                    "Value": t["value"], "Target": t["threshold"], "Finding": t["details"]}
                                   for t in res["tests"]]), use_container_width=True, hide_index=True)

    with t_gate:
        for c in gate["checks"]:
            mark = "✅" if c["passed"] else "➖" if c["passed"] is None else "❌"
            st.write(f"{mark} **{c['name']}** — {c['value']}")
else:
    st.info("Choose a dataset and model in the sidebar, then press **Run automated tests**.")
