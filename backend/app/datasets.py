"""Built-in sample datasets + dataset loading helpers."""
import os

import numpy as np
import pandas as pd
from sklearn import datasets as skd

from . import db

MAX_ROWS = 6000  # cap for responsiveness


def _from_sklearn(loader, target_name="target", rename_classes=None):
    b = loader(as_frame=True)
    df = b.frame.copy()
    if rename_classes is not None:
        df[target_name] = df[target_name].map(lambda i: rename_classes[int(i)])
    return df


def _churn():
    """Messy synthetic customer-churn data: missing values, duplicates,
    class imbalance, a constant column and unscaled features."""
    rng = np.random.RandomState(7)
    n = 1800
    tenure = rng.randint(1, 72, n)
    monthly = rng.normal(70, 25, n).clip(15, 140)
    support_calls = rng.poisson(2, n)
    contract = rng.choice(["Month-to-month", "One year", "Two year"], n, p=[0.55, 0.25, 0.2])
    internet = rng.choice(["DSL", "Fiber", "None"], n, p=[0.35, 0.45, 0.2])
    total = tenure * monthly + rng.normal(0, 200, n)
    logit = (
        -3.0
        + 1.7 * (contract == "Month-to-month")
        - 0.045 * tenure
        + 0.03 * (monthly - 70)
        + 0.55 * support_calls
        + 0.9 * (internet == "Fiber")
    )
    logit = 2.8 * (logit - np.quantile(logit, 0.74))  # clearer pattern, ~26% churn
    churn = (rng.rand(n) < 1 / (1 + np.exp(-logit))).astype(int)
    df = pd.DataFrame(
        {
            "tenure_months": tenure,
            "monthly_charges": monthly.round(2),
            "total_charges": total.round(2) * 10,  # deliberately large scale
            "support_calls": support_calls,
            "contract": contract,
            "internet_service": internet,
            "country_code": "IN",  # constant column
            "churn": np.where(churn == 1, "Yes", "No"),
        }
    )
    for col, frac in [("monthly_charges", 0.08), ("tenure_months", 0.05), ("contract", 0.04)]:
        idx = rng.choice(n, int(n * frac), replace=False)
        df[col] = df[col].astype(object) if col == "contract" else df[col].astype(float)
        df.loc[idx, col] = np.nan
    dup = df.sample(90, random_state=1)
    return pd.concat([df, dup], ignore_index=True)


def _credit():
    """Synthetic credit-default data with severe imbalance + leakage feature."""
    rng = np.random.RandomState(11)
    n = 2500
    income = rng.lognormal(10.6, 0.5, n)
    debt_ratio = rng.beta(2, 5, n)
    age = rng.randint(21, 70, n)
    late_payments = rng.poisson(0.6, n)
    credit_lines = rng.randint(1, 15, n)
    logit = -4.6 + 6.5 * debt_ratio + 1.0 * late_payments - 0.00004 * (income - 40000) - 0.03 * (age - 40)
    logit = 2.8 * (logit - np.quantile(logit, 0.85))  # clearer pattern, ~15% default
    default = (rng.rand(n) < 1 / (1 + np.exp(-logit))).astype(int)
    collections_flag = np.where(default == 1, rng.rand(n) < 0.97, rng.rand(n) < 0.01).astype(int)  # leakage
    gender = rng.choice(["Male", "Female"], n)
    region = rng.choice(["Urban", "Semi-urban", "Rural"], n, p=[0.45, 0.30, 0.25])
    df = pd.DataFrame(
        {
            "gender": gender,
            "region": region,
            "annual_income": income.round(0),
            "debt_ratio": debt_ratio.round(3),
            "age": age,
            "late_payments": late_payments,
            "open_credit_lines": credit_lines,
            "collections_flag": collections_flag,
            "default": np.where(default == 1, "Default", "Paid"),
        }
    )
    idx = rng.choice(n, int(n * 0.03), replace=False)
    df.loc[idx, "annual_income"] = np.nan
    return df


