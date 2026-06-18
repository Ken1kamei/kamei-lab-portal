from __future__ import annotations

import os

import streamlit as st


def authenticated_email() -> str:
    dev_email = os.environ.get("PORTAL_DEV_EMAIL") or _secret_value("PORTAL_DEV_EMAIL")
    if dev_email:
        return dev_email

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
