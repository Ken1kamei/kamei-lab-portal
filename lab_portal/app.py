from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from lab_portal.portal.auth import authenticated_email, clear_session_authenticated_email, oidc_configured, set_session_authenticated_email
from lab_portal.portal.config import (
    PortalSettings,
    open_spreadsheet_by_key_with_retry,
    registry_store_from_settings,
    settings_from_mapping,
)
from lab_portal.portal.constants import APP_ROLES, PORTAL_ROLES
from lab_portal.portal.permissions import can_admin_portal, resolve_member_by_email
from lab_portal.portal.services import add_member, add_team, deactivate_member, grant_app_role, update_app_url, update_member
from lab_portal.portal.storage import GoogleSheetRegistryStore
from lab_portal.portal.theme import apply_theme
from lab_portal.portal.views import app_card_html, app_cards, dashboard_header_html


APP_TITLE = "Kamei Lab Portal"
VIEWS = ["Home", "Members", "Teams", "App Access", "Audit"]
SAMPLE_REGISTRY_DIR = Path(__file__).parent / "data" / "sample"


def get_registry_store():
    settings = get_portal_settings()
    if settings.registry_spreadsheet_id and settings.service_account_info:
        spreadsheet = _cached_registry_spreadsheet(
            settings.registry_spreadsheet_id,
            json.dumps(settings.service_account_info, sort_keys=True),
        )
        return GoogleSheetRegistryStore(spreadsheet)
    return registry_store_from_settings(settings, SAMPLE_REGISTRY_DIR, _gspread_service_account_from_dict)


@st.cache_resource(ttl=300, show_spinner=False)
def _cached_registry_spreadsheet(spreadsheet_id: str, service_account_info_json: str):
    client = _gspread_service_account_from_dict(json.loads(service_account_info_json))
    return open_spreadsheet_by_key_with_retry(client, spreadsheet_id)


@st.cache_data(ttl=120, show_spinner=False)
def _cached_registry_data(spreadsheet_id: str, service_account_info_json: str):
    spreadsheet = _cached_registry_spreadsheet(spreadsheet_id, service_account_info_json)
    return GoogleSheetRegistryStore(spreadsheet).load()


def get_portal_settings():
    try:
        return settings_from_mapping(st.secrets)
    except StreamlitSecretNotFoundError:
        return PortalSettings()


def load_registry(store=None):
    if store is None:
        settings = get_portal_settings()
        if settings.registry_spreadsheet_id and settings.service_account_info:
            return _cached_registry_data(
                settings.registry_spreadsheet_id,
                json.dumps(settings.service_account_info, sort_keys=True),
            )
    return (store or get_registry_store()).load()


def save_registry(registry, store=None) -> None:
    (store or get_registry_store()).save(registry)
    _cached_registry_data.clear()


def selected_view_from_query(views: list[str]) -> str:
    view = st.query_params.get("view", views[0])
    return view if view in views else views[0]


def render_home(registry) -> None:
    st.html(dashboard_header_html(APP_TITLE, "Shared entry point for Kamei Reverse Bioengineering Lab apps"))
    cards = app_cards(registry)
    columns = st.columns(3)
    for index, card in enumerate(cards):
        with columns[index % 3]:
            st.html(app_card_html(card))

    st.markdown("### Lab registry")
    st.caption("Use the shared registry to manage members, teams, and app access for every app.")
    registry_columns = st.columns(3)
    with registry_columns[0]:
        render_registry_nav_button("Members", "Register new members and deactivate inactive ones.", "Members")
    with registry_columns[1]:
        render_registry_nav_button("Teams", "Create teams and working groups.", "Teams")
    with registry_columns[2]:
        render_registry_nav_button("App access", "Grant app roles and update app URLs.", "App Access")


