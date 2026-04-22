from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime

import pandas as pd


REQUIRED_COLUMNS = [
    "timestamp",
    "player_name",
    "phone",
    "session_date",
    "venue",
    "session_id",
]

OPTIONAL_COLUMNS = [
    "username_reclub",
    "session_slot",
    "referral_code",
    "referral_code_used",
    "attendance_type",
    "notes",
]

COLUMN_ALIASES = {
    "name": "player_name",
    "nama": "player_name",
    "nama_lengkap": "player_name",
    "nomor_whatsapp": "phone",
    "nomor_hp": "phone",
    "whatsapp": "phone",
    "wa": "phone",
    "created_at": "timestamp",
    "check_in": "timestamp",
    "checkin": "timestamp",
    "date": "session_date",
    "tanggal": "session_date",
    "tanggal_main": "session_date",
    "username": "username_reclub",
    "reclub_username": "username_reclub",
    "session": "session_slot",
    "slot": "session_slot",
    "jam_main": "session_slot",
    "referal_code": "referral_code",
    "kode_referral": "referral_code",
    "kode_referal": "referral_code",
    "catatan": "notes",
}

REWARD_MILESTONES = [
    (3, "10% diskon session"),
    (5, "Free coffee"),
    (8, "20% diskon session"),
    (10, "50% diskon session"),
]


@dataclass(frozen=True)
class DataStatus:
    ok: bool
    message: str
    using_dummy_data: bool = False


def get_dummy_attendance() -> pd.DataFrame:
    """Small realistic dataset so the app stays usable before Sheets is connected."""
    rows = [
        ["2026-04-01 07:01", "Alya Pratama", "081234567801", "2026-04-01", "Bintaro Padel", "SPC-20260401-AM", "AM", "RAKA01", ""],
        ["2026-04-01 07:05", "Raka Wijaya", "081234567802", "2026-04-01", "Bintaro Padel", "SPC-20260401-AM", "AM", "", ""],
        ["2026-04-03 18:12", "Nadia Putri", "081234567803", "2026-04-03", "Kemang Padel", "SPC-20260403-PM", "PM", "ALYA01", ""],
        ["2026-04-05 07:04", "Alya Pratama", "081234567801", "2026-04-05", "Senayan Padel", "SPC-20260405-AM", "AM", "", ""],
        ["2026-04-05 07:08", "Dimas Hadi", "081234567804", "2026-04-05", "Senayan Padel", "SPC-20260405-AM", "AM", "", ""],
        ["2026-04-07 19:01", "Raka Wijaya", "081234567802", "2026-04-07", "Kemang Padel", "SPC-20260407-PM", "PM", "", ""],
        ["2026-04-09 07:00", "Nadia Putri", "081234567803", "2026-04-09", "Bintaro Padel", "SPC-20260409-AM", "AM", "", ""],
        ["2026-04-10 18:45", "Alya Pratama", "081234567801", "2026-04-10", "Kemang Padel", "SPC-20260410-PM", "PM", "", ""],
        ["2026-04-12 07:11", "Raka Wijaya", "081234567802", "2026-04-12", "Senayan Padel", "SPC-20260412-AM", "AM", "", ""],
        ["2026-04-12 07:13", "Tara Kusuma", "081234567805", "2026-04-12", "Senayan Padel", "SPC-20260412-AM", "AM", "NADIA01", ""],
        ["2026-04-14 18:52", "Nadia Putri", "081234567803", "2026-04-14", "Kemang Padel", "SPC-20260414-PM", "PM", "", ""],
        ["2026-04-15 07:03", "Alya Pratama", "081234567801", "2026-04-15", "Bintaro Padel", "SPC-20260415-AM", "AM", "", ""],
        ["2026-04-15 07:06", "Dimas Hadi", "081234567804", "2026-04-15", "Bintaro Padel", "SPC-20260415-AM", "AM", "", ""],
        ["2026-04-17 19:04", "Raka Wijaya", "081234567802", "2026-04-17", "Kemang Padel", "SPC-20260417-PM", "PM", "", ""],
        ["2026-04-18 07:00", "Alya Pratama", "081234567801", "2026-04-18", "Senayan Padel", "SPC-20260418-AM", "AM", "", ""],
        ["2026-04-18 07:09", "Nadia Putri", "081234567803", "2026-04-18", "Senayan Padel", "SPC-20260418-AM", "AM", "", ""],
    ]
    return pd.DataFrame(rows, columns=REQUIRED_COLUMNS + OPTIONAL_COLUMNS)


def ensure_required_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [
        re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", str(col).strip().lower())).strip("_")
        for col in df.columns
    ]
    df = df.rename(columns={source: target for source, target in COLUMN_ALIASES.items() if source in df.columns})
    for column in REQUIRED_COLUMNS + OPTIONAL_COLUMNS:
        if column not in df.columns:
            df[column] = ""
    return df[REQUIRED_COLUMNS + OPTIONAL_COLUMNS]


