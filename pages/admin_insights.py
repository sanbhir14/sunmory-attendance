from __future__ import annotations

import plotly.express as px
import streamlit as st

from utils.app_data import load_app_data
from utils.data_processing import monthly_attendance, players_near_reward, repeat_vs_new
from utils.ui import dataframe_dates

attendance_df, player_summary, _ = load_app_data()

st.title("Admin Insights")
st.caption("Ringkasan operasional komunitas untuk venue, repeat player, dan reward.")

if attendance_df.empty:
    st.info("Belum ada data attendance.")
    st.stop()

venue_counts = attendance_df["venue"].value_counts().rename_axis("venue").reset_index(name="attendance")
monthly = monthly_attendance(attendance_df)
repeat_new = repeat_vs_new(attendance_df)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total attendance", len(attendance_df))
k2.metric("Venue aktif", attendance_df["venue"].nunique())
k3.metric("Player unik", player_summary["player_id"].nunique() if not player_summary.empty else 0)
k4.metric("Repeat player", int((player_summary["total_session"] > 1).sum()) if not player_summary.empty else 0)

chart_layout = dict(
    height=340,
    margin=dict(l=8, r=8, t=20, b=8),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#f5f7fb"),
)

left, right = st.columns(2)

with left:
    st.subheader("Attendance per venue")
    fig = px.bar(
        venue_counts,
        x="venue",
        y="attendance",
        text="attendance",
        labels={"venue": "Venue", "attendance": "Attendance"},
        color_discrete_sequence=["#2dd4bf"],
    )
    fig.update_traces(textposition="outside", marker_line_width=0)
    fig.update_layout(**chart_layout)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(venue_counts, hide_index=True, use_container_width=True)

with right:
    st.subheader("Repeat vs new player")
    fig = px.pie(
        repeat_new,
        names="type",
        values="count",
        hole=0.45,
        color_discrete_sequence=["#f2c94c", "#2dd4bf"],
    )
    fig.update_layout(**chart_layout)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(repeat_new, hide_index=True, use_container_width=True)

st.subheader("Attendance per bulan")
fig = px.line(
    monthly,
    x="month",
    y="attendance",
    markers=True,
    labels={"month": "Bulan", "attendance": "Attendance"},
    color_discrete_sequence=["#2dd4bf"],
)
fig.update_traces(line=dict(width=3), marker=dict(size=9))
fig.update_layout(**chart_layout)
st.plotly_chart(fig, use_container_width=True)
st.dataframe(monthly, hide_index=True, use_container_width=True)

loyal_cols, reward_cols = st.columns(2)

with loyal_cols:
    st.subheader("Player paling loyal")
    loyal = player_summary.head(10)[["player_name", "total_session", "total_stamp", "last_played"]]
    st.dataframe(
        dataframe_dates(loyal, ["last_played"]),
        hide_index=True,
        use_container_width=True,
        column_config={
            "player_name": "Player",
            "total_session": "Session",
            "total_stamp": "Stamp",
            "last_played": "Last played",
        },
    )

with reward_cols:
    st.subheader("Hampir mencapai reward")
    near_reward = players_near_reward(player_summary, limit=10)
    if near_reward.empty:
        st.info("Belum ada player yang berjarak 1-2 stamp dari reward berikutnya.")
    else:
        st.dataframe(
            near_reward[["player_name", "total_stamp", "next_reward", "stamps_remaining"]],
            hide_index=True,
            use_container_width=True,
            column_config={
                "player_name": "Player",
                "total_stamp": "Stamp",
                "next_reward": "Reward berikutnya",
                "stamps_remaining": "Sisa stamp",
            },
        )
