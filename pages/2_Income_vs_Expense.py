# pages/2_Income_vs_Expense.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.title("📊 Income vs Expense Deep Analysis")

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
# MONTHLY SUMMARY
# =========================

monthly = (
    df.groupby(["year", "month"])
    .agg({"credit": "sum", "debit": "sum"})
    .reset_index()
    .sort_values(["year", "month"])
)

monthly["savings"] = monthly["credit"] - monthly["debit"]
monthly["month_year"] = (
    monthly["month"].astype(str) + "-" + monthly["year"].astype(str)
)

# =========================
# KPIs
# =========================

avg_income = monthly["credit"].mean()
avg_expense = monthly["debit"].mean()
avg_savings = monthly["savings"].mean()

expense_growth = (
    monthly["debit"].pct_change().mean() * 100
    if len(monthly) > 1 else 0
)

col1, col2, col3, col4 = st.columns(4)

col1.metric("📈 Avg Monthly Income", f"₹ {avg_income:,.2f}")
col2.metric("📉 Avg Monthly Expense", f"₹ {avg_expense:,.2f}")
col3.metric("💰 Avg Monthly Savings", f"₹ {avg_savings:,.2f}")
col4.metric("📊 Avg Expense Growth %", f"{expense_growth:.2f} %")

st.divider()

# =========================
# MONTHLY COMPARISON CHART
# =========================

st.subheader("📅 Monthly Income vs Expense Comparison")

fig = go.Figure()

fig.add_trace(go.Bar(
    x=monthly["month_year"],
    y=monthly["credit"],
    name="Income"
))

fig.add_trace(go.Bar(
    x=monthly["month_year"],
    y=monthly["debit"],
    name="Expense"
))

fig.update_layout(
    barmode='group',
    xaxis_title="Month",
    yaxis_title="Amount (₹)"
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# =========================
# DAILY TREND ANALYSIS
# =========================

st.subheader("📆 Daily Income vs Expense Trend")

daily = (
    df.groupby("date")
    .agg({"credit": "sum", "debit": "sum"})
    .reset_index()
)

fig_daily = px.line(
    daily,
    x="date",
    y=["credit", "debit"],
    labels={"value": "Amount (₹)", "date": "Date"},
)

st.plotly_chart(fig_daily, use_container_width=True)

st.divider()

# =========================
# CUMULATIVE CASH FLOW
# =========================

st.subheader("💹 Cumulative Cash Flow")

df_sorted = df.sort_values("date").copy()
df_sorted["cumulative_cashflow"] = df_sorted["net_amount"].cumsum()

fig_cashflow = px.line(
    df_sorted,
    x="date",
    y="cumulative_cashflow",
    labels={"cumulative_cashflow": "Cumulative Cash Flow (₹)"}
)

st.plotly_chart(fig_cashflow, use_container_width=True)

st.divider()

# =========================
# EXPENSE VOLATILITY
# =========================

st.subheader("📊 Expense Volatility (Distribution)")

expense_only = df[df["debit"] > 0]

fig_box = px.box(
    expense_only,
    y="debit",
    points="all",
    labels={"debit": "Expense Amount (₹)"}
)

st.plotly_chart(fig_box, use_container_width=True)

st.info("Higher spread indicates unstable spending behavior.")