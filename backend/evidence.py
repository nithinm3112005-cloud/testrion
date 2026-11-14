#!/usr/bin/env python3
"""Generate EVIDENCE.md: example results for every test type + measured benchmarks.

  python evidence.py            # full run (1M-record and 100-model benchmarks, takes a few minutes)
  python evidence.py --quick    # test evidence only

Nothing in the output is estimated: every number is measured on the machine that runs it.
"""
import argparse
import os
import platform
import sys
import tempfile
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

os.environ.setdefault("MLTESTLAB_MAX_ROWS", "2000000")  # lift the interactive 6,000-row cap for benchmarks

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import db  # noqa: E402

db.DB_PATH = os.path.join(tempfile.mkdtemp(), "evidence.db")
from app import datasets, fixer, testing  # noqa: E402

OUT = []


def w(line=""):
    OUT.append(line)
    print(line, flush=True)


def table(headers, rows):
    w("| " + " | ".join(headers) + " |")
    w("|" + "|".join("---" for _ in headers) + "|")
    for r in rows:
        w("| " + " | ".join(str(c) for c in r) + " |")
    w()


def by_id(res):
    return {t["id"]: t for t in res["tests"]}


def evidence():
    df, target = datasets.load_df("builtin:house_price"), "price_lakhs"
    before = testing.run_suite(df, target, "linear_regression")
    after_cfg = {"impute": True, "dedupe": True, "log_target": True, "scale": "standard",
                 "protected": ["region"], "params": {"n_estimators": 200, "max_depth": 3, "learning_rate": 0.1}}
    after = testing.run_suite(df, target, "gradient_boosting_reg", after_cfg)
    w("## 1. Evidence for each test type (house-price dataset)")
    w()
    w("*Before* = Linear Regression, raw data. *After* = Gradient Boosting with the repaired pipeline "
      "(imputation, de-duplication, log-target, scaling).")
    w()
    rows = []
    for tid, label in (("edge_cases", "Edge-case inputs"), ("adversarial", "Adversarial perturbation"),
                       ("slices", "Data-slice performance"), ("fairness", "Demographic parity difference"),
                       ("holdout_r2", "Hold-out R²"), ("valid_range", "Positive predictions")):
        b, a = by_id(before)[tid], by_id(after)[tid]
        rows.append([label, f"{b['value']} ({b['status']})", f"{a['value']} ({a['status']})", a["threshold"]])
    table(["Test", "Before", "After", "Target"], rows)
    w("**Edge cases generated (before):**")
    w()
    table(["Edge-case type", "Cases", "Crashed / invalid"],
          [[k, v["cases"], v["failed"]] for k, v in by_id(before)["edge_cases"]["data"]["by_kind"].items()])
    w("**Data slices by region (after):**")
    w()
    table(["Region", "Test rows", "Mean abs. % error"],
          [[s["group"], s["n"], f"{s['metric'] * 100:.1f}%"] for s in after["metrics"]["slices"] if s["column"] == "region"])
    for label, res in (("Before", before), ("After", after)):
        g = res["summary"]["gate"]
        w(f"**Deployment gate - {label}: {g['status']}** (score {res['summary']['score']}, grade {res['summary']['grade']})")
        w()
        table(["Check", "Value", "Result"], [[c["name"], c["value"], {True: "pass", False: "FAIL", None: "n/a"}[c["passed"]]]
                                              for c in g["checks"]])
    m = after["metrics"]
    w(f"**Regression metrics (after):** R² {m['r2']:.3f} · RMSE {m['rmse']:.2f} · MAE {m['mae']:.2f} · MAPE {m['mape'] * 100:.1f}% (price in lakhs)")
    w()
    w("**Actual vs predicted (first 8 test rows, after):**")
    w()
    table(["Actual", "Predicted", "Error %"], [[f"{r['actual']:.1f}", f"{r['predicted']:.1f}", f"{r['error_pct'] * 100:.1f}%"]
                                               for r in m["comparison_table"][:8]])
    # auto-repair evidence (the project title says "problem solving")
    fixed, mid, steps, _ = fixer.autofix(df, target, "linear_regression", before)
    w(f"**Automatic problem solving:** score {before['summary']['score']} → {fixed['summary']['score']}, "
      f"gate {before['summary']['gate']['status']} → {fixed['summary']['gate']['status']} after these automatic steps:")
    w()
    for s in steps:
        w(f"- {s['title']} — `{s['change']}`")
    w()


def bench_million():
    w("## 2. Benchmark: test execution speed (target: 1M records, full suite < 15 min)")
    w()
    t = time.time()
    big = datasets._house(1_000_000)
    gen = time.time() - t
    t = time.time()
    res = testing.run_suite(big, "price_lakhs", "ridge", {"impute": True, "dedupe": True, "log_target": True,
                                                          "scale": "standard"})
    dur = time.time() - t
    n = res["profile"]["usable_rows"]
    table(["Dataset rows", "Model", "Tests executed", "Wall-clock", "Target", "Result"],
          [[f"{len(big):,} ({n:,} usable)", "Ridge Regression", res["summary"]["total"], f"{dur:.0f} s ({dur / 60:.1f} min)",
            "< 15 min", "MET" if dur < 900 else "NOT MET"]])
    w(f"*(Synthetic data generation took {gen:.0f}s and is not included.)* Tree ensembles are much slower per row; "
      "this result applies to the linear model tested.")
    w()


