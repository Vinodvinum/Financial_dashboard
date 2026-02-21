# pages/9_Salary_Tracker.py

import pandas as pd
import plotly.express as px
import streamlit as st

st.title("VISONVERSE Salary Tracker")

if "full_df" in st.session_state:
    df = st.session_state["full_df"].copy()
elif "filtered_df" in st.session_state:
    df = st.session_state["filtered_df"].copy()
else:
    st.warning("Please upload data from the main page first.")
    st.stop()

if df.empty:
    st.warning("No data available.")
    st.stop()

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df[df["date"].notna()].copy()

st.caption(
    "Rule applied: salary for work month M should be credited in month M+1. "
    "December work salary can be credited in January next year."
)

col1, col2, col3, col4 = st.columns(4)
join_date = col1.date_input("Join Date", value=pd.Timestamp("2025-01-20").date())
leave_date = col2.date_input("Leave Date", value=pd.Timestamp("2025-12-31").date())
monthly_salary = col3.number_input("Monthly Salary (Rs)", min_value=0.0, value=18000.0, step=500.0)
carry_months = int(col4.number_input("Post-Leave Credit Window (Months)", min_value=0, max_value=3, value=1, step=1))

join_date = pd.Timestamp(join_date) #type: ignore
leave_date = pd.Timestamp(leave_date) #type: ignore

if join_date > leave_date:
    st.error("Join date cannot be after leave date.")
    st.stop()

work_months = pd.date_range(
    join_date.to_period("M").to_timestamp(),
    leave_date.to_period("M").to_timestamp(),
    freq="MS"
)
work_df = pd.DataFrame({"work_month": work_months})
work_df["work_month_end"] = work_df["work_month"] + pd.offsets.MonthEnd(1)


def expected_for_month(row):
    active_start = max(row["work_month"], join_date) #type: ignore
    active_end = min(row["work_month_end"], leave_date) #type: ignore
    if active_start > active_end:
        return 0.0
    active_days = (active_end - active_start).days + 1
    month_days = row["work_month_end"].day
    return round(float(monthly_salary) * active_days / month_days, 2)


work_df["expected_salary"] = work_df.apply(expected_for_month, axis=1)
work_df["work_month_label"] = work_df["work_month"].dt.strftime("%b %Y")
work_df["target_credit_month"] = work_df["work_month"] + pd.offsets.MonthBegin(1)
work_df["target_credit_label"] = work_df["target_credit_month"].dt.strftime("%b %Y")

credit_window_end = (leave_date.to_period("M").to_timestamp() + pd.offsets.MonthEnd(carry_months + 1))

salary_mask = (
    (df["credit"] > 0)
    & df["description"].astype(str).str.contains(r"visonverse|visionverse", case=False, na=False)
    & (df["date"] >= join_date)
    & (df["date"] <= credit_window_end)
)
salary_txn = df[salary_mask].copy().sort_values("date")

if salary_txn.empty:
    st.warning("No VISONVERSE salary credits found in the selected window.")
    st.dataframe(work_df[["work_month_label", "expected_salary", "target_credit_label"]], use_container_width=True)
    st.stop()

st.subheader("VISONVERSE Transactions")
total_transactions = len(salary_txn)
total_debit = salary_txn["debit"].sum()
total_credit = salary_txn["credit"].sum()
net_amount = total_credit - total_debit

col_t1, col_t2, col_t3, col_t4 = st.columns(4)
col_t1.metric("Total Transactions", total_transactions)
col_t2.metric("Total Debit", f"Rs {total_debit:,.2f}")
col_t3.metric("Total Credit", f"Rs {total_credit:,.2f}")
col_t4.metric("Net (Credit - Debit)", f"Rs {net_amount:,.2f}")

st.dataframe(
    salary_txn.assign(
        month_name=salary_txn["date"].dt.strftime("%B"),
        day_name=salary_txn["date"].dt.strftime("%A"),
    )[["date", "day_name", "month_name", "description",  "credit"]].sort_values("date", ascending=False),
    use_container_width=True,
)

st.divider()

salary_txn["credit_month"] = salary_txn["date"].dt.to_period("M").dt.to_timestamp()
credit_monthly = salary_txn.groupby("credit_month", as_index=False).agg(credit_amount=("credit", "sum"))
credit_monthly["credit_month_label"] = credit_monthly["credit_month"].dt.strftime("%b %Y")

