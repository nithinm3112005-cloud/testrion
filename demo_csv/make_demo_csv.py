#!/usr/bin/env python3
"""Generates the demo CSV files in this folder (synthetic, seeded, reproducible).
Run:  backend/.venv/bin/python demo_csv/make_demo_csv.py
"""
import os

import numpy as np
import pandas as pd

OUT = os.path.dirname(os.path.abspath(__file__))
sig = lambda z: 1 / (1 + np.exp(-z))


def save(df, name):
    df.to_csv(os.path.join(OUT, name), index=False)
    print(f"{name:<26} {df.shape[0]:>5} rows x {df.shape[1]:>2} cols")


# 1 ---------------------------------------------------------------- used cars (regression, messy)
def used_cars():
    r = np.random.RandomState(101); n = 1500
    brand = r.choice(["Maruti", "Hyundai", "Honda", "Toyota", "Tata"], n, p=[.3, .25, .17, .15, .13])
    fuel = r.choice(["Petrol", "Diesel", "CNG"], n, p=[.55, .38, .07])
    trans = r.choice(["Manual", "Automatic"], n, p=[.72, .28])
    year = r.randint(2008, 2025, n)
    km = (2025 - year) * r.normal(11000, 3500, n).clip(2500, 30000) + r.normal(0, 4000, n)
    km = km.clip(500, 300000).round(0)
    owners = np.clip(r.poisson(0.7, n) + 1, 1, 4)
    engine = r.choice([800, 1000, 1200, 1500, 1800, 2000], n, p=[.1, .2, .3, .2, .12, .08])
    region = r.choice(["North", "South", "East", "West"], n, p=[.3, .3, .15, .25])
    bf = pd.Series(brand).map({"Maruti": 1.0, "Hyundai": 1.12, "Honda": 1.2, "Toyota": 1.45, "Tata": 1.05}).values
    base = 3.2 + engine / 650 + (year - 2008) * 0.42 - km / 45000 + (trans == "Automatic") * 1.4 + (fuel == "Diesel") * 0.9
    price = np.maximum(base * bf * np.exp(r.normal(0, 0.1, n)) - (owners - 1) * 0.35, 0.6).round(2)
    df = pd.DataFrame({"brand": brand, "fuel_type": fuel, "transmission": trans, "year": year, "km_driven": km,
                       "owner_count": owners, "engine_cc": engine, "region": region, "price_lakhs": price})
    for c, f in (("km_driven", .06), ("engine_cc", .04), ("fuel_type", .03)):
        idx = r.choice(n, int(n * f), replace=False)
        df[c] = df[c].astype(object) if c == "fuel_type" else df[c].astype(float)
        df.loc[idx, c] = np.nan
    out = r.choice(n, 10, replace=False); df.loc[out, "km_driven"] = df.loc[out, "km_driven"] * 6 + 400000
    return pd.concat([df, df.sample(35, random_state=3)], ignore_index=True)


# 2 ---------------------------------------------------------------- energy use (regression, clean)
def energy():
    r = np.random.RandomState(202); n = 1200
    temp = r.normal(24, 7, n).clip(2, 44)
    humidity = r.normal(55, 15, n).clip(15, 95)
    occupancy = r.randint(5, 400, n)
    hour = r.randint(0, 24, n)
    weekend = r.choice(["No", "Yes"], n, p=[.71, .29])
    area = r.choice([800, 1200, 2000, 3500, 5000], n)
    kwh = (area * 0.018 + occupancy * 0.22 + np.maximum(temp - 22, 0) * 3.1 + np.where((hour > 8) & (hour < 20), 14, 4)
           - (weekend == "Yes") * 6 + humidity * 0.05 + r.normal(0, 3.0, n))
    return pd.DataFrame({"temperature_c": temp.round(1), "humidity_pct": humidity.round(0), "occupancy": occupancy,
                         "hour_of_day": hour, "weekend": weekend, "floor_area_sqft": area, "energy_kwh": kwh.round(2)})


