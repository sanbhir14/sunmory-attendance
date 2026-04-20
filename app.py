from __future__ import annotations

import streamlit as st

from utils.auth import is_admin_authenticated, logout_admin
from utils.ui import apply_theme, render_sidebar_brand


apply_theme()

with st.sidebar:
    render_sidebar_brand()
    if is_admin_authenticated():
        st.success("Admin mode aktif")
        if st.button("Logout Admin", use_container_width=True):
            logout_admin()
            st.rerun()
    else:
        st.caption("Player mode")
    if st.button("Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

public_pages = [
    st.Page("pages/leaderboard.py", title="Leaderboard"),
]

if is_admin_authenticated():
    pages = {
        "Admin": [
            st.Page("pages/home.py", title="Home"),
            st.Page("pages/session_generator.py", title="Session Generator"),
            st.Page("pages/player_dashboard.py", title="Player Dashboard"),
            st.Page("pages/admin_insights.py", title="Admin Insights"),
        ],
        "Player": public_pages,
    }
else:
    pages = {
        "Player": public_pages,
        "Admin": [st.Page("pages/admin_login.py", title="Admin Login")],
    }

navigation = st.navigation(pages)
navigation.run()
