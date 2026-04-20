from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from utils.performance import load_performance_data


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


def prepare_records(records: pd.DataFrame) -> pd.DataFrame:
    clean = records.copy()
    for column in ["points", "matches_played", "wins", "losses"]:
        if column not in clean.columns:
            clean[column] = 0
        clean[column] = pd.to_numeric(clean[column], errors="coerce").fillna(0)

    for column in ["player_name", "player_key", "session_id", "venue"]:
        if column not in clean.columns:
            clean[column] = ""
        clean[column] = clean[column].astype(str).fillna("").str.strip()

    if "session_date" not in clean.columns:
        clean["session_date"] = ""

    clean["session_date_dt"] = pd.to_datetime(clean["session_date"], errors="coerce")
    clean["month_key"] = clean["session_date_dt"].dt.strftime("%Y-%m")
    clean["player_group"] = clean["player_key"]
    clean.loc[clean["player_group"] == "", "player_group"] = clean["player_name"].str.lower()
    return clean


def month_label(month_key: str) -> str:
    try:
        year, month = month_key.split("-")
        return f"{MONTH_NAMES[int(month)]} {year}"
    except Exception:
        return month_key


def aggregate_ranking(records: pd.DataFrame) -> pd.DataFrame:
    if records.empty:
        return pd.DataFrame(
            columns=[
                "rank",
                "player_name",
                "sessions",
                "total_points",
                "avg_points",
                "win_rate",
            ]
        )

    grouped = records.groupby("player_group", dropna=False).agg(
        player_name=("player_name", "last"),
        sessions=("session_id", lambda value: value.replace("", pd.NA).nunique()),
        total_points=("points", "sum"),
        matches_played=("matches_played", "sum"),
        wins=("wins", "sum"),
        losses=("losses", "sum"),
    )
    grouped = grouped.reset_index(drop=True)
    grouped["sessions"] = grouped["sessions"].replace(0, 1)
    grouped["avg_points"] = grouped["total_points"] / grouped["sessions"]
    grouped["win_rate"] = grouped.apply(
        lambda row: (row["wins"] / row["matches_played"] * 100) if row["matches_played"] else 0,
        axis=1,
    )
    grouped = grouped.sort_values(
        ["total_points", "avg_points", "win_rate", "player_name"],
        ascending=[False, False, False, True],
    ).reset_index(drop=True)
    grouped["rank"] = grouped.index + 1
    return grouped


st.title("Match Recap")
st.caption("Ringkasan match komunitas: poin, match, win, dan aktivitas session.")

_, records, message = load_performance_data()

if message != "Data performance dari Google Sheets":
    st.warning(message)

if records.empty:
    st.info("Belum ada performance data.")
    st.stop()

records = prepare_records(records)
current_month_key = pd.Timestamp.today().strftime("%Y-%m")
available_months = sorted(
    [month for month in records["month_key"].dropna().unique().tolist() if month],
    reverse=True,
)
other_months = [month for month in available_months if month != current_month_key]
period_options = [current_month_key, "all_time"] + other_months

selected_period = st.selectbox(
    "Periode",
    options=period_options,
    format_func=lambda value: "Bulan ini" if value == current_month_key else ("All time" if value == "all_time" else month_label(value)),
)

filtered_records = records if selected_period == "all_time" else records[records["month_key"] == selected_period]
ranking = aggregate_ranking(filtered_records)

period_title = "All time" if selected_period == "all_time" else month_label(selected_period)
st.markdown(f"### {period_title}")

total_players = int(ranking["player_name"].nunique()) if not ranking.empty else 0
total_points = int(ranking["total_points"].sum()) if not ranking.empty else 0
total_matches = int(filtered_records["matches_played"].sum()) if not filtered_records.empty else 0
avg_win_rate = float(ranking["win_rate"].mean()) if not ranking.empty else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Player aktif", total_players)
k2.metric("Total match", total_matches)
k3.metric("Total poin", total_points)
k4.metric("Avg win rate", f"{avg_win_rate:.1f}%")

if ranking.empty:
    st.info("Belum ada data performance untuk periode ini.")
    st.stop()

st.subheader("Community highlights")
top_cols = st.columns(3)
top_labels = ["Most points", "Strong run", "On form"]
for idx, player in enumerate(ranking.head(3).itertuples()):
    with top_cols[idx]:
        st.metric(top_labels[idx], player.player_name, f"{int(player.total_points)} poin")

st.subheader("Ranking")
search_col, page_size_col = st.columns([2, 1])
with search_col:
    search_query = st.text_input("Search nama", placeholder="Cari player...")
with page_size_col:
    page_size = st.selectbox("Rows per page", options=[10, 20, 50], index=0)

table = ranking.copy()
if search_query.strip():
    table = table[table["player_name"].str.contains(search_query.strip(), case=False, na=False)]

if table.empty:
    st.info("Nama player tidak ditemukan di periode ini.")
    st.stop()

total_rows = len(table)
total_pages = max(1, math.ceil(total_rows / page_size))
page_number = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
start = (page_number - 1) * page_size
end = start + page_size

display = table.iloc[start:end][
    [
        "rank",
        "player_name",
        "sessions",
        "total_points",
        "avg_points",
        "win_rate",
    ]
].copy()
display["total_points"] = display["total_points"].round(0).astype(int)
display["avg_points"] = display["avg_points"].round(1)
display["win_rate"] = display["win_rate"].round(1)

st.caption(f"Menampilkan {start + 1}-{min(end, total_rows)} dari {total_rows} player.")
st.dataframe(
    display,
    hide_index=True,
    use_container_width=True,
    column_config={
        "rank": "Rank",
        "player_name": "Nama",
        "sessions": "Sessions",
        "total_points": "Total poin",
        "avg_points": "Avg",
        "win_rate": "Win rate %",
    },
)

with st.expander("Recent performance records"):
    recent = filtered_records.sort_values("session_date_dt", ascending=False).head(20)
    public_columns = ["session_date", "venue", "player_name", "matches_played", "wins", "losses", "points"]
    existing_columns = [column for column in public_columns if column in recent.columns]
    st.dataframe(recent[existing_columns], hide_index=True, use_container_width=True)
