from __future__ import annotations

import re
import secrets
import string
from datetime import date, datetime


def slugify(value: object) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower())
    return cleaned.strip("-") or "session"


def generate_session_code(length: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    confusing_chars = {"0", "O", "1", "I", "L"}
    safe_alphabet = "".join(char for char in alphabet if char not in confusing_chars)
    return "".join(secrets.choice(safe_alphabet) for _ in range(length))


def make_session_id(session_date: date, venue: str, session_slot: str = "") -> str:
    date_part = session_date.strftime("%Y%m%d")
    venue_part = slugify(venue)
    slot_part = slugify(session_slot) if session_slot else "session"
    return f"SPC-{date_part}-{venue_part}-{slot_part}".upper()


def build_session_record(
    session_date: date,
    venue: str,
    session_slot: str,
    session_code: str,
    expense_amount: int,
    player_price: int,
    paid_by: str,
    status: str = "open",
) -> dict:
    return {
        "session_id": make_session_id(session_date, venue, session_slot),
        "session_code": session_code.strip().upper(),
        "venue": venue.strip(),
        "session_date": session_date.isoformat(),
        "session_slot": session_slot.strip() or "Session",
        "status": status,
        "expense_amount": int(expense_amount or 0),
        "player_price": int(player_price or 0),
        "paid_by": paid_by.strip(),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def session_record_to_csv(record: dict) -> str:
    header = "session_id,session_code,venue,session_date,session_slot,status,expense_amount,player_price,paid_by,created_at"
    row = ",".join(str(record[key]) for key in header.split(","))
    return f"{header}\n{row}\n"