rows = []
for r in work_df.itertuples(index=False):
    rows.append({
        "work_month": r.work_month,
        "work_month_label": r.work_month_label,
        "target_credit_month": r.target_credit_month,
        "target_credit_label": r.target_credit_label,
        "expected_salary": float(r.expected_salary), # type: ignore
        "paid_total": 0.0,
        "due_remaining": float(r.expected_salary), #type: ignore
        "first_credit_month": None,
        "last_credit_month": None,
    })

allocations = []
credit_summary_rows = []

for cm in credit_monthly.itertuples(index=False):
    amount_left = float(cm.credit_amount)
    allocated_total = 0.0
    covered = []

    preferred_work_month = cm.credit_month - pd.offsets.MonthBegin(1)

    for w in rows:
        if w["work_month"] == preferred_work_month and w["due_remaining"] > 0 and amount_left > 0:
            alloc = min(amount_left, w["due_remaining"])
            w["due_remaining"] = round(w["due_remaining"] - alloc, 2)
            w["paid_total"] = round(w["paid_total"] + alloc, 2)
            w["first_credit_month"] = cm.credit_month if w["first_credit_month"] is None else w["first_credit_month"]
            w["last_credit_month"] = cm.credit_month
            amount_left = round(amount_left - alloc, 2)
            allocated_total += alloc
            covered.append(f"{w['work_month_label']} (Rs {alloc:,.2f})")
            allocations.append({
                "credit_month": cm.credit_month_label,
                "work_month": w["work_month_label"],
                "allocated_amount": round(alloc, 2),
            })
            break

    # Remaining amount clears nearest previous pending months first
    # (ex: July double credit should cover June, then May).
    previous_pending = [
        w for w in rows
        if w["work_month"] < preferred_work_month and w["due_remaining"] > 0
    ]
    previous_pending.sort(key=lambda x: x["work_month"], reverse=True)

    for w in previous_pending:
        if amount_left <= 0:
            break
        alloc = min(amount_left, w["due_remaining"])
        w["due_remaining"] = round(w["due_remaining"] - alloc, 2)
        w["paid_total"] = round(w["paid_total"] + alloc, 2)
        w["first_credit_month"] = cm.credit_month if w["first_credit_month"] is None else w["first_credit_month"]
        w["last_credit_month"] = cm.credit_month
        amount_left = round(amount_left - alloc, 2)
        allocated_total += alloc
        covered.append(f"{w['work_month_label']} (Rs {alloc:,.2f})")
        allocations.append({
            "credit_month": cm.credit_month_label,
            "work_month": w["work_month_label"],
            "allocated_amount": round(alloc, 2),
        })

    # If still remaining, clear any other pending dues.
    for w in rows:
        if amount_left <= 0:
            break
        if w["due_remaining"] <= 0:
            continue
        alloc = min(amount_left, w["due_remaining"])
        w["due_remaining"] = round(w["due_remaining"] - alloc, 2)
        w["paid_total"] = round(w["paid_total"] + alloc, 2)
        w["first_credit_month"] = cm.credit_month if w["first_credit_month"] is None else w["first_credit_month"]
        w["last_credit_month"] = cm.credit_month
        amount_left = round(amount_left - alloc, 2)
        allocated_total += alloc
        covered.append(f"{w['work_month_label']} (Rs {alloc:,.2f})")
        allocations.append({
            "credit_month": cm.credit_month_label,
            "work_month": w["work_month_label"],
            "allocated_amount": round(alloc, 2),
        })

    sunday_extra = amount_left if 1000 <= amount_left <= 3000 else 0.0

    credit_summary_rows.append({
        "credit_month": cm.credit_month,
        "credit_month_label": cm.credit_month_label,
        "credited_amount": float(cm.credit_amount),
        "allocated_to_salary": round(allocated_total, 2),
        "unallocated_amount": round(amount_left, 2),
        "sunday_extra_flag": round(sunday_extra, 2),
        "allocation_statement": "; ".join(covered) if covered else "No salary month covered",
    })

out = pd.DataFrame(rows)
credit_out = pd.DataFrame(credit_summary_rows)


