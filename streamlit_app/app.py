from __future__ import annotations

from pathlib import Path

import streamlit as st

from streamlit_app.progress_tracker.storage import CsvLedgerStore
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
APP_TITLE = "Project Tracker"


def load_ledger():
    return CsvLedgerStore(SAMPLE_LEDGER_DIR).load()


def save_ledger(ledger) -> None:
    CsvLedgerStore(SAMPLE_LEDGER_DIR).save(ledger)


def main() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="K",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_theme()

    ledger = load_ledger()
    views = ["Overview", "Members", "Milestones", "Experiments", "Review"]
    with st.sidebar:
        st.html(sidebar_brand_html("Kamei Lab", "Progress Tracker", "Shared research portal"))
        selected_view = st.radio("View", views)
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
            save_ledger(updated_ledger)
            st.success("Milestone update saved.")
            st.rerun()
        render_milestones(display_ledger)
    elif selected_view == "Experiments":
        updated_ledger = render_member_update_form(ledger, selected_member_id, display_ledger)
        if updated_ledger is not ledger:
            save_ledger(updated_ledger)
            st.success("Progress update saved.")
            st.rerun()
        render_experiments(display_ledger)
    elif selected_view == "Review":
        reviewed_ledger = render_review(ledger, selected_member_id, display_ledger)
        if reviewed_ledger is not ledger:
            save_ledger(reviewed_ledger)
            st.success("Review saved.")
            st.rerun()


if __name__ == "__main__":
    main()
