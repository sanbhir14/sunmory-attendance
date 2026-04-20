from __future__ import annotations

import hmac

import streamlit as st


def get_admin_password() -> str:
    try:
        return str(st.secrets.get("ADMIN_PASSWORD", ""))
    except Exception:
        return ""


def is_admin_authenticated() -> bool:
    return bool(st.session_state.get("admin_authenticated"))


def authenticate_admin(password: str) -> bool:
    configured_password = get_admin_password()
    if not configured_password:
        return False
    return hmac.compare_digest(password, configured_password)


def logout_admin() -> None:
    st.session_state.admin_authenticated = False


def require_admin() -> None:
    if is_admin_authenticated():
        return
    st.error("Halaman ini khusus admin. Login dulu dari menu Admin Login.")
    st.stop()
