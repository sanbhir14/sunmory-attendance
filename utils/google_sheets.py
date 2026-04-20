from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import quote

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

from utils.data_processing import REQUIRED_COLUMNS


SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


class GoogleSheetsConfigError(RuntimeError):
    pass


def _secret_value(key: str, default: Any = None) -> Any:
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


def _get_service_account_info() -> dict:
    inline_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON") or _secret_value("GOOGLE_SERVICE_ACCOUNT_JSON")
    if inline_json:
        try:
            return json.loads(inline_json)
        except json.JSONDecodeError as exc:
            raise GoogleSheetsConfigError("GOOGLE_SERVICE_ACCOUNT_JSON tidak valid.") from exc

    account_info = _secret_value("gcp_service_account")
    if account_info:
        return dict(account_info)

    raise GoogleSheetsConfigError("Credentials service account belum diset di Streamlit secrets.")


def _has_service_account_info() -> bool:
    return bool(
        os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        or _secret_value("GOOGLE_SERVICE_ACCOUNT_JSON")
        or _secret_value("gcp_service_account")
    )


def _get_sheet_id() -> str:
    sheet_id = os.getenv("GOOGLE_SHEET_ID") or _secret_value("GOOGLE_SHEET_ID")
    if not sheet_id:
        raise GoogleSheetsConfigError("GOOGLE_SHEET_ID atau GOOGLE_SHEET_CSV_URL belum diset.")
    return str(sheet_id)


def _get_public_csv_url() -> str | None:
    direct_url = os.getenv("GOOGLE_SHEET_CSV_URL") or _secret_value("GOOGLE_SHEET_CSV_URL")
    if direct_url:
        return str(direct_url)

    sheet_id = os.getenv("GOOGLE_SHEET_ID") or _secret_value("GOOGLE_SHEET_ID")
    if not sheet_id:
        return None

    gid = os.getenv("GOOGLE_SHEET_GID") or _secret_value("GOOGLE_SHEET_GID", "0")
    return f"https://docs.google.com/spreadsheets/d/{quote(str(sheet_id))}/export?format=csv&gid={quote(str(gid))}"


def _load_public_csv() -> pd.DataFrame:
    csv_url = _get_public_csv_url()
    if not csv_url:
        raise GoogleSheetsConfigError("Public CSV Google Sheet belum diset.")

    try:
        df = pd.read_csv(csv_url)
    except Exception as exc:
        raise GoogleSheetsConfigError(
            "Gagal membaca public CSV. Pastikan Google Sheet bisa diakses oleh anyone with the link atau sudah dipublish."
        ) from exc

    if df.empty:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    return df


def _load_with_service_account(worksheet_name: str) -> pd.DataFrame:
    service_account_info = _get_service_account_info()
    sheet_id = _get_sheet_id()

    credentials = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    client = gspread.authorize(credentials)
    worksheet = client.open_by_key(sheet_id).worksheet(worksheet_name)
    records = worksheet.get_all_records()

    if not records:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    return pd.DataFrame(records)


@st.cache_data(ttl=60, show_spinner=False)
def load_attendance_from_google_sheet(worksheet_name: str = "attendance") -> pd.DataFrame:
    if not _get_public_csv_url():
        if _has_service_account_info():
            return _load_with_service_account(worksheet_name)
        raise GoogleSheetsConfigError("GOOGLE_SHEET_ID atau GOOGLE_SHEET_CSV_URL belum diset.")

    try:
        return _load_public_csv()
    except GoogleSheetsConfigError:
        if _has_service_account_info():
            return _load_with_service_account(worksheet_name)
        raise
