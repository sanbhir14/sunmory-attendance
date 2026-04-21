from __future__ import annotations

import streamlit as st
import pandas as pd

from utils.attendance import load_players_db, rebuild_players_db
from utils.auth import require_admin
from utils.ui import dataframe_dates


require_admin()

st.title("Player Database")
st.caption("Cari player, referral code, total attendance, reward, dan status referral.")

players, message = load_players_db()
if message != "Data players_db dari Google Sheets":
    st.info(message)

if players.empty:
    st.warning("Belum ada players_db. Submit attendance pertama dulu atau jalankan proses di Apps Script.")
    st.stop()

for column in [
    "total_attendance",
    "total_stamp",
    "valid_referral_count",
    "referral_bonus_attendance",
    "stamps_remaining",
]:
    if column in players.columns:
        players[column] = pd.to_numeric(players[column], errors="coerce").fillna(0).astype(int)

if {"total_attendance", "total_stamp"}.issubset(players.columns):
    players["total_attendance"] = players[["total_attendance", "total_stamp"]].max(axis=1)

if st.button("Sync players_db dari attendance_log", use_container_width=True):
    ok, sync_message = rebuild_players_db()
    if ok:
        st.success(sync_message)
        st.cache_data.clear()
        st.rerun()
    else:
        st.error(sync_message)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total player", len(players))
k2.metric("Total attendance", int(players.get("total_attendance", pd.Series(dtype=int)).sum()))
k3.metric("Referral valid", int(players.get("valid_referral_count", pd.Series(dtype=int)).sum()))
k4.metric("Bonus referral", int(players.get("referral_bonus_attendance", pd.Series(dtype=int)).sum()))

query = st.text_input("Search username atau nama", placeholder="contoh: sandi atau @sandibh")
filtered = players.copy()
if query.strip():
    needle = query.strip().lstrip("@").lower()
    name_matches = filtered.get("player_name", pd.Series("", index=filtered.index)).astype(str).str.lower().str.contains(needle, na=False)
    username_matches = filtered.get("username_reclub", pd.Series("", index=filtered.index)).astype(str).str.lower().str.contains(needle, na=False)
    filtered = filtered[name_matches | username_matches]

if filtered.empty:
    st.info("Player tidak ditemukan.")
    st.stop()

display_columns = [
    "username_reclub",
    "player_name",
    "referral_code",
    "total_attendance",
    "total_stamp",
    "valid_referral_count",
    "referral_bonus_attendance",
    "referral_used_code",
    "next_reward",
    "stamps_remaining",
    "last_played",
]
existing_columns = [column for column in display_columns if column in filtered.columns]

st.dataframe(
    dataframe_dates(filtered[existing_columns], ["last_played"]),
    hide_index=True,
    use_container_width=True,
    column_config={
        "username_reclub": "Username Reclub",
        "player_name": "Nama",
        "referral_code": "Referral code",
        "total_attendance": "Attendance",
        "total_stamp": "Stamp",
        "valid_referral_count": "Referral valid",
        "referral_bonus_attendance": "Bonus attendance",
        "referral_used_code": "Referral dipakai",
        "next_reward": "Reward berikutnya",
        "stamps_remaining": "Sisa stamp",
        "last_played": "Last played",
    },
)
