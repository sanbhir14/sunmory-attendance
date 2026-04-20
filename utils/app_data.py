from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.data_processing import build_player_summary, clean_attendance, get_dummy_attendance
from utils.google_sheets import GoogleSheetsConfigError, load_attendance_from_google_sheet


@st.cache_data(ttl=60, show_spinner=False)
def load_app_data() -> tuple[pd.DataFrame, pd.DataFrame, str]:
    try:
        raw_df = load_attendance_from_google_sheet("attendance")
        source_message = "Data dari Google Sheets"
        if raw_df.empty:
            raw_df = get_dummy_attendance()
            source_message = "Google Sheets kosong, menampilkan dummy data"
    except GoogleSheetsConfigError as exc:
        raw_df = get_dummy_attendance()
        source_message = f"Setup belum lengkap: {exc} Menampilkan dummy data."
    except Exception as exc:
        raw_df = get_dummy_attendance()
        source_message = f"Gagal membaca Google Sheets: {exc}. Menampilkan dummy data."

    attendance = clean_attendance(raw_df)
    summary = build_player_summary(attendance)
    return attendance, summary, source_message
