#!/usr/bin/env python3
"""CI gate: run the automated ML test-suite and exit non-zero if deployment must be blocked.

  python ci_check.py --dataset house_price --model gradient_boosting_reg
  python ci_check.py --csv data.csv --target label --model random_forest --impute
"""
import argparse
import json
import sys

import pandas as pd

from app import datasets, testing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", help="built-in dataset id, e.g. house_price")
    ap.add_argument("--csv", help="path to a CSV file")
    ap.add_argument("--target")
    ap.add_argument("--model", default="random_forest")
    ap.add_argument("--impute", action="store_true")
    ap.add_argument("--report", default="ci-report.json")
    a = ap.parse_args()

    if a.csv:
        df, target = pd.read_csv(a.csv), a.target
    else:
        name = a.dataset or "house_price"
        df, target = datasets.load_df(f"builtin:{name}"), a.target or datasets.BUILTIN[name]["target"]
    res = testing.run_suite(df, target, a.model, {"impute": a.impute, "dedupe": a.impute})
    s = res["summary"]
    print(f"Score {s['score']} (grade {s['grade']}) - {s['passed']} passed / {s['warned']} warnings / {s['failed']} failed")
    for t in res["tests"]:
        if t["status"] in ("warn", "fail"):
            print(f"  [{t['status'].upper():4}] {t['name']}: {t['value']} (target {t['threshold']})")
    print("Deployment gate:", s["gate"]["status"])
    for c in s["gate"]["checks"]:
        print(f"  {'OK ' if c['passed'] else 'N/A' if c['passed'] is None else 'FAIL'} {c['name']} -> {c['value']}")
    with open(a.report, "w") as f:
        json.dump({"summary": s, "tests": res["tests"]}, f, indent=2)
    sys.exit(0 if s["gate"]["status"] == "APPROVED" else 1)


if __name__ == "__main__":
    main()