def month_diff(a, b):
    if a is None or b is None:
        return None
    return (b.year - a.year) * 12 + (b.month - a.month)


status_list = []
for r in out.itertuples(index=False):
    delay_vs_target = month_diff(r.target_credit_month, r.first_credit_month)

    if r.paid_total == 0:
        status = "Missing"
        statement = (
            f"{r.work_month_label} work salary expected in {r.target_credit_label} is missing. "
            f"Pending Rs {r.due_remaining:,.2f}."
        )
    elif r.due_remaining > 0:       #type: ignore
        status = "Partial Pending"
        statement = (
            f"{r.work_month_label} work salary expected in {r.target_credit_label} is partially credited. "
            f"Pending Rs {r.due_remaining:,.2f}."
        )
    elif delay_vs_target is not None and delay_vs_target <= 0:
        status = "On Time"
        statement = (
            f"{r.work_month_label} work salary was credited by {r.target_credit_label} (as expected)."
        )
    else:
        credited_label = r.first_credit_month.strftime("%b %Y") # type: ignore
        status = "Delayed"
        statement = (
            f"{r.work_month_label} work salary expected in {r.target_credit_label} was credited in "
            f"{credited_label} ({delay_vs_target} month delay)."
        )

    status_list.append({
        "work_month": r.work_month,
        "work_month_label": r.work_month_label,
        "target_credit_label": r.target_credit_label,
        "expected_salary": r.expected_salary,
        "paid_total": r.paid_total,
        "due_remaining": r.due_remaining,
        "status": status,
        "statement": statement,
    })

status_out = pd.DataFrame(status_list)

missing_count = int((status_out["status"] == "Missing").sum())
partial_count = int((status_out["status"] == "Partial Pending").sum())
delayed_count = int((status_out["status"] == "Delayed").sum())
ontime_count = int((status_out["status"] == "On Time").sum())

col_a, col_b, col_c, col_d = st.columns(4)
col_a.metric("Expected Salary", f"Rs {status_out['expected_salary'].sum():,.2f}")
col_b.metric("Salary Credited", f"Rs {status_out['paid_total'].sum():,.2f}")
col_c.metric("Outstanding Due", f"Rs {status_out['due_remaining'].sum():,.2f}")
col_d.metric("Sunday Extra", f"Rs {credit_out['sunday_extra_flag'].sum():,.2f}")

st.divider()

st.subheader("Decision Summary")
summary_text = (
    f"On-time months: {ontime_count}, delayed months: {delayed_count}, "
    f"partial pending months: {partial_count}, missing months: {missing_count}. "
    f"Total pending salary: Rs {status_out['due_remaining'].sum():,.2f}."
)
st.info(summary_text)

st.subheader("Monthly Decision Statements")
for s in status_out["statement"].tolist():
    st.write(f"- {s}")

st.subheader("Expected vs Paid by Work Month")
fig_work = px.bar(
    status_out,
    x="work_month_label",
    y=["expected_salary", "paid_total", "due_remaining"],
    barmode="group",
    labels={"value": "Amount (Rs)", "work_month_label": "Work Month", "variable": "Metric"}
)
st.plotly_chart(fig_work, use_container_width=True)

st.subheader("Credit Month Allocation Statements")
st.dataframe(
    credit_out[[
        "credit_month_label",
        "credited_amount",
        "allocated_to_salary",
        "unallocated_amount",
        "sunday_extra_flag",
        "allocation_statement",
    ]].sort_values("credit_month_label"),
    use_container_width=True,
)

multi_cover = credit_out[
    credit_out["allocation_statement"].astype(str).str.contains(";", regex=False)
]
if not multi_cover.empty:
    st.info(
        "Arrears interpretation: Some credit months covered multiple work months "
        "(for example, July credit can cover both current expected month and pending previous month dues)."
    )

st.subheader("Detailed Work-Month Decision Table")
st.dataframe(
    status_out[[
        "work_month_label",
        "target_credit_label",
        "expected_salary",
        "paid_total",
        "due_remaining",
        "status",
        "statement",
    ]],
    use_container_width=True,
)

st.subheader("Raw VISONVERSE Credits")
st.dataframe(
    salary_txn[["date", "description", "credit"]].sort_values("date", ascending=False),
    use_container_width=True,
)
