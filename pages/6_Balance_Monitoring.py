# pages/6_Balance_Monitoring.py

import streamlit as st
import pandas as pd
import plotly.express as px

st.title("🏦 Balance Monitoring & Financial Stability")

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

# Sort data by date
df = df.sort_values("date").copy()

# =========================
# BALANCE KPIs
# =========================

min_balance = df["balance"].min()
max_balance = df["balance"].max()
avg_balance = df["balance"].mean()
current_balance = df["balance"].iloc[-1]

col1, col2, col3, col4 = st.columns(4)

col1.metric("📉 Minimum Balance", f"₹ {min_balance:,.2f}")
col2.metric("📈 Maximum Balance", f"₹ {max_balance:,.2f}")
col3.metric("📊 Average Balance", f"₹ {avg_balance:,.2f}")
col4.metric("💰 Current Balance", f"₹ {current_balance:,.2f}")

st.divider()

# =========================
# BALANCE TREND LINE
# =========================

st.subheader("📈 Balance Trend Over Time")

fig_balance = px.line(
    df,
    x="date",
    y="balance",
    labels={"balance": "Account Balance (₹)", "date": "Date"},
)

st.plotly_chart(fig_balance, use_container_width=True)

st.divider()

# =========================
# LOW BALANCE ALERT SYSTEM
# =========================

st.subheader("🚨 Low Balance Alert")

threshold = st.slider(
    "Select Low Balance Threshold (₹)",
    min_value=0,
    max_value=int(max_balance),
    value=2000,
    step=500
)

low_balance_days = df[df["balance"] < threshold]

col1, col2 = st.columns(2)

col1.metric("⚠ Days Below Threshold", len(low_balance_days))
col2.metric("🔻 Lowest Recorded Balance", f"₹ {min_balance:,.2f}")

if len(low_balance_days) > 0:
    st.warning("Your balance dropped below selected threshold on some days.")
else:
    st.success("No critical low balance detected.")

st.divider()

# =========================
# BALANCE VOLATILITY
# =========================

st.subheader("📊 Balance Volatility")

df["balance_change"] = df["balance"].diff()

fig_volatility = px.histogram(
    df,
    x="balance_change",
    nbins=40,
    labels={"balance_change": "Daily Balance Change (₹)"}
)

st.plotly_chart(fig_volatility, use_container_width=True)

st.info("Large spikes indicate unstable cash flow behavior.")

st.divider()

# =========================
# LOW BALANCE TABLE
# =========================

with st.expander("🔎 View Low Balance Records"):
    st.dataframe(
        low_balance_days[["date", "balance"]],
        use_container_width=True
    )