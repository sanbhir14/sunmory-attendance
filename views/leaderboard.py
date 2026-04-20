from __future__ import annotations

import streamlit as st

from utils.app_data import load_app_data
from utils.data_processing import build_leaderboard
from utils.ui import dataframe_dates, rank_label

attendance_df, _, _ = load_app_data()

st.title("Leaderboard")
st.caption("Ranking player berdasarkan total stamp.")

venues = ["All venues"] + sorted(attendance_df["venue"].dropna().unique().tolist()) if not attendance_df.empty else ["All venues"]

filter_col1, filter_col2 = st.columns(2)
period = filter_col1.selectbox("Periode", ["All time", "Bulan ini"])
venue = filter_col2.selectbox("Venue", venues)

leaderboard = build_leaderboard(attendance_df, period=period, venue=venue)

if leaderboard.empty:
    st.info("Belum ada data untuk filter ini.")
    st.stop()

public_leaderboard = leaderboard.drop(columns=["phone"], errors="ignore")

st.subheader("Top 3")
top_cols = st.columns(3)
for idx, player in enumerate(leaderboard.head(3).itertuples()):
    with top_cols[idx]:
        st.metric(rank_label(int(player.rank)), player.player_name, f"{player.total_stamp} stamp")

st.subheader("Ranking lengkap")
st.dataframe(
    dataframe_dates(public_leaderboard, ["last_played"]),
    hide_index=True,
    use_container_width=True,
    column_config={
        "rank": "Rank",
        "player_name": "Nama",
        "total_session": "Session",
        "total_stamp": "Stamp",
        "last_played": "Last played",
    },
)
