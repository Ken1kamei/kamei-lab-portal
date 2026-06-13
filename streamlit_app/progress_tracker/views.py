from __future__ import annotations

from datetime import datetime

import altair as alt
import pandas as pd
import streamlit as st

from .constants import REVIEW_STATUSES, STATUSES
from .services import review_record, update_progress_record
from .summary import (
    completed_records,
    milestone_gantt_data,
    overview_summary_rows,
    records_by_member,
    team_gantt_data,
)


def render_overview(ledger: dict[str, pd.DataFrame]) -> None:
    st.subheader("Summary")
    st.dataframe(overview_summary_rows(ledger), width="stretch", hide_index=True)

    team_gantt = team_gantt_data(ledger)
    st.subheader("Team Gantt chart")
    if team_gantt.empty:
        st.info("No team schedule data available.")
    else:
        team_chart = (
            alt.Chart(team_gantt)
            .mark_bar()
            .encode(
                x=alt.X("start_date:T", title="Start"),
                x2="end_date:T",
                y=alt.Y("lane:N", title="Team member / work item", sort=None),
                color=alt.Color("record_type:N", title="Record type"),
                tooltip=[
                    "team_member:N",
                    "record_type:N",
                    "project:N",
                    "aim:N",
                    "title:N",
                    "status:N",
                    "review_status:N",
                    "start_date:T",
                    "end_date:T",
                ],
            )
            .properties(height=max(220, 36 * len(team_gantt)))
        )
        st.altair_chart(team_chart, width="stretch")

    blocked = pd.concat(
        [
            ledger["Milestones"].assign(record_type="Milestone", title=ledger["Milestones"]["milestone"]),
            ledger["Experiments"].assign(record_type="Experiment", title=ledger["Experiments"]["experiment_title"]),
        ],
        ignore_index=True,
    )
    blocked = blocked[blocked["status"] == "Blocked"]
    st.subheader("Blocked items")
    st.dataframe(blocked[["record_type", "title", "blocker_reason", "help_needed_from"]], width="stretch")


def render_members(ledger: dict[str, pd.DataFrame]) -> None:
    st.subheader("Progress by member")
    st.dataframe(records_by_member(ledger), width="stretch")


def render_milestones(ledger: dict[str, pd.DataFrame]) -> None:
    st.subheader("Milestones")
    frame = ledger["Milestones"]
    gantt = milestone_gantt_data(ledger)
    if gantt.empty:
        st.info("No milestone dates available for Gantt chart.")
    else:
        chart = (
            alt.Chart(gantt)
            .mark_bar()
            .encode(
                x=alt.X("start_date:T", title="Start"),
                x2="end_date:T",
                y=alt.Y("milestone:N", title="Milestone", sort=None),
                color=alt.Color("status:N", title="Status"),
                tooltip=[
                    "project:N",
                    "aim:N",
                    "milestone:N",
                    "time_window:N",
                    "owner_member_id:N",
                    "status:N",
                    "review_status:N",
                    "start_date:T",
                    "end_date:T",
                ],
            )
            .properties(height=max(180, 46 * len(gantt)))
        )
        st.altair_chart(chart, width="stretch")
    st.dataframe(
        frame[
            [
                "project",
                "aim",
                "milestone",
                "time_window",
                "owner_member_id",
                "start_date",
                "due_date",
                "status",
                "review_status",
                "next_action",
            ]
        ],
        width="stretch",
    )
    completed = completed_records(ledger)
    completed_milestones = completed[completed["record_type"] == "Milestone"]
    st.subheader("Completed milestones")
    if completed_milestones.empty:
        st.info("No milestones are marked Completed yet.")
    else:
        st.dataframe(
            completed_milestones[
                ["project", "aim", "title", "owner_id", "status", "review_status", "updated_at"]
            ],
            width="stretch",
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
                "protocol_link",
                "analysis_folder_link",
            ]
        ],
        width="stretch",
        column_config={
            "experiment_data_link": st.column_config.LinkColumn("Data"),
            "protocol_link": st.column_config.LinkColumn("Protocol"),
            "analysis_folder_link": st.column_config.LinkColumn("Analysis"),
        },
    )