def bench_parallel(n_models=100):
    w(f"## 3. Benchmark: parallel model testing (target: {n_models} models)")
    w()
    df, target = datasets.load_df("builtin:house_price"), "price_lakhs"
    ids = ["linear_regression", "ridge", "decision_tree_reg", "random_forest_reg", "gradient_boosting_reg", "knn_reg"]
    jobs = []
    for i in range(n_models):
        mid = ids[i % len(ids)]
        params = {}
        if mid == "random_forest_reg":
            params = {"n_estimators": 20 + 5 * (i % 5)}
        elif mid == "gradient_boosting_reg":
            params = {"n_estimators": 30 + 10 * (i % 4)}
        elif mid == "ridge":
            params = {"alpha": 0.1 * (1 + i % 7)}
        elif mid == "knn_reg":
            params = {"n_neighbors": 5 + 2 * (i % 5)}
        jobs.append((mid, {"impute": True, "scale": "standard", "params": params}))
    workers = os.cpu_count() or 4
    t = time.time()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda j: testing.run_suite(df, target, j[0], j[1]), jobs))
    wall = time.time() - t
    seq = sum(r["duration_sec"] for r in results)
    table(["Models tested", "Worker threads", "Wall-clock", "Sum of individual run times", "Speed-up", "Target", "Result"],
          [[len(results), workers, f"{wall:.0f} s", f"{seq:.0f} s", f"{seq / wall:.2f}×", f"{n_models} models",
            "MET" if len(results) >= n_models else "NOT MET"]])


def bench_latency():
    w("## 4. Benchmark: drift-detection latency (target: < 5 s) and dashboard load (target: < 3 s)")
    w()
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": "demo@mltestlab.com",
                                                                     "password": "demo1234"}).json()["token"]}
    run = c.post("/api/runs", headers=H, json={"dataset_id": "builtin:house_price", "target": "price_lakhs",
                                               "model": "random_forest_reg", "config": {"impute": True}}).json()
    c.get(f"/api/runs/{run['id']}/monitor", headers=H)  # warm the model cache
    c.post(f"/api/runs/{run['id']}/simulate", headers=H, json={"n": 200, "drift": True})
    t = time.perf_counter()
    m = c.get(f"/api/runs/{run['id']}/monitor", headers=H).json()
    verdict = (time.perf_counter() - t) * 1000
    rows = [["Drift verdict after 200 live (drifted) predictions", f"{verdict:.0f} ms (server-side compute {m['detect_ms']} ms)",
             "< 5 s", "MET" if verdict < 5000 else "NOT MET"],
            ["Verdict returned", m["drift_status"], "DRIFT DETECTED", "MET" if m["drift_status"] == "DRIFT DETECTED" else "NOT MET"],
            ["Mean single-prediction latency", f"{m['avg_latency_ms']} ms (p95 {m['p95_latency_ms']} ms)", "-", "-"]]
    try:  # dashboard: fetch the page, its bundles and the stats API from the running server
        base = "http://127.0.0.1:8000"
        t = time.perf_counter()
        html = urllib.request.urlopen(base + "/app", timeout=5).read().decode()
        import re
        for a in re.findall(r'(?:src|href)="(/assets/[^"]+)"', html):
            urllib.request.urlopen(base + a, timeout=5).read()
        total = (time.perf_counter() - t) * 1000
        rows.append(["Dashboard page + JS/CSS bundles over localhost (excludes browser render)", f"{total:.0f} ms", "< 3 s",
                     "MET" if total < 3000 else "NOT MET"])
    except Exception:
        rows.append(["Dashboard load", "server not running - skipped", "< 3 s", "-"])
    table(["Measurement", "Result", "Target", "Status"], rows)
    w("*Interpretation of the slide: \"under 5 delay\" is taken to mean 5 seconds.* In the app the browser-measured "
      "dashboard load time is also displayed live on the Dashboard page.")
    w()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    w("# Testrion - evidence and benchmarks")
    w()
    w(f"Generated {time.strftime('%Y-%m-%d %H:%M')} on {platform.platform()} · Python {platform.python_version()} · "
      f"{os.cpu_count()} CPU cores.")
    w()
    evidence()
    if not a.quick:
        bench_million()
        bench_parallel(100)
        bench_latency()
    w("## Validation discipline")
    w()
    w("Every model is evaluated on a 25% hold-out test split that is never used to fit, tune or select a model. "
      "Cross-validation (the *validation* score) runs only inside the remaining 75%, and the auto-fix engine keeps "
      "a tuning or model change only if that validation score does not get worse. The final deployed/exported model "
      "(`model.pkl`) is re-trained on all rows after evaluation.")
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "EVIDENCE.md")
    with open(path, "w") as f:
        f.write("\n".join(OUT) + "\n")
    print("\nwritten:", path)


if __name__ == "__main__":
    main()
