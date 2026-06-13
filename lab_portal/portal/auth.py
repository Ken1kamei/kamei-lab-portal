from __future__ import annotations

import os

import streamlit as st


def authenticated_email() -> str:
    if os.environ.get("PORTAL_DEV_EMAIL"):
        return os.environ["PORTAL_DEV_EMAIL"]

    user = getattr(st, "user", None)
    if user and getattr(user, "is_logged_in", False):
        email = user.get("email") if hasattr(user, "get") else getattr(user, "email", None)
        if email:
            return str(email)

    return ""
