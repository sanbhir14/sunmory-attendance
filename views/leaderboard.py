from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from utils.app_data import load_app_data
from utils.data_processing import build_leaderboard
from utils.ui import dataframe_dates, rank_label


MONTH_NAMES = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "Mei",
    6: "Jun",
    7: "Jul",
    8: "Agu",
    9: "Sep",
    10: "Okt",
    11: "Nov",
    12: "Des",
}


def month_label(month_key: str) -> str:
    try:
        year, month = month_key.split("-")
        return f"{MONTH_NAMES[int(month)]} {year}"
    except Exception:
        return month_key


def filter_by_month(df: pd.DataFrame, period: str) -> pd.DataFrame:
    if df.empty or period == "all_time":
        return df
    dates = pd.to_datetime(df["session_date"], errors="coerce")
    return df[dates.dt.strftime("%Y-%m") == period]


attendance_df, _, _ = load_app_data()

st.title("Attendance Leaderboard")
st.caption("Ranking player berdasarkan total stamp.")

if attendance_df.empty:
    st.info("Belum ada data attendance.")
    st.stop()

attendance_months = pd.to_datetime(attendance_df["session_date"], errors="coerce").dt.strftime("%Y-%m")
available_months = sorted([month for month in attendance_months.dropna().unique().tolist() if month], reverse=True)
current_month_key = pd.Timestamp.today().strftime("%Y-%m")
other_months = [month for month in available_months if month != current_month_key]
period_options = [current_month_key, "all_time"] + other_months

venues = ["All venues"] + sorted(attendance_df["venue"].dropna().unique().tolist())

filter_col1, filter_col2 = st.columns(2)
period = filter_col1.selectbox(
    "Periode",
    period_options,
    format_func=lambda value: "Bulan ini" if value == current_month_key else ("All time" if value == "all_time" else month_label(value)),
)
venue = filter_col2.selectbox("Venue", venues)

filtered_attendance = filter_by_month(attendance_df, period)
leaderboard = build_leaderboard(filtered_attendance, period="All time", venue=venue)

period_title = "All time" if period == "all_time" else month_label(period)
st.markdown(f"### {period_title}")

if leaderboard.empty:
    st.info("Belum ada data untuk filter ini.")
    st.stop()

public_leaderboard = leaderboard.drop(columns=["phone"], errors="ignore")

st.subheader("Top 3")
top_cols = st.columns(3)
for idx, player in enumerate(leaderboard.head(3).itertuples()):
    with top_cols[idx]:
        st.metric(rank_label(int(player.rank)), player.player_name, f"{int(player.total_stamp)} stamp")

st.subheader("Ranking lengkap")
search_col, page_size_col = st.columns([2, 1])
with search_col:
    search_query = st.text_input("Search nama", placeholder="Cari player...")
with page_size_col:
    page_size = st.selectbox("Rows per page", options=[10, 20, 50], index=0)

table = public_leaderboard.copy()
if search_query.strip():
    query = search_query.strip()
    name_matches = table["player_name"].str.contains(query, case=False, na=False)
    username_matches = table["username_reclub"].str.contains(query.lstrip("@"), case=False, na=False)
    table = table[name_matches | username_matches]

if table.empty:
    st.info("Nama player tidak ditemukan di periode ini.")
    st.stop()

total_rows = len(table)
total_pages = max(1, math.ceil(total_rows / page_size))
page_number = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
start = (page_number - 1) * page_size
end = start + page_size

display = table.iloc[start:end].copy()

st.caption(f"Menampilkan {start + 1}-{min(end, total_rows)} dari {total_rows} player.")
st.dataframe(
    dataframe_dates(display, ["last_played"]),
    hide_index=True,
    use_container_width=True,
    column_config={
        "rank": "Rank",
        "player_name": "Nama",
        "username_reclub": "Username",
        "total_session": "Session",
        "total_stamp": "Stamp",
        "last_played": "Last played",
    },
)
