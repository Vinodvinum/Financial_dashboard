# pages/3_Monthly_Trends.py

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.title("📅 Monthly & Seasonal Trends Analysis")

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
# MONTHLY AGGREGATION
# =========================

monthly = (
    df.groupby(["year", "month", "month_name"])
    .agg({"credit": "sum", "debit": "sum"})
    .reset_index()
    .sort_values(["year", "month"])
)

monthly["savings"] = monthly["credit"] - monthly["debit"]
monthly["month_year"] = (
    monthly["month_name"] + " " + monthly["year"].astype(str)
)

# =========================
# BEST & WORST MONTH
# =========================

best_month = monthly.loc[monthly["savings"].idxmax()]
worst_month = monthly.loc[monthly["savings"].idxmin()]

col1, col2 = st.columns(2)

col1.success(
    f"🏆 Best Month: {best_month['month_year']} | Savings: ₹ {best_month['savings']:,.2f}"
)

col2.error(
    f"⚠ Worst Month: {worst_month['month_year']} | Savings: ₹ {worst_month['savings']:,.2f}"
)

st.divider()

# =========================
# MONTHLY EXPENSE TREND
# =========================

st.subheader("📉 Monthly Expense Trend")

fig_expense = px.line(
    monthly,
    x="month_year",
    y="debit",
    markers=True,
    labels={"debit": "Expense (₹)", "month_year": "Month"}
)

st.plotly_chart(fig_expense, use_container_width=True)

st.divider()

# =========================
# WEEKDAY SPENDING PATTERN
# =========================

st.subheader("📆 Weekday Spending Pattern")

weekday_spending = (
    df[df["debit"] > 0]
    .groupby("day_name")["debit"]
    .sum()
    .reset_index()
)

# Sort weekdays properly
weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", 
                 "Friday", "Saturday", "Sunday"]

weekday_spending["day_name"] = pd.Categorical(
    weekday_spending["day_name"],
    categories=weekday_order,
    ordered=True
)

weekday_spending = weekday_spending.sort_values("day_name")

fig_weekday = px.bar(
    weekday_spending,
    x="day_name",
    y="debit",
    labels={"debit": "Total Expense (₹)", "day_name": "Day of Week"}
)

st.plotly_chart(fig_weekday, use_container_width=True)

st.divider()

# =========================
# HEATMAP (MONTH vs YEAR)
# =========================

st.subheader("🔥 Monthly Spending Heatmap")

heatmap_data = (
    df[df["debit"] > 0]
    .groupby(["year", "month"])["debit"]
    .sum()
    .reset_index()
)

heatmap_pivot = heatmap_data.pivot(
    index="year",
    columns="month",
    values="debit"
)

fig_heatmap = px.imshow(
    heatmap_pivot,
    labels=dict(x="Month", y="Year", color="Expense (₹)"),
    aspect="auto"
)

st.plotly_chart(fig_heatmap, use_container_width=True)

st.divider()

# =========================
# SEASONAL SAVINGS ANALYSIS
# =========================

st.subheader("🌦 Seasonal Savings Pattern")

seasonal = (
    monthly.groupby("month_name")["savings"]
    .mean()
    .reset_index()
)

fig_season = px.bar(
    seasonal,
    x="month_name",
    y="savings",
    labels={"savings": "Average Savings (₹)", "month_name": "Month"}
)

st.plotly_chart(fig_season, use_container_width=True)

st.info("This shows average savings behavior across different months.")