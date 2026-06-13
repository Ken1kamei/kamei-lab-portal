from __future__ import annotations

from datetime import datetime
import html

import pandas as pd
import streamlit as st

from .constants import REVIEW_STATUSES, STATUSES
from .services import review_record, update_progress_record
from .summary import (
    completed_records,
    milestone_gantt_data,
    overview_counts,
    records_by_member,
    team_gantt_data,
)
from .theme import metric_card_html, metric_grid_html


def _gantt_chart_html(frame: pd.DataFrame, lane_column: str) -> str:
    chart_frame = frame.copy()
    if chart_frame.empty:
        return ""

    chart_frame["start_date"] = pd.to_datetime(chart_frame["start_date"], errors="coerce")
    chart_frame["end_date"] = pd.to_datetime(chart_frame["end_date"], errors="coerce")
    chart_frame = chart_frame.dropna(subset=["start_date", "end_date"])
    if chart_frame.empty:
        return ""

    min_date = chart_frame["start_date"].min()
    max_date = chart_frame["end_date"].max()
    total_days = max(int((max_date - min_date).days), 1)
    start_label = min_date.strftime("%b %d")
    end_label = max_date.strftime("%b %d")

    rows = []
    for row in chart_frame.itertuples(index=False):
        start = getattr(row, "start_date")
        end = getattr(row, "end_date")
        left = max(0, int((start - min_date).days)) / total_days * 100
        width = max(3.5, (max(1, int((end - start).days) + 1) / (total_days + 1)) * 100)
        lane = html.escape(str(getattr(row, lane_column)))
        record_type = html.escape(str(getattr(row, "record_type", "Milestone")))
        status = html.escape(str(getattr(row, "status", "")))
        bar_class = "lab-gantt-bar-experiment" if record_type == "Experiment" else "lab-gantt-bar-milestone"
        rows.append(
            f"""
            <div class="lab-gantt-row">
              <div>
                <div class="lab-gantt-label">{lane}</div>
                <div class="lab-gantt-meta">{record_type} / {status}</div>
              </div>
              <div class="lab-gantt-track">
                <div class="lab-gantt-bar {bar_class}" style="left:{left:.2f}%; width:{width:.2f}%;"></div>
              </div>
            </div>
            """
        )

    return f"""
    <div class="lab-gantt">
      <div class="lab-gantt-scale"><span>{html.escape(start_label)}</span><span>{html.escape(end_label)}</span></div>
      {''.join(rows)}
    </div>
    """


def render_overview(ledger: dict[str, pd.DataFrame]) -> None:
    st.subheader("Summary")
    counts = overview_counts(ledger)
    st.html(
        metric_grid_html(
            [
                metric_card_html("Milestones", str(counts["milestones_total"]), "active project milestones", "cyan"),
                metric_card_html("Experiments", str(counts["experiments_total"]), "linked experimental records", "green"),
                metric_card_html("Pending review", str(counts["pending_review"]), "items awaiting PI or lead review", "amber"),
                metric_card_html("Blocked", str(counts["blocked"]), "records needing help or unblock", "danger"),
            ]
        )
    )

    team_gantt = team_gantt_data(ledger)
    st.markdown('<div class="lab-chart-title"><span class="lab-handle">::</span>Team Gantt chart</div>', unsafe_allow_html=True)
    if team_gantt.empty:
        st.info("No team schedule data available.")
    else:
        st.html(_gantt_chart_html(team_gantt, "lane"))

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
        gantt = gantt.copy()
        gantt["lane"] = gantt["milestone"]
        gantt["record_type"] = "Milestone"
        st.html(_gantt_chart_html(gantt, "lane"))
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


def render_review(
    ledger: dict[str, pd.DataFrame],
    reviewer_member_id: str,
    display_ledger: dict[str, pd.DataFrame] | None = None,
) -> dict[str, pd.DataFrame]:
    st.subheader("Review queue")
    source_ledger = display_ledger if display_ledger is not None else ledger
    review_items = pd.concat(
        [
            source_ledger["Milestones"].assign(
                record_type="Milestones",
                record_id=source_ledger["Milestones"]["milestone_id"],
                title=source_ledger["Milestones"]["milestone"],
            ),
            source_ledger["Experiments"].assign(
                record_type="Experiments",
                record_id=source_ledger["Experiments"]["experiment_id"],
                title=source_ledger["Experiments"]["experiment_title"],
            ),
        ],
        ignore_index=True,
    )
    review_items = review_items[review_items["review_status"].isin(["Pending", "Needs revision"])]
    st.dataframe(
        review_items[["record_type", "record_id", "title", "status", "review_status", "next_action"]],
        width="stretch",
    )
    completed = completed_records(source_ledger)
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


def render_member_update_form(
    ledger: dict[str, pd.DataFrame],
    member_id: str,
    display_ledger: dict[str, pd.DataFrame] | None = None,
) -> dict[str, pd.DataFrame]:
    st.subheader("Update my experiment")
    source_ledger = display_ledger if display_ledger is not None else ledger
    experiments = source_ledger["Experiments"]
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


def render_milestone_update_form(
    ledger: dict[str, pd.DataFrame],
    member_id: str,
    display_ledger: dict[str, pd.DataFrame] | None = None,
) -> dict[str, pd.DataFrame]:
    st.subheader("Update my milestone")
    source_ledger = display_ledger if display_ledger is not None else ledger
    milestones = source_ledger["Milestones"]
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
