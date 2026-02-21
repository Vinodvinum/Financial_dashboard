# app.py

import streamlit as st
import pandas as pd
import os

from utils.data_loader import load_excel_data, save_to_sqlite, load_from_sqlite
from utils.data_cleaning import clean_data
from utils.feature_engineering import add_features
from utils.category_classifier import add_category

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="Financial Intelligence Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# LOAD CUSTOM CSS
# =========================

def load_css():
    if os.path.exists("assets/styles.css"):
        with open("assets/styles.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# =========================
# HEADER
# =========================

st.markdown("""
# 💰 Personal Financial Intelligence Dashboard
### AI-Powered Banking Analytics System
""")

st.markdown("---")

# =========================
# SIDEBAR
# =========================

st.sidebar.header("📂 Upload & Filters")

uploaded_file = st.sidebar.file_uploader(
    "Upload Bank Statement (Excel)",
    type=["xlsx"]
)

# =========================
# DATA PROCESSING
# =========================

if uploaded_file:
    with st.spinner("Processing data..."):
        df = load_excel_data(uploaded_file)
        df = clean_data(df)
        df = add_features(df)
        df = add_category(df)
        save_to_sqlite(df)

    st.sidebar.success("✅ Data Processed Successfully")

# =========================
# LOAD FROM DATABASE
# =========================

if os.path.exists("database/finance.db"):

    df = load_from_sqlite()

    if df.empty:
        st.warning("Database is empty. Please upload data.")
        st.stop()

    # Ensure datetime
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Keep a full copy for analysis pages that should ignore sidebar filters
    st.session_state["full_df"] = df.copy()

    # =========================
    # DATE FILTER
    # =========================

    min_date = df["date"].min().date()
    max_date = df["date"].max().date()

    start_date = st.sidebar.date_input(
        "📅 Start Date",
        value=min_date,
        min_value=min_date,
        max_value=max_date
    )

    end_date = st.sidebar.date_input(
        "📅 End Date",
        value=max_date,
        min_value=min_date,
        max_value=max_date
    )

    start_date = pd.Timestamp(start_date) #type: ignore
    end_date = pd.Timestamp(end_date) #type: ignore

    if start_date > end_date:
        st.sidebar.error("Start date cannot be after End date.")
        st.stop()

    # =========================
    # CATEGORY FILTER
    # =========================

    categories = sorted(df["category"].dropna().unique().tolist())

    category_filter = st.sidebar.multiselect(
        "🏷 Select Categories",
        options=categories,
        default=categories
    )

    # =========================
    # APPLY FILTERS
    # =========================

    filtered_df = df[
        (df["date"] >= start_date) &
        (df["date"] <= end_date) &
        (df["category"].isin(category_filter))
    ].copy()

    st.session_state["filtered_df"] = filtered_df

    st.sidebar.info(f"Filtered Records: {len(filtered_df)}")

    # =========================
    # VISONVERSE SECTION
    # =========================

    visonverse_mask = (
        filtered_df["category"].astype(str).str.contains(
            "visonverse", case=False, na=False
        )
        | filtered_df["description"].astype(str).str.contains(
            r"visonverse|visionverse", case=False, na=False
        )
    )
    visonverse_df = filtered_df[visonverse_mask].copy()

    if not visonverse_df.empty:
        st.markdown("## VISONVERSE Transactions")

        total_transactions = len(visonverse_df)
        total_debit = visonverse_df["debit"].sum()
        total_credit = visonverse_df["credit"].sum()
        net_amount = total_credit - total_debit

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total VISONVERSE Transactions", total_transactions)
        col2.metric("Total Debit", f"Rs {total_debit:,.2f}")
        col3.metric("Total Credit", f"Rs {total_credit:,.2f}")
        col4.metric("Net (Credit - Debit)", f"Rs {net_amount:,.2f}")

        st.dataframe(
            visonverse_df.sort_values("date", ascending=False),
            use_container_width=True
        )

        st.markdown("---")

    # =========================
    # MAIN PREVIEW
    # =========================

    st.subheader("📊 Filtered Data Preview")
    st.dataframe(filtered_df, use_container_width=True)

else:
    st.warning("📂 Please upload your bank statement to begin.")