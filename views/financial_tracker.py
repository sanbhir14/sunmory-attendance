from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.attendance import load_attendance_records, rebuild_finance
from utils.auth import require_admin
from utils.performance import load_all_sessions


require_admin()

st.title("Financial Tracker")
st.caption("Ringkasan income attendance, expense venue, dan profit per session.")

attendance, attendance_message = load_attendance_records()
sessions, sessions_message = load_all_sessions()

if attendance_message != "Data attendance dari attendance_log":
    st.info(attendance_message)
if sessions_message != "Sessions dari Google Sheets":
    st.info(sessions_message)

if sessions.empty:
    st.warning("Belum ada session.")
    st.stop()

if "session_id" not in sessions.columns:
    st.warning("Data sessions belum punya kolom session_id. Generate session baru atau redeploy Apps Script terbaru.")
    st.stop()

if st.button("Sync finance sheets", use_container_width=True):
    ok, sync_message = rebuild_finance()
    if ok:
        st.success(sync_message)
        st.cache_data.clear()
        st.rerun()
    else:
        st.error(sync_message)

for column in ["expense_amount", "player_price"]:
    if column not in sessions.columns:
        sessions[column] = 0
    sessions[column] = pd.to_numeric(sessions[column], errors="coerce").fillna(0)

if attendance.empty:
    attendance = pd.DataFrame(columns=["session_id", "income_amount", "attendance_type", "claimed_reward"])

for column in ["income_amount", "base_price", "discount_percent"]:
    if column not in attendance.columns:
        attendance[column] = 0
    attendance[column] = pd.to_numeric(attendance[column], errors="coerce").fillna(0)

for column in ["session_id", "attendance_type", "claimed_reward", "player_name", "username_reclub"]:
    if column not in attendance.columns:
        attendance[column] = ""
    attendance[column] = attendance[column].astype(str)

regular_attendance = attendance[attendance["attendance_type"].str.lower().ne("referral_bonus")].copy()
if regular_attendance.empty:
    income_by_session = pd.DataFrame(columns=["session_id", "players", "income", "rewards_claimed"])
else:
    income_by_session = regular_attendance.groupby("session_id").agg(
        players=("session_id", "size"),
        income=("income_amount", "sum"),
        rewards_claimed=("claimed_reward", lambda values: int(values.astype(str).str.strip().ne("").sum())),
    ).reset_index()

finance = sessions.merge(income_by_session, on="session_id", how="left")
for column in ["players", "income", "rewards_claimed"]:
    if column not in finance.columns:
        finance[column] = 0
    finance[column] = pd.to_numeric(finance[column], errors="coerce").fillna(0)
finance["profit"] = finance["income"] - finance["expense_amount"]
finance["session_date_dt"] = pd.to_datetime(finance["session_date"], errors="coerce")

months = finance["session_date_dt"].dt.strftime("%Y-%m").dropna().unique().tolist()
months = sorted(months, reverse=True)
current_month = pd.Timestamp.today().strftime("%Y-%m")
period_options = [current_month, "all_time"] + [month for month in months if month != current_month]
period = st.selectbox(
    "Periode",
    period_options,
    format_func=lambda value: "Bulan ini" if value == current_month else ("All time" if value == "all_time" else value),
)

filtered = finance if period == "all_time" else finance[finance["session_date_dt"].dt.strftime("%Y-%m") == period]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Income", f"Rp {int(filtered['income'].sum()):,}")
k2.metric("Expense", f"Rp {int(filtered['expense_amount'].sum()):,}")
k3.metric("Profit", f"Rp {int(filtered['profit'].sum()):,}")
k4.metric("Players paid", int(filtered["players"].sum()))

st.subheader("Session finance")
display_columns = [
    "session_date",
    "venue",
    "session_slot",
    "players",
    "player_price",
    "income",
    "expense_amount",
    "profit",
    "rewards_claimed",
    "paid_by",
    "status",
]
existing_columns = [column for column in display_columns if column in filtered.columns]
st.dataframe(
    filtered.sort_values("session_date_dt", ascending=False)[existing_columns],
    hide_index=True,
    use_container_width=True,
    column_config={
        "session_date": "Tanggal",
        "venue": "Venue",
        "session_slot": "Slot",
        "players": "Players",
        "player_price": "Harga/player",
        "income": "Income",
        "expense_amount": "Expense",
        "profit": "Profit",
        "rewards_claimed": "Reward claim",
        "paid_by": "Paid by",
        "status": "Status",
    },
)

st.subheader("Reward claims")
reward_claims = regular_attendance[regular_attendance["claimed_reward"].astype(str).str.strip().ne("")]
if reward_claims.empty:
    st.info("Belum ada reward yang diklaim.")
else:
    claim_columns = ["session_date", "venue", "username_reclub", "player_name", "claimed_reward", "discount_percent", "income_amount"]
    existing_claim_columns = [column for column in claim_columns if column in reward_claims.columns]
    st.dataframe(
        reward_claims[existing_claim_columns].sort_values("session_date", ascending=False),
        hide_index=True,
        use_container_width=True,
        column_config={
            "session_date": "Tanggal",
            "venue": "Venue",
            "username_reclub": "Username",
            "player_name": "Nama",
            "claimed_reward": "Reward",
            "discount_percent": "Diskon %",
            "income_amount": "Income",
        },
    )
