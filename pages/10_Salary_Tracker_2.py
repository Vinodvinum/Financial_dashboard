# pages/10_Salary_Tracker_2.py

import pandas as pd
import plotly.express as px
import streamlit as st

st.title("VISONVERSE Salary Tracker 2 (15 to 14 Policy)")

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
    "Scenario 2: Monthly logic (same as Salary Tracker 1) before policy change month, "
    "then strict 15-to-14 cycles from change date onward. Salary fixed at Rs 18,000."
)

col1, col2, col3, col4 = st.columns(4)
join_date = pd.Timestamp(col1.date_input("Join Date", value=pd.Timestamp("2025-01-20").date())) # type: ignore
leave_date = pd.Timestamp(col2.date_input("Leave Date", value=pd.Timestamp("2025-12-31").date())) # type: ignore
policy_change_date = pd.Timestamp(col3.date_input("15-to-14 Start Date", value=pd.Timestamp("2025-07-15").date())) # type: ignore
carry_months = int(col4.number_input("Post-Leave Credit Window (Months)", min_value=0, max_value=3, value=1, step=1)) 

monthly_salary = 18000.0
st.info(f"Fixed Salary Considered: Rs {monthly_salary:,.2f}")

if join_date > leave_date:
    st.error("Join date cannot be after leave date.")
    st.stop()

if policy_change_date < join_date:
    st.error("Policy change date cannot be before join date.")
    st.stop()


def prorated_by_days(start_date: pd.Timestamp, end_date: pd.Timestamp, full_month_salary: float) -> float:
    if start_date > end_date:
        return 0.0
    days = pd.date_range(start_date, end_date, freq="D")
    amount = sum(float(full_month_salary) / d.days_in_month for d in days)
    return round(amount, 2)


credit_window_end = leave_date.to_period("M").to_timestamp() + pd.offsets.MonthEnd(carry_months + 1)

salary_mask = (
    (df["credit"] > 0)
    & df["description"].astype(str).str.contains(r"visonverse|visionverse", case=False, na=False)
    & (df["date"] >= join_date)
    & (df["date"] <= credit_window_end)
)
salary_txn = df[salary_mask].copy().sort_values("date")

if salary_txn.empty:
    st.warning("No VISONVERSE salary credits found in selected window.")
    st.stop()

st.subheader("VISONVERSE Transactions")
col_t1, col_t2 = st.columns(2)
col_t1.metric("Total Transactions", len(salary_txn))
col_t2.metric("Total Credit", f"Rs {salary_txn['credit'].sum():,.2f}")

st.dataframe(
    salary_txn.assign(
        month_name=salary_txn["date"].dt.strftime("%B"),
        day_name=salary_txn["date"].dt.strftime("%A"),
    )[["date", "day_name", "month_name", "description", "credit"]].sort_values("date", ascending=False),
    use_container_width=True,
)

st.divider()

# -------------------------------------------------
# Build expected periods
# 1) Monthly periods before change month (same as tracker 1)
# 2) 15->14 cycles from policy change date onward
# -------------------------------------------------

periods = []

change_month_start = policy_change_date.to_period("M").to_timestamp()
pre_change_end = min(leave_date, change_month_start - pd.Timedelta(days=1))

if pre_change_end >= join_date:
    monthly_starts = pd.date_range(
        join_date.to_period("M").to_timestamp(),
        pre_change_end.to_period("M").to_timestamp(),
        freq="MS",
    )
    for m_start in monthly_starts:
        m_end = m_start + pd.offsets.MonthEnd(1)
        p_start = max(join_date, m_start)
        p_end = min(pre_change_end, m_end)
        if p_start <= p_end:
            periods.append({
                "kind": "monthly",
                "label": p_start.strftime("%b %Y"),
                "period_start": p_start,
                "period_end": p_end,
                "expected_salary": prorated_by_days(p_start, p_end, monthly_salary),
                "target_credit_month": (m_start + pd.offsets.MonthBegin(1)).to_period("M").to_timestamp(),
                "target_credit_label": (m_start + pd.offsets.MonthBegin(1)).strftime("%b %Y"),
                "paid_total": 0.0,
                "due_remaining": 0.0,
                "first_credit_month": None,
            })

# Transition gap (e.g., Jul 01-Jul 14)
transition_gap_start = max(join_date, change_month_start)
transition_gap_end = min(leave_date, policy_change_date - pd.Timedelta(days=1))
has_transition_gap = transition_gap_start <= transition_gap_end
transition_gap_amount = (
    prorated_by_days(transition_gap_start, transition_gap_end, monthly_salary) if has_transition_gap else 0.0
)

