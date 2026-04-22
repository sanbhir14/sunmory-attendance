from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.auth import require_admin
from utils.performance import load_open_sessions, prepare_performance_records, submit_performance_records


require_admin()

st.title("Performance Input")
st.caption("Input poin dan hasil match per session. Data akan masuk ke tab `performance_log`.")

sessions, sessions_message = load_open_sessions()
if sessions_message != "Open sessions dari Google Sheets":
    st.info(sessions_message)

with st.form("performance_session_form"):
    if not sessions.empty:
        sessions = sessions.reset_index(drop=True)
        sessions["label"] = (
            sessions["session_date"].astype(str)
            + " - "
            + sessions["venue"].astype(str)
            + " - "
            + sessions["session_slot"].astype(str)
            + " ("
            + sessions["session_code"].astype(str)
            + ")"
        )
        selected_label = st.selectbox("Pilih open session", sessions["label"].tolist())
        selected_session = sessions[sessions["label"] == selected_label].iloc[0]

        col1, col2, col3 = st.columns(3)
        col1.text_input("Session ID", value=str(selected_session["session_id"]), disabled=True)
        col2.text_input("Session Code", value=str(selected_session["session_code"]), disabled=True)
        col3.text_input("Tanggal session", value=str(selected_session["session_date"]), disabled=True)
        st.text_input("Venue", value=str(selected_session["venue"]), disabled=True)

        session_id = str(selected_session["session_id"])
        session_code = str(selected_session["session_code"])
        session_date = selected_session["session_date"]
        venue = str(selected_session["venue"])
    else:
        st.warning("Tidak ada session open. Generate session dulu dari Session Generator.")
        st.stop()

    st.info("Poin diisi manual sesuai hasil skor/match. Win/Lose tetap dicatat untuk recap.")

    st.markdown("**Player performance**")
    initial_rows = pd.DataFrame(
        [
            {"username_reclub": "", "player_name": "", "matches_played": 0, "wins": 0, "losses": 0, "points": 0, "notes": ""},
            {"username_reclub": "", "player_name": "", "matches_played": 0, "wins": 0, "losses": 0, "points": 0, "notes": ""},
            {"username_reclub": "", "player_name": "", "matches_played": 0, "wins": 0, "losses": 0, "points": 0, "notes": ""},
            {"username_reclub": "", "player_name": "", "matches_played": 0, "wins": 0, "losses": 0, "points": 0, "notes": ""},
        ]
    )
    rows = st.data_editor(
        initial_rows,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "username_reclub": st.column_config.TextColumn("Username", required=False),
            "player_name": st.column_config.TextColumn("Nama", required=False),
            "matches_played": st.column_config.NumberColumn("Match", min_value=0, step=1),
            "wins": st.column_config.NumberColumn("Win", min_value=0, step=1),
            "losses": st.column_config.NumberColumn("Lose", min_value=0, step=1),
            "points": st.column_config.NumberColumn("Poin", min_value=0, step=1),
            "notes": st.column_config.TextColumn("Notes"),
        },
    )

    submitted = st.form_submit_button("Submit Performance", use_container_width=True)

if submitted:
    if not session_id.strip() and not session_code.strip():
        st.error("Isi minimal Session ID atau Session Code.")
        st.stop()

    records = prepare_performance_records(
        session_id=session_id,
        session_code=session_code,
        session_date=session_date,
        venue=venue,
        rows=rows,
    )

    if not records:
        st.error("Isi minimal satu player.")
        st.stop()

    ok, message = submit_performance_records(records)
    if ok:
        st.success(message)
        st.cache_data.clear()
    else:
        st.error(message)
