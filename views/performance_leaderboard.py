from __future__ import annotations

import streamlit as st

from utils.performance import load_performance_data


st.title("Performance Leaderboard")
st.caption("Ranking performa berdasarkan poin match yang diinput admin.")

summary, records, message = load_performance_data()

if message != "Data performance dari Google Sheets":
    st.warning(message)

if summary.empty:
    st.info("Belum ada performance data.")
    st.stop()

top_cols = st.columns(3)
for idx, player in enumerate(summary.head(3).itertuples()):
    with top_cols[idx]:
        st.metric(f"#{int(player.rank)}", player.player_name, f"{int(player.total_points)} poin")

st.subheader("Ranking lengkap")
display = summary[
    [
        "rank",
        "player_name",
        "total_points",
        "matches_played",
        "wins",
        "losses",
        "win_rate",
        "sessions_played",
        "last_session_date",
    ]
].copy()

st.dataframe(
    display,
    hide_index=True,
    use_container_width=True,
    column_config={
        "rank": "Rank",
        "player_name": "Player",
        "total_points": "Poin",
        "matches_played": "Match",
        "wins": "Win",
        "losses": "Lose",
        "win_rate": "Win rate %",
        "sessions_played": "Session",
        "last_session_date": "Last session",
    },
)

with st.expander("Recent performance records"):
    if records.empty:
        st.info("Belum ada record.")
    else:
        recent = records.tail(20).iloc[::-1]
        public_columns = ["session_date", "venue", "player_name", "matches_played", "wins", "losses", "points"]
        existing_columns = [column for column in public_columns if column in recent.columns]
        st.dataframe(recent[existing_columns], hide_index=True, use_container_width=True)
