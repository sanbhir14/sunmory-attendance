from __future__ import annotations

import streamlit as st

from utils.auth import require_admin
from utils.performance import load_all_sessions, update_session_status


require_admin()

st.title("Session Manager")
st.caption("Lihat semua session dan ubah status open/closed.")

sessions, message = load_all_sessions()
if message != "Sessions dari Google Sheets":
    st.info(message)

if sessions.empty:
    st.warning("Belum ada session. Generate session dulu dari Session Generator.")
    st.stop()

display_columns = [
    "session_date",
    "venue",
    "session_slot",
    "session_code",
    "status",
    "expense_amount",
    "player_price",
    "paid_by",
    "session_id",
]
existing_columns = [column for column in display_columns if column in sessions.columns]

open_count = int((sessions["status"].astype(str).str.lower() == "open").sum())
closed_count = int((sessions["status"].astype(str).str.lower() == "closed").sum())
k1, k2, k3 = st.columns(3)
k1.metric("Total session", len(sessions))
k2.metric("Open", open_count)
k3.metric("Closed", closed_count)

st.subheader("All sessions")
st.dataframe(
    sessions[existing_columns],
    hide_index=True,
    use_container_width=True,
    column_config={
        "session_date": "Tanggal",
        "venue": "Venue",
        "session_slot": "Slot",
        "session_code": "Code",
        "status": "Status",
        "expense_amount": "Expense",
        "player_price": "Harga/player",
        "paid_by": "Paid by",
        "session_id": "Session ID",
    },
)

sessions = sessions.reset_index(drop=True)
sessions["label"] = (
    sessions["session_date"].astype(str)
    + " - "
    + sessions["venue"].astype(str)
    + " - "
    + sessions["session_slot"].astype(str)
    + " ("
    + sessions["status"].astype(str)
    + ")"
)

st.subheader("Update status")
with st.form("session_status_form"):
    selected_label = st.selectbox("Pilih session", sessions["label"].tolist())
    selected_session = sessions[sessions["label"] == selected_label].iloc[0]
    new_status = st.selectbox(
        "Status baru",
        ["open", "closed"],
        index=0 if str(selected_session["status"]).lower() != "open" else 1,
    )
    st.caption(f"Session ID: {selected_session['session_id']}")
    submitted = st.form_submit_button("Update Session Status", use_container_width=True)

if submitted:
    ok, update_message = update_session_status(str(selected_session["session_id"]), new_status)
    if ok:
        st.success(update_message)
        st.cache_data.clear()
    else:
        st.error(update_message)
