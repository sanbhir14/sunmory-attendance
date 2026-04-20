from __future__ import annotations

from datetime import datetime

import pandas as pd
import requests
import streamlit as st


def secret_value(key: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(key, default))
    except Exception:
        return default


def performance_webhook_url() -> str:
    return secret_value("SESSION_WEBHOOK_URL")


def performance_webhook_token() -> str:
    return secret_value("SESSION_WEBHOOK_TOKEN")


@st.cache_data(ttl=60, show_spinner=False)
def load_open_sessions() -> tuple[pd.DataFrame, str]:
    sessions, message = load_all_sessions()
    if sessions.empty:
        return sessions, "Belum ada session open." if message == "Sessions dari Google Sheets" else message
    open_sessions = sessions[sessions["status"].astype(str).str.lower() == "open"].reset_index(drop=True)
    if open_sessions.empty:
        return open_sessions, "Belum ada session open."
    return open_sessions, "Open sessions dari Google Sheets"


@st.cache_data(ttl=60, show_spinner=False)
def load_all_sessions() -> tuple[pd.DataFrame, str]:
    webhook_url = performance_webhook_url()
    if not webhook_url:
        return pd.DataFrame(), "SESSION_WEBHOOK_URL belum diset."

    try:
        response = requests.get(webhook_url, params={"action": "all_sessions"}, timeout=20)
        response.raise_for_status()
        result = response.json()
    except Exception as exc:
        return pd.DataFrame(), f"Gagal membaca sessions: {exc}"

    if not result.get("ok"):
        return pd.DataFrame(), result.get("error", "Gagal membaca sessions.")

    sessions = pd.DataFrame(result.get("data", []))
    if sessions.empty:
        return sessions, "Belum ada session."

    for column in ["session_id", "session_code", "venue", "session_date", "session_slot", "status"]:
        if column not in sessions.columns:
            sessions[column] = ""
    return sessions, "Sessions dari Google Sheets"


def update_session_status(session_id: str, status: str) -> tuple[bool, str]:
    webhook_url = performance_webhook_url()
    if not webhook_url:
        return False, "SESSION_WEBHOOK_URL belum diset di Streamlit secrets."

    payload = {
        "action": "update_session_status",
        "token": performance_webhook_token(),
        "session_id": session_id,
        "status": status,
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=20)
        response.raise_for_status()
        result = response.json()
    except Exception as exc:
        return False, f"Gagal connect ke Apps Script webhook: {exc}"

    if not result.get("ok"):
        return False, result.get("error", "Gagal update session status.")

    return True, f"Session {session_id} berhasil diubah menjadi {status}."


@st.cache_data(ttl=60, show_spinner=False)
def load_performance_data() -> tuple[pd.DataFrame, pd.DataFrame, str]:
    webhook_url = performance_webhook_url()
    if not webhook_url:
        return pd.DataFrame(), pd.DataFrame(), "SESSION_WEBHOOK_URL belum diset."

    try:
        response = requests.get(webhook_url, params={"action": "performance_summary"}, timeout=20)
        response.raise_for_status()
        result = response.json()
    except Exception as exc:
        return pd.DataFrame(), pd.DataFrame(), f"Gagal membaca performance data: {exc}"

    if not result.get("ok"):
        return pd.DataFrame(), pd.DataFrame(), result.get("error", "Gagal membaca performance data.")

    data = result.get("data", {})
    summary = pd.DataFrame(data.get("summary", []))
    records = pd.DataFrame(data.get("records", []))

    if not summary.empty:
        numeric_columns = ["rank", "total_points", "matches_played", "wins", "losses", "win_rate", "sessions_played"]
        for column in numeric_columns:
            if column in summary.columns:
                summary[column] = pd.to_numeric(summary[column], errors="coerce").fillna(0)
        if "win_rate" in summary.columns:
            summary["win_rate"] = (summary["win_rate"] * 100).round(1)

    return summary, records, "Data performance dari Google Sheets"


def submit_performance_records(records: list[dict]) -> tuple[bool, str]:
    webhook_url = performance_webhook_url()
    if not webhook_url:
        return False, "SESSION_WEBHOOK_URL belum diset di Streamlit secrets."

    payload = {
        "action": "append_performance",
        "token": performance_webhook_token(),
        "records": records,
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=20)
        response.raise_for_status()
        result = response.json()
    except Exception as exc:
        return False, f"Gagal connect ke Apps Script webhook: {exc}"

    if not result.get("ok"):
        return False, result.get("error", "Gagal menulis performance.")

    return True, f"{result.get('inserted', len(records))} performance record berhasil ditulis."


def prepare_performance_records(
    session_id: str,
    session_code: str,
    session_date,
    venue: str,
    rows: pd.DataFrame,
) -> list[dict]:
    records: list[dict] = []
    for row in rows.fillna("").to_dict("records"):
        player_name = str(row.get("player_name", "")).strip()
        if not player_name:
            continue

        matches_played = int(row.get("matches_played") or 0)
        wins = int(row.get("wins") or 0)
        losses = int(row.get("losses") or 0)
        points = int(row.get("points") or 0)

        records.append(
            {
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "session_id": session_id.strip(),
                "session_code": session_code.strip().upper(),
                "session_date": pd.to_datetime(session_date).date().isoformat(),
                "venue": venue.strip(),
                "player_name": player_name,
                "matches_played": matches_played,
                "wins": wins,
                "losses": losses,
                "points": points,
                "notes": str(row.get("notes", "")).strip(),
            }
        )
    return records
