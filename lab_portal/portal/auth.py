from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
from collections.abc import Mapping
from urllib.parse import urlencode

import streamlit as st


SESSION_EMAIL_KEY = "portal_authenticated_email"
HANDOFF_QUERY_PARAM = "portal_token"
HANDOFF_TTL_SECONDS = 600


def authenticated_email() -> str:
    dev_email = os.environ.get("PORTAL_DEV_EMAIL") or _secret_value("PORTAL_DEV_EMAIL")
    if dev_email:
        return dev_email.strip().lower()

    oidc_email = authenticated_oidc_email()
    if oidc_email:
        return oidc_email

    handoff_email = consume_handoff_token_from_query()
    if handoff_email:
        return handoff_email

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


def app_url_with_handoff(url: str, email: str) -> str:
    url = str(url or "").strip()
    email = str(email or "").strip().lower()
    if not url or not email or not handoff_configured():
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}{urlencode({HANDOFF_QUERY_PARAM: make_handoff_token(email)})}"


def handoff_configured() -> bool:
    return bool(_handoff_secret())


def make_handoff_token(email: str, ttl_seconds: int = HANDOFF_TTL_SECONDS) -> str:
    email = str(email or "").strip().lower()
    if not email.endswith("@nyu.edu"):
        raise ValueError("Only NYU email addresses can be used for app handoff.")
    expires_at = str(int(time.time()) + int(ttl_seconds))
    payload = f"{email}|{expires_at}"
    signature = hmac.new(_handoff_secret().encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return _b64encode(f"{payload}|{signature}")


def consume_handoff_token_from_query() -> str:
    try:
        token = st.query_params.get(HANDOFF_QUERY_PARAM, "")
    except Exception:
        return ""
    email = verify_handoff_token(token)
    if not email:
        return ""
    set_session_authenticated_email(email)
    try:
        del st.query_params[HANDOFF_QUERY_PARAM]
    except Exception:
        pass
    return email


def verify_handoff_token(token: str) -> str:
    secret = _handoff_secret()
    if not token or not secret:
        return ""
    try:
        decoded = _b64decode(token)
        email, expires_at, signature = decoded.rsplit("|", 2)
        email = email.strip().lower()
        expires = int(expires_at)
    except Exception:
        return ""
    if expires < int(time.time()) or not email.endswith("@nyu.edu"):
        return ""
    payload = f"{email}|{expires_at}"
    expected = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return ""
    return email


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


def _handoff_secret() -> str:
    explicit_secret = _secret_value("PORTAL_SESSION_SECRET")
    if explicit_secret:
        return explicit_secret
    try:
        auth = st.secrets.get("auth", {})
        if hasattr(auth, "to_dict"):
            auth = auth.to_dict()
        if isinstance(auth, Mapping):
            cookie_secret = str(auth.get("cookie_secret", "")).strip()
            if cookie_secret:
                return cookie_secret
    except Exception:
        pass
    return ""


def _b64encode(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode("utf-8")).decode("ascii").rstrip("=")


def _b64decode(value: str) -> str:
    padded = value + ("=" * (-len(value) % 4))
    return base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")


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
