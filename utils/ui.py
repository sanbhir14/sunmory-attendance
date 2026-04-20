from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


LOGO_PATH = Path("assets/logo.png")


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
            --sunmory-ink: #13201e;
            --sunmory-muted: #62716d;
            --sunmory-line: #e7dfcf;
            --sunmory-card: #ffffff;
            --sunmory-soft: #fff7df;
            --sunmory-bg: #f8f4e8;
            --sunmory-teal: #0f4c4c;
            --sunmory-green: #2e7d59;
            --sunmory-amber: #f59e0b;
            --sunmory-gold: #f2c94c;
            --sunmory-coral: #e85d04;
            --sunmory-shadow: rgba(36, 27, 12, 0.08);
        }
        @media (prefers-color-scheme: dark) {
            :root {
                --sunmory-ink: #f9f4e7;
                --sunmory-muted: #c8d0c7;
                --sunmory-line: #31413b;
                --sunmory-card: #121a18;
                --sunmory-soft: #221c10;
                --sunmory-bg: #090f0e;
                --sunmory-shadow: rgba(0, 0, 0, 0.18);
            }
        }
        html, body, [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at top left, rgba(245, 158, 11, 0.12), transparent 32rem),
                linear-gradient(180deg, var(--sunmory-bg), var(--sunmory-bg));
        }
        [data-testid="stSidebar"] {
            border-right: 1px solid var(--sunmory-line);
            background: #fbf7ec;
        }
        [data-testid="stSidebar"] * {
            color: #13201e;
        }
        [data-testid="stSidebarNav"] {
            color: #13201e;
        }
        [data-testid="stSidebarNav"] ul {
            padding-left: 0;
        }
        [data-testid="stSidebarNav"] a {
            border-radius: 8px;
            margin: 4px 0;
            padding: 8px 10px;
            color: #13201e;
            font-weight: 700;
            opacity: 1;
        }
        [data-testid="stSidebarNav"] a span,
        [data-testid="stSidebarNav"] a p,
        [data-testid="stSidebarNav"] div,
        [data-testid="stSidebarNav"] li,
        [data-testid="stSidebarNav"] [data-testid="stMarkdownContainer"] p {
            color: #13201e;
            opacity: 1;
        }
        [data-testid="stSidebarNav"] [role="heading"],
        [data-testid="stSidebarNav"] [data-testid="stNavSectionHeader"] {
            color: #0f4c4c;
            font-weight: 800;
            opacity: 1;
        }
        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: #fff1c7;
            color: #13201e;
            font-weight: 700;
        }
        .main .block-container {
            padding-top: 2.25rem;
            padding-bottom: 3rem;
            max-width: 1180px;
        }
        h1, h2, h3 {
            letter-spacing: 0;
            color: var(--sunmory-ink);
        }
        h1 {
            font-size: clamp(2.1rem, 5vw, 3.4rem);
            line-height: 1.05;
        }
        h2 {
            margin-top: 1.6rem;
        }
        p, label, span {
            letter-spacing: 0;
        }
        .sunmory-brand {
            border: 1px solid #eadfca;
            border-radius: 8px;
            padding: 12px;
            background: #ffffff;
            box-shadow: 0 8px 18px rgba(36, 27, 12, 0.08);
            margin-bottom: 12px;
        }
        .sunmory-brand-title {
            color: #13201e;
            font-weight: 800;
            letter-spacing: 0;
            margin: 0;
        }
        .sunmory-brand-subtitle {
            color: #5d6b65;
            font-size: 0.82rem;
            margin-top: 2px;
        }
        .sunmory-header {
            border: 1px solid var(--sunmory-line);
            border-radius: 8px;
            padding: 22px 24px;
            margin-bottom: 18px;
            background:
                linear-gradient(135deg, rgba(15, 76, 76, 0.10), rgba(245, 158, 11, 0.10)),
                var(--sunmory-card);
            box-shadow: 0 12px 30px var(--sunmory-shadow);
        }
        .sunmory-eyebrow {
            color: var(--sunmory-amber);
            font-weight: 800;
            text-transform: uppercase;
            font-size: 0.76rem;
            letter-spacing: 0.08em;
            margin-bottom: 8px;
        }
        .sunmory-title {
            color: var(--sunmory-ink);
            font-size: clamp(2rem, 5vw, 3.2rem);
            font-weight: 850;
            line-height: 1.05;
            margin: 0;
        }
        .sunmory-caption {
            color: var(--sunmory-muted);
            margin-top: 10px;
            max-width: 780px;
        }
        div[data-testid="stMetric"] {
            background: var(--sunmory-card);
            border: 1px solid var(--sunmory-line);
            border-radius: 8px;
            padding: 16px 18px;
            box-shadow: 0 10px 24px var(--sunmory-shadow);
            position: relative;
            overflow: hidden;
        }
        div[data-testid="stMetric"]::before {
            content: "";
            position: absolute;
            inset: 0 0 auto 0;
            height: 4px;
            background: linear-gradient(90deg, var(--sunmory-teal), var(--sunmory-amber));
        }
        div[data-testid="stMetricLabel"] p,
        div[data-testid="stMetricLabel"] {
            color: var(--sunmory-muted);
            font-weight: 700;
        }
        div[data-testid="stMetricValue"],
        div[data-testid="stMetricValue"] div {
            color: var(--sunmory-ink);
            font-weight: 850;
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
            border-left: 4px solid var(--sunmory-amber);
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
        .stButton > button,
        [data-testid="stDownloadButton"] button {
            border-radius: 8px;
            border: 1px solid var(--sunmory-line);
            background: linear-gradient(135deg, var(--sunmory-teal), var(--sunmory-green));
            color: #ffffff;
            font-weight: 800;
        }
        .stButton > button:hover,
        [data-testid="stDownloadButton"] button:hover {
            border-color: var(--sunmory-amber);
            color: #ffffff;
        }
        [data-testid="stSidebar"] .stButton > button,
        [data-testid="stSidebar"] .stButton > button p,
        [data-testid="stSidebar"] .stButton > button span {
            color: #ffffff;
        }
        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div {
            border-radius: 8px;
            border-color: var(--sunmory-line);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def has_logo() -> bool:
    return LOGO_PATH.exists()


def render_sidebar_brand() -> None:
    if has_logo():
        st.image(str(LOGO_PATH), use_container_width=True)
    st.markdown(
        """
        <div class="sunmory-brand">
            <p class="sunmory-brand-title">Sunmory Padel Club</p>
            <div class="sunmory-brand-subtitle">Attendance • Stamp • Reward</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, caption: str, eyebrow: str = "Sunmory Padel Club") -> None:
    st.markdown(
        f"""
        <div class="sunmory-header">
            <div class="sunmory-eyebrow">{eyebrow}</div>
            <div class="sunmory-title">{title}</div>
            <div class="sunmory-caption">{caption}</div>
        </div>
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
