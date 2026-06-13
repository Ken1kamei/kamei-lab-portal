from __future__ import annotations

import pandas as pd
import streamlit as st

from .constants import REVIEW_STATUSES, STATUSES
from .summary import overview_counts, records_by_member


def render_overview(ledger: dict[str, pd.DataFrame]) -> None:
    counts = overview_counts(ledger)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Milestones", counts["milestones_total"])
    col2.metric("Experiments", counts["experiments_total"])
    col3.metric("Pending review", counts["pending_review"])
    col4.metric("Blocked", counts["blocked"])

    blocked = pd.concat(
        [
            ledger["Milestones"].assign(record_type="Milestone", title=ledger["Milestones"]["milestone"]),
            ledger["Experiments"].assign(record_type="Experiment", title=ledger["Experiments"]["experiment_title"]),
        ],
        ignore_index=True,
    )
    blocked = blocked[blocked["status"] == "Blocked"]
    st.subheader("Blocked items")
    st.dataframe(blocked[["record_type", "title", "blocker_reason", "help_needed_from"]], use_container_width=True)


def render_members(ledger: dict[str, pd.DataFrame]) -> None:
    st.subheader("Progress by member")
    st.dataframe(records_by_member(ledger), use_container_width=True)


def render_milestones(ledger: dict[str, pd.DataFrame]) -> None:
    st.subheader("Milestones")
    frame = ledger["Milestones"]
    st.dataframe(
        frame[["project", "aim", "milestone", "time_window", "owner_member_id", "status", "review_status", "next_action"]],
        use_container_width=True,
    )


def render_experiments(ledger: dict[str, pd.DataFrame]) -> None:
    st.subheader("Experiments")
    frame = ledger["Experiments"].copy()
    for field in ["experiment_data_link", "protocol_link", "analysis_folder_link"]:
        frame[field] = frame[field].apply(lambda value: value if str(value).startswith("http") else "")
    st.dataframe(
        frame[
            [
                "experiment_title",
                "experiment_type",
                "member_id",
                "status",
                "review_status",
                "next_action",
                "due_date",
                "experiment_data_link",
                "analysis_folder_link",
            ]
        ],
        use_container_width=True,
        column_config={
            "experiment_data_link": st.column_config.LinkColumn("Data"),
            "analysis_folder_link": st.column_config.LinkColumn("Analysis"),
        },
    )


def render_review(ledger: dict[str, pd.DataFrame]) -> None:
    st.subheader("Review queue")
    review_items = pd.concat(
        [
            ledger["Milestones"].assign(record_type="Milestone", title=ledger["Milestones"]["milestone"]),
            ledger["Experiments"].assign(record_type="Experiment", title=ledger["Experiments"]["experiment_title"]),
        ],
        ignore_index=True,
    )
    review_items = review_items[review_items["review_status"].isin(["Pending", "Needs revision"])]
    st.dataframe(review_items[["record_type", "title", "status", "review_status", "next_action"]], use_container_width=True)


def render_member_update_form() -> None:
    st.subheader("Prototype update form")
    st.selectbox("Status", STATUSES)
    st.selectbox("Review status", REVIEW_STATUSES, index=0, disabled=True)
    st.text_input("Next action")
    st.text_area("Update note")
    st.text_input("Dropbox data link")
    st.info("The first prototype screen shows the form shape. Persistence is covered by service tests and can be wired to this form in the next task.")
