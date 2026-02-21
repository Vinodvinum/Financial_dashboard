# pages/8_Predictions.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.linear_model import LinearRegression

st.title("🔮 Financial Forecasting & Budget Intelligence")

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
    df.groupby(["year", "month"])
    .agg({"credit": "sum", "debit": "sum"})
    .reset_index()
    .sort_values(["year", "month"])
)

monthly["month_index"] = np.arange(len(monthly))
monthly["savings"] = monthly["credit"] - monthly["debit"]

if len(monthly) < 3:
    st.warning("Need at least 3 months of data for reliable prediction.")
    st.stop()

# =========================
# LINEAR REGRESSION MODEL
# =========================

X = monthly[["month_index"]]

# Expense model
y_expense = monthly["debit"]
model_expense = LinearRegression()
model_expense.fit(X, y_expense)

# Income model
y_income = monthly["credit"]
model_income = LinearRegression()
model_income.fit(X, y_income)

# Next month prediction
next_month_index = np.array([[monthly["month_index"].max() + 1]])

predicted_expense = model_expense.predict(next_month_index)[0]
predicted_income = model_income.predict(next_month_index)[0]
predicted_savings = predicted_income - predicted_expense

# =========================
# DISPLAY PREDICTIONS
# =========================

col1, col2, col3 = st.columns(3)

col1.metric("📉 Predicted Next Month Expense", f"₹ {predicted_expense:,.2f}")
col2.metric("📈 Predicted Next Month Income", f"₹ {predicted_income:,.2f}")
col3.metric("💰 Predicted Savings", f"₹ {predicted_savings:,.2f}")

st.divider()

# =========================
# FORECAST VISUALIZATION
# =========================

st.subheader("📊 Expense Forecast Trend")

monthly["type"] = "Actual"
future_row = pd.DataFrame({
    "year": [None],
    "month": [None],
    "credit": [predicted_income],
    "debit": [predicted_expense],
    "month_index": [next_month_index[0][0]],
    "savings": [predicted_savings],
    "type": ["Predicted"]
})

forecast_df = pd.concat([monthly, future_row], ignore_index=True)

fig_forecast = px.line(
    forecast_df,
    x="month_index",
    y="debit",
    color="type",
    markers=True,
    labels={"debit": "Expense (₹)", "month_index": "Month Index"}
)

st.plotly_chart(fig_forecast, use_container_width=True)

st.divider()

# =========================
# BUDGET RECOMMENDATION ENGINE
# =========================

st.subheader("💡 Budget Recommendation")

avg_expense = monthly["debit"].mean()
recommended_budget = avg_expense * 0.9  # Suggest 10% reduction
emergency_fund = avg_expense * 6  # 6 months coverage

st.write(f"📌 Average Monthly Expense: ₹ {avg_expense:,.2f}")
st.success(f"✅ Recommended Monthly Budget: ₹ {recommended_budget:,.2f}")
st.info(f"🏦 Suggested Emergency Fund Target (6 months): ₹ {emergency_fund:,.2f}")

st.divider()

# =========================
# SAVINGS GOAL PLANNER
# =========================

st.subheader("🎯 Savings Goal Planner")

goal_amount = st.number_input(
    "Enter Savings Goal Amount (₹)",
    min_value=1000,
    value=50000,
    step=1000
)

if predicted_savings > 0:
    months_required = goal_amount / predicted_savings
    st.success(
        f"At predicted savings rate, you can reach ₹ {goal_amount:,.2f} "
        f"in approximately {months_required:.1f} months."
    )
else:
    st.error("Predicted savings is negative. Reduce expenses first.")

st.info(
    "Predictions are based on simple linear regression trend. "
    "More data improves accuracy."
)