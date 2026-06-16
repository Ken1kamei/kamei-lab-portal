from __future__ import annotations

from datetime import datetime
import html

import pandas as pd
import streamlit as st

from .constants import REVIEW_STATUSES, STATUSES
from .services import (
    create_milestone,
    create_project,
    import_from_docx_bytes,
    import_from_excel_bytes,
    review_record,
    update_progress_record,
)
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


def _member_options(ledger: dict[str, pd.DataFrame]) -> list[tuple[str, str]]:
    members = ledger["Members"][["member_id", "name"]].fillna("")
    return [(str(row.member_id), str(row.name)) for row in members.itertuples() if str(row.member_id).strip()]


def _project_options(ledger: dict[str, pd.DataFrame]) -> list[tuple[str, str]]:
    projects = ledger["Projects"][["project_id", "project", "aim"]].fillna("")
    return [
        (str(row.project_id), f"{row.project} - {row.aim}".strip(" -"))
        for row in projects.itertuples()
        if str(row.project_id).strip()
    ]


def _owner_selectbox(ledger: dict[str, pd.DataFrame], label: str, key: str) -> str:
    options = _member_options(ledger)
    if not options:
        st.warning("No members are available for assignment.")
        return ""
    selected_label = st.selectbox(label, [label_text for _, label_text in options], key=key)
    for member_id, member_label in options:
        if member_label == selected_label:
            return member_id
    return options[0][0]


def _load_import_bytes(uploaded_file) -> bytes:
    return uploaded_file.getvalue() if uploaded_file is not None else b""


def render_projects(
    ledger: dict[str, pd.DataFrame],
    display_ledger: dict[str, pd.DataFrame] | None = None,
) -> dict[str, pd.DataFrame]:
    st.subheader("Projects")
    st.caption("Create projects manually or import them from Excel / Word.")
    source_ledger = display_ledger if display_ledger is not None else ledger
    frame = source_ledger["Projects"].copy()
    st.dataframe(
        frame[["project_id", "project", "aim", "owner_member_id", "start_date", "target_date", "notes"]],
        width="stretch",
    )

    with st.expander("Add project", expanded=True):
        with st.form("add-project"):
            project = st.text_input("Project name")
            aim = st.text_input("Aim")
            owner_member_id = _owner_selectbox(source_ledger, "Project owner", "project-owner")
            start_date = st.date_input("Start date")
            target_date = st.date_input("Target date")
            notes = st.text_area("Notes")
            submitted = st.form_submit_button("Create project")
            if submitted:
                try:
                    return create_project(
                        ledger,
                        project=project,
                        aim=aim,
                        owner_member_id=owner_member_id,
                        start_date=start_date.isoformat(),
                        target_date=target_date.isoformat(),
                        notes=notes,
                    )
                except ValueError as exc:
                    st.error(str(exc))
                    return ledger

    with st.expander("Import projects or milestones", expanded=False):
        upload = st.file_uploader(
            "Upload `.xlsx` or `.docx`",
            type=["xlsx", "docx"],
            accept_multiple_files=False,
            key="project-import",
        )
        if st.button("Import file", key="import-projects"):
            if upload is None:
                st.error("Choose an Excel or Word file first.")
                return ledger
            blob = _load_import_bytes(upload)
            try:
                if upload.name.lower().endswith(".xlsx"):
                    return import_from_excel_bytes(ledger, blob)
                return import_from_docx_bytes(ledger, blob)
            except ValueError as exc:
                st.error(str(exc))
                return ledger
            except Exception as exc:  # pragma: no cover - narrow UX fallback
                st.error(f"Could not import {upload.name}: {exc}")
                return ledger

    return ledger


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


def render_milestone_create_form(
    ledger: dict[str, pd.DataFrame],
    *,
    default_member_id: str | None = None,
    display_ledger: dict[str, pd.DataFrame] | None = None,
) -> dict[str, pd.DataFrame]:
    st.subheader("Add milestone")
    source_ledger = display_ledger if display_ledger is not None else ledger
    projects = _project_options(source_ledger)
    members = _member_options(source_ledger)
    if not projects:
        st.info("Create a project first.")
        return ledger
    if not members:
        st.info("No members are available to assign.")
        return ledger

    with st.form("add-milestone"):
        project_label = st.selectbox("Project", [label for _, label in projects])
        project_id = next(project_id for project_id, label in projects if label == project_label)
        project_row = source_ledger["Projects"].loc[source_ledger["Projects"]["project_id"] == project_id].iloc[0]
        milestone = st.text_input("Milestone")
        time_window = st.text_input("Time window")
        owner_member_id = _owner_selectbox(source_ledger, "Responsible person", "milestone-owner")
        if default_member_id and default_member_id in set(source_ledger["Members"]["member_id"].astype(str)):
            owner_member_id = default_member_id
        start_date = st.date_input("Start date", key="milestone-start")
        status = st.selectbox("Status", STATUSES)
        review_status = st.selectbox("Review status", REVIEW_STATUSES, index=0)
        next_action = st.text_input("Next action")
        due_date = st.date_input("Due date", key="milestone-due")
        blocker_reason = st.text_input("Blocker reason", value="")
        help_needed_from = st.text_input("Help needed from", value="")
        submitted = st.form_submit_button("Create milestone")
        if submitted:
            try:
                return create_milestone(
                    ledger,
                    project_id=project_id,
                    project=str(project_row["project"]),
                    aim=str(project_row["aim"]),
                    milestone=milestone,
                    time_window=time_window,
                    owner_member_id=owner_member_id,
                    start_date=start_date.isoformat(),
                    status=status,
                    review_status=review_status,
                    next_action=next_action,
                    due_date=due_date.isoformat(),
                    blocker_reason=blocker_reason,
                    help_needed_from=help_needed_from,
                    updated_at=datetime.now().isoformat(timespec="seconds"),
                )
            except ValueError as exc:
                st.error(str(exc))
                return ledger
    return ledger


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
