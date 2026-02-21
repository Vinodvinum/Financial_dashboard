# pages/5_UPI_Insights.py

import streamlit as st
import pandas as pd
import plotly.express as px

st.title("📱 UPI Transaction Insights")

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
# FILTER UPI TRANSACTIONS
# =========================

upi_df = df[df["category"] == "UPI Transfer"].copy()

if upi_df.empty:
    st.warning("No UPI transactions found.")
    st.stop()

# =========================
# BASIC KPIs
# =========================

total_upi_transactions = len(upi_df)
total_upi_spend = upi_df["debit"].sum()
avg_upi_amount = upi_df["debit"].mean()

small_payments = upi_df[upi_df["debit"] < 200]
small_payment_count = len(small_payments)

col1, col2, col3, col4 = st.columns(4)

col1.metric("🔢 Total UPI Transactions", total_upi_transactions)
col2.metric("💸 Total UPI Spend", f"₹ {total_upi_spend:,.2f}")
col3.metric("📊 Avg UPI Amount", f"₹ {avg_upi_amount:,.2f}")
col4.metric("🪙 Small Payments (<₹200)", small_payment_count)

st.divider()

# =========================
# UPI AMOUNT DISTRIBUTION
# =========================

st.subheader("📊 UPI Payment Distribution")

fig_hist = px.histogram(
    upi_df,
    x="debit",
    nbins=30,
    labels={"debit": "UPI Amount (₹)"}
)

st.plotly_chart(fig_hist, use_container_width=True)

st.divider()

# =========================
# DAILY UPI FREQUENCY
# =========================

st.subheader("📆 Daily UPI Transaction Frequency")

daily_upi = (
    upi_df.groupby("date")
    .size()
    .reset_index(name="transaction_count")
)

fig_daily = px.line(
    daily_upi,
    x="date",
    y="transaction_count",
    labels={"transaction_count": "Number of Transactions"}
)

st.plotly_chart(fig_daily, use_container_width=True)

st.divider()

# =========================
# TOP RECEIVERS ANALYSIS
# =========================

st.subheader("🏆 Top UPI Receivers")

# Extract receiver name from description (simple split logic)
upi_df["receiver"] = upi_df["description"].str.split("/").str[2]

top_receivers = (
    upi_df.groupby("receiver")["debit"]
    .sum()
    .reset_index()
    .sort_values("debit", ascending=False)
    .head(10)
)

fig_top = px.bar(
    top_receivers,
    x="receiver",
    y="debit",
    labels={"debit": "Total Paid (₹)", "receiver": "Receiver"}
)

st.plotly_chart(fig_top, use_container_width=True)

st.divider()

# =========================
# MICRO-SPENDING ALERT
# =========================

micro_spend_total = small_payments["debit"].sum()

st.subheader("⚠ Micro-Spending Impact")

st.info(
    f"You made {small_payment_count} small UPI payments totaling ₹ {micro_spend_total:,.2f}. "
    "Frequent small payments can reduce savings over time."
)

# =========================
# RAW UPI TABLE
# =========================

with st.expander("🔎 View UPI Transactions Table"):
    st.dataframe(
        upi_df[["date", "description", "debit", "balance"]],
        use_container_width=True
    )