# 15->14 cycles from policy change date
cycle_start = policy_change_date
while cycle_start <= leave_date:
    cycle_end = cycle_start + pd.DateOffset(months=1) - pd.Timedelta(days=1)

    p_start = max(join_date, cycle_start)
    p_end = min(leave_date, cycle_end)

    if p_start <= p_end:
        full_cycle_days = (cycle_end - cycle_start).days + 1
        worked_days = (p_end - p_start).days + 1
        expected = round(monthly_salary * worked_days / full_cycle_days, 2)

        periods.append({
            "kind": "cycle",
            # Show only the employed span so post-leave days (e.g., Jan 2026) are not shown.
            "label": f"{p_start.strftime('%d %b %Y')} to {p_end.strftime('%d %b %Y')}",
            "period_start": p_start,
            "period_end": p_end,
            "expected_salary": expected,
            "target_credit_month": p_end.to_period("M").to_timestamp(),
            "target_credit_label": p_end.strftime("%b %Y"),
            "paid_total": 0.0,
            "due_remaining": 0.0,
            "first_credit_month": None,
        })

    cycle_start = cycle_end + pd.Timedelta(days=1)

if not periods:
    st.warning("No expected periods generated for selected dates.")
    st.stop()

# Initialize dues
for p in periods:
    p["due_remaining"] = float(p["expected_salary"])

# -------------------------------------------------
# Allocate credits
# -------------------------------------------------

salary_txn["credit_month"] = salary_txn["date"].dt.to_period("M").dt.to_timestamp()
credit_monthly = salary_txn.groupby("credit_month", as_index=False).agg(credit_amount=("credit", "sum"))
credit_monthly["credit_month_label"] = credit_monthly["credit_month"].dt.strftime("%b %Y")

credit_rows = []
for cm in credit_monthly.itertuples(index=False):
    amount_left = float(cm.credit_amount)
    covered = []
    allocated_total = 0.0

    # 1) allocate to periods expected in this credit month
    matching = [p for p in periods if p["target_credit_month"] == cm.credit_month and p["due_remaining"] > 0]
    matching.sort(key=lambda x: x["period_start"])

    for p in matching:
        if amount_left <= 0:
            break
        alloc = min(amount_left, p["due_remaining"])
        p["due_remaining"] = round(p["due_remaining"] - alloc, 2)
        p["paid_total"] = round(p["paid_total"] + alloc, 2)
        if p["first_credit_month"] is None:
            p["first_credit_month"] = cm.credit_month
        amount_left = round(amount_left - alloc, 2)
        allocated_total += alloc
        covered.append(f"{p['label']} (Rs {alloc:,.2f})")

    # 2) remaining amount clears nearest past pending dues first
    past_pending = [p for p in periods if p["target_credit_month"] < cm.credit_month and p["due_remaining"] > 0]
    past_pending.sort(key=lambda x: x["target_credit_month"], reverse=True)

    for p in past_pending:
        if amount_left <= 0:
            break
        alloc = min(amount_left, p["due_remaining"])
        p["due_remaining"] = round(p["due_remaining"] - alloc, 2)
        p["paid_total"] = round(p["paid_total"] + alloc, 2)
        if p["first_credit_month"] is None:
            p["first_credit_month"] = cm.credit_month
        amount_left = round(amount_left - alloc, 2)
        allocated_total += alloc
        covered.append(f"{p['label']} (Rs {alloc:,.2f})")

    sunday_extra = amount_left if 1000 <= amount_left <= 3000 else 0.0

    credit_rows.append({
        "credit_month": cm.credit_month,
        "credit_month_label": cm.credit_month_label,
        "credited_amount": float(cm.credit_amount),
        "allocated_amount": round(allocated_total, 2),
        "unallocated_amount": round(amount_left, 2),
        "sunday_extra_flag": round(sunday_extra, 2),
        "allocation_statement": "; ".join(covered) if covered else "No period covered",
    })

period_out = pd.DataFrame(periods).sort_values("period_start").reset_index(drop=True)
credit_out = pd.DataFrame(credit_rows)

# -------------------------------------------------
# Statements
# -------------------------------------------------