# 3 ---------------------------------------------------------------- loan approval (binary, fairness)
def loans():
    r = np.random.RandomState(303); n = 2200
    age = r.randint(21, 66, n)
    gender = r.choice(["Male", "Female"], n, p=[.55, .45])
    region = r.choice(["Urban", "Semi-urban", "Rural"], n, p=[.45, .3, .25])
    income = r.lognormal(10.9, 0.45, n).round(0)
    amount = (income * r.uniform(0.4, 3.5, n)).round(0)
    score = np.clip(r.normal(680, 70, n) + (region == "Urban") * 10, 400, 850).round(0)
    years = np.clip(r.normal(7, 5, n), 0, 35).round(1)
    loans_n = r.poisson(1.1, n)
    z = (0.035 * (score - 650) + 0.6 * np.log(income / amount.clip(1)) + 0.05 * years - 0.35 * loans_n
         - 0.9 * (region == "Rural") - 0.4 * (gender == "Female") - 0.5)       # deliberate bias terms
    z = 2.0 * (z - np.quantile(z, 0.62))
    ok = r.rand(n) < sig(z)
    df = pd.DataFrame({"age": age, "gender": gender, "region": region, "annual_income": income, "loan_amount": amount,
                       "credit_score": score, "employment_years": years, "existing_loans": loans_n,
                       "approved": np.where(ok, "Yes", "No")})
    idx = r.choice(n, int(n * .05), replace=False); df.loc[idx, "annual_income"] = np.nan
    return df


# 4 ---------------------------------------------------------------- student grades (multi-class, clean)
def students():
    r = np.random.RandomState(404); n = 900
    study = r.gamma(3.0, 1.1, n).clip(0, 14)
    attend = np.clip(r.normal(82, 11, n), 40, 100)
    prev = np.clip(r.normal(62, 16, n), 10, 100)
    sleep = np.clip(r.normal(7, 1.1, n), 3.5, 10)
    net = r.choice(["Yes", "No"], n, p=[.8, .2])
    support = r.choice(["Low", "Medium", "High"], n, p=[.25, .45, .3])
    gender = r.choice(["Male", "Female"], n)
    s = (0.55 * prev + 2.4 * study + 0.25 * attend + 1.2 * sleep + (support == "High") * 4 - (support == "Low") * 3
         + (net == "No") * -2 + r.normal(0, 4.0, n))
    band = pd.cut(s, [-np.inf, np.quantile(s, .33), np.quantile(s, .70), np.inf], labels=["Low", "Medium", "High"])
    return pd.DataFrame({"study_hours": study.round(1), "attendance_pct": attend.round(0), "previous_score": prev.round(0),
                         "sleep_hours": sleep.round(1), "internet_access": net, "parental_support": support,
                         "gender": gender, "grade_band": band.astype(str)})


# 5 ---------------------------------------------------------------- fraud (binary, leakage + imbalance + messy)
def fraud():
    r = np.random.RandomState(505); n = 3000
    amount = r.lognormal(6.0, 1.0, n).round(2)
    hour = r.randint(0, 24, n)
    dist = r.gamma(2.0, 12, n).round(1)
    cat = r.choice(["Grocery", "Fuel", "Travel", "Electronics", "Dining", "Online"], n, p=[.25, .2, .08, .1, .17, .2])
    chan = r.choice(["POS", "Online", "ATM"], n, p=[.5, .38, .12])
    age_acc = r.randint(1, 120, n)
    z = (0.0007 * amount + 0.045 * dist + 1.1 * ((hour < 5) | (hour > 23)) + 1.0 * (chan == "Online") - 0.012 * age_acc
         + 0.8 * (cat == "Electronics"))
    z = 2.4 * (z - np.quantile(z, 0.95))
    fr = (r.rand(n) < sig(z)).astype(int)
    leak = np.where(fr == 1, r.rand(n) < 0.96, r.rand(n) < 0.01).astype(int)   # set AFTER fraud is known
    df = pd.DataFrame({"amount": amount, "hour": hour, "distance_from_home_km": dist, "merchant_category": cat,
                       "channel": chan, "account_age_days": age_acc, "currency": "INR",
                       "chargeback_flag": leak, "is_fraud": np.where(fr == 1, "Fraud", "Legit")})
    idx = r.choice(n, int(n * .04), replace=False); df["merchant_category"] = df["merchant_category"].astype(object)
    df.loc[idx, "merchant_category"] = np.nan
    return pd.concat([df, df.sample(60, random_state=4)], ignore_index=True)


# 6 ---------------------------------------------------------------- tiny quick file (binary, tiny + clean)
def quick():
    r = np.random.RandomState(606); n = 120
    a = r.normal(0, 1, n); b = r.normal(0, 1, n)
    y = (a + 0.6 * b + r.normal(0, 0.5, n)) > 0
    return pd.DataFrame({"feature_a": a.round(3), "feature_b": b.round(3), "colour": r.choice(["red", "blue", "green"], n),
                         "label": np.where(y, "positive", "negative")})


if __name__ == "__main__":
    save(used_cars(), "used_car_prices.csv")
    save(energy(), "energy_consumption.csv")
    save(loans(), "loan_approval.csv")
    save(students(), "student_grades.csv")
    save(fraud(), "fraud_transactions.csv")
    save(quick(), "quick_small_test.csv")
