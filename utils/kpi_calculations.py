# utils/kpi_calculations.py

def calculate_kpis(df):
    total_income = df["credit"].sum()
    total_expense = df["debit"].sum()
    net_savings = total_income - total_expense
    total_transactions = len(df)
    current_balance = df["balance"].iloc[-1] if len(df) > 0 else 0

    savings_ratio = (net_savings / total_income * 100) if total_income > 0 else 0

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "net_savings": net_savings,
        "total_transactions": total_transactions,
        "current_balance": current_balance,
        "savings_ratio": savings_ratio,
    }