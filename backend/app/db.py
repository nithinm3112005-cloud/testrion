"""SQLite persistence for datasets and test runs."""
import json
import os
import sqlite3
import threading
from contextlib import contextmanager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
DB_PATH = os.path.join(DATA_DIR, "mltestlab.db")

os.makedirs(UPLOAD_DIR, exist_ok=True)
_lock = threading.Lock()


@contextmanager
def conn():
    with _lock:
        c = sqlite3.connect(DB_PATH)
        c.row_factory = sqlite3.Row
        try:
            yield c
            c.commit()
        finally:
            c.close()


def init_db():
    with conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS prediction_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                features TEXT NOT NULL,
                prediction TEXT,
                latency_ms REAL,
                simulated INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS datasets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                filename TEXT,
                rows INTEGER,
                cols INTEGER,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id TEXT NOT NULL,
                dataset_name TEXT,
                target TEXT NOT NULL,
                model TEXT NOT NULL,
                score REAL,
                passed INTEGER,
                warned INTEGER,
                failed INTEGER,
                parent_run_id INTEGER,
                kind TEXT DEFAULT 'test',
                result TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
            """
        )
        # lightweight migrations for databases created before accounts existed
        for table in ("datasets", "runs"):
            cols = [r["name"] for r in c.execute(f"PRAGMA table_info({table})")]
            if "user_id" not in cols:
                c.execute(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER")


def row_to_dict(r):
    return dict(r) if r is not None else None


# ---------- datasets ----------
def add_dataset(ds_id, name, filename, rows, cols, user_id):
    with conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO datasets (id, name, filename, rows, cols, user_id) VALUES (?,?,?,?,?,?)",
            (ds_id, name, filename, rows, cols, user_id),
        )


def list_datasets(user_id):
    with conn() as c:
        return [
            dict(r)
            for r in c.execute("SELECT * FROM datasets WHERE user_id=? ORDER BY created_at DESC", (user_id,))
        ]


def get_dataset(ds_id, user_id=None):
    with conn() as c:
        d = row_to_dict(c.execute("SELECT * FROM datasets WHERE id=?", (ds_id,)).fetchone())
        if d and user_id is not None and d["user_id"] != user_id:
            return None
        return d


def delete_dataset(ds_id, user_id):
    with conn() as c:
        c.execute("DELETE FROM datasets WHERE id=? AND user_id=?", (ds_id, user_id))


# ---------- runs ----------
def add_run(user_id, dataset_id, dataset_name, target, model, result, parent_run_id=None, kind="test"):
    s = result["summary"]
    with conn() as c:
        cur = c.execute(
            """INSERT INTO runs (dataset_id, dataset_name, target, model, score, passed, warned, failed,
                                 parent_run_id, kind, result, user_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                dataset_id,
                dataset_name,
                target,
                model,
                s["score"],
                s["passed"],
                s["warned"],
                s["failed"],
                parent_run_id,
                kind,
                json.dumps(result),
                user_id,
            ),
        )
        return cur.lastrowid


def list_runs(user_id):
    with conn() as c:
        rows = c.execute(
            """SELECT id, dataset_id, dataset_name, target, model, score, passed, warned, failed,
                      parent_run_id, kind, created_at FROM runs WHERE user_id=? ORDER BY id DESC""",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_run(run_id, user_id):
    with conn() as c:
        r = c.execute("SELECT * FROM runs WHERE id=? AND user_id=?", (run_id, user_id)).fetchone()
        if not r:
            return None
        d = dict(r)
        d["result"] = json.loads(d["result"])
        return d


def delete_run(run_id, user_id):
    with conn() as c:
        c.execute("DELETE FROM runs WHERE id=? AND user_id=?", (run_id, user_id))


# ---------- users & sessions ----------
def create_user(name, email, password_hash, salt):
    with conn() as c:
        cur = c.execute(
            "INSERT INTO users (name, email, password_hash, salt) VALUES (?,?,?,?)",
            (name, email, password_hash, salt),
        )
        return cur.lastrowid


def get_user_by_email(email):
    with conn() as c:
        return row_to_dict(c.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone())


def create_session(token, user_id):
    with conn() as c:
        c.execute("INSERT INTO sessions (token, user_id) VALUES (?,?)", (token, user_id))


def get_user_by_token(token, max_age_days=7):
    with conn() as c:
        return row_to_dict(
            c.execute(
                """SELECT u.id, u.name, u.email, u.created_at FROM sessions s JOIN users u ON u.id = s.user_id
                   WHERE s.token=? AND s.created_at > datetime('now', ?)""",
                (token, f"-{max_age_days} days"),
            ).fetchone()
        )


def delete_session(token):
    with conn() as c:
        c.execute("DELETE FROM sessions WHERE token=?", (token,))


# ---------- prediction log (live monitoring) ----------
def log_predictions(user_id, run_id, rows, simulated=False):
    """rows: list of (features_dict, prediction, latency_ms)"""
    with conn() as c:
        c.executemany(
            "INSERT INTO prediction_log (run_id, user_id, features, prediction, latency_ms, simulated) VALUES (?,?,?,?,?,?)",
            [(run_id, user_id, json.dumps(f), str(p), l, int(simulated)) for f, p, l in rows],
        )


def get_prediction_log(user_id, run_id, limit=2000):
    with conn() as c:
        rows = c.execute(
            "SELECT features, prediction, latency_ms, simulated, created_at FROM prediction_log "
            "WHERE user_id=? AND run_id=? ORDER BY id DESC LIMIT ?", (user_id, run_id, limit)).fetchall()
        return [dict(r, features=json.loads(r["features"])) for r in rows]


def clear_prediction_log(user_id, run_id):
    with conn() as c:
        c.execute("DELETE FROM prediction_log WHERE user_id=? AND run_id=?", (user_id, run_id))
