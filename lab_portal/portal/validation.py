from __future__ import annotations

from .constants import APP_ROLES, PORTAL_ROLES, TABLES
from .schema import REQUIRED_COLUMNS
from .storage import Registry


def _active_values(frame):
    return frame["active"].astype(str).str.upper().isin(["TRUE", "1", "YES", "Y"])


def validate_registry(registry: Registry) -> list[str]:
    errors: list[str] = []

    for table_name in TABLES:
        if table_name not in registry:
            errors.append(f"Missing registry table: {table_name}")
            continue
        missing = [column for column in REQUIRED_COLUMNS[table_name] if column not in registry[table_name].columns]
        for column in missing:
            errors.append(f"{table_name} missing required column {column}")

    if errors:
        return errors

    members = registry["Members"].fillna("")
    active_members = members[_active_values(members)]
    duplicate_emails = active_members["email"][active_members["email"].duplicated()].tolist()
    for email in sorted(set(duplicate_emails)):
        errors.append(f"Duplicate active member email: {email}")

    for _, row in active_members.iterrows():
        if row["global_role"] not in PORTAL_ROLES:
            errors.append(f"Members {row['member_id']} has invalid global_role {row['global_role']}")

    member_ids = set(members["member_id"])
    teams = registry["Teams"].fillna("")
    team_ids = set(teams["team_id"])
    apps = registry["Apps"].fillna("")
    app_ids = set(apps["app_id"])

    for _, row in registry["Member_Teams"].fillna("").iterrows():
        if row["member_id"] not in member_ids:
            errors.append(f"Member_Teams {row['member_team_id']} references unknown member_id {row['member_id']}")
        if row["team_id"] not in team_ids:
            errors.append(f"Member_Teams {row['member_team_id']} references unknown team_id {row['team_id']}")

    for _, row in registry["App_Roles"].fillna("").iterrows():
        if row["member_id"] not in member_ids:
            errors.append(f"App_Roles {row['app_role_id']} references unknown member_id {row['member_id']}")
        if row["app_id"] not in app_ids:
            errors.append(f"App_Roles {row['app_role_id']} references unknown app_id {row['app_id']}")
        if row["scope_team_id"] and row["scope_team_id"] not in team_ids:
            errors.append(f"App_Roles {row['app_role_id']} references unknown scope_team_id {row['scope_team_id']}")
        if row["app_role"] not in APP_ROLES:
            errors.append(f"App_Roles {row['app_role_id']} has invalid app_role {row['app_role']}")

    return errors
