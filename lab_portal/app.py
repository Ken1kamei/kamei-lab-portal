from __future__ import annotations

from pathlib import Path

import streamlit as st

from lab_portal.portal.auth import authenticated_email
from lab_portal.portal.permissions import can_admin_portal, resolve_member_by_email
from lab_portal.portal.storage import CsvRegistryStore
from lab_portal.portal.theme import apply_theme
from lab_portal.portal.views import app_cards, dashboard_header_html


APP_TITLE = "Kamei Lab Portal"
VIEWS = ["Home", "Members", "Teams", "App Access", "Audit"]
SAMPLE_REGISTRY_DIR = Path(__file__).parent / "data" / "sample"


def load_registry():
    return CsvRegistryStore(SAMPLE_REGISTRY_DIR).load()


def render_home(registry) -> None:
    st.html(dashboard_header_html(APP_TITLE, "Shared entry point for Kamei Reverse Bioengineering Lab apps"))
    cards = app_cards(registry)
    columns = st.columns(3)
    for index, card in enumerate(cards):
        with columns[index % 3]:
            st.markdown(
                f"""
                <div class="portal-card">
                  <div class="portal-status">{card['status']}</div>
                  <div class="portal-card-title">{card['label']}</div>
                  <div class="portal-card-muted">{card['description']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if card["enabled"]:
                st.link_button(f"Open {card['label']}", str(card["url"]))
            else:
                st.button(f"{card['label']} unavailable", disabled=True)


def render_table_page(title: str, subtitle: str, frame) -> None:
    st.html(dashboard_header_html(title, subtitle))
    st.dataframe(frame, use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="K", layout="wide", initial_sidebar_state="expanded")
    apply_theme()

    registry = load_registry()
    email = authenticated_email()
    member = resolve_member_by_email(registry, email)
    is_admin = can_admin_portal(member)

    with st.sidebar:
        st.title("Kamei Lab")
        st.caption("Portal")
        st.caption(f"Signed in as `{email}`")
        visible_views = VIEWS if is_admin else ["Home"]
        view = st.radio("View", visible_views)

    if view == "Home":
        render_home(registry)
    elif view == "Members":
        render_table_page("Members", "Central lab member registry", registry["Members"])
    elif view == "Teams":
        render_table_page("Teams", "Lab teams and working groups", registry["Teams"])
    elif view == "App Access":
        render_table_page("App Access", "Per-app member roles", registry["App_Roles"])
    elif view == "Audit":
        render_table_page("Audit", "Append-only administrative history", registry["Audit_Log"])


if __name__ == "__main__":
    main()
