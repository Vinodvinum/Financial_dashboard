# utils/feature_engineering.py

import pandas as pd

def add_features(df):

    # Safety: ensure datetime
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Remove invalid rows again (double safety)
    df = df[df["date"].notna()]

    # -----------------------------
    # Date Features
    # -----------------------------
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%B")
    df["day"] = df["date"].dt.day
    df["day_name"] = df["date"].dt.strftime("%A")

    # -----------------------------
    # Financial Feature
    # -----------------------------
    df["net_amount"] = df["credit"] - df["debit"]

    return df