def render_registry_nav_button(title: str, description: str, target_view: str) -> None:
    key = f"registry_nav_{target_view.lower().replace(' ', '_')}"
    label = f"Manage\n\n**{title}**\n\n{description}"
    if st.button(label, key=key, use_container_width=True):
        st.query_params["view"] = target_view
        st.rerun()


def render_table_page(title: str, subtitle: str, frame) -> None:
    st.html(dashboard_header_html(title, subtitle))
    st.dataframe(frame, width="stretch", hide_index=True)


def member_display_frame(registry) -> pd.DataFrame:
    hidden_columns = {"password_hash"}
    return registry["Members"].drop(columns=[column for column in hidden_columns if column in registry["Members"].columns])


def render_member_admin(registry, store, actor_email: str) -> None:
    st.subheader("Member administration")
    st.caption("Use this panel to register lab members in the shared registry. Changes flow into the other apps after refresh.")
    active_teams = registry["Teams"][registry["Teams"]["active"].astype(str).str.upper() == "TRUE"].fillna("")
    active_apps = registry["Apps"][registry["Apps"]["active"].astype(str).str.upper() == "TRUE"].fillna("")
    team_options = active_teams["team_id"].astype(str).tolist()
    app_options = active_apps["app_id"].astype(str).tolist()
    default_team_ids = [team_id for team_id in team_options if _team_label(registry, team_id) == "Core Lab"] or team_options[:1]
    with st.form("portal-add-member"):
        st.write("Add member")
        email = st.text_input("Email")
        name = st.text_input("Full name")
        display_name = st.text_input("Display name")
        global_role = st.selectbox("Global role", PORTAL_ROLES, index=PORTAL_ROLES.index("member"))
        password = st.text_input("Initial password", type="password")
        confirm_password = st.text_input("Confirm initial password", type="password")
        selected_team_ids = st.multiselect(
            "Teams",
            team_options,
            default=default_team_ids,
            format_func=lambda value: _team_label(registry, value),
        )
        team_role = st.selectbox("Team role", ["member", "lead", "manager", "viewer"], index=0)
        selected_app_ids = st.multiselect(
            "App access",
            app_options,
            default=app_options,
            format_func=lambda value: _app_label(registry, value),
        )
        app_role = st.selectbox("App role", APP_ROLES, index=APP_ROLES.index("viewer"))
        start_date = st.date_input("Start date", value=date.today())
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add member")
    if submitted:
        try:
            if password != confirm_password:
                raise ValueError("Initial password and confirmation do not match.")
            updated = add_member(
                registry,
                actor_email=actor_email,
                email=email,
                name=name,
                display_name=display_name or name,
                global_role=global_role,
                start_date=start_date.isoformat(),
                password=password,
                notes=notes,
                team_ids=selected_team_ids,
                team_role=team_role,
                app_ids=selected_app_ids,
                app_role=app_role,
            )
            save_registry(updated, store)
            st.success("Member added.")
            st.rerun()
        except ValueError as error:
            st.error(str(error))

    active_members = registry["Members"][registry["Members"]["active"].astype(str).str.upper() == "TRUE"]
    member_options = active_members["member_id"].astype(str).tolist()
    all_member_options = registry["Members"]["member_id"].astype(str).tolist()
    if all_member_options:
        with st.form("portal-edit-member"):
            st.write("Edit member")
            edit_member_id = st.selectbox(
                "Member to edit",
                all_member_options,
                format_func=lambda value: _member_label(registry, value),
                key="edit-member-id",
            )
            current_member = registry["Members"].set_index("member_id").loc[edit_member_id].fillna("")
            edit_email = st.text_input("Email", value=_text_value(current_member.get("email", "")), key="edit-member-email")
            edit_name = st.text_input("Full name", value=_text_value(current_member.get("name", "")), key="edit-member-name")
            edit_display_name = st.text_input(
                "Display name",
                value=_text_value(current_member.get("display_name", "")),
                key="edit-member-display-name",
            )
            edit_global_role = st.selectbox(
                "Global role",
                PORTAL_ROLES,
                index=PORTAL_ROLES.index(_text_value(current_member.get("global_role", "member")))
                if _text_value(current_member.get("global_role", "member")) in PORTAL_ROLES
                else PORTAL_ROLES.index("member"),
                key="edit-member-global-role",
            )
            edit_active = st.selectbox(
                "Active",
                ["TRUE", "FALSE"],
                index=0 if _text_value(current_member.get("active", "")).upper() == "TRUE" else 1,
                key="edit-member-active",
            )
            edit_start_date = st.text_input(
                "Start date",
                value=_text_value(current_member.get("start_date", "")),
                key="edit-member-start-date",
            )
            edit_end_date = st.text_input(
                "End date",
                value=_text_value(current_member.get("end_date", "")),
                key="edit-member-end-date",
            )
            edit_password = st.text_input("New password", type="password", key="edit-member-password")
            edit_confirm_password = st.text_input(
                "Confirm new password",
                type="password",
                key="edit-member-confirm-password",
            )
            edit_password_must_change = st.selectbox(
                "Require password change",
                ["TRUE", "FALSE"],
                index=0 if _text_value(current_member.get("password_must_change", "TRUE")).upper() != "FALSE" else 1,
                key="edit-member-password-must-change",
            )
            edit_notes = st.text_area("Notes", value=_text_value(current_member.get("notes", "")), key="edit-member-notes")
            edit_submitted = st.form_submit_button("Save member")
        if edit_submitted:
            try:
                if edit_password != edit_confirm_password:
                    raise ValueError("New password and confirmation do not match.")
                updated = update_member(
                    registry,
                    actor_email=actor_email,
                    member_id=edit_member_id,
                    email=edit_email,
                    name=edit_name,
                    display_name=edit_display_name or edit_name,
                    global_role=edit_global_role,
                    active=edit_active,
                    start_date=edit_start_date,
                    end_date=edit_end_date,
                    notes=edit_notes,
                    password=edit_password,
                    password_must_change=edit_password_must_change,
                )
                save_registry(updated, store)
                st.success("Member updated.")
                st.rerun()
            except ValueError as error:
                st.error(str(error))

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