def render_review(ledger: dict[str, pd.DataFrame], reviewer_member_id: str) -> dict[str, pd.DataFrame]:
    st.subheader("Review queue")
    review_items = pd.concat(
        [
            ledger["Milestones"].assign(
                record_type="Milestones",
                record_id=ledger["Milestones"]["milestone_id"],
                title=ledger["Milestones"]["milestone"],
            ),
            ledger["Experiments"].assign(
                record_type="Experiments",
                record_id=ledger["Experiments"]["experiment_id"],
                title=ledger["Experiments"]["experiment_title"],
            ),
        ],
        ignore_index=True,
    )
    review_items = review_items[review_items["review_status"].isin(["Pending", "Needs revision"])]
    st.dataframe(
        review_items[["record_type", "record_id", "title", "status", "review_status", "next_action"]],
        width="stretch",
    )
    completed = completed_records(ledger)
    st.subheader("Completed records")
    if completed.empty:
        st.info("No milestones or experiments are marked Completed yet.")
    else:
        st.dataframe(
            completed[["record_type", "project", "aim", "title", "owner_id", "review_status", "updated_at"]],
            width="stretch",
        )

    if review_items.empty:
        return ledger

    choices = [f"{row.record_type}:{row.record_id} - {row.title}" for row in review_items.itertuples()]
    selected = st.selectbox("Review item", choices)
    record_type, rest = selected.split(":", 1)
    record_id = rest.split(" - ", 1)[0]
    review_status = st.selectbox("Decision", REVIEW_STATUSES, index=1)
    review_note = st.text_area("Review note")
    if st.button("Save review"):
        record_id_column = "milestone_id" if record_type == "Milestones" else "experiment_id"
        try:
            return review_record(
                ledger,
                table_name=record_type,
                record_id_column=record_id_column,
                record_id=record_id,
                reviewed_by=reviewer_member_id,
                review_status=review_status,
                review_note=review_note,
                timestamp=datetime.now().isoformat(timespec="seconds"),
            )
        except ValueError as exc:
            st.error(str(exc))
            return ledger
    return ledger


def render_member_update_form(ledger: dict[str, pd.DataFrame], member_id: str) -> dict[str, pd.DataFrame]:
    st.subheader("Update my experiment")
    experiments = ledger["Experiments"]
    mine = experiments[experiments["member_id"] == member_id]
    if mine.empty:
        st.info("No experiments assigned to this member.")
        return ledger

    choices = [f"{row.experiment_id} - {row.experiment_title}" for row in mine.itertuples()]
    selected = st.selectbox("Experiment", choices)
    experiment_id = selected.split(" - ", 1)[0]
    current = mine[mine["experiment_id"] == experiment_id].iloc[0]
    status = st.selectbox("Status", STATUSES, index=STATUSES.index(current["status"]))
    next_action = st.text_input("Next action", value=current["next_action"])
    blocker_reason = st.text_input("Blocker reason", value=current["blocker_reason"])
    experiment_data_link = st.text_input("Dropbox data link", value=current["experiment_data_link"])
    update_note = st.text_area("Update note")

    if st.button("Save progress update"):
        try:
            return update_progress_record(
                ledger,
                table_name="Experiments",
                record_id_column="experiment_id",
                record_id=experiment_id,
                updated_by=member_id,
                changes={
                    "status": status,
                    "next_action": next_action,
                    "blocker_reason": blocker_reason,
                    "experiment_data_link": experiment_data_link,
                },
                update_note=update_note,
                timestamp=datetime.now().isoformat(timespec="seconds"),
            )
        except ValueError as exc:
            st.error(str(exc))
            return ledger
    return ledger


def render_milestone_update_form(ledger: dict[str, pd.DataFrame], member_id: str) -> dict[str, pd.DataFrame]:
    st.subheader("Update my milestone")
    milestones = ledger["Milestones"]
    mine = milestones[milestones["owner_member_id"] == member_id]
    if mine.empty:
        st.info("No milestones assigned to this member.")
        return ledger

    choices = [f"{row.milestone_id} - {row.milestone}" for row in mine.itertuples()]
    selected = st.selectbox("Milestone", choices)
    milestone_id = selected.split(" - ", 1)[0]
    current = mine[mine["milestone_id"] == milestone_id].iloc[0]
    status = st.selectbox("Status", STATUSES, index=STATUSES.index(current["status"]))
    next_action = st.text_input("Next action", value=current["next_action"])
    blocker_reason = st.text_input("Blocker reason", value=current["blocker_reason"])
    update_note = st.text_area("Update note")

    if st.button("Save milestone progress update"):
        try:
            return update_progress_record(
                ledger,
                table_name="Milestones",
                record_id_column="milestone_id",
                record_id=milestone_id,
                updated_by=member_id,
                changes={
                    "status": status,
                    "next_action": next_action,
                    "blocker_reason": blocker_reason,
                },
                update_note=update_note,
                timestamp=datetime.now().isoformat(timespec="seconds"),
            )
        except ValueError as exc:
            st.error(str(exc))
            return ledger
    return ledger
