from __future__ import annotations

import streamlit as st

from utils.auth import authenticate_admin, get_admin_password, is_admin_authenticated
from utils.ui import page_header


page_header(
    "Admin Login",
    "Masuk untuk membuka Home, Session Generator, Player Dashboard, dan Admin Insights.",
    eyebrow="Admin Area",
)

if is_admin_authenticated():
    st.success("Admin sudah login.")
    st.stop()

if not get_admin_password():
    st.warning("ADMIN_PASSWORD belum diset di Streamlit secrets.")
    st.code('ADMIN_PASSWORD = "password-admin-lo"', language="toml")
    st.stop()

with st.form("admin_login_form"):
    password = st.text_input("Password admin", type="password")
    submitted = st.form_submit_button("Login", use_container_width=True)

if submitted:
    if authenticate_admin(password):
        st.session_state.admin_authenticated = True
        st.success("Login berhasil.")
        st.rerun()
    else:
        st.error("Password salah.")
