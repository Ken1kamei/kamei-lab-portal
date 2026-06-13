from __future__ import annotations

from pathlib import Path

import streamlit as st

from streamlit_app.progress_tracker.storage import CsvLedgerStore
from streamlit_app.progress_tracker.views import (
    render_experiments,
    render_member_update_form,
    render_members,
    render_milestones,
    render_overview,
    render_review,
)


SAMPLE_LEDGER_DIR = Path(__file__).parent / "data" / "sample"


def load_ledger():
    return CsvLedgerStore(SAMPLE_LEDGER_DIR).load()


def main() -> None:
    st.set_page_config(page_title="Endometriosis Progress Tracker", layout="wide")
    st.title("Endometriosis Project Progress Tracker")
    st.caption("Prototype: local CSV ledger with Dropbox links")

    ledger = load_ledger()
    member_names = ledger["Members"]["name"].tolist()
    st.sidebar.selectbox("Member", member_names)
    st.sidebar.info("Prototype mode: member-name selection. Login roles are planned for Streamlit Cloud.")

    tabs = st.tabs(["Overview", "Members", "Milestones", "Experiments", "Review"])
    with tabs[0]:
        render_overview(ledger)
    with tabs[1]:
        render_members(ledger)
        render_member_update_form()
    with tabs[2]:
        render_milestones(ledger)
    with tabs[3]:
        render_experiments(ledger)
    with tabs[4]:
        render_review(ledger)


if __name__ == "__main__":
    main()
