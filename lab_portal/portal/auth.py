from __future__ import annotations

import os

import streamlit as st


SESSION_EMAIL_KEY = "portal_authenticated_email"


def authenticated_email() -> str:
    dev_email = os.environ.get("PORTAL_DEV_EMAIL") or _secret_value("PORTAL_DEV_EMAIL")
    if dev_email:
        return dev_email

    session_email = session_authenticated_email()
    if session_email:
        return session_email

    user = getattr(st, "user", None)
    if user and getattr(user, "is_logged_in", False):
        email = user.get("email") if hasattr(user, "get") else getattr(user, "email", None)
        if email:
            return str(email)

    return ""


def _secret_value(key: str) -> str:
    try:
        return str(st.secrets.get(key, "")).strip()
    except Exception:
        return ""


def session_authenticated_email() -> str:
    try:
        return str(st.session_state.get(SESSION_EMAIL_KEY, "")).strip()
    except Exception:
        return ""


def set_session_authenticated_email(email: str) -> None:
    st.session_state[SESSION_EMAIL_KEY] = email.strip()


def clear_session_authenticated_email() -> None:
    try:
        st.session_state.pop(SESSION_EMAIL_KEY, None)
    except Exception:
        pass
