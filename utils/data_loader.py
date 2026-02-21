# utils/data_loader.py

import pandas as pd
import sqlite3
import os

def load_excel_data(file):

    # Read entire sheet without header
    raw_df = pd.read_excel(file, header=None)

    # Find row index where first column contains "Date"
    header_row = None
    for i in range(len(raw_df)):
        first_cell = str(raw_df.iloc[i, 0]).strip().lower()
        if first_cell == "date":
            header_row = i
            break

    if header_row is None:
        raise ValueError("Could not detect transaction header row (Date column not found).")

    # Now read again using correct header row
    df = pd.read_excel(file, header=header_row)

    print("Detected Header Row:", header_row)
    print("Detected Columns:", df.columns.tolist())

    return df


def save_to_sqlite(df, db_path="database/finance.db", table_name="transactions"):
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()


def load_from_sqlite(db_path="database/finance.db", table_name="transactions"):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df