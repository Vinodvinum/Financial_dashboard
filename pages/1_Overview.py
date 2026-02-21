# pages/1_Overview.py

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.kpi_calculations import calculate_kpis

st.title("📊 Executive Financial Overview")

# Load filtered data from session
if "filtered_df" not in st.session_state:
    st.warning("Please upload data from the main page first.")
    st.stop()

df = st.session_state["filtered_df"]

if df.empty:
    st.warning("No data available for selected date range.")
    st.stop()

# =========================
# 🔹 KPI SECTION
# =========================

kpis = calculate_kpis(df)

col1, col2, col3 = st.columns(3)
col4, col5, col6 = st.columns(3)

col1.metric("💰 Total Income", f"₹ {kpis['total_income']:,.2f}")
col2.metric("💸 Total Expense", f"₹ {kpis['total_expense']:,.2f}")
col3.metric("📈 Net Savings", f"₹ {kpis['net_savings']:,.2f}")

col4.metric("🏦 Current Balance", f"₹ {kpis['current_balance']:,.2f}")
col5.metric("📊 Total Transactions", kpis["total_transactions"])
col6.metric("💎 Savings Ratio", f"{kpis['savings_ratio']:.2f} %")

st.divider()

# =========================
# 🔹 INCOME VS EXPENSE TREND
# =========================

st.subheader("📈 Income vs Expense Trend")

monthly_summary = (
    df.groupby(["year", "month_name"])
    .agg({"credit": "sum", "debit": "sum"})
    .reset_index()
)

monthly_summary["month_year"] = (
    monthly_summary["month_name"] + " " + monthly_summary["year"].astype(str)
)

fig_income_expense = px.line(
    monthly_summary,
    x="month_year",
    y=["credit", "debit"],
    markers=True,
    labels={"value": "Amount (₹)", "month_year": "Month"},
    title="Monthly Income vs Expense"
)

st.plotly_chart(fig_income_expense, use_container_width=True)

st.divider()

# =========================
# 🔹 MONTHLY SAVINGS BAR
# =========================

st.subheader("📊 Monthly Savings")

monthly_summary["savings"] = (
    monthly_summary["credit"] - monthly_summary["debit"]
)

fig_savings = px.bar(
    monthly_summary,
    x="month_year",
    y="savings",
    labels={"savings": "Savings (₹)", "month_year": "Month"},
    title="Monthly Net Savings"
)

st.plotly_chart(fig_savings, use_container_width=True)

st.divider()

# =========================
# 🔹 EXPENSE DISTRIBUTION
# =========================

st.subheader("🥧 Expense Distribution by Category")

expense_by_category = (
    df[df["debit"] > 0]
    .groupby("category")["debit"]
    .sum()
    .reset_index()
)

fig_pie = px.pie(
    expense_by_category,
    names="category",
    values="debit",
    title="Expense Breakdown"
)

st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# =========================
# 🔹 RECENT TRANSACTIONS
# =========================

st.subheader("📝 Recent Transactions")

st.dataframe(
    df.sort_values("date", ascending=False).head(10),
    use_container_width=True
)