def _house(n=1600):
    """Synthetic house-price data (lakhs of rupees) - the project's regression dataset.
    Messy on purpose: missing values, duplicates, outliers and a skewed target."""
    rng = np.random.RandomState(21)
    area = rng.normal(1250, 420, n).clip(350, 4200)
    bedrooms = np.clip(np.round(area / 480 + rng.normal(0, 0.7, n)), 1, 6).astype(int)
    bathrooms = np.clip(bedrooms - rng.randint(0, 2, n), 1, 5)
    year_built = rng.randint(1975, 2025, n)
    dist = rng.gamma(3.0, 3.2, n).clip(0.5, 40)
    garage = rng.choice([0, 1, 2], n, p=[0.3, 0.5, 0.2])
    region = rng.choice(["North", "South", "East", "West", "Central"], n, p=[0.2, 0.25, 0.15, 0.2, 0.2])
    ptype = rng.choice(["Apartment", "Independent House", "Villa"], n, p=[0.5, 0.35, 0.15])
    rf = pd.Series(region).map({"North": 1.0, "South": 1.12, "East": 0.9, "West": 1.25, "Central": 1.18}).values
    tf = pd.Series(ptype).map({"Apartment": 1.0, "Independent House": 1.15, "Villa": 1.6}).values
    base = (area * 0.052 + bedrooms * 3.2 + bathrooms * 2.1 + garage * 4.5 + (year_built - 1975) * 0.35
            - dist * 0.9 + 12)
    price = base * rf * tf * np.exp(rng.normal(0, 0.12, n))
    df = pd.DataFrame({
        "area_sqft": area.round(0), "bedrooms": bedrooms, "bathrooms": bathrooms, "year_built": year_built,
        "distance_to_city_km": dist.round(1), "garage_spaces": garage, "region": region,
        "property_type": ptype, "price_lakhs": price.round(2),
    })
    for col, frac in [("area_sqft", 0.05), ("distance_to_city_km", 0.06), ("region", 0.03)]:
        idx = rng.choice(n, int(n * frac), replace=False)
        if col == "region":
            df[col] = df[col].astype(object)
        df.loc[idx, col] = np.nan
    out = rng.choice(n, max(12, n // 130), replace=False)
    df.loc[out, "area_sqft"] = df.loc[out, "area_sqft"] * 4 + 3000  # data-entry outliers
    return pd.concat([df, df.sample(max(40, n // 40), random_state=2)], ignore_index=True)


BUILTIN = {
    "house_price": {
        "source": "Generated by Testrion (seeded, reproducible)",
        "origin": "synthetic",
        "name": "House Price Prediction",
        "description": "Regression dataset from the project spec: predict price (lakhs) from area, rooms, region and age.",
        "target": "price_lakhs",
        "tags": ["Regression", "Messy", "Project dataset"],
        "loader": _house,
    },
    "iris": {
        "source": "scikit-learn built-in (UCI Iris, Fisher 1936)",
        "origin": "real",
        "name": "Iris Flowers",
        "description": "Classic 3-class flower measurements. Clean and balanced.",
        "target": "species",
        "tags": ["Clean", "Multi-class"],
        "loader": lambda: _from_sklearn(
            skd.load_iris, "target", ["setosa", "versicolor", "virginica"]
        ).rename(columns={"target": "species"}),
    },
    "wine": {
        "source": "scikit-learn built-in (UCI Wine recognition)",
        "origin": "real",
        "name": "Wine Quality Classes",
        "description": "13 chemical features, 3 cultivars. Unscaled features.",
        "target": "cultivar",
        "tags": ["Unscaled", "Multi-class"],
        "loader": lambda: _from_sklearn(skd.load_wine, "target", ["class_0", "class_1", "class_2"]).rename(
            columns={"target": "cultivar"}
        ),
    },
    "breast_cancer": {
        "source": "scikit-learn built-in (UCI Breast Cancer Wisconsin)",
        "origin": "real",
        "name": "Breast Cancer Diagnosis",
        "description": "30 cell-nucleus measurements, benign vs malignant. Unscaled, mildly imbalanced.",
        "target": "diagnosis",
        "tags": ["Real", "Binary", "Unscaled"],
        "loader": lambda: _from_sklearn(skd.load_breast_cancer, "target", ["malignant", "benign"]).rename(
            columns={"target": "diagnosis"}),
    },
    "diabetes": {
        "source": "scikit-learn built-in (Efron et al. diabetes progression)",
        "origin": "real",
        "name": "Diabetes Progression",
        "description": "10 baseline patient features (age, sex, bmi, ...) predicting disease progression. Noisy regression.",
        "target": "progression",
        "tags": ["Real", "Regression", "Noisy"],
        "loader": lambda: _from_sklearn(skd.load_diabetes).rename(columns={"target": "progression"}),
    },
    "digits": {
        "source": "scikit-learn built-in (UCI optical digits)",
        "origin": "real",
        "name": "Handwritten Digits",
        "description": "8x8 pixel images of digits 0-9 (64 features, 1797 rows). Multi-class stress test.",
        "target": "digit",
        "tags": ["Real", "Multi-class", "High-dimensional"],
        "loader": lambda: _from_sklearn(skd.load_digits).rename(columns={"target": "digit"}),
    },
    "wine_alcohol": {
        "source": "scikit-learn built-in (UCI Wine) - regression view",
        "origin": "real",
        "name": "Wine Alcohol Content (regression)",
        "description": "Predict alcohol from other wine chemistry. Small (178 rows) - shows the data's accuracy ceiling.",
        "target": "alcohol",
        "tags": ["Real", "Regression", "Small"],
        "loader": lambda: _from_sklearn(skd.load_wine).drop(columns=["target"]),
    },
    "churn": {
        "source": "Generated by Testrion (seeded, reproducible)",
        "origin": "synthetic",
        "name": "Customer Churn (messy)",
        "description": "Missing values, duplicates, imbalance and a constant column. Ideal auto-fix demo.",
        "target": "churn",
        "tags": ["Messy", "Imbalanced", "Binary"],
        "loader": _churn,
    },
    "credit": {
        "source": "Generated by Testrion (seeded, reproducible)",
        "origin": "synthetic",
        "name": "Credit Default (risky)",
        "description": "Severe imbalance, missing income and a data-leakage feature.",
        "target": "default",
        "tags": ["Leakage", "Imbalanced", "Binary"],
        "loader": _credit,
    },
}


COLUMN_DOCS = {
    "house_price": {
        "area_sqft": "Built-up area in square feet (some values missing, a few data-entry outliers)",
        "bedrooms": "Number of bedrooms (1-6)",
        "bathrooms": "Number of bathrooms (1-5)",
        "year_built": "Year the house was built (property age = 2025 - year)",
        "distance_to_city_km": "Distance to the city centre in km (some values missing)",
        "garage_spaces": "Number of garage / parking spaces (0-2)",
        "region": "Region of the city: North, South, East, West or Central (used for slice and fairness tests)",
        "property_type": "Apartment, Independent House or Villa",
        "price_lakhs": "TARGET - sale price in lakhs of rupees",
    },
    "churn": {
        "tenure_months": "Months the customer has been with the company (some missing)",
        "monthly_charges": "Monthly bill amount (some missing)",
        "total_charges": "Total billed so far (deliberately on a very large scale)",
        "support_calls": "Number of customer-support calls",
        "contract": "Month-to-month, One year or Two year (some missing)",
        "internet_service": "DSL, Fiber or None",
        "country_code": "Constant column (always the same value) - a data-quality trap",
        "churn": "TARGET - did the customer leave (Yes / No)",
    },
    "credit": {
        "gender": "Male / Female (protected attribute for the fairness test)",
        "region": "Urban, Semi-urban or Rural (protected attribute)",
        "annual_income": "Yearly income (some missing)",
        "debt_ratio": "Debt-to-income ratio (0-1)",
        "age": "Age in years (protected attribute, tested in age bands)",
        "late_payments": "Count of late payments",
        "open_credit_lines": "Number of open credit lines",
        "collections_flag": "LEAKAGE - flag set after the customer defaulted; it reveals the answer",
        "default": "TARGET - Default / Paid",
    },
}


def builtin_list():
    out = []
    for key, v in BUILTIN.items():
        df = v["loader"]()
        out.append(
            {
                "id": f"builtin:{key}",
                "name": v["name"],
                "description": v["description"],
                "target": v["target"],
                "tags": v["tags"],
                "source": v["source"],
                "origin": v["origin"],
                "rows": int(len(df)),
                "cols": int(df.shape[1]),
                "builtin": True,
            }
        )
    return out


def load_df(dataset_id: str) -> pd.DataFrame:
    if dataset_id.startswith("builtin:"):
        key = dataset_id.split(":", 1)[1]
        if key not in BUILTIN:
            raise KeyError("Unknown built-in dataset")
        return BUILTIN[key]["loader"]()
    path = os.path.join(db.UPLOAD_DIR, f"{dataset_id}.csv")
    if not os.path.exists(path):
        raise KeyError("Dataset file not found")
    return pd.read_csv(path)


def dataset_name(dataset_id: str) -> str:
    if dataset_id.startswith("builtin:"):
        return BUILTIN[dataset_id.split(":", 1)[1]]["name"]
    d = db.get_dataset(dataset_id)
    return d["name"] if d else dataset_id


def preview(dataset_id: str):
    df = load_df(dataset_id)
    cols = []
    for c in df.columns:
        s = df[c]
        numeric = pd.api.types.is_numeric_dtype(s)
        nu = int(s.nunique(dropna=True))
        task = "regression" if numeric and nu > 20 else "classification" if 2 <= nu <= 30 else None
        cols.append(
            {
                "name": str(c),
                "dtype": "numeric" if numeric else "categorical",
                "missing": int(s.isna().sum()),
                "unique": nu,
                "suitable": task is not None,
                "task": task,
                "doc": COLUMN_DOCS.get(dataset_id.split(":", 1)[1], {}).get(str(c)) if dataset_id.startswith("builtin:") else None,
            }
        )
    # suggest a target: last column with few unique values, else any low-cardinality column
    suggested = None
    if dataset_id.startswith("builtin:"):
        suggested = BUILTIN[dataset_id.split(":", 1)[1]]["target"]
    else:
        for c in reversed(cols):
            if c["suitable"]:
                suggested = c["name"]
                break
    head = df.head(8).astype(object).where(df.head(8).notna(), None)
    src = BUILTIN[dataset_id.split(":", 1)[1]]["source"] if dataset_id.startswith("builtin:") else "Uploaded CSV"
    return {
        "id": dataset_id,
        "name": dataset_name(dataset_id),
        "source": src,
        "rows": int(len(df)),
        "cols": int(df.shape[1]),
        "columns": cols,
        "suggested_target": suggested,
        "head": head.values.tolist(),
        "head_columns": [str(c) for c in df.columns],
    }