def _gspread_service_account_from_dict(service_account_info):
    import gspread

    return gspread.service_account_from_dict(service_account_info)


def render_auth_controls(email: str, is_admin: bool, registry) -> None:
    if email:
        st.caption(f"Signed in as `{email}`")
        if not is_admin:
            st.warning("This account is not an active Portal admin.")
        if st.button("Sign out", use_container_width=True):
            clear_session_authenticated_email()
            if hasattr(st, "logout"):
                st.logout()
            st.rerun()
        return

    st.caption("Signed in as `unknown`")
    if auth_configured() and hasattr(st, "login"):
        if st.button("Sign in", use_container_width=True):
            try:
                st.login()
            except Exception as error:
                st.error(f"Sign in is not configured yet: {error}")
    elif admin_passcode_configured():
        render_passcode_signin(registry)
    else:
        st.info("Sign in is not configured. Add `[auth]`, `PORTAL_ADMIN_PASSCODE`, or `PORTAL_DEV_EMAIL` in Streamlit secrets.")


def render_passcode_signin(registry) -> None:
    with st.form("portal-passcode-signin"):
        admin_email = st.text_input("Admin email")
        passcode = st.text_input("Access code", type="password")
        submitted = st.form_submit_button("Sign in")
    if not submitted:
        return

    if passcode != portal_admin_passcode():
        st.error("Access code is incorrect.")
        return
    member = resolve_member_by_email(registry, admin_email)
    if not can_admin_portal(member):
        st.error("This email is not an active Portal admin.")
        return
    set_session_authenticated_email(admin_email)
    st.success("Signed in.")
    st.rerun()


def auth_configured() -> bool:
    return oidc_configured()


