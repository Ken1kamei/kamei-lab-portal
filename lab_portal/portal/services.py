from __future__ import annotations

import json
from datetime import UTC, datetime

import pandas as pd

from .constants import APP_ROLES
from .storage import Registry


def _next_id(frame: pd.DataFrame, column: str, prefix: str) -> str:
    values = frame[column].astype(str).tolist() if column in frame else []
    numbers = []
    for value in values:
        if value.startswith(prefix):
            suffix = value.removeprefix(prefix)
            if suffix.isdigit():
                numbers.append(int(suffix))
    return f"{prefix}{max(numbers, default=0) + 1:03d}"


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _append_audit(
    registry: Registry,
    *,
    actor_email: str,
    action: str,
    target_type: str,
    target_id: str,
    before: dict[str, str] | None,
    after: dict[str, str] | None,
) -> Registry:
    updated = {name: frame.copy() for name, frame in registry.items()}
    audit = updated["Audit_Log"]
    row = {
        "audit_id": _next_id(audit, "audit_id", "AU"),
        "timestamp": _now_iso(),
        "actor_email": actor_email,
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "before": json.dumps(before or {}, sort_keys=True),
        "after": json.dumps(after or {}, sort_keys=True),
    }
    updated["Audit_Log"] = pd.concat([audit, pd.DataFrame([row])], ignore_index=True)
    return updated


def add_member(
    registry: Registry,
    *,
    actor_email: str,
    email: str,
    name: str,
    display_name: str,
    global_role: str,
    start_date: str,
    notes: str,
) -> Registry:
    updated = {table: frame.copy() for table, frame in registry.items()}
    members = updated["Members"]
    row = {
        "member_id": _next_id(members, "member_id", "M"),
        "email": email,
        "name": name,
        "display_name": display_name,
        "global_role": global_role,
        "active": "TRUE",
        "start_date": start_date,
        "end_date": "",
        "notes": notes,
    }
    updated["Members"] = pd.concat([members, pd.DataFrame([row])], ignore_index=True)
    return _append_audit(
        updated,
        actor_email=actor_email,
        action="member.add",
        target_type="Members",
        target_id=row["member_id"],
        before=None,
        after=row,
    )


def deactivate_member(registry: Registry, *, actor_email: str, member_id: str, end_date: str) -> Registry:
    updated = {table: frame.copy() for table, frame in registry.items()}
    members = updated["Members"].copy()
    mask = members["member_id"] == member_id
    if not mask.any():
        raise ValueError(f"Unknown member_id {member_id}")
    before = members.loc[mask].iloc[0].to_dict()
    members.loc[mask, "active"] = "FALSE"
    members.loc[mask, "end_date"] = end_date
    after = members.loc[mask].iloc[0].to_dict()
    updated["Members"] = members
    return _append_audit(
        updated,
        actor_email=actor_email,
        action="member.deactivate",
        target_type="Members",
        target_id=member_id,
        before=before,
        after=after,
    )


def grant_app_role(
    registry: Registry,
    *,
    actor_email: str,
    member_id: str,
    app_id: str,
    app_role: str,
    scope_team_id: str,
    start_date: str,
) -> Registry:
    updated = {table: frame.copy() for table, frame in registry.items()}
    app_roles = updated["App_Roles"]
    if member_id not in set(updated["Members"]["member_id"]):
        raise ValueError(f"Unknown member_id {member_id}")
    if app_id not in set(updated["Apps"]["app_id"]):
        raise ValueError(f"Unknown app_id {app_id}")
    if scope_team_id and scope_team_id not in set(updated["Teams"]["team_id"]):
        raise ValueError(f"Unknown scope_team_id {scope_team_id}")
    if app_role not in APP_ROLES:
        raise ValueError(f"Invalid app_role {app_role}")
    row = {
        "app_role_id": _next_id(app_roles, "app_role_id", "AR"),
        "member_id": member_id,
        "app_id": app_id,
        "app_role": app_role,
        "scope_team_id": scope_team_id,
        "active": "TRUE",
        "start_date": start_date,
        "end_date": "",
    }
    updated["App_Roles"] = pd.concat([app_roles, pd.DataFrame([row])], ignore_index=True)
    return _append_audit(
        updated,
        actor_email=actor_email,
        action="app_role.grant",
        target_type="App_Roles",
        target_id=row["app_role_id"],
        before=None,
        after=row,
    )
