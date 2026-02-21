# pages/7_Outlier_Detection.py

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.title("🚨 Outlier & Anomaly Detection")

# =========================
# LOAD DATA
# =========================
if "filtered_df" not in st.session_state:
    st.warning("Please upload data from the main page first.")
    st.stop()

df = st.session_state["filtered_df"]

if df.empty:
    st.warning("No data available for selected date range.")
    st.stop()

# Separate expense and income
expense_df = df[df["debit"] > 0].copy()
income_df = df[df["credit"] > 0].copy()

# =========================
# USER-DEFINED LARGE TRANSACTION THRESHOLD
# =========================

st.subheader("🔎 Large Transaction Detection")

max_debit = int(expense_df["debit"].max()) if not expense_df.empty else 10000

threshold = st.slider(
    "Select Expense Threshold (₹)",
    min_value=1000,
    max_value=max_debit if max_debit > 1000 else 10000,
    value=5000,
    step=1000
)

large_expenses = expense_df[expense_df["debit"] > threshold]

col1, col2 = st.columns(2)
col1.metric("💸 Large Expense Count", len(large_expenses))
col2.metric("💰 Total Large Expense", f"₹ {large_expenses['debit'].sum():,.2f}")

st.divider()

# =========================
# STATISTICAL OUTLIER DETECTION (IQR METHOD)
# =========================

st.subheader("📊 Statistical Outlier Detection (IQR Method)")

if not expense_df.empty:
    Q1 = expense_df["debit"].quantile(0.25)
    Q3 = expense_df["debit"].quantile(0.75)
    IQR = Q3 - Q1

    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    outliers = expense_df[
        (expense_df["debit"] < lower_bound) |
        (expense_df["debit"] > upper_bound)
    ]

    st.write(f"Lower Bound: ₹ {lower_bound:,.2f}")
    st.write(f"Upper Bound: ₹ {upper_bound:,.2f}")

    st.metric("⚠ Statistical Outliers Detected", len(outliers))

else:
    outliers = pd.DataFrame()

st.divider()

# =========================
# EXPENSE DISTRIBUTION WITH OUTLIERS
# =========================

st.subheader("📦 Expense Distribution Box Plot")

fig_box = px.box(
    expense_df,
    y="debit",
    points="all",
    labels={"debit": "Expense Amount (₹)"}
)

st.plotly_chart(fig_box, use_container_width=True)

st.divider()

# =========================
# EXPENSE SPIKE DETECTION (DAILY)
# =========================

st.subheader("📈 Daily Expense Spike Detection")

daily_expense = (
    expense_df.groupby("date")["debit"]
    .sum()
    .reset_index()
)

daily_expense["daily_change"] = daily_expense["debit"].diff()

spike_threshold = daily_expense["daily_change"].mean() + \
                  2 * daily_expense["daily_change"].std()

spikes = daily_expense[daily_expense["daily_change"] > spike_threshold]

st.metric("🚀 Expense Spike Days", len(spikes))

fig_spike = px.line(
    daily_expense,
    x="date",
    y="debit",
    labels={"debit": "Daily Expense (₹)"}
)

st.plotly_chart(fig_spike, use_container_width=True)

st.divider()

# =========================
# DISPLAY OUTLIER TABLES
# =========================

with st.expander("🔎 View Large Expense Transactions"):
    st.dataframe(
        large_expenses[["date", "description", "debit", "balance"]],
        use_container_width=True
    )

with st.expander("📊 View Statistical Outliers"):
    st.dataframe(
        outliers[["date", "description", "debit", "balance"]],
        use_container_width=True
    )

with st.expander("🚀 View Spike Days"):
    st.dataframe(
        spikes,
        use_container_width=True
    )

st.info(
    "Outliers and spikes may indicate unusual spending behavior or major life events."
)