def render_login_required() -> None:
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.html(
            """
            <div class="portal-login-panel">
              <div class="portal-login-brand">
                <div class="portal-login-icon" aria-hidden="true">&#128300;</div>
                <h1 class="portal-login-title">Kamei Lab Portal</h1>
              </div>
              <p class="portal-login-subtitle">Kamei Reverse Bioengineering Lab · NYUAD</p>
              <div class="portal-login-rule"></div>
              <p class="portal-login-copy">Sign in with your NYU Google account to continue.</p>
            </div>
            """
        )
        if auth_configured() and hasattr(st, "login"):
            if st.button("Sign in with Google", key="portal_login_google", use_container_width=True):
                st.login()
        else:
            st.error("NYU Google login is not configured yet. Add [auth] OIDC settings in Streamlit Cloud secrets.")


def render_unregistered_account(email: str) -> None:
    st.html(dashboard_header_html(APP_TITLE, "Shared entry point for Kamei Reverse Bioengineering Lab apps"))
    st.error("This NYU Google account is not linked to an active lab member.")
    st.caption(f"Signed in as `{email}`")
    st.info("Ask a Portal admin to register this exact email in Members.")
    if st.button("Sign out", use_container_width=True):
        clear_session_authenticated_email()
        if hasattr(st, "logout"):
            st.logout()
        st.rerun()


def admin_passcode_configured() -> bool:
    return bool(portal_admin_passcode())


def portal_admin_passcode() -> str:
    try:
        return str(st.secrets.get("PORTAL_ADMIN_PASSCODE", "")).strip()
    except Exception:
        return ""


def render_registry_connection_error(error: Exception) -> None:
    st.html(dashboard_header_html(APP_TITLE, "Shared entry point for Kamei Reverse Bioengineering Lab apps"))
    st.error("The shared lab registry could not be loaded.")
    st.info(
        "Please refresh the app. If this repeats, check that the Google Sheet is shared with the service account "
        "and that `REGISTRY_SPREADSHEET_ID` is correct in Streamlit Cloud secrets."
    )
    with st.expander("Technical detail"):
        st.code(f"{type(error).__name__}: {error}")


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="K", layout="wide", initial_sidebar_state="expanded")
    apply_theme()

    try:
        store = get_registry_store()
        registry = load_registry()
    except Exception as error:
        render_registry_connection_error(error)
        st.stop()

    email = authenticated_email()
    member = resolve_member_by_email(registry, email)
    is_admin = can_admin_portal(member)

    if not email and auth_configured():
        render_login_required()
        st.stop()
    if email and member is None:
        render_unregistered_account(email)
        st.stop()

    view_from_query = selected_view_from_query(VIEWS)
    with st.sidebar:
        st.title("Kamei Lab")
        st.caption("Portal")
        render_auth_controls(email, is_admin, registry)
        view = st.radio("View", VIEWS, index=VIEWS.index(view_from_query))
        if st.query_params.get("view") != view:
            st.query_params["view"] = view

    if view == "Home":
        render_home(registry)
    elif view == "Members":
        render_table_page("Members", "Central lab member registry", member_display_frame(registry))
        if is_admin:
            render_member_admin(registry, store, email)
        else:
            st.info("Admin sign-in is required to add or deactivate members.")
    elif view == "Teams":
        render_table_page("Teams", "Lab teams and working groups", registry["Teams"])
        if is_admin:
            render_team_admin(registry, store, email)
        else:
            st.info("Admin sign-in is required to add teams.")
    elif view == "App Access":
        render_table_page("App Access", "Per-app member roles", registry["App_Roles"])
        if is_admin:
            render_app_access_admin(registry, store, email)
        else:
            st.info("Admin sign-in is required to manage app access.")
    elif view == "Audit":
        render_table_page("Audit", "Append-only administrative history", registry["Audit_Log"])


if __name__ == "__main__":
    main()
