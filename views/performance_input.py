from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from utils.auth import require_admin
from utils.performance import prepare_performance_records, submit_performance_records


require_admin()

st.title("Performance Input")
st.caption("Input poin dan hasil match per session. Data akan masuk ke tab `performance_log`.")

with st.form("performance_session_form"):
    col1, col2 = st.columns(2)
    with col1:
        session_id = st.text_input("Session ID", placeholder="Contoh: SPC-20260420-NEO-PADEL-JATIWARINGIN-MORNING")
        session_code = st.text_input("Session Code", placeholder="Contoh: A7K2Q9")
        session_date = st.date_input("Tanggal session", value=date.today())
    with col2:
        venue = st.selectbox(
            "Venue",
            [
                "Neo Padel Jatiwaringin",
                "Victoria Social Club Kemang",
            ],
        )
        auto_points = st.checkbox("Auto hitung poin: win 3, lose 1", value=True)

    st.markdown("**Player performance**")
    initial_rows = pd.DataFrame(
        [
            {"player_name": "", "matches_played": 0, "wins": 0, "losses": 0, "points": 0, "notes": ""},
            {"player_name": "", "matches_played": 0, "wins": 0, "losses": 0, "points": 0, "notes": ""},
            {"player_name": "", "matches_played": 0, "wins": 0, "losses": 0, "points": 0, "notes": ""},
            {"player_name": "", "matches_played": 0, "wins": 0, "losses": 0, "points": 0, "notes": ""},
        ]
    )
    rows = st.data_editor(
        initial_rows,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "player_name": st.column_config.TextColumn("Player", required=False),
            "matches_played": st.column_config.NumberColumn("Match", min_value=0, step=1),
            "wins": st.column_config.NumberColumn("Win", min_value=0, step=1),
            "losses": st.column_config.NumberColumn("Lose", min_value=0, step=1),
            "points": st.column_config.NumberColumn("Poin", min_value=0, step=1, disabled=auto_points),
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
        auto_points=auto_points,
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
