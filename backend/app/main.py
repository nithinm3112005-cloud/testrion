"""Testrion API - automated testing and problem solving for ML models."""
import io
import os
import re
import uuid
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

import pandas as pd
import numpy as np
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import auth, datasets, db, fixer, models, testing

app = FastAPI(title="Testrion API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
db.init_db()
auth.ensure_demo_user()
_model_cache = {}
_cache_lock = threading.Lock()

MAX_UPLOAD = 10 * 1024 * 1024


class RunRequest(BaseModel):
    dataset_id: str
    target: str
    model: str = "random_forest"
    config: Optional[dict] = None


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class PredictRequest(BaseModel):
    values: dict


class SimulateRequest(BaseModel):
    n: int = 100
    drift: bool = False


class BatchRequest(BaseModel):
    dataset_id: str
    target: str
    models: Optional[List[str]] = None  # None -> every model that fits the target's task
    config: Optional[dict] = None


def clean_config(cfg):
    """Whitelist + validate user supplied pipeline options."""
    if not cfg:
        return {}
    out = {}
    if isinstance(cfg.get("protected"), list):
        out["protected"] = [str(c) for c in cfg["protected"]][:20]
    for k in ("impute", "dedupe", "drop_constant", "log_target"):
        if k in cfg:
            out[k] = bool(cfg[k])
    if cfg.get("scale") in ("none", "standard", "robust"):
        out["scale"] = cfg["scale"]
    if cfg.get("balance") in (None, "class_weight", "oversample"):
        out["balance"] = cfg.get("balance")
    return out


def owned_dataset(dataset_id, user):
    """Built-ins are shared; uploaded datasets belong to one user."""
    if dataset_id.startswith("builtin:"):
        return
    if not db.get_dataset(dataset_id, user["id"]):
        raise HTTPException(404, "Dataset not found")


def owned_run(run_id, user):
    run = db.get_run(run_id, user["id"])
    if not run:
        raise HTTPException(404, "Run not found")
    return run


# ------------------------------------------------------------------ auth
@app.post("/api/auth/signup")
def signup(req: SignupRequest):
    return auth.signup(req.name, req.email, req.password)


@app.post("/api/auth/login")
def login(req: LoginRequest):
    return auth.login(req.email, req.password)


@app.get("/api/auth/me")
def me(user=Depends(auth.current_user)):
    return {"id": user["id"], "name": user["name"], "email": user["email"], "created_at": user["created_at"]}


@app.post("/api/auth/logout")
def logout(user=Depends(auth.current_user)):
    db.delete_session(user["token"])
    return {"ok": True}


# ------------------------------------------------------------------ meta
@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/models")
def list_models(user=Depends(auth.current_user)):
    return models.model_list()


@app.get("/api/test-catalog")
def test_catalog(user=Depends(auth.current_user)):
    """Static description of every test, used for the 'How it works' page."""
    return [
        {"category": "Data Quality", "tests": [
            ["Missing values handled", "Detects gaps and checks the pipeline handles them."],
            ["Duplicate rows", "Finds duplicates that leak between train and test."],
            ["Class balance / target skew", "Minority ratio (classification) or target skewness (regression)."],
            ["Constant features", "Finds columns with a single value."],
            ["Outlier exposure", "Counts extreme values (|z| > 4)."],
            ["Target leakage", "Flags features that almost perfectly predict the target."],
            ["Sufficient sample size", "Checks rows per feature."]]},
        {"category": "Model Performance", "tests": [
            ["Hold-out macro F1 / R²", "Class-balanced quality (or variance explained) on unseen data."],
            ["Mean absolute % error", "Regression: average relative error of predictions."],
            ["Cross-validation", "k-fold average score."],
            ["Cross-validation stability", "Variance between folds."],
            ["Overfitting gap", "Train vs test difference."],
            ["Worst-class recall / valid predictions", "Weakest class (classification) or positive, finite predictions (regression)."]]},
        {"category": "Robustness", "tests": [
            ["Gaussian noise robustness", "Score drop under input noise."],
            ["Missing values at inference", "Crashes / drop with blank inputs."],
            ["Unit-change invariance", "Metamorphic test: rescale features, retrain, compare."],
            ["Training-order invariance", "Metamorphic test: shuffle training rows."],
            ["Edge-case inputs (generated)", "FR-1.1: min/max, zero, out-of-distribution, null, unseen & special-character inputs."],
            ["Adversarial perturbation", "FR-1.2: worst-case search for prediction flips."]]},
        {"category": "Reliability", "tests": [
            ["Reproducibility", "Same seed must give identical predictions."],
            ["Train/test drift (PSI)", "Distribution shift per feature."],
            ["Prediction latency", "Milliseconds per 1,000 predictions."]]},
        {"category": "Fairness & Slices", "tests": [
            ["Data-slice performance", "FR-1.3: accuracy / error per gender, age and region slice."],
            ["Demographic parity difference", "FR-1.5: outcome-rate gap between protected groups must be < 10%."]]},
    ]


# -------------------------------------------------------------- datasets
@app.get("/api/datasets")
def list_datasets(user=Depends(auth.current_user)):
    uploaded = [{**d, "builtin": False, "description": f"Uploaded file: {d['filename']}", "tags": ["Uploaded"],
                 "source": "Uploaded CSV (your own data)", "origin": "uploaded",
                 "target": None} for d in db.list_datasets(user["id"])]
    return datasets.builtin_list() + uploaded


@app.post("/api/datasets")
async def upload_dataset(file: UploadFile = File(...), user=Depends(auth.current_user)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Only .csv files are supported")
    raw = await file.read()
    if len(raw) > MAX_UPLOAD:
        raise HTTPException(400, "File too large (max 10 MB)")
    try:
        df = pd.read_csv(io.BytesIO(raw))
    except Exception:
        raise HTTPException(400, "Could not parse the CSV file")
    if df.shape[0] < 20 or df.shape[1] < 2:
        raise HTTPException(400, "Dataset needs at least 20 rows and 2 columns")
    ds_id = uuid.uuid4().hex[:10]
    with open(os.path.join(db.UPLOAD_DIR, f"{ds_id}.csv"), "wb") as f:
        f.write(raw)
    name = re.sub(r"\.csv$", "", file.filename, flags=re.I)
    db.add_dataset(ds_id, name, file.filename, int(df.shape[0]), int(df.shape[1]), user["id"])
    return {"id": ds_id, "name": name, "rows": int(df.shape[0]), "cols": int(df.shape[1])}


@app.get("/api/datasets/{dataset_id}/preview")
def dataset_preview(dataset_id: str, user=Depends(auth.current_user)):
    owned_dataset(dataset_id, user)
    try:
        return datasets.preview(dataset_id)
    except KeyError as e:
        raise HTTPException(404, str(e))


@app.get("/api/datasets/{dataset_id}/download")
def dataset_download(dataset_id: str, user=Depends(auth.current_user)):
    owned_dataset(dataset_id, user)
    try:
        df = datasets.load_df(dataset_id)
    except KeyError as e:
        raise HTTPException(404, str(e))
    fname = re.sub(r"[^A-Za-z0-9_-]+", "_", datasets.dataset_name(dataset_id)).strip("_").lower() or "dataset"
    return Response(df.to_csv(index=False), media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="{fname}.csv"'})


@app.delete("/api/datasets/{dataset_id}")
def remove_dataset(dataset_id: str, user=Depends(auth.current_user)):
    if dataset_id.startswith("builtin:"):
        raise HTTPException(400, "Built-in datasets cannot be deleted")
    owned_dataset(dataset_id, user)
    path = os.path.join(db.UPLOAD_DIR, f"{dataset_id}.csv")
    if os.path.exists(path):
        os.remove(path)
    db.delete_dataset(dataset_id, user["id"])
    return {"ok": True}


# ------------------------------------------------------------------ runs
@app.post("/api/runs")
def create_run(req: RunRequest, user=Depends(auth.current_user)):
    owned_dataset(req.dataset_id, user)
    if req.model not in models.REGISTRY:
        raise HTTPException(422, "Unknown model")
    try:
        df = datasets.load_df(req.dataset_id)
    except KeyError as e:
        raise HTTPException(404, str(e))
    try:
        result = testing.run_suite(df, req.target, req.model, clean_config(req.config))
    except ValueError as e:
        raise HTTPException(422, str(e))
    run_id = db.add_run(user["id"], req.dataset_id, datasets.dataset_name(req.dataset_id), req.target,
                        req.model, result)
    return db.get_run(run_id, user["id"])


@app.get("/api/runs")
def list_runs(user=Depends(auth.current_user)):
    return db.list_runs(user["id"])


@app.get("/api/runs/{run_id}")
def get_run(run_id: int, user=Depends(auth.current_user)):
    return owned_run(run_id, user)


@app.delete("/api/runs/{run_id}")
def remove_run(run_id: int, user=Depends(auth.current_user)):
    owned_run(run_id, user)
    db.delete_run(run_id, user["id"])
    with _cache_lock:
        _model_cache.pop(run_id, None)
    return {"ok": True}


@app.post("/api/runs/{run_id}/autofix")
def autofix_run(run_id: int, user=Depends(auth.current_user)):
    run = owned_run(run_id, user)
    try:
        df = datasets.load_df(run["dataset_id"])
        result, model_id, steps, comparison = fixer.autofix(df, run["target"], run["model"], run["result"])
    except (ValueError, KeyError) as e:
        raise HTTPException(422, str(e))
    result["fix"] = {
        "parent_run_id": run_id,
        "original_score": run["score"],
        "original_grade": run["result"]["summary"]["grade"],
        "original_model": run["model"],
        "steps": steps,
        "comparison": comparison,
    }
    new_id = db.add_run(user["id"], run["dataset_id"], run["dataset_name"], run["target"], model_id, result,
                        parent_run_id=run_id, kind="autofix")
    return db.get_run(new_id, user["id"])


# ------------------------------------------- playground & model export
def _trained(run):
    with _cache_lock:
        hit = _model_cache.get(run["id"])
    if hit:
        return hit
    cfg = {k: run["result"]["config"][k] for k in testing.DEFAULT_CONFIG}
    try:
        built = testing.fit_final(datasets.load_df(run["dataset_id"]), run["target"], run["model"], cfg)
    except (ValueError, KeyError) as e:
        raise HTTPException(422, str(e))
    with _cache_lock:
        if len(_model_cache) > 20:
            _model_cache.pop(next(iter(_model_cache)))
        _model_cache[run["id"]] = built
    return built


@app.get("/api/runs/{run_id}/schema")
def run_schema(run_id: int, user=Depends(auth.current_user)):
    run = owned_run(run_id, user)
    _, classes, features, _ = _trained(run)
    return {"classes": classes or [], "features": features, "target": run["target"],
            "task": run["result"].get("task", "classification")}


@app.post("/api/runs/{run_id}/predict")
def run_predict(run_id: int, req: PredictRequest, user=Depends(auth.current_user)):
    run = owned_run(run_id, user)
    model, classes, features, _ = _trained(run)
    row = {}
    for f in features:
        v = req.values.get(f["name"])
        blank = v is None or (isinstance(v, str) and v.strip() == "")
        if f["type"] == "numeric":
            try:
                row[f["name"]] = np.nan if blank else float(v)
            except (TypeError, ValueError):
                raise HTTPException(422, f"'{f['name']}' must be a number")
        else:
            row[f["name"]] = np.nan if blank else str(v)
    X = pd.DataFrame([row], columns=[f["name"] for f in features])
    t0 = time.perf_counter()
    try:
        raw_pred = model.predict(X)[0]
    except ValueError:
        raise HTTPException(422, "This model was trained without imputation and cannot handle blank fields. "
                                 "Fill in every field (or run Auto-fix to add imputation).")
    latency = (time.perf_counter() - t0) * 1000
    shown = {k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in row.items()}
    if classes is None:  # regression
        value = float(raw_pred)
        db.log_predictions(user["id"], run_id, [(shown, round(value, 4), latency)])
        return {"label": round(value, 4), "probabilities": None, "task": "regression", "latency_ms": round(latency, 2)}
    pred = int(raw_pred)
    db.log_predictions(user["id"], run_id, [(shown, classes[pred], latency)])
    probs = None
    if hasattr(model, "predict_proba"):
        try:
            p = model.predict_proba(X)[0]
            probs = [{"class": c, "p": float(x)} for c, x in zip(classes, p)]
        except Exception:
            probs = None
    return {"label": classes[pred], "probabilities": probs, "task": "classification",
            "latency_ms": round(latency, 2)}


@app.get("/api/runs/{run_id}/export")
def run_export(run_id: int, user=Depends(auth.current_user)):
    import io as _io
    import pickle

    run = owned_run(run_id, user)
    model, classes, features, _ = _trained(run)
    buf = _io.BytesIO()
    pickle.dump({"model": model, "classes": classes, "features": features, "target": run["target"],
                 "config": run["result"]["config"]}, buf)
    return Response(buf.getvalue(), media_type="application/octet-stream",
                    headers={"Content-Disposition": f'attachment; filename="model-run{run_id}.pkl"'})


# ----------------------------------------------- live drift monitoring
def _psi_series(ref, live, numeric):
    ref, live = ref.dropna(), live.dropna()
    if len(ref) < 20 or len(live) < 10:
        return None
    if numeric:
        edges = np.unique(np.quantile(ref.astype(float), np.linspace(0, 1, 9)))
        if len(edges) < 3:
            return 0.0
        edges[0], edges[-1] = -np.inf, np.inf
        pa = np.histogram(ref.astype(float), edges)[0] / len(ref)
        pb = np.histogram(live.astype(float), edges)[0] / len(live)
    else:
        cats = sorted(set(ref.astype(str)) | set(live.astype(str)))
        pa = np.array([(ref.astype(str) == c).mean() for c in cats])
        pb = np.array([(live.astype(str) == c).mean() for c in cats])
    pa, pb = np.clip(pa, 1e-4, None), np.clip(pb, 1e-4, None)
    return float(np.sum((pb - pa) * np.log(pb / pa)))


@app.get("/api/runs/{run_id}/monitor")
def run_monitor(run_id: int, user=Depends(auth.current_user)):
    t0 = time.perf_counter()
    run = owned_run(run_id, user)
    _, _, features, ref = _trained(run)
    log = db.get_prediction_log(user["id"], run_id)
    lat = sorted(r["latency_ms"] for r in log if r["latency_ms"] is not None)
    feats = []
    if log:
        live = pd.DataFrame([r["features"] for r in log])
        for f in features:
            if f["name"] not in live:
                continue
            numeric = f["type"] == "numeric"
            psi = _psi_series(ref[f["name"]], live[f["name"]], numeric)
            feats.append({"name": f["name"], "psi": psi,
                          "status": None if psi is None else "pass" if psi < 0.10 else "warn" if psi < 0.25 else "fail",
                          "ref_mean": float(ref[f["name"]].mean()) if numeric else None,
                          "live_mean": float(pd.to_numeric(live[f["name"]], errors="coerce").mean()) if numeric else None})
    worst = max((f["psi"] for f in feats if f["psi"] is not None), default=0.0)
    return {
        "n": len(log),
        "avg_latency_ms": round(sum(lat) / len(lat), 2) if lat else 0,
        "p95_latency_ms": round(lat[int(0.95 * (len(lat) - 1))], 2) if lat else 0,
        "features": feats,
        "drift_status": "insufficient data" if len(log) < 30 else "DRIFT DETECTED" if worst >= 0.25
                        else "warning" if worst >= 0.10 else "stable",
        "max_psi": round(worst, 3),
        "detect_ms": round((time.perf_counter() - t0) * 1000, 1),
        "recent": [{"features": r["features"], "prediction": r["prediction"],
                    "latency_ms": round(r["latency_ms"], 2), "simulated": bool(r["simulated"]),
                    "at": r["created_at"]} for r in log[:12]],
        "latency_series": [round(r["latency_ms"], 2) for r in reversed(log[:60])],
    }


@app.post("/api/runs/{run_id}/simulate")
def run_simulate(run_id: int, req: SimulateRequest, user=Depends(auth.current_user)):
    """Replays training-like traffic (optionally shifted) through the live model to demo drift detection."""
    run = owned_run(run_id, user)
    model, classes, features, ref = _trained(run)
    n = max(10, min(req.n, 200))
    rng = np.random.RandomState(int(time.time()) % 10_000)
    sample = ref.sample(n, replace=True, random_state=rng).reset_index(drop=True)
    num = [f["name"] for f in features if f["type"] == "numeric"]
    cats = [f for f in features if f["type"] == "categorical"]
    if req.drift:
        for c in num[:3]:
            sample[c] = sample[c].astype(float) + 1.6 * float(ref[c].std() or 1.0)
        for f in cats[:1]:
            sample[f["name"]] = f["options"][-1] if f["options"] else sample[f["name"]]
    rows = []
    for i in range(n):
        one = sample.iloc[[i]]
        t0 = time.perf_counter()
        try:
            raw = model.predict(one)[0]
        except Exception:
            continue
        lat = (time.perf_counter() - t0) * 1000
        pred = round(float(raw), 4) if classes is None else classes[int(raw)]
        feat = {k: (None if isinstance(v, float) and np.isnan(v) else (v.item() if hasattr(v, "item") else v))
                for k, v in one.iloc[0].to_dict().items()}
        rows.append((feat, pred, lat))
    db.log_predictions(user["id"], run_id, rows, simulated=True)
    return {"logged": len(rows), "drift": req.drift}


@app.delete("/api/runs/{run_id}/monitor")
def clear_monitor(run_id: int, user=Depends(auth.current_user)):
    owned_run(run_id, user)
    db.clear_prediction_log(user["id"], run_id)
    return {"ok": True}


# ------------------------------------------- parallel benchmark (scalability)
@app.post("/api/batch")
def batch_run(req: BatchRequest, user=Depends(auth.current_user)):
    owned_dataset(req.dataset_id, user)
    try:
        df = datasets.load_df(req.dataset_id)
    except KeyError as e:
        raise HTTPException(404, str(e))
    if req.target not in df.columns:
        raise HTTPException(422, f"Target column '{req.target}' not found in dataset")
    task = testing.detect_task(df, req.target)
    ids = [m for m in (req.models or []) if m in models.REGISTRY] or \
          [k for k, v in models.REGISTRY.items() if v["task"] == task]
    ids = [m for m in ids if models.REGISTRY[m]["task"] == task]
    if not ids:
        raise HTTPException(422, "No models selected for this target")
    cfg = clean_config(req.config)
    t0 = time.perf_counter()

    def work(mid):
        try:
            return mid, testing.run_suite(df, req.target, mid, cfg), None
        except ValueError as e:
            return mid, None, str(e)

    with ThreadPoolExecutor(max_workers=min(8, len(ids))) as pool:
        results = list(pool.map(work, ids))
    elapsed = time.perf_counter() - t0
    out, sequential = [], 0.0
    for mid, res, err in results:
        if res is None:
            out.append({"model": mid, "error": err})
            continue
        sequential += res["duration_sec"]
        rid = db.add_run(user["id"], req.dataset_id, datasets.dataset_name(req.dataset_id), req.target, mid, res)
        out.append({"id": rid, "model": mid, "score": res["summary"]["score"],
                    "gate": res["summary"]["gate"]["status"]})
    return {"runs": out, "elapsed_sec": round(elapsed, 2), "sequential_sec": round(sequential, 2),
            "speedup": round(sequential / elapsed, 2) if elapsed else 1.0, "models": len(ids)}


@app.get("/api/stats")
def stats(user=Depends(auth.current_user)):
    runs = db.list_runs(user["id"])
    tests = [r for r in runs if r["kind"] == "test"]
    fixes = [r for r in runs if r["kind"] == "autofix"]
    gains = []
    parents = {r["id"]: r for r in runs}
    for f in fixes:
        p = parents.get(f["parent_run_id"])
        if p:
            gains.append(f["score"] - p["score"])
    return {
        "total_runs": len(runs),
        "avg_score": round(sum(r["score"] for r in runs) / len(runs), 1) if runs else 0,
        "tests_passed": sum(r["passed"] for r in runs),
        "issues_found": sum(r["failed"] + r["warned"] for r in tests),
        "auto_fixes": len(fixes),
        "avg_improvement": round(sum(gains) / len(gains), 1) if gains else 0,
        "trend": [{"id": r["id"], "score": r["score"], "label": f"#{r['id']}", "kind": r["kind"]}
                  for r in reversed(runs[:15])],
    }


# --------------------------------------------------- static frontend (prod)
DIST = os.path.join(os.path.dirname(db.BASE_DIR), "frontend", "dist")
if os.path.isdir(DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(404, "Not found")
        candidate = os.path.join(DIST, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(DIST, "index.html"))
