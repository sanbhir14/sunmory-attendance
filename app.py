from __future__ import annotations

import streamlit as st

from utils.ui import apply_theme


apply_theme()

with st.sidebar:
    st.markdown("### Sunmory Padel Club")
    if st.button("Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

pages = [
    st.Page("pages/home.py", title="Home"),
    st.Page("pages/session_generator.py", title="Session Generator"),
    st.Page("pages/player_dashboard.py", title="Player Dashboard"),
    st.Page("pages/leaderboard.py", title="Leaderboard"),
    st.Page("pages/admin_insights.py", title="Admin Insights"),
]

navigation = st.navigation(pages)
navigation.run()
