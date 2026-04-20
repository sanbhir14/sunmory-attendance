from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.app_data import load_app_data
from utils.auth import require_admin
from utils.data_processing import find_player
from utils.ui import dataframe_dates, format_date

require_admin()

attendance_df, player_summary, _ = load_app_data()

st.title("Player Dashboard")
st.caption("Cari player dari nama atau nomor HP untuk cek stamp, reward, dan history session.")

query = st.text_input("Nama atau nomor HP", placeholder="Contoh: Sandi atau 0812...")
matches = find_player(player_summary, query)

if not query:
    st.info("Masukkan nama atau nomor HP untuk mulai mencari player.")
    st.stop()

if matches.empty:
    st.warning(f"Player `{query}` belum ditemukan. Coba cek ejaan nama atau nomor HP yang dipakai saat isi form.")
    st.stop()

selected_name = st.selectbox("Pilih player", matches["player_name"].tolist(), key=f"player_select_{query.lower()}")
player = matches[matches["player_name"] == selected_name].iloc[0]
history = attendance_df[attendance_df["player_id"] == player["player_id"]].sort_values("session_date", ascending=False)

st.subheader(player["player_name"])
st.caption(f"Player ID: {player['player_id']}")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total session", int(player["total_session"]))
k2.metric("Total stamp", int(player["total_stamp"]))
k3.metric("Last played", format_date(player["last_played"]))
k4.metric("Venue pernah dimainkan", int(player["venue_count"]))

st.markdown("**Nomor HP**")
st.write(player["phone"] or "-")

st.markdown("**Daftar venue**")
st.write(player["venues"] or "-")

st.subheader("Progress reward")
st.progress(float(player["progress"]))
if int(player["stamps_remaining"]) == 0:
    st.success(player["next_reward"])
else:
    st.info(
        f"Reward berikutnya: {player['next_reward']} "
        f"di {int(player['next_milestone'])} stamp. "
        f"Sisa {int(player['stamps_remaining'])} stamp lagi."
    )

st.subheader("History session")
if history.empty:
    st.info("Belum ada history session.")
else:
    history_display = history[["session_date", "venue", "session_id", "timestamp"]].copy()
    history_display["timestamp"] = pd.to_datetime(history_display["timestamp"], errors="coerce").dt.strftime("%d %b %Y %H:%M")
    st.dataframe(
        dataframe_dates(history_display, ["session_date"]),
        hide_index=True,
        use_container_width=True,
        column_config={
            "session_date": "Tanggal session",
            "venue": "Venue",
            "session_id": "Session ID",
            "timestamp": "Check-in",
        },
    )
