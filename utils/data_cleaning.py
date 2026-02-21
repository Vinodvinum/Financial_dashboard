# utils/data_cleaning.py

import pandas as pd

def clean_data(df):

    # -----------------------------
    # Normalize column names
    # -----------------------------
    df.columns = df.columns.str.strip().str.lower()

    # -----------------------------
    # Rename Karnataka Bank columns
    # -----------------------------
    df = df.rename(columns={
        "date": "date",
        "description": "description",
        "withdrawals": "debit",
        "deposits": "credit",
        "balance": "balance"
    })

    # -----------------------------
    # Convert date column safely
    # -----------------------------
    if "date" not in df.columns:
        raise ValueError(f"'date' column not found. Available columns: {df.columns.tolist()}")

    # Handle mixed bank date formats by selecting the parse with more valid rows.
    date_raw = df["date"].astype(str).str.strip()
    parsed_dayfirst = pd.to_datetime(date_raw, errors="coerce", dayfirst=True)
    parsed_monthfirst = pd.to_datetime(date_raw, errors="coerce", dayfirst=False)

    if parsed_dayfirst.notna().sum() >= parsed_monthfirst.notna().sum():
        df["date"] = parsed_dayfirst
    else:
        df["date"] = parsed_monthfirst

    # Remove invalid date rows (like Opening Balance row)
    df = df[df["date"].notna()]

    # Force proper datetime dtype
    df["date"] = df["date"].astype("datetime64[ns]")

    # -----------------------------
    # Convert numeric columns safely
    # -----------------------------
    for col in ["debit", "credit", "balance"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", "", regex=False)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Fill remaining NaNs
    df = df.fillna(0)

    return df
