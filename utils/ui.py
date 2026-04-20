from __future__ import annotations

import pandas as pd
import streamlit as st


def apply_theme() -> None:
    st.set_page_config(
        page_title="Sunmory Padel Club",
        page_icon=":tennis:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        :root {
            --sunmory-ink: #14213d;
            --sunmory-muted: #5d6979;
            --sunmory-line: #e6e8ec;
            --sunmory-card: #ffffff;
            --sunmory-soft: #fffaf0;
            --sunmory-green: #1b8a5a;
            --sunmory-yellow: #f2c94c;
            --sunmory-shadow: rgba(20, 33, 61, 0.05);
        }
        @media (prefers-color-scheme: dark) {
            :root {
                --sunmory-ink: #f5f7fb;
                --sunmory-muted: #b7c0ce;
                --sunmory-line: #343b49;
                --sunmory-card: #171c26;
                --sunmory-soft: #251f11;
                --sunmory-shadow: rgba(0, 0, 0, 0.18);
            }
        }
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1180px;
        }
        h1, h2, h3 {
            letter-spacing: 0;
            color: var(--sunmory-ink);
        }
        p, label, span {
            letter-spacing: 0;
        }
        div[data-testid="stMetric"] {
            background: var(--sunmory-card);
            border: 1px solid var(--sunmory-line);
            border-radius: 8px;
            padding: 14px 16px;
            box-shadow: 0 8px 20px var(--sunmory-shadow);
        }
        div[data-testid="stMetricLabel"] p,
        div[data-testid="stMetricLabel"] {
            color: var(--sunmory-muted);
        }
        div[data-testid="stMetricValue"],
        div[data-testid="stMetricValue"] div {
            color: var(--sunmory-ink);
        }
        div[data-testid="stMetricDelta"] {
            color: var(--sunmory-muted);
        }
        .sunmory-panel {
            background: var(--sunmory-card);
            border: 1px solid var(--sunmory-line);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
            color: var(--sunmory-ink);
        }
        .top-player {
            border-left: 4px solid var(--sunmory-yellow);
            padding: 10px 12px;
            background: var(--sunmory-soft);
            border-radius: 8px;
            margin-bottom: 8px;
            color: var(--sunmory-ink);
        }
        .muted {
            color: var(--sunmory-muted);
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--sunmory-line);
            border-radius: 8px;
            overflow: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_date(value) -> str:
    if pd.isna(value):
        return "-"
    return pd.to_datetime(value).strftime("%d %b %Y")


def show_empty_state(message: str = "Belum ada data attendance.") -> None:
    st.info(message)


def dataframe_dates(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy()
    for column in columns:
        if column in out.columns:
            out[column] = pd.to_datetime(out[column], errors="coerce").dt.strftime("%d %b %Y")
    return out


def rank_label(rank: int) -> str:
    if rank == 1:
        return "Gold"
    if rank == 2:
        return "Silver"
    if rank == 3:
        return "Bronze"
    return str(rank)
