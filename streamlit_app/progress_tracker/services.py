from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from io import BytesIO
import uuid

import pandas as pd

from .schema import REQUIRED_COLUMNS
from .validation import validate_progress_record, validate_project_record, validate_review


def _append_history(
    ledger: dict[str, pd.DataFrame],
    *,
    record_type: str,
    record_id: str,
    updated_by: str = "",
    update_note: str = "",
    old_status: str = "",
    new_status: str = "",
    reviewed_by: str = "",
    review_status: str = "",
    review_note: str = "",
    timestamp: str,
) -> None:
    history_row = {
        "update_id": f"UPD-{uuid.uuid4().hex[:10]}",
        "record_type": record_type,
        "record_id": record_id,
        "updated_by": updated_by,
        "update_note": update_note,
        "old_status": old_status,
        "new_status": new_status,
        "reviewed_by": reviewed_by,
        "review_status": review_status,
        "review_note": review_note,
        "timestamp": timestamp,
    }
    ledger["Updates_Reviews"] = pd.concat(
        [ledger["Updates_Reviews"], pd.DataFrame([history_row])], ignore_index=True
    )


def _next_identifier(frame: pd.DataFrame, column: str, prefix: str) -> str:
    values = frame.get(column, pd.Series(dtype=str)).astype(str)
    numeric = []
    for value in values:
        if value.startswith(prefix):
            suffix = value[len(prefix) :].lstrip("-")
            if suffix.isdigit():
                numeric.append(int(suffix))
    return f"{prefix}{(max(numeric) + 1) if numeric else 1:03d}"


def _append_row(frame: pd.DataFrame, row: dict[str, object], columns: Iterable[str]) -> pd.DataFrame:
    output = frame.copy()
    ordered = {column: row.get(column, "") for column in columns}
    return pd.concat([output, pd.DataFrame([ordered])], ignore_index=True)


def create_project(
    ledger: dict[str, pd.DataFrame],
    *,
    project: str,
    aim: str,
    owner_member_id: str,
    start_date: str,
    target_date: str,
    notes: str,
) -> dict[str, pd.DataFrame]:
    output = {name: frame.copy() for name, frame in ledger.items()}
    row = {
        "project_id": _next_identifier(output["Projects"], "project_id", "P"),
        "project": project.strip(),
        "aim": aim.strip(),
        "owner_member_id": owner_member_id.strip(),
        "start_date": start_date.strip(),
        "target_date": target_date.strip(),
        "notes": notes.strip(),
    }
    errors = validate_project_record(row)
    if errors:
        raise ValueError(" ".join(errors))
    output["Projects"] = _append_row(output["Projects"], row, REQUIRED_COLUMNS["Projects"])
    return output


def create_milestone(
    ledger: dict[str, pd.DataFrame],
    *,
    project_id: str,
    project: str,
    aim: str,
    milestone: str,
    time_window: str,
    owner_member_id: str,
    start_date: str,
    status: str,
    review_status: str,
    next_action: str,
    due_date: str,
    blocker_reason: str,
    help_needed_from: str,
    updated_at: str,
) -> dict[str, pd.DataFrame]:
    output = {name: frame.copy() for name, frame in ledger.items()}
    row = {
        "milestone_id": _next_identifier(output["Milestones"], "milestone_id", "MS"),
        "project_id": project_id.strip(),
        "project": project.strip(),
        "aim": aim.strip(),
        "milestone": milestone.strip(),
        "time_window": time_window.strip(),
        "owner_member_id": owner_member_id.strip(),
        "start_date": start_date.strip(),
        "status": status.strip(),
        "review_status": review_status.strip(),
        "next_action": next_action.strip(),
        "due_date": due_date.strip(),
        "blocker_reason": blocker_reason.strip(),
        "help_needed_from": help_needed_from.strip(),
        "updated_at": updated_at.strip(),
    }
    errors = validate_progress_record(row)
    if errors:
        raise ValueError(" ".join(errors))
    output["Milestones"] = _append_row(output["Milestones"], row, REQUIRED_COLUMNS["Milestones"])
    return output


