# pages/4_Category_Analysis.py

import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Category Wise Financial Analysis")

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

# =========================
# TRANSACTION SCOPE
# =========================

scope = st.radio(
    "Transaction Scope",
    options=["Expense (Debit)", "Income (Credit)", "Both"],
    horizontal=True
)

if scope == "Expense (Debit)":
    analysis_df = df[df["debit"] > 0].copy()
    analysis_df["analysis_amount"] = analysis_df["debit"]
    amount_label = "Expense"
elif scope == "Income (Credit)":
    analysis_df = df[df["credit"] > 0].copy()
    analysis_df["analysis_amount"] = analysis_df["credit"]
    amount_label = "Income"
else:
    analysis_df = df[(df["debit"] > 0) | (df["credit"] > 0)].copy()
    analysis_df["analysis_amount"] = analysis_df["debit"] + analysis_df["credit"]
    amount_label = "Transaction Amount"

if analysis_df.empty:
    st.warning(f"No transactions found for {scope} in selected date range.")
    st.stop()

# =========================
# CATEGORY SUMMARY
# =========================

category_summary = (
    analysis_df
    .groupby("category")["analysis_amount"]
    .agg(["sum", "count"])
    .reset_index()
)

category_summary.columns = ["category", "total_amount", "transaction_count"]
category_summary = category_summary.sort_values(
    "total_amount", ascending=False
)

# =========================
# TOP KPIs
# =========================

top_category = category_summary.iloc[0]

col1, col2, col3 = st.columns(3)

col1.metric("Top Category", top_category["category"])
col2.metric(f"Top Category {amount_label}", f"Rs {top_category['total_amount']:,.2f}")
col3.metric("Transactions in Top Category", int(top_category["transaction_count"]))

st.divider()

# =========================
# CATEGORY AMOUNT BAR CHART
# =========================

st.subheader(f"Total {amount_label} by Category")

fig_bar = px.bar(
    category_summary,
    x="category",
    y="total_amount",
    labels={"total_amount": f"Total {amount_label} (Rs)"},
)

st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# =========================
# CATEGORY SHARE PIE CHART
# =========================

st.subheader(f"{amount_label} Share Distribution")

fig_pie = px.pie(
    category_summary,
    names="category",
    values="total_amount",
)

st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# =========================
# CATEGORY TREND OVER TIME
# =========================

st.subheader("Category Trend Over Time")

category_trend = (
    analysis_df
    .groupby(["year", "month", "category"])["analysis_amount"]
    .sum()
    .reset_index()
)

category_trend["month_year"] = (
    category_trend["month"].astype(str)
    + "-"
    + category_trend["year"].astype(str)
)

selected_categories = st.multiselect(
    "Select Categories to Compare",
    options=category_summary["category"].tolist(),
    default=category_summary["category"].tolist()[:3]
)

trend_filtered = category_trend[
    category_trend["category"].isin(selected_categories)
]

fig_trend = px.line(
    trend_filtered,
    x="month_year",
    y="analysis_amount",
    color="category",
    markers=True,
    labels={"analysis_amount": f"{amount_label} (Rs)", "month_year": "Month"}
)

st.plotly_chart(fig_trend, use_container_width=True)

st.divider()

# =========================
# DRILL-DOWN TABLE
# =========================

st.subheader("Drill Down: Transactions by Category")

selected_category = st.selectbox(
    "Select Category to View Transactions",
    options=category_summary["category"].tolist()
)

category_transactions = analysis_df[
    analysis_df["category"] == selected_category
].sort_values("date", ascending=False)

st.dataframe(
    category_transactions[[
        "date", "description", "debit", "credit", "balance"
    ]],
    use_container_width=True
)

st.info("Use this table to inspect transaction-level details for the selected category.")
