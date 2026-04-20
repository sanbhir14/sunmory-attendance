from __future__ import annotations

import streamlit as st

from utils.performance import load_performance_data


st.title("Match Recap")
st.caption("Ringkasan match komunitas: poin, match, win, dan aktivitas session.")

summary, records, message = load_performance_data()

if message != "Data performance dari Google Sheets":
    st.warning(message)

if summary.empty:
    st.info("Belum ada performance data.")
    st.stop()

total_players = int(summary["player_name"].nunique()) if "player_name" in summary else 0
total_points = int(summary["total_points"].sum()) if "total_points" in summary else 0
total_matches = int(summary["matches_played"].sum()) if "matches_played" in summary else 0
avg_win_rate = float(summary["win_rate"].mean()) if "win_rate" in summary and not summary.empty else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Player aktif", total_players)
k2.metric("Total match", total_matches)
k3.metric("Total poin", total_points)
k4.metric("Avg win rate", f"{avg_win_rate:.1f}%")

st.subheader("Community highlights")
top_cols = st.columns(3)
for idx, player in enumerate(summary.head(3).itertuples()):
    with top_cols[idx]:
        label = ["Most points", "Strong run", "On form"][idx]
        st.metric(label, player.player_name, f"{int(player.total_points)} poin")

st.subheader("Match table")
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