def import_projects_from_frame(ledger: dict[str, pd.DataFrame], frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    output = {name: table.copy() for name, table in ledger.items()}
    required = ["project", "aim", "owner_member_id", "start_date"]
    for _, raw in frame.fillna("").iterrows():
        row = {column: str(raw.get(column, "")).strip() for column in REQUIRED_COLUMNS["Projects"]}
        if not any(row.values()):
            continue
        missing = [column for column in required if not row.get(column)]
        if missing:
            raise ValueError(f"Projects import row is missing required columns: {', '.join(missing)}")
        row["project_id"] = row.get("project_id") or _next_identifier(output["Projects"], "project_id", "P")
        output["Projects"] = _append_row(output["Projects"], row, REQUIRED_COLUMNS["Projects"])
    return output


def import_milestones_from_frame(ledger: dict[str, pd.DataFrame], frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    output = {name: table.copy() for name, table in ledger.items()}
    required = ["project", "aim", "milestone", "owner_member_id", "start_date", "status", "review_status", "next_action", "due_date"]
    for _, raw in frame.fillna("").iterrows():
        row = {column: str(raw.get(column, "")).strip() for column in REQUIRED_COLUMNS["Milestones"]}
        if not any(row.values()):
            continue
        missing = [column for column in required if not row.get(column)]
        if missing:
            raise ValueError(f"Milestones import row is missing required columns: {', '.join(missing)}")
        row["milestone_id"] = row.get("milestone_id") or _next_identifier(output["Milestones"], "milestone_id", "MS")
        if not row.get("project_id"):
            project_match = output["Projects"].loc[output["Projects"]["project"] == row["project"]]
            if not project_match.empty:
                row["project_id"] = str(project_match.iloc[0]["project_id"])
        output["Milestones"] = _append_row(output["Milestones"], row, REQUIRED_COLUMNS["Milestones"])
    return output


def _normalize_table_frame(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    normalized = frame.copy()
    normalized.columns = [str(column).strip() for column in normalized.columns]
    for column in columns:
        if column not in normalized.columns:
            normalized[column] = ""
    return normalized[columns].copy()


def import_from_excel_bytes(ledger: dict[str, pd.DataFrame], blob: bytes) -> dict[str, pd.DataFrame]:
    sheets = pd.read_excel(BytesIO(blob), sheet_name=None, dtype=str)
    output = {name: table.copy() for name, table in ledger.items()}
    if "Projects" in sheets:
        output = import_projects_from_frame(output, _normalize_table_frame(sheets["Projects"], REQUIRED_COLUMNS["Projects"]))
    if "Milestones" in sheets:
        output = import_milestones_from_frame(output, _normalize_table_frame(sheets["Milestones"], REQUIRED_COLUMNS["Milestones"]))
    return output


def import_from_docx_bytes(ledger: dict[str, pd.DataFrame], blob: bytes) -> dict[str, pd.DataFrame]:
    from docx import Document

    document = Document(BytesIO(blob))
    output = {name: table.copy() for name, table in ledger.items()}
    for table in document.tables:
        headers = [cell.text.strip() for cell in table.rows[0].cells]
        if not headers:
            continue
        header_set = set(headers)
        frame = pd.DataFrame([[cell.text.strip() for cell in row.cells] for row in table.rows[1:]], columns=headers)
        if {"project", "aim", "owner_member_id", "start_date"}.issubset(header_set):
            output = import_projects_from_frame(output, _normalize_table_frame(frame, REQUIRED_COLUMNS["Projects"]))
            continue
        if {"milestone", "owner_member_id", "status", "review_status", "next_action", "due_date"}.issubset(header_set):
            output = import_milestones_from_frame(output, _normalize_table_frame(frame, REQUIRED_COLUMNS["Milestones"]))
    return output


def update_progress_record(
    ledger: dict[str, pd.DataFrame],
    *,
    table_name: str,
    record_id_column: str,
    record_id: str,
    updated_by: str,
    changes: dict[str, object],
    update_note: str,
    timestamp: str,
) -> dict[str, pd.DataFrame]:
    output = {name: frame.copy() for name, frame in ledger.items()}
    table = output[table_name].copy()
    mask = table[record_id_column] == record_id
    if not mask.any():
        raise ValueError(f"{table_name} record not found: {record_id}")

    index = table.index[mask][0]
    old_status = str(table.at[index, "status"])
    for key, value in changes.items():
        table.at[index, key] = "" if value is None else str(value)
    table.at[index, "review_status"] = "Pending"
    table.at[index, "updated_at"] = timestamp

    errors = validate_progress_record(table.loc[index].to_dict())
    if errors:
        raise ValueError(" ".join(errors))

    output[table_name] = table
    _append_history(
        output,
        record_type=table_name[:-1],
        record_id=record_id,
        updated_by=updated_by,
        update_note=update_note,
        old_status=old_status,
        new_status=str(table.at[index, "status"]),
        review_status="Pending",
        timestamp=timestamp,
    )
    return output


def review_record(
    ledger: dict[str, pd.DataFrame],
    *,
    table_name: str,
    record_id_column: str,
    record_id: str,
    reviewed_by: str,
    review_status: str,
    review_note: str,
    timestamp: str,
) -> dict[str, pd.DataFrame]:
    output = {name: frame.copy() for name, frame in ledger.items()}
    table = output[table_name].copy()
    mask = table[record_id_column] == record_id
    if not mask.any():
        raise ValueError(f"{table_name} record not found: {record_id}")

    errors = validate_review({"review_status": review_status, "review_note": review_note})
    if errors:
        raise ValueError(" ".join(errors))

    index = table.index[mask][0]
    table.at[index, "review_status"] = review_status
    table.at[index, "updated_at"] = timestamp
    output[table_name] = table
    _append_history(
        output,
        record_type=table_name[:-1],
        record_id=record_id,
        reviewed_by=reviewed_by,
        review_status=review_status,
        review_note=review_note,
        timestamp=timestamp,
    )
    return output
