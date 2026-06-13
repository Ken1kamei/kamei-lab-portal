from __future__ import annotations

from pathlib import Path

import streamlit as st

from streamlit_app.progress_tracker.storage import CsvLedgerStore
from streamlit_app.progress_tracker.summary import filter_ledger_by_team, team_options
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


def load_ledger():
    return CsvLedgerStore(SAMPLE_LEDGER_DIR).load()


def save_ledger(ledger) -> None:
    CsvLedgerStore(SAMPLE_LEDGER_DIR).save(ledger)


def main() -> None:
    st.set_page_config(page_title="Endometriosis Progress Tracker", layout="wide")
    st.title("Endometriosis Project Progress Tracker")
    st.caption("Prototype: local CSV ledger with Dropbox links")

    ledger = load_ledger()
    selected_team = st.sidebar.selectbox("Team", team_options(ledger))
    display_ledger = filter_ledger_by_team(ledger, selected_team)
    member_names = display_ledger["Members"]["name"].tolist()
    if not member_names:
        st.warning("No members are assigned to this team yet.")
        return
    selected_member = st.sidebar.selectbox("Member", member_names)
    selected_member_id = display_ledger["Members"].set_index("name").loc[selected_member, "member_id"]
    st.sidebar.caption(f"Showing: {selected_team}")
    st.sidebar.info("Prototype mode: member-name selection. Login roles are planned for Streamlit Cloud.")

    tabs = st.tabs(["Overview", "Members", "Milestones", "Experiments", "Review"])
    with tabs[0]:
        render_overview(display_ledger)
    with tabs[1]:
        render_members(display_ledger)
    with tabs[2]:
        updated_ledger = render_milestone_update_form(ledger, selected_member_id, display_ledger)
        if updated_ledger is not ledger:
            save_ledger(updated_ledger)
            st.success("Milestone update saved.")
            st.rerun()
        render_milestones(display_ledger)
    with tabs[3]:
        updated_ledger = render_member_update_form(ledger, selected_member_id, display_ledger)
        if updated_ledger is not ledger:
            save_ledger(updated_ledger)
            st.success("Progress update saved.")
            st.rerun()
        render_experiments(display_ledger)
    with tabs[4]:
        reviewed_ledger = render_review(ledger, selected_member_id, display_ledger)
        if reviewed_ledger is not ledger:
            save_ledger(reviewed_ledger)
            st.success("Review saved.")
            st.rerun()


if __name__ == "__main__":
    main()
