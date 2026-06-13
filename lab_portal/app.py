from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from lab_portal.portal.auth import authenticated_email
from lab_portal.portal.constants import APP_ROLES, PORTAL_ROLES
from lab_portal.portal.permissions import can_admin_portal, resolve_member_by_email
from lab_portal.portal.services import add_member, add_team, deactivate_member, grant_app_role, update_app_url
from lab_portal.portal.storage import CsvRegistryStore
from lab_portal.portal.theme import apply_theme
from lab_portal.portal.views import app_cards, dashboard_header_html


APP_TITLE = "Kamei Lab Portal"
VIEWS = ["Home", "Members", "Teams", "App Access", "Audit"]
SAMPLE_REGISTRY_DIR = Path(__file__).parent / "data" / "sample"


def get_registry_store():
    return CsvRegistryStore(SAMPLE_REGISTRY_DIR)


def load_registry(store=None):
    return (store or get_registry_store()).load()


def save_registry(registry, store=None) -> None:
    (store or get_registry_store()).save(registry)


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


def render_member_admin(registry, store, actor_email: str) -> None:
    st.subheader("Member administration")
    with st.form("portal-add-member"):
        st.write("Add member")
        email = st.text_input("Email")
        name = st.text_input("Full name")
        display_name = st.text_input("Display name")
        global_role = st.selectbox("Global role", PORTAL_ROLES, index=PORTAL_ROLES.index("member"))
        start_date = st.date_input("Start date", value=date.today())
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add member")
    if submitted:
        try:
            updated = add_member(
                registry,
                actor_email=actor_email,
                email=email,
                name=name,
                display_name=display_name or name,
                global_role=global_role,
                start_date=start_date.isoformat(),
                notes=notes,
            )
            save_registry(updated, store)
            st.success("Member added.")
            st.rerun()
        except ValueError as error:
            st.error(str(error))

    active_members = registry["Members"][registry["Members"]["active"].astype(str).str.upper() == "TRUE"]
    member_options = active_members["member_id"].astype(str).tolist()
    if member_options:
        with st.form("portal-deactivate-member"):
            st.write("Deactivate member")
            member_id = st.selectbox("Member", member_options, format_func=lambda value: _member_label(registry, value))
            end_date = st.date_input("End date", value=date.today())
            submitted = st.form_submit_button("Deactivate")
        if submitted:
            try:
                updated = deactivate_member(registry, actor_email=actor_email, member_id=member_id, end_date=end_date.isoformat())
                save_registry(updated, store)
                st.success("Member deactivated.")
                st.rerun()
            except ValueError as error:
                st.error(str(error))
    else:
        st.info("No active members available to deactivate.")


def render_team_admin(registry, store, actor_email: str) -> None:
    st.subheader("Team administration")
    with st.form("portal-add-team"):
        team_name = st.text_input("Team name")
        description = st.text_area("Description")
        submitted = st.form_submit_button("Add team")
    if submitted:
        try:
            updated = add_team(registry, actor_email=actor_email, team_name=team_name, description=description)
            save_registry(updated, store)
            st.success("Team added.")
            st.rerun()
        except ValueError as error:
            st.error(str(error))


def render_app_access_admin(registry, store, actor_email: str) -> None:
    st.subheader("App administration")
    active_members = registry["Members"][registry["Members"]["active"].astype(str).str.upper() == "TRUE"]
    member_options = active_members["member_id"].astype(str).tolist()
    app_options = registry["Apps"]["app_id"].astype(str).tolist()
    team_options = [""] + registry["Teams"]["team_id"].astype(str).tolist()
    if member_options and app_options:
        with st.form("portal-grant-app-role"):
            st.write("Grant app role")
            member_id = st.selectbox("Member", member_options, format_func=lambda value: _member_label(registry, value))
            app_id = st.selectbox("App", app_options, format_func=lambda value: _app_label(registry, value))
            app_role = st.selectbox("Role", APP_ROLES)
            scope_team_id = st.selectbox("Team scope", team_options, format_func=lambda value: "All teams" if not value else _team_label(registry, value))
            start_date = st.date_input("Start date", value=date.today(), key="grant-role-start-date")
            submitted = st.form_submit_button("Grant role")
        if submitted:
            try:
                updated = grant_app_role(
                    registry,
                    actor_email=actor_email,
                    member_id=member_id,
                    app_id=app_id,
                    app_role=app_role,
                    scope_team_id=scope_team_id,
                    start_date=start_date.isoformat(),
                )
                save_registry(updated, store)
                st.success("App role granted.")
                st.rerun()
            except ValueError as error:
                st.error(str(error))
    else:
        st.info("Members and apps are required before granting app roles.")

    if app_options:
        with st.form("portal-update-app-url"):
            st.write("Update launcher URL")
            app_id = st.selectbox("App", app_options, format_func=lambda value: _app_label(registry, value), key="update-app-url-id")
            current_app = registry["Apps"].set_index("app_id").loc[app_id]
            app_url = st.text_input("App URL", value=_text_value(current_app.get("app_url", "")))
            active = st.selectbox("Active", ["TRUE", "FALSE"], index=0 if _text_value(current_app.get("active", "")).upper() == "TRUE" else 1)
            submitted = st.form_submit_button("Update URL")
        if submitted:
            try:
                updated = update_app_url(registry, actor_email=actor_email, app_id=app_id, app_url=app_url, active=active)
                save_registry(updated, store)
                st.success("App URL updated.")
                st.rerun()
            except ValueError as error:
                st.error(str(error))
    else:
        st.info("No apps are available to update.")


def _member_label(registry, member_id: str) -> str:
    members = registry["Members"].set_index("member_id")
    if member_id not in members.index:
        return member_id
    row = members.loc[member_id]
    return f"{row['display_name']} ({row['email']})"


def _team_label(registry, team_id: str) -> str:
    teams = registry["Teams"].set_index("team_id")
    return str(teams.loc[team_id, "team_name"]) if team_id in teams.index else team_id


def _app_label(registry, app_id: str) -> str:
    apps = registry["Apps"].set_index("app_id")
    return str(apps.loc[app_id, "app_name"]) if app_id in apps.index else app_id


def _text_value(value) -> str:
    return "" if pd.isna(value) else str(value)


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="K", layout="wide", initial_sidebar_state="expanded")
    apply_theme()

    store = get_registry_store()
    registry = load_registry(store)
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
        render_member_admin(registry, store, email)
    elif view == "Teams":
        render_table_page("Teams", "Lab teams and working groups", registry["Teams"])
        render_team_admin(registry, store, email)
    elif view == "App Access":
        render_table_page("App Access", "Per-app member roles", registry["App_Roles"])
        render_app_access_admin(registry, store, email)
    elif view == "Audit":
        render_table_page("Audit", "Append-only administrative history", registry["Audit_Log"])


if __name__ == "__main__":
    main()
