from __future__ import annotations

import json
from datetime import UTC, datetime
from urllib.parse import urlparse

import pandas as pd

from .constants import APP_ROLES, PORTAL_ROLES
from .permissions import is_active
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
    team_ids: list[str] | None = None,
    team_role: str = "member",
    app_ids: list[str] | None = None,
    app_role: str = "viewer",
) -> Registry:
    updated = {table: frame.copy() for table, frame in registry.items()}
    members = updated["Members"]
    if global_role not in PORTAL_ROLES:
        raise ValueError(f"Invalid global_role {global_role}")
    normalized_email = email.strip().lower()
    active_emails = members[members["active"].map(is_active)]["email"].astype(str).str.strip().str.lower()
    if normalized_email in set(active_emails):
        raise ValueError(f"Duplicate active member email {normalized_email}")
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
    updated = _append_audit(
        updated,
        actor_email=actor_email,
        action="member.add",
        target_type="Members",
        target_id=row["member_id"],
        before=None,
        after=row,
    )
    for team_id in team_ids or []:
        updated = assign_member_to_team(
            updated,
            actor_email=actor_email,
            member_id=row["member_id"],
            team_id=team_id,
            team_role=team_role,
            start_date=start_date,
        )
    for app_id in app_ids or []:
        updated = grant_app_role(
            updated,
            actor_email=actor_email,
            member_id=row["member_id"],
            app_id=app_id,
            app_role=app_role,
            scope_team_id="",
            start_date=start_date,
        )
    return updated


def assign_member_to_team(
    registry: Registry,
    *,
    actor_email: str,
    member_id: str,
    team_id: str,
    team_role: str,
    start_date: str,
) -> Registry:
    updated = {table: frame.copy() for table, frame in registry.items()}
    member_teams = updated["Member_Teams"]
    members = updated["Members"]
    teams = updated["Teams"]
    member_mask = members["member_id"] == member_id
    if not member_mask.any():
        raise ValueError(f"Unknown member_id {member_id}")
    if member_mask.sum() > 1:
        raise ValueError(f"Duplicate member_id {member_id}")
    if not is_active(members.loc[member_mask].iloc[0]["active"]):
        raise ValueError(f"Inactive member_id {member_id}")
    team_mask = teams["team_id"] == team_id
    if not team_mask.any():
        raise ValueError(f"Unknown team_id {team_id}")
    if team_mask.sum() > 1:
        raise ValueError(f"Duplicate team_id {team_id}")
    if not is_active(teams.loc[team_mask].iloc[0]["active"]):
        raise ValueError(f"Inactive team_id {team_id}")
    duplicate_mask = (
        (member_teams["member_id"] == member_id)
        & (member_teams["team_id"] == team_id)
        & member_teams["active"].map(is_active)
    )
    if duplicate_mask.any():
        raise ValueError(f"Duplicate active member_team {member_id} {team_id}")
    row = {
        "member_team_id": _next_id(member_teams, "member_team_id", "MT"),
        "member_id": member_id,
        "team_id": team_id,
        "team_role": team_role.strip() or "member",
        "active": "TRUE",
        "start_date": start_date,
        "end_date": "",
    }
    updated["Member_Teams"] = pd.concat([member_teams, pd.DataFrame([row])], ignore_index=True)
    return _append_audit(
        updated,
        actor_email=actor_email,
        action="member_team.assign",
        target_type="Member_Teams",
        target_id=row["member_team_id"],
        before=None,
        after=row,
    )


def deactivate_member(registry: Registry, *, actor_email: str, member_id: str, end_date: str) -> Registry:
    updated = {table: frame.copy() for table, frame in registry.items()}
    members = updated["Members"].copy()
    mask = members["member_id"] == member_id
    if not mask.any():
        raise ValueError(f"Unknown member_id {member_id}")
    if mask.sum() > 1:
        raise ValueError(f"Duplicate member_id {member_id}")
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
    members = updated["Members"]
    app_ids = {value for value in updated["Apps"]["app_id"] if str(value).strip()}
    team_ids = {value for value in updated["Teams"]["team_id"] if str(value).strip()}
    member_mask = members["member_id"] == member_id
    if not member_mask.any():
        raise ValueError(f"Unknown member_id {member_id}")
    if member_mask.sum() > 1:
        raise ValueError(f"Duplicate member_id {member_id}")
    if not is_active(members.loc[member_mask].iloc[0]["active"]):
        raise ValueError(f"Inactive member_id {member_id}")
    if app_id not in app_ids:
        raise ValueError(f"Unknown app_id {app_id}")
    if scope_team_id and scope_team_id not in team_ids:
        raise ValueError(f"Unknown scope_team_id {scope_team_id}")
    if app_role not in APP_ROLES:
        raise ValueError(f"Invalid app_role {app_role}")
    duplicate_mask = (
        (app_roles["member_id"] == member_id)
        & (app_roles["app_id"] == app_id)
        & (app_roles["app_role"] == app_role)
        & (app_roles["scope_team_id"] == scope_team_id)
        & app_roles["active"].map(is_active)
    )
    if duplicate_mask.any():
        raise ValueError(f"Duplicate active app_role {member_id} {app_id} {app_role}")
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


def add_team(registry: Registry, *, actor_email: str, team_name: str, description: str) -> Registry:
    updated = {table: frame.copy() for table, frame in registry.items()}
    teams = updated["Teams"]
    normalized_name = team_name.strip()
    if not normalized_name:
        raise ValueError("team_name is required")
    active_team_names = teams[teams["active"].map(is_active)]["team_name"].astype(str).str.strip().str.lower()
    if normalized_name.lower() in set(active_team_names):
        raise ValueError(f"Duplicate active team_name {normalized_name.lower()}")
    row = {
        "team_id": _next_id(teams, "team_id", "T"),
        "team_name": normalized_name,
        "description": description,
        "active": "TRUE",
    }
    updated["Teams"] = pd.concat([teams, pd.DataFrame([row])], ignore_index=True)
    return _append_audit(
        updated,
        actor_email=actor_email,
        action="team.add",
        target_type="Teams",
        target_id=row["team_id"],
        before=None,
        after=row,
    )


def update_app_url(
    registry: Registry,
    *,
    actor_email: str,
    app_id: str,
    app_url: str,
    active: str,
) -> Registry:
    updated = {table: frame.copy() for table, frame in registry.items()}
    apps = updated["Apps"].copy()
    normalized_active = active.strip().upper()
    normalized_url = app_url.strip()
    mask = apps["app_id"] == app_id
    if not mask.any():
        raise ValueError(f"Unknown app_id {app_id}")
    if mask.sum() > 1:
        raise ValueError(f"Duplicate app_id {app_id}")
    if normalized_active not in {"TRUE", "FALSE"}:
        raise ValueError(f"Invalid active {active}")
    if normalized_url:
        parsed_url = urlparse(normalized_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise ValueError("app_url must start with http:// or https://")
    before = apps.loc[mask].iloc[0].to_dict()
    apps.loc[mask, "app_url"] = normalized_url
    apps.loc[mask, "active"] = normalized_active
    after = apps.loc[mask].iloc[0].to_dict()
    updated["Apps"] = apps
    return _append_audit(
        updated,
        actor_email=actor_email,
        action="app.update_url",
        target_type="Apps",
        target_id=app_id,
        before=before,
        after=after,
    )
