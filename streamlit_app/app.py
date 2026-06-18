from __future__ import annotations

import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from lab_portal.portal.config import (
    PortalSettings,
    open_spreadsheet_by_key_with_retry,
    registry_store_from_settings,
    settings_from_mapping,
)
from lab_portal.portal.storage import GoogleSheetRegistryStore
from streamlit_app.progress_tracker.storage import CsvLedgerStore, GoogleSheetLedgerStore, SharedRegistryLedgerStore
from streamlit_app.progress_tracker.summary import filter_ledger_by_team, team_options
from streamlit_app.progress_tracker.theme import apply_theme, dashboard_header_html, sidebar_brand_html
from streamlit_app.progress_tracker.views import (
    render_projects,
    render_experiments,
    render_member_update_form,
    render_members,
    render_milestone_update_form,
    render_milestone_create_form,
    render_milestones,
    render_overview,
    render_review,
)


SAMPLE_LEDGER_DIR = Path(__file__).parent / "data" / "sample"
SAMPLE_REGISTRY_DIR = Path(__file__).parents[1] / "lab_portal" / "data" / "sample"
APP_TITLE = "Project Tracker"
VIEWS = ["Overview", "Projects", "Members", "Milestones", "Experiments", "Review"]
DEFAULT_PORTAL_URL = "https://kamei-lab-tools.streamlit.app/"


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


def get_portal_settings():
    try:
        return settings_from_mapping(st.secrets)
    except StreamlitSecretNotFoundError:
        return PortalSettings()


def get_ledger_store():
    return SharedRegistryLedgerStore(get_progress_store(), get_registry_store())


def get_progress_store():
    settings = get_portal_settings()
    if settings.progress_spreadsheet_id and settings.service_account_info:
        spreadsheet = _cached_progress_spreadsheet(
            settings.progress_spreadsheet_id,
            json.dumps(settings.service_account_info, sort_keys=True),
        )
        return GoogleSheetLedgerStore(spreadsheet)
    return CsvLedgerStore(SAMPLE_LEDGER_DIR)


@st.cache_resource(ttl=300, show_spinner=False)
def _cached_progress_spreadsheet(spreadsheet_id: str, service_account_info_json: str):
    client = _gspread_service_account_from_dict(json.loads(service_account_info_json))
    return open_spreadsheet_by_key_with_retry(client, spreadsheet_id)


def load_ledger(store=None):
    return (store or get_ledger_store()).load()


def save_ledger(ledger, store=None) -> None:
    (store or get_ledger_store()).save(ledger)


def _gspread_service_account_from_dict(service_account_info):
    import gspread

    return gspread.service_account_from_dict(service_account_info)


def selected_view_from_query(views: list[str]) -> str:
    view = st.query_params.get("view", views[0])
    return view if view in views else views[0]


def main() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="K",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_theme()

    try:
        ledger_store = get_ledger_store()
        ledger = load_ledger(ledger_store)
    except Exception as error:
        st.html(dashboard_header_html(APP_TITLE, "Shared research ledger with data links"))
        st.error("The shared project tracker data could not be loaded.")
        st.info(
            "Please refresh the app. If this repeats, check the Google Sheet sharing and the registry/progress "
            "spreadsheet IDs in Streamlit Cloud secrets."
        )
        with st.expander("Technical detail"):
            st.code(f"{type(error).__name__}: {error}")
        st.stop()

    view_from_query = selected_view_from_query(VIEWS)
    with st.sidebar:
        st.html(sidebar_brand_html("Kamei Lab", "Progress Tracker", "Shared research portal"))
        portal_url = get_portal_settings().portal_app_url or DEFAULT_PORTAL_URL
        st.link_button("Back to Kamei Lab Portal", portal_url, use_container_width=True)
        selected_view = st.radio("View", VIEWS, index=VIEWS.index(view_from_query))
        if st.query_params.get("view") != selected_view:
            st.query_params["view"] = selected_view
        selected_team = st.selectbox("Team", team_options(ledger))
        display_ledger = filter_ledger_by_team(ledger, selected_team)
        member_rows = display_ledger["Members"][["member_id", "name", "email"]].fillna("")
        if member_rows.empty:
            st.warning("No members are assigned to this team yet.")
            return
        member_labels = {
            row["member_id"]: _member_label(row["name"], row["email"])
            for _, row in member_rows.iterrows()
        }
        selected_member_id = st.selectbox("Member", list(member_labels), format_func=lambda value: member_labels[value])
        st.caption(f"Showing: `{selected_team}`")
        st.caption("Members registered in Kamei Lab Portal appear here after refresh.")

    st.html(
        dashboard_header_html(
            APP_TITLE,
            f"{selected_team} overview - shared research ledger with data links",
            active_tab=selected_view,
        )
    )

    if selected_view == "Overview":
        render_overview(display_ledger)
    elif selected_view == "Members":
        render_members(display_ledger)
    elif selected_view == "Projects":
        updated_ledger = render_projects(ledger, display_ledger)
        if updated_ledger is not ledger:
            save_ledger(updated_ledger, ledger_store)
            st.success("Project data saved.")
            st.rerun()
    elif selected_view == "Milestones":
        updated_ledger = render_milestone_update_form(ledger, selected_member_id, display_ledger)
        if updated_ledger is not ledger:
            save_ledger(updated_ledger, ledger_store)
            st.success("Milestone update saved.")
            st.rerun()
        created_ledger = render_milestone_create_form(ledger, default_member_id=selected_member_id, display_ledger=display_ledger)
        if created_ledger is not ledger:
            save_ledger(created_ledger, ledger_store)
            st.success("Milestone created.")
            st.rerun()
        render_milestones(display_ledger)
    elif selected_view == "Experiments":
        updated_ledger = render_member_update_form(ledger, selected_member_id, display_ledger)
        if updated_ledger is not ledger:
            save_ledger(updated_ledger, ledger_store)
            st.success("Progress update saved.")
            st.rerun()
        render_experiments(display_ledger)
    elif selected_view == "Review":
        reviewed_ledger = render_review(ledger, selected_member_id, display_ledger)
        if reviewed_ledger is not ledger:
            save_ledger(reviewed_ledger, ledger_store)
            st.success("Review saved.")
            st.rerun()


def _member_label(name: str, email: str) -> str:
    name = str(name).strip()
    email = str(email).strip()
    if name and email:
        return f"{name} ({email})"
    if name:
        return name
    return email or "Unnamed member"


if __name__ == "__main__":
    main()
