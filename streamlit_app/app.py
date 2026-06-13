from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from lab_portal.portal.config import PortalSettings, registry_store_from_settings, settings_from_mapping
from streamlit_app.progress_tracker.storage import CsvLedgerStore, SharedRegistryLedgerStore
from streamlit_app.progress_tracker.summary import filter_ledger_by_team, team_options
from streamlit_app.progress_tracker.theme import apply_theme, dashboard_header_html, sidebar_brand_html
from streamlit_app.progress_tracker.views import (
    render_experiments,
    render_member_update_form,
    render_members,
    render_milestone_update_form,
    render_milestones,
    render_overview,
    render_review,
)


SAMPLE_LEDGER_DIR = Path(__file__).parent / "data" / "sample"
SAMPLE_REGISTRY_DIR = Path(__file__).parents[1] / "lab_portal" / "data" / "sample"
APP_TITLE = "Project Tracker"
VIEWS = ["Overview", "Members", "Milestones", "Experiments", "Review"]


def get_registry_store():
    settings = get_portal_settings()
    return registry_store_from_settings(settings, SAMPLE_REGISTRY_DIR, _gspread_service_account_from_dict)


def get_portal_settings():
    try:
        return settings_from_mapping(st.secrets)
    except StreamlitSecretNotFoundError:
        return PortalSettings()


def get_ledger_store():
    return SharedRegistryLedgerStore(CsvLedgerStore(SAMPLE_LEDGER_DIR), get_registry_store())


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

    ledger_store = get_ledger_store()
    ledger = load_ledger(ledger_store)
    view_from_query = selected_view_from_query(VIEWS)
    with st.sidebar:
        st.html(sidebar_brand_html("Kamei Lab", "Progress Tracker", "Shared research portal"))
        selected_view = st.radio("View", VIEWS, index=VIEWS.index(view_from_query))
        if st.query_params.get("view") != selected_view:
            st.query_params["view"] = selected_view
        selected_team = st.selectbox("Team", team_options(ledger))
        display_ledger = filter_ledger_by_team(ledger, selected_team)
        member_names = display_ledger["Members"]["name"].tolist()
        if not member_names:
            st.warning("No members are assigned to this team yet.")
            return
        selected_member = st.selectbox("Member", member_names)
        selected_member_id = display_ledger["Members"].set_index("name").loc[selected_member, "member_id"]
        st.caption(f"Showing: `{selected_team}`")
        st.caption("Prototype mode: member-name selection. Login roles are planned for Streamlit Cloud.")

    st.html(
        dashboard_header_html(
            APP_TITLE,
            f"{selected_team} overview - local CSV ledger with Dropbox links",
            active_tab=selected_view,
        )
    )

    if selected_view == "Overview":
        render_overview(display_ledger)
    elif selected_view == "Members":
        render_members(display_ledger)
    elif selected_view == "Milestones":
        updated_ledger = render_milestone_update_form(ledger, selected_member_id, display_ledger)
        if updated_ledger is not ledger:
            save_ledger(updated_ledger, ledger_store)
            st.success("Milestone update saved.")
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


if __name__ == "__main__":
    main()
