from __future__ import annotations

import pandas as pd
import requests
import streamlit as st

from utils.performance import performance_webhook_token, performance_webhook_url


@st.cache_data(ttl=60, show_spinner=False)
def load_attendance_records() -> tuple[pd.DataFrame, str]:
    webhook_url = performance_webhook_url()
    if not webhook_url:
        return pd.DataFrame(), "SESSION_WEBHOOK_URL belum diset."

    try:
        response = requests.get(webhook_url, params={"action": "attendance_records"}, timeout=20)
        response.raise_for_status()
        result = response.json()
    except Exception as exc:
        return pd.DataFrame(), f"Gagal membaca attendance_log: {exc}"

    if not result.get("ok"):
        return pd.DataFrame(), result.get("error", "Gagal membaca attendance_log.")

    records = pd.DataFrame(result.get("data", []))
    if records.empty:
        return records, "Belum ada attendance_log."
    return records, "Data attendance dari attendance_log"


@st.cache_data(ttl=60, show_spinner=False)
def load_players_db() -> tuple[pd.DataFrame, str]:
    webhook_url = performance_webhook_url()
    if not webhook_url:
        return pd.DataFrame(), "SESSION_WEBHOOK_URL belum diset."

    try:
        response = requests.get(webhook_url, params={"action": "players_db"}, timeout=20)
        response.raise_for_status()
        result = response.json()
    except Exception as exc:
        return pd.DataFrame(), f"Gagal membaca players_db: {exc}"

    if not result.get("ok"):
        return pd.DataFrame(), result.get("error", "Gagal membaca players_db.")

    players = pd.DataFrame(result.get("data", []))
    if players.empty:
        return players, "Belum ada players_db."
    return players, "Data players_db dari Google Sheets"


def submit_attendance(record: dict) -> tuple[bool, str]:
    webhook_url = performance_webhook_url()
    if not webhook_url:
        return False, "SESSION_WEBHOOK_URL belum diset di Streamlit secrets."

    payload = {
        "action": "append_attendance",
        "token": performance_webhook_token(),
        "attendance": record,
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=20)
        response.raise_for_status()
        result = response.json()
    except Exception as exc:
        return False, f"Gagal connect ke Apps Script webhook: {exc}"

    if not result.get("ok"):
        return False, result.get("error", "Gagal menulis attendance.")

    player_name = result.get("player_name") or record.get("player_name") or record.get("username_reclub")
    referral_status = result.get("referral_status")
    suffix = f" Referral: {referral_status}." if referral_status else ""
    return True, f"Attendance {player_name} berhasil ditulis.{suffix}"


def rebuild_players_db() -> tuple[bool, str]:
    webhook_url = performance_webhook_url()
    if not webhook_url:
        return False, "SESSION_WEBHOOK_URL belum diset di Streamlit secrets."

    payload = {
        "action": "rebuild_players_db",
        "token": performance_webhook_token(),
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
    except Exception as exc:
        return False, f"Gagal rebuild players_db: {exc}"

    if not result.get("ok"):
        return False, result.get("error", "Gagal rebuild players_db.")

    return True, "players_db berhasil disinkron ulang dari attendance_log."
