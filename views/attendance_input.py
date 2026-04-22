from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.attendance import (
    eligible_reward_options,
    load_attendance_records,
    load_players_db,
    reward_discount_percent,
    submit_attendance,
)
from utils.auth import require_admin
from utils.performance import load_open_sessions


require_admin()

st.title("Attendance Input")
st.caption("Input check-in player langsung dari Streamlit ke tab `attendance_log`.")

sessions, sessions_message = load_open_sessions()
players, players_message = load_players_db()
attendance, attendance_message = load_attendance_records()

if sessions_message != "Open sessions dari Google Sheets":
    st.info(sessions_message)
if players_message not in {"Data players_db dari Google Sheets", "Belum ada players_db."}:
    st.info(players_message)
if attendance_message not in {"Data attendance dari attendance_log", "Belum ada attendance_log."}:
    st.info(attendance_message)

if sessions.empty:
    st.warning("Tidak ada session open. Generate session dulu dari Session Generator.")
    st.stop()

sessions = sessions.reset_index(drop=True)
sessions["label"] = (
    sessions["session_date"].astype(str)
    + " - "
    + sessions["venue"].astype(str)
    + " - "
    + sessions["session_slot"].astype(str)
    + " ("
    + sessions["session_code"].astype(str)
    + ")"
)

selected_session_label = st.selectbox("Pilih open session", sessions["label"].tolist())
selected_session = sessions[sessions["label"] == selected_session_label].iloc[0]
selected_session_id = str(selected_session["session_id"])

checked_in_usernames: set[str] = set()
if not attendance.empty and {"session_id", "username_reclub"}.issubset(attendance.columns):
    session_attendance = attendance[
        attendance["session_id"].astype(str).str.strip().eq(selected_session_id)
    ].copy()
    if "attendance_type" in session_attendance.columns:
        session_attendance = session_attendance[
            session_attendance["attendance_type"].astype(str).str.lower().ne("referral_bonus")
        ]
    checked_in_usernames = {
        str(username).strip().lstrip("@").lower()
        for username in session_attendance["username_reclub"].fillna("")
        if str(username).strip()
    }

col1, col2, col3 = st.columns(3)
col1.text_input("Session Code", value=str(selected_session["session_code"]), disabled=True)
col2.text_input("Tanggal", value=str(selected_session["session_date"]), disabled=True)
col3.text_input("Venue", value=str(selected_session["venue"]), disabled=True)
if checked_in_usernames:
    st.caption(f"{len(checked_in_usernames)} player sudah check-in di session ini.")

base_price = int(float(selected_session.get("player_price", 0) or 0))
expense_amount = int(float(selected_session.get("expense_amount", 0) or 0))
paid_by = str(selected_session.get("paid_by", "") or "")
money1, money2, money3 = st.columns(3)
money1.metric("Harga/player", f"Rp {base_price:,}")
money2.metric("Expense venue", f"Rp {expense_amount:,}")
money3.metric("Paid by", paid_by or "-")

player_options = ["Tambah player baru"]
player_lookup = {}
if not players.empty:
    for row in players.fillna("").to_dict("records"):
        username = str(row.get("username_reclub", "")).strip().lstrip("@").lower()
        if username in checked_in_usernames:
            continue
        name = str(row.get("player_name") or row.get("name") or "").strip()
        label = f"@{username} - {name}" if username and name else (f"@{username}" if username else name)
        if label:
            player_options.append(label)
            player_lookup[label] = row

selected_player_label = st.selectbox("Username Reclub", player_options)
selected_player = player_lookup.get(selected_player_label, {})

with st.form("attendance_input_form"):
    if selected_player:
        username_reclub = str(selected_player.get("username_reclub", "")).strip().lstrip("@").lower()
        player_name = str(selected_player.get("player_name") or selected_player.get("name") or "").strip()
        st.text_input("Username Reclub", value=f"@{username_reclub}" if username_reclub else "", disabled=True)
        st.text_input("Name (optional)", value=player_name, disabled=True)
        st.caption("Player existing dipilih dari players_db.")
        referral_code = ""
        st.text_input("Referral code", value="Referral hanya untuk player baru", disabled=True)
    else:
        username_reclub = st.text_input("Username Reclub", placeholder="contoh: sandibh")
        player_name = st.text_input("Name (optional)", placeholder="Nama player kalau ada")
        referral_code = st.text_input("Referral code", placeholder="Kosongkan kalau tidak pakai referral").upper()

    reward_options = eligible_reward_options(selected_player) if selected_player else ["Tidak claim reward"]
    claimed_reward = st.selectbox("Claim reward", reward_options)
    discount_percent = reward_discount_percent(claimed_reward)
    discount_amount = 20_000 if claimed_reward == "Free coffee" else 0
    income_amount = max(int(round(base_price * (100 - discount_percent) / 100)) - discount_amount, 0)
    if claimed_reward == "Free coffee":
        st.info("Free coffee memotong Rp 20,000 dari harga session player ini.")
    discount_label = f"-{discount_percent}% discount" if discount_percent else (f"-Rp {discount_amount:,}" if discount_amount else None)
    st.metric("Income player ini", f"Rp {income_amount:,}", discount_label)

    notes = st.text_input("Notes", placeholder="Optional")

    submitted = st.form_submit_button("Submit Attendance", use_container_width=True)

if submitted:
    username_reclub = username_reclub.strip().lstrip("@").lower()
    player_name = player_name.strip()

    if not username_reclub:
        st.error("Username Reclub wajib diisi.")
        st.stop()
    if username_reclub in checked_in_usernames:
        st.error(f"@{username_reclub} sudah check-in di session ini.")
        st.stop()

    record = {
        "session_id": selected_session_id,
        "session_code": str(selected_session["session_code"]),
        "session_date": str(selected_session["session_date"]),
        "session_slot": str(selected_session.get("session_slot", "")),
        "venue": str(selected_session["venue"]),
        "player_name": player_name,
        "username_reclub": username_reclub,
        "referral_code": referral_code.strip(),
        "base_price": base_price,
        "claimed_reward": "" if claimed_reward == "Tidak claim reward" else claimed_reward,
        "discount_percent": discount_percent,
        "income_amount": income_amount,
        "notes": notes.strip(),
    }

    ok, message = submit_attendance(record)
    if ok:
        st.success(message)
        st.cache_data.clear()
    else:
        st.error(message)
