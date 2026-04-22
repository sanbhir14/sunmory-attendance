from __future__ import annotations

import streamlit as st

from utils.auth import authenticate_admin, get_admin_password, is_admin_authenticated, login_admin


st.title("Admin Login")
st.caption("Masuk untuk membuka Home, Session Generator, dan Admin Insights.")

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
        login_admin()
        st.success("Login berhasil.")
        st.rerun()
    else:
        st.error("Password salah.")