def normalize_name(name: object) -> str:
    cleaned = re.sub(r"\s+", " ", str(name or "").strip())
    return cleaned.title()


def normalize_phone(phone: object) -> str:
    digits = re.sub(r"\D+", "", str(phone or ""))
    if digits.startswith("0"):
        return "62" + digits[1:]
    if digits.startswith("8"):
        return "62" + digits
    return digits


def normalize_referral_code(code: object) -> str:
    cleaned = str(code or "").strip().upper()
    if cleaned in {"", "-", "NO", "NONE", "N/A", "NA", "TIDAK", "GA", "GAK"}:
        return ""
    return cleaned


def normalize_username(username: object) -> str:
    return str(username or "").strip().lstrip("@").lower()


def make_player_id(name: str, phone: str, username: str = "") -> str:
    username = normalize_username(username)
    if username:
        base = f"reclub::{username}"
    else:
        base = f"{normalize_name(name).lower()}::{normalize_phone(phone)}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:12]


def reward_state(total_stamp: int) -> dict:
    achieved = [reward for stamp, reward in REWARD_MILESTONES if total_stamp >= stamp]
    next_item = next(((stamp, reward) for stamp, reward in REWARD_MILESTONES if total_stamp < stamp), None)

    if next_item is None:
        last_milestone = REWARD_MILESTONES[-1][0]
        return {
            "achieved_rewards": achieved,
            "achieved_count": len(achieved),
            "next_milestone": last_milestone,
            "next_reward": "Semua reward utama sudah tercapai",
            "stamps_remaining": 0,
            "progress": 1.0,
        }

    next_stamp, next_reward = next_item
    previous_stamp = max([stamp for stamp, _ in REWARD_MILESTONES if stamp < next_stamp], default=0)
    progress = (total_stamp - previous_stamp) / max(next_stamp - previous_stamp, 1)
    return {
        "achieved_rewards": achieved,
        "achieved_count": len(achieved),
        "next_milestone": next_stamp,
        "next_reward": next_reward,
        "stamps_remaining": max(next_stamp - total_stamp, 0),
        "progress": min(max(progress, 0.0), 1.0),
    }


def clean_attendance(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = ensure_required_columns(raw_df)
    if df.empty:
        return df

    df["player_name"] = df["player_name"].map(normalize_name)
    df["username_reclub"] = df["username_reclub"].map(normalize_username)
    df.loc[df["player_name"].eq("") & df["username_reclub"].ne(""), "player_name"] = df["username_reclub"]
    df["phone"] = df["phone"].map(normalize_phone)
    df["venue"] = df["venue"].fillna("").astype(str).str.strip().replace("", "Unknown venue")
    df["session_slot"] = df["session_slot"].fillna("").astype(str).str.strip()
    df["referral_code"] = df["referral_code"].map(normalize_referral_code)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["session_date"] = pd.to_datetime(df["session_date"], errors="coerce")
    df["session_id"] = df["session_id"].fillna("").astype(str).str.strip()
    generated_session_id = (
        df["session_date"].dt.strftime("%Y%m%d").fillna("unknown")
        + "-"
        + df["venue"].str.lower().str.replace(r"[^a-z0-9]+", "-", regex=True).str.strip("-")
        + "-"
        + df["session_slot"].replace("", "session").str.lower().str.replace(r"[^a-z0-9]+", "-", regex=True).str.strip("-")
    )
    df.loc[df["session_id"].eq(""), "session_id"] = generated_session_id[df["session_id"].eq("")]
    df["player_id"] = df.apply(lambda row: make_player_id(row["player_name"], row["phone"], row["username_reclub"]), axis=1)

    with_session_id = df[df["session_id"].ne("")].drop_duplicates(["player_id", "session_id"])
    without_session_id = df[df["session_id"].eq("")].drop_duplicates(["player_id", "session_date", "venue"])
    cleaned = pd.concat([with_session_id, without_session_id], ignore_index=True)
    cleaned = cleaned.dropna(subset=["session_date"])
    return cleaned.sort_values(["session_date", "timestamp"], ascending=[False, False]).reset_index(drop=True)


def current_month_mask(df: pd.DataFrame, today: datetime | None = None) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=bool)
    today = today or datetime.now()
    dates = pd.to_datetime(df["session_date"], errors="coerce")
    return (dates.dt.year == today.year) & (dates.dt.month == today.month)


