from __future__ import annotations

import os

import streamlit as st


def authenticated_email() -> str:
    if "PORTAL_DEV_EMAIL" in os.environ:
        return os.environ["PORTAL_DEV_EMAIL"]

    user = getattr(st, "user", None)
    if user and getattr(user, "is_logged_in", False):
        email = user.get("email") if hasattr(user, "get") else None
        if email:
            return str(email)

    return "kkamei@nyu.edu"
