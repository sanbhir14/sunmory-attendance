from __future__ import annotations

import plotly.express as px
import streamlit as st

from utils.app_data import load_app_data
from utils.auth import require_admin
from utils.data_processing import (
    attendance_trend,
    build_leaderboard,
    dashboard_metrics,
    players_near_reward,
)
from utils.ui import dataframe_dates, format_date, page_header, render_logo, show_empty_state


require_admin()

attendance_df, player_summary, source_message = load_app_data()
metrics = dashboard_metrics(attendance_df, player_summary)

render_logo(width=180)
page_header(
    "Sunmory Padel Club",
    "Dashboard komunitas untuk attendance, stamp, reward, dan leaderboard player.",
)

if "dummy" in source_message.lower() or "gagal" in source_message.lower() or "setup" in source_message.lower():
    st.warning(source_message)
else:
    st.success(source_message)

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("Player unik", metrics["total_players"])
kpi2.metric("Total attendance", metrics["total_attendance"])
kpi3.metric("Repeat player", metrics["repeat_players"])
kpi4.metric("Venue paling ramai", metrics["busiest_venue"])
kpi5.metric("Reward tercapai", metrics["total_rewards"])

st.divider()

if attendance_df.empty:
    show_empty_state()
    st.stop()

left, right = st.columns([1.25, 1])

with left:
    st.subheader("Top 10 Leaderboard")
    leaderboard = build_leaderboard(attendance_df).head(10)
    st.dataframe(
        dataframe_dates(leaderboard, ["last_played"]),
        hide_index=True,
        use_container_width=True,
        column_config={
            "rank": "Rank",
            "player_name": "Player",
            "total_session": "Session",
            "total_stamp": "Stamp",
            "last_played": "Last played",
        },
    )

with right:
    st.subheader("Top Player bulan ini")
    month_leaderboard = build_leaderboard(attendance_df, period="Bulan ini").head(5)
    if month_leaderboard.empty:
        show_empty_state("Belum ada attendance bulan ini.")
    else:
        for row in month_leaderboard.itertuples():
            st.markdown(
                f"""
                <div class="top-player">
                    <strong>#{row.rank} {row.player_name}</strong><br>
                    <span class="muted">{row.total_stamp} stamp - last played {format_date(row.last_played)}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

chart_col, recent_col = st.columns([1.2, 1])

with chart_col:
    st.subheader("Trend attendance")
    trend_df = attendance_trend(attendance_df)
    fig = px.line(
        trend_df,
        x="session_date",
        y="attendance",
        markers=True,
        labels={"session_date": "Tanggal", "attendance": "Attendance"},
    )
    fig.update_layout(height=340, margin=dict(l=8, r=8, t=20, b=8))
    st.plotly_chart(fig, use_container_width=True)

with recent_col:
    st.subheader("Recent activity")
    recent = attendance_df[["session_date", "player_name", "venue", "session_id"]].head(8)
    st.dataframe(
        dataframe_dates(recent, ["session_date"]),
        hide_index=True,
        use_container_width=True,
        column_config={
            "session_date": "Tanggal",
            "player_name": "Player",
            "venue": "Venue",
            "session_id": "Session",
        },
    )

st.subheader("Player yang hampir dapet reward")
near_reward = players_near_reward(player_summary, limit=8)
if near_reward.empty:
    st.info("Belum ada player yang berjarak 1-2 stamp dari reward berikutnya.")
else:
    display_cols = ["player_name", "total_stamp", "next_reward", "stamps_remaining", "last_played"]
    st.dataframe(
        dataframe_dates(near_reward[display_cols], ["last_played"]),
        hide_index=True,
        use_container_width=True,
        column_config={
            "player_name": "Player",
            "total_stamp": "Stamp",
            "next_reward": "Reward berikutnya",
            "stamps_remaining": "Sisa stamp",
            "last_played": "Last played",
        },
    )
