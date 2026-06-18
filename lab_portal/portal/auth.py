from __future__ import annotations

import os
from collections.abc import Mapping

import streamlit as st


SESSION_EMAIL_KEY = "portal_authenticated_email"


def authenticated_email() -> str:
    dev_email = os.environ.get("PORTAL_DEV_EMAIL") or _secret_value("PORTAL_DEV_EMAIL")
    if dev_email:
        return dev_email.strip().lower()

    oidc_email = authenticated_oidc_email()
    if oidc_email:
        return oidc_email

    session_email = session_authenticated_email()
    if session_email:
        return session_email.strip().lower()

    return ""


def authenticated_oidc_email() -> str:
    if not bool(_user_value("is_logged_in", False)):
        return ""
    email = str(_user_value("email", "") or "").strip().lower()
    if not email.endswith("@nyu.edu"):
        return ""
    verified = _user_value("email_verified", True)
    if verified is False:
        return ""
    return email


def oidc_configured() -> bool:
    try:
        auth = st.secrets.get("auth", {})
    except Exception:
        return False
    if hasattr(auth, "to_dict"):
        auth = auth.to_dict()
    if not isinstance(auth, Mapping):
        return False
    required = {"client_id", "client_secret", "server_metadata_url"}
    if required.issubset({key for key, value in auth.items() if str(value or "").strip()}):
        return True
    return any(
        isinstance(provider, Mapping)
        and required.issubset({key for key, value in provider.items() if str(value or "").strip()})
        for provider in auth.values()
    )


def _user_value(key: str, default=None):
    try:
        user = getattr(st, "user", None)
        if user is None:
            return default
        if hasattr(user, key):
            return getattr(user, key)
        if hasattr(user, "get"):
            return user.get(key, default)
    except Exception:
        pass
    return default


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
