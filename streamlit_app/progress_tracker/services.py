from __future__ import annotations

import uuid

import pandas as pd

from .validation import validate_progress_record, validate_review


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
        table.at[index, key] = str(value)
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