def build_player_summary(df: pd.DataFrame, today: datetime | None = None) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=[
                "player_id",
                "player_name",
                "username_reclub",
                "phone",
                "total_session",
                "total_stamp",
                "last_played",
                "sessions_this_month",
                "venue_count",
                "venues",
                "achieved_count",
                "next_reward",
                "stamps_remaining",
                "progress",
            ]
        )

    month_df = df[current_month_mask(df, today)]
    month_counts = month_df.groupby("player_id").size().rename("sessions_this_month")

    summary = (
        df.groupby("player_id")
        .agg(
            player_name=("player_name", "first"),
            username_reclub=("username_reclub", "first"),
            phone=("phone", "first"),
            total_session=("session_id", "size"),
            total_stamp=("session_id", "size"),
            last_played=("session_date", "max"),
            venue_count=("venue", "nunique"),
            venues=("venue", lambda values: ", ".join(sorted(set(values)))),
        )
        .join(month_counts, how="left")
        .fillna({"sessions_this_month": 0})
        .reset_index()
    )
    summary["sessions_this_month"] = summary["sessions_this_month"].astype(int)

    rewards = summary["total_stamp"].map(reward_state).apply(pd.Series)
    summary = pd.concat([summary, rewards], axis=1)
    return summary.sort_values(["total_stamp", "last_played"], ascending=[False, False]).reset_index(drop=True)


def filter_attendance(df: pd.DataFrame, period: str = "All time", venue: str = "All venues") -> pd.DataFrame:
    filtered = df.copy()
    if period == "Bulan ini":
        filtered = filtered[current_month_mask(filtered)]
    if venue != "All venues":
        filtered = filtered[filtered["venue"] == venue]
    return filtered


def build_leaderboard(df: pd.DataFrame, period: str = "All time", venue: str = "All venues") -> pd.DataFrame:
    filtered = filter_attendance(df, period, venue)
    leaderboard = build_player_summary(filtered)
    if leaderboard.empty:
        return leaderboard
    leaderboard = leaderboard[["player_name", "username_reclub", "phone", "total_session", "total_stamp", "last_played"]].copy()
    leaderboard.insert(0, "rank", range(1, len(leaderboard) + 1))
    return leaderboard


def dashboard_metrics(df: pd.DataFrame, summary: pd.DataFrame) -> dict:
    total_attendance = len(df)
    total_players = summary["player_id"].nunique() if not summary.empty else 0
    repeat_players = int((summary["total_session"] > 1).sum()) if not summary.empty else 0
    busiest_venue = "Belum ada data"
    if not df.empty:
        venue_counts = df["venue"].value_counts()
        busiest_venue = str(venue_counts.index[0]) if not venue_counts.empty else "Belum ada data"
    total_rewards = int(summary["achieved_count"].sum()) if not summary.empty and "achieved_count" in summary else 0
    return {
        "total_players": total_players,
        "total_attendance": total_attendance,
        "repeat_players": repeat_players,
        "busiest_venue": busiest_venue,
        "total_rewards": total_rewards,
    }


def attendance_trend(df: pd.DataFrame, frequency: str = "D") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["session_date", "attendance"])
    trend = (
        df.set_index("session_date")
        .resample(frequency)
        .size()
        .rename("attendance")
        .reset_index()
    )
    return trend[trend["attendance"] > 0]


def monthly_attendance(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["month", "attendance"])
    out = df.copy()
    out["month"] = out["session_date"].dt.to_period("M").astype(str)
    return out.groupby("month").size().rename("attendance").reset_index()


def repeat_vs_new(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame({"type": ["New player", "Repeat player"], "count": [0, 0]})
    first_play = df.groupby("player_id")["session_date"].transform("min")
    out = df.copy()
    out["type"] = ["New player" if row.session_date == first else "Repeat player" for row, first in zip(out.itertuples(), first_play)]
    return out["type"].value_counts().rename_axis("type").reset_index(name="count")


def players_near_reward(summary: pd.DataFrame, limit: int = 8) -> pd.DataFrame:
    if summary.empty:
        return summary
    near = summary[(summary["stamps_remaining"] > 0) & (summary["stamps_remaining"] <= 2)].copy()
    return near.sort_values(["stamps_remaining", "total_stamp"], ascending=[True, False]).head(limit)


def find_player(summary: pd.DataFrame, query: str) -> pd.DataFrame:
    query = str(query or "").strip().lower()
    if not query or summary.empty:
        return pd.DataFrame()
    phone_query = normalize_phone(query)
    name_pattern = rf"(?:^|\s){re.escape(query)}"
    name_matches = summary["player_name"].str.lower().str.contains(name_pattern, na=False, regex=True)
    username_matches = pd.Series(False, index=summary.index)
    if "username_reclub" in summary.columns:
        username_query = normalize_username(query)
        username_matches = summary["username_reclub"].str.lower().str.contains(username_query, na=False) if username_query else username_matches
    if not phone_query:
        return summary[name_matches | username_matches]
    phone_matches = summary["phone"].str.contains(phone_query, na=False)
    return summary[name_matches | username_matches | phone_matches]