statement_rows = []
for p in period_out.itertuples(index=False):
    if p.paid_total == 0:
        status = "Pending"
    elif p.due_remaining > 0: # type: ignore
        status = "Partial Pending"
    else:
        if p.first_credit_month is None:
            status = "Pending"
        else:
            delay = (p.first_credit_month.year - p.target_credit_month.year) * 12 + (p.first_credit_month.month - p.target_credit_month.month) # type: ignore
            status = "On Time" if delay <= 0 else "Delayed"

    if p.kind == "monthly":
        if status == "On Time":
            statement = f"{p.label} work salary was credited by {p.target_credit_label} (as expected)."
        elif status == "Delayed":
            credited_label = p.first_credit_month.strftime("%b %Y") # type: ignore
            statement = f"{p.label} work salary expected in {p.target_credit_label} was credited later in {credited_label}."
        elif status == "Partial Pending":
            statement = f"{p.label} work salary expected in {p.target_credit_label} is partially pending. Rs {p.due_remaining:,.2f} due."
        else:
            statement = f"{p.label} work salary expected in {p.target_credit_label} is pending. Rs {p.due_remaining:,.2f} due."
    else:
        if status == "On Time":
            statement = f"Cycle {p.label} was credited on time (by {p.target_credit_label})."
        elif status == "Delayed":
            credited_label = p.first_credit_month.strftime("%b %Y") # type: ignore
            statement = f"Cycle {p.label} was credited later in {credited_label} (expected by {p.target_credit_label})."
        elif status == "Partial Pending":
            statement = f"Cycle {p.label} is partially paid. Pending Rs {p.due_remaining:,.2f}."
        else:
            statement = f"Cycle {p.label} is pending. Rs {p.due_remaining:,.2f} due."

    statement_rows.append({
        "kind": p.kind,
        "label": p.label,
        "target_credit_label": p.target_credit_label,
        "expected_salary": p.expected_salary,
        "paid_total": p.paid_total,
        "due_remaining": p.due_remaining,
        "status": status,
        "statement": statement,
    })

status_out = pd.DataFrame(statement_rows)

# Add transition gap as its own pending line item so it is visible in month-level decisions.
if has_transition_gap and transition_gap_amount > 0:
    transition_label = (
        f"{transition_gap_start.strftime('%d %b %Y')} to "
        f"{transition_gap_end.strftime('%d %b %Y')} (Transition)"
    )
    transition_target = (transition_gap_end + pd.offsets.MonthBegin(1)).strftime("%b %Y")
    transition_statement = (
        f"{transition_label} salary portion became pending due to cycle change. "
        f"Pending Rs {transition_gap_amount:,.2f}."
    )
    transition_row = pd.DataFrame([{
        "kind": "transition",
        "label": transition_label,
        "target_credit_label": transition_target,
        "expected_salary": transition_gap_amount,
        "paid_total": 0.0,
        "due_remaining": transition_gap_amount,
        "status": "Pending",
        "statement": transition_statement,
    }])
    status_out = pd.concat([status_out, transition_row], ignore_index=True)

# Final pending statement for last cycle period
final_pending_statement = ""
cycle_only = status_out[status_out["kind"] == "cycle"]
if not cycle_only.empty:
    last_cycle = cycle_only.iloc[-1]
    if float(last_cycle["due_remaining"]) > 0:
        final_pending_statement = (
            f"Final period pending: {last_cycle['label']} still has Rs {float(last_cycle['due_remaining']):,.2f} due."
        )

col_a, col_b, col_c, col_d = st.columns(4)
col_a.metric("Expected Salary", f"Rs {status_out['expected_salary'].sum():,.2f}")
col_b.metric("Credited to Salary", f"Rs {status_out['paid_total'].sum():,.2f}")
col_c.metric("Outstanding Due", f"Rs {status_out['due_remaining'].sum():,.2f}")
col_d.metric("Sunday Extra", f"Rs {credit_out['sunday_extra_flag'].sum():,.2f}" if not credit_out.empty else "Rs 0.00")

st.divider()

st.subheader("Decision Summary")
pending_count = int((status_out["status"] == "Pending").sum() + (status_out["status"] == "Partial Pending").sum())
pending_due = float(status_out["due_remaining"].sum())
st.info(
    f"On-time: {(status_out['status'] == 'On Time').sum()}, "
    f"Delayed: {(status_out['status'] == 'Delayed').sum()}, "
    f"Partial pending: {(status_out['status'] == 'Partial Pending').sum()}, "
    f"Pending: {(status_out['status'] == 'Pending').sum()}, "
    f"Total pending records: {pending_count}, "
    f"Total due amount: Rs {pending_due:,.2f}."
)

st.subheader("Decision Statements")
for line in status_out["statement"].tolist():
    st.write(f"- {line}")
if final_pending_statement:
    st.write(f"- {final_pending_statement}")

st.subheader("Expected vs Paid")
fig = px.bar(
    status_out,
    x="label",
    y=["expected_salary", "paid_total", "due_remaining"],
    barmode="group",
    labels={"value": "Amount (Rs)", "label": "Period", "variable": "Metric"}
)
st.plotly_chart(fig, use_container_width=True)

if not credit_out.empty:
    st.subheader("Credit Month Allocation")
    st.dataframe(
        credit_out.sort_values("credit_month")[[
            "credit_month_label",
            "credited_amount",
            "allocated_amount",
            "unallocated_amount",
            "sunday_extra_flag",
            "allocation_statement",
        ]],
        use_container_width=True,
    )

st.subheader("Detailed Statement Table")
st.dataframe(
    status_out[[
        "label",
        "target_credit_label",
        "expected_salary",
        "paid_total",
        "due_remaining",
        "status",
        "statement",
    ]],
    use_container_width=True,
)
