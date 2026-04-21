from __future__ import annotations

import streamlit as st

from utils.auth import is_admin_authenticated, logout_admin
from utils.ui import apply_theme


apply_theme()

with st.sidebar:
    st.markdown("### Sunmory Padel Club")
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
    st.Page("views/leaderboard.py", title="Attendance Leaderboard"),
    st.Page("views/performance_leaderboard.py", title="Match Leaderboard"),
]

if is_admin_authenticated():
    pages = {
        "Admin": [
            st.Page("views/home.py", title="Home"),
            st.Page("views/session_generator.py", title="Session Generator"),
            st.Page("views/session_manager.py", title="Session Manager"),
            st.Page("views/attendance_input.py", title="Attendance Input"),
            st.Page("views/performance_input.py", title="Performance Input"),
            st.Page("views/player_database.py", title="Player Database"),
            st.Page("views/player_dashboard.py", title="Player Dashboard"),
            st.Page("views/admin_insights.py", title="Admin Insights"),
        ],
        "Player": public_pages,
    }
else:
    pages = {
        "Player": public_pages,
        "Admin": [st.Page("views/admin_login.py", title="Admin Login")],
    }

navigation = st.navigation(pages)
navigation.run()
