from __future__ import annotations

import pandas as pd

from .constants import TABLES


REQUIRED_COLUMNS = {
    "Members": [
        "member_id",
        "email",
        "name",
        "display_name",
        "global_role",
        "active",
        "start_date",
        "end_date",
        "password_hash",
        "password_set_at",
        "password_must_change",
        "notes",
    ],
    "Teams": ["team_id", "team_name", "description", "active"],
    "Member_Teams": [
        "member_team_id",
        "member_id",
        "team_id",
        "team_role",
        "active",
        "start_date",
        "end_date",
    ],
    "Apps": ["app_id", "app_name", "app_url", "description", "category", "active", "sort_order"],
    "App_Roles": [
        "app_role_id",
        "member_id",
        "app_id",
        "app_role",
        "scope_team_id",
        "active",
        "start_date",
        "end_date",
    ],
    "Audit_Log": ["audit_id", "timestamp", "actor_email", "action", "target_type", "target_id", "before", "after"],
}


def empty_registry() -> dict[str, pd.DataFrame]:
    return {table_name: pd.DataFrame(columns=REQUIRED_COLUMNS[table_name]) for table_name in TABLES}
