from __future__ import annotations

import pandas as pd

from .constants import TABLES


REQUIRED_COLUMNS = {
    "Members": ["member_id", "name", "email", "role", "team", "lead_id", "active"],
    "Projects": [
        "project_id",
        "project",
        "aim",
        "owner_member_id",
        "start_date",
        "target_date",
        "notes",
    ],
    "Milestones": [
        "milestone_id",
        "project_id",
        "project",
        "aim",
        "milestone",
        "time_window",
        "owner_member_id",
        "status",
        "review_status",
        "next_action",
        "due_date",
        "blocker_reason",
        "help_needed_from",
        "updated_at",
    ],
    "Experiments": [
        "experiment_id",
        "milestone_id",
        "project_id",
        "member_id",
        "experiment_title",
        "experiment_type",
        "status",
        "review_status",
        "next_action",
        "due_date",
        "experiment_data_link",
        "protocol_link",
        "analysis_folder_link",
        "blocker_reason",
        "help_needed_from",
        "updated_at",
    ],
    "Updates_Reviews": [
        "update_id",
        "record_type",
        "record_id",
        "updated_by",
        "update_note",
        "old_status",
        "new_status",
        "reviewed_by",
        "review_status",
        "review_note",
        "timestamp",
    ],
}


def empty_ledger() -> dict[str, pd.DataFrame]:
    return {table_name: pd.DataFrame(columns=REQUIRED_COLUMNS[table_name]) for table_name in TABLES}
