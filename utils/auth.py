from __future__ import annotations

import hmac
import time

import streamlit as st


ADMIN_SESSION_TTL_SECONDS = 12 * 60 * 60
ADMIN_LOGIN_TIME_KEY = "admin_login_time"


def get_admin_password() -> str:
    try:
        return str(st.secrets.get("ADMIN_PASSWORD", ""))
    except Exception:
        return ""


def is_admin_authenticated() -> bool:
    if not st.session_state.get("admin_authenticated"):
        return False

    login_time = float(st.session_state.get(ADMIN_LOGIN_TIME_KEY, 0) or 0)
    if login_time and time.time() - login_time <= ADMIN_SESSION_TTL_SECONDS:
        return True

    logout_admin()
    return False


def authenticate_admin(password: str) -> bool:
    configured_password = get_admin_password()
    if not configured_password:
        return False
    return hmac.compare_digest(password, configured_password)


def login_admin() -> None:
    st.session_state.admin_authenticated = True
    st.session_state[ADMIN_LOGIN_TIME_KEY] = time.time()


def logout_admin() -> None:
    st.session_state.admin_authenticated = False
    st.session_state.pop(ADMIN_LOGIN_TIME_KEY, None)


def require_admin() -> None:
    if is_admin_authenticated():
        return
    st.error("Halaman ini khusus admin. Login dulu dari menu Admin Login.")
    st.stop()
