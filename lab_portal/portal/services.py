from __future__ import annotations

import base64
import hashlib
import json
import secrets
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


def _password_hash(password: str) -> str:
    normalized_password = str(password)
    if len(normalized_password) < 8:
        raise ValueError("password must be at least 8 characters")
    iterations = 200_000
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", normalized_password.encode("utf-8"), salt, iterations)
    return "pbkdf2_sha256${}${}${}".format(
        iterations,
        base64.urlsafe_b64encode(salt).decode("ascii").rstrip("="),
        base64.urlsafe_b64encode(digest).decode("ascii").rstrip("="),
    )


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
        "before": json.dumps(_redact_sensitive_fields(before), sort_keys=True),
        "after": json.dumps(_redact_sensitive_fields(after), sort_keys=True),
    }
    updated["Audit_Log"] = pd.concat([audit, pd.DataFrame([row])], ignore_index=True)
    return updated


def _redact_sensitive_fields(record: dict[str, str] | None) -> dict[str, str]:
    redacted = dict(record or {})
    for key in ("password_hash",):
        if key in redacted:
            redacted[key] = "<redacted>"
    return redacted


def add_member(
    registry: Registry,
    *,
    actor_email: str,
    email: str,
    name: str,
    display_name: str,
    global_role: str,
    start_date: str,
    password: str,
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
    if not normalized_email:
        raise ValueError("email is required")
    active_emails = members[members["active"].map(is_active)]["email"].astype(str).str.strip().str.lower()
    if normalized_email in set(active_emails):
        raise ValueError(f"Duplicate active member email {normalized_email}")
    row = {
        "member_id": _next_id(members, "member_id", "M"),
        "email": normalized_email,
        "name": name.strip(),
        "display_name": display_name.strip() or name.strip(),
        "global_role": global_role,
        "active": "TRUE",
        "start_date": start_date,
        "end_date": "",
        "password_hash": _password_hash(password),
        "password_set_at": _now_iso(),
        "password_must_change": "TRUE",
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


def update_member(
    registry: Registry,
    *,
    actor_email: str,
    member_id: str,
    email: str,
    name: str,
    display_name: str,
    global_role: str,
    active: str,
    start_date: str,
    end_date: str,
    notes: str,
    password: str = "",
    password_must_change: str = "TRUE",
) -> Registry:
    updated = {table: frame.copy() for table, frame in registry.items()}
    members = updated["Members"].copy()
    mask = members["member_id"] == member_id
    if not mask.any():
        raise ValueError(f"Unknown member_id {member_id}")
    if mask.sum() > 1:
        raise ValueError(f"Duplicate member_id {member_id}")
    if global_role not in PORTAL_ROLES:
        raise ValueError(f"Invalid global_role {global_role}")
    normalized_active = active.strip().upper()
    if normalized_active not in {"TRUE", "FALSE"}:
        raise ValueError(f"Invalid active {active}")
    normalized_password_must_change = password_must_change.strip().upper()
    if normalized_password_must_change not in {"TRUE", "FALSE"}:
        raise ValueError(f"Invalid password_must_change {password_must_change}")
    normalized_email = email.strip().lower()
    if not normalized_email:
        raise ValueError("email is required")
    duplicate_mask = (
        (members["member_id"] != member_id)
        & members["active"].map(is_active)
        & (members["email"].astype(str).str.strip().str.lower() == normalized_email)
    )
    if duplicate_mask.any():
        raise ValueError(f"Duplicate active member email {normalized_email}")

    before = members.loc[mask].iloc[0].to_dict()
    members.loc[mask, "email"] = normalized_email
    members.loc[mask, "name"] = name.strip()
    members.loc[mask, "display_name"] = display_name.strip() or name.strip()
    members.loc[mask, "global_role"] = global_role
    members.loc[mask, "active"] = normalized_active
    members.loc[mask, "start_date"] = start_date
    members.loc[mask, "end_date"] = end_date if normalized_active == "FALSE" else ""
    members.loc[mask, "password_must_change"] = normalized_password_must_change
    members.loc[mask, "notes"] = notes
    if password:
        members.loc[mask, "password_hash"] = _password_hash(password)
        members.loc[mask, "password_set_at"] = _now_iso()
        members.loc[mask, "password_must_change"] = "TRUE"
    after = members.loc[mask].iloc[0].to_dict()
    updated["Members"] = members
    return _append_audit(
        updated,
        actor_email=actor_email,
        action="member.update",
        target_type="Members",
        target_id=member_id,
        before=before,
        after=after,
    )


def set_member_relationships(
    registry: Registry,
    *,
    actor_email: str,
    member_id: str,
    team_ids: list[str],
    team_role: str,
    app_roles: dict[str, str],
    start_date: str,
    end_date: str = "",
) -> Registry:
    updated = {table: frame.copy() for table, frame in registry.items()}
    _validate_active_member(updated, member_id)
    team_ids = [team_id for team_id in dict.fromkeys(team_ids) if str(team_id).strip()]
    app_roles = {app_id: role for app_id, role in app_roles.items() if str(app_id).strip()}

    for team_id in team_ids:
        _validate_active_team(updated, team_id)
    for app_id, app_role in app_roles.items():
        if app_role:
            _validate_app_role_input(updated, app_id, app_role, "")

    updated = _set_member_team_rows(
        updated,
        actor_email=actor_email,
        member_id=member_id,
        team_ids=team_ids,
        team_role=team_role,
        start_date=start_date,
        end_date=end_date,
    )
    updated = _set_member_app_role_rows(
        updated,
        actor_email=actor_email,
        member_id=member_id,
        app_roles=app_roles,
        start_date=start_date,
        end_date=end_date,
    )
    return updated


def _validate_active_member(registry: Registry, member_id: str) -> None:
    members = registry["Members"]
    member_mask = members["member_id"] == member_id
    if not member_mask.any():
        raise ValueError(f"Unknown member_id {member_id}")
    if member_mask.sum() > 1:
        raise ValueError(f"Duplicate member_id {member_id}")
    if not is_active(members.loc[member_mask].iloc[0]["active"]):
        raise ValueError(f"Inactive member_id {member_id}")


def _validate_active_team(registry: Registry, team_id: str) -> None:
    teams = registry["Teams"]
    team_mask = teams["team_id"] == team_id
    if not team_mask.any():
        raise ValueError(f"Unknown team_id {team_id}")
    if team_mask.sum() > 1:
        raise ValueError(f"Duplicate team_id {team_id}")
    if not is_active(teams.loc[team_mask].iloc[0]["active"]):
        raise ValueError(f"Inactive team_id {team_id}")


def _validate_app_role_input(registry: Registry, app_id: str, app_role: str, scope_team_id: str) -> None:
    app_ids = {value for value in registry["Apps"]["app_id"] if str(value).strip()}
    team_ids = {value for value in registry["Teams"]["team_id"] if str(value).strip()}
    if app_id not in app_ids:
        raise ValueError(f"Unknown app_id {app_id}")
    if scope_team_id and scope_team_id not in team_ids:
        raise ValueError(f"Unknown scope_team_id {scope_team_id}")
    if app_role not in APP_ROLES:
        raise ValueError(f"Invalid app_role {app_role}")


def _set_member_team_rows(
    registry: Registry,
    *,
    actor_email: str,
    member_id: str,
    team_ids: list[str],
    team_role: str,
    start_date: str,
    end_date: str,
) -> Registry:
    updated = {table: frame.copy() for table, frame in registry.items()}
    desired_team_ids = set(team_ids)
    member_teams = updated["Member_Teams"].copy()
    active_mask = (member_teams["member_id"] == member_id) & member_teams["active"].map(is_active)
    for index, row in member_teams[active_mask].iterrows():
        if row["team_id"] in desired_team_ids:
            continue
        before = row.to_dict()
        member_teams.loc[index, "active"] = "FALSE"
        member_teams.loc[index, "end_date"] = end_date or start_date
        after = member_teams.loc[index].to_dict()
        updated["Member_Teams"] = member_teams
        updated = _append_audit(
            updated,
            actor_email=actor_email,
            action="member_team.deactivate",
            target_type="Member_Teams",
            target_id=after["member_team_id"],
            before=before,
            after=after,
        )
        member_teams = updated["Member_Teams"].copy()

    active_member_team_ids = set(
        member_teams[
            (member_teams["member_id"] == member_id)
            & member_teams["active"].map(is_active)
        ]["team_id"].astype(str)
    )
    for team_id in team_ids:
        if team_id not in active_member_team_ids:
            updated = assign_member_to_team(
                updated,
                actor_email=actor_email,
                member_id=member_id,
                team_id=team_id,
                team_role=team_role,
                start_date=start_date,
            )
    return updated


def _set_member_app_role_rows(
    registry: Registry,
    *,
    actor_email: str,
    member_id: str,
    app_roles: dict[str, str],
    start_date: str,
    end_date: str,
) -> Registry:
    updated = {table: frame.copy() for table, frame in registry.items()}
    app_role_rows = updated["App_Roles"].copy()
    managed_app_ids = set(app_roles)
    active_mask = (app_role_rows["member_id"] == member_id) & app_role_rows["active"].map(is_active)
    for index, row in app_role_rows[active_mask].iterrows():
        app_id = str(row["app_id"])
        if app_id not in managed_app_ids:
            continue
        desired_role = app_roles.get(app_id, "")
        keep_row = desired_role and row["app_role"] == desired_role and str(row.get("scope_team_id", "")) == ""
        if keep_row:
            continue
        before = row.to_dict()
        app_role_rows.loc[index, "active"] = "FALSE"
        app_role_rows.loc[index, "end_date"] = end_date or start_date
        after = app_role_rows.loc[index].to_dict()
        updated["App_Roles"] = app_role_rows
        updated = _append_audit(
            updated,
            actor_email=actor_email,
            action="app_role.deactivate",
            target_type="App_Roles",
            target_id=after["app_role_id"],
            before=before,
            after=after,
        )
        app_role_rows = updated["App_Roles"].copy()

    active_roles = app_role_rows[(app_role_rows["member_id"] == member_id) & app_role_rows["active"].map(is_active)]
    for app_id, app_role in app_roles.items():
        if not app_role:
            continue
        matching = active_roles[
            (active_roles["app_id"] == app_id)
            & (active_roles["app_role"] == app_role)
            & (active_roles["scope_team_id"].astype(str) == "")
        ]
        if matching.empty:
            updated = grant_app_role(
                updated,
                actor_email=actor_email,
                member_id=member_id,
                app_id=app_id,
                app_role=app_role,
                scope_team_id="",
                start_date=start_date,
            )
            app_role_rows = updated["App_Roles"].copy()
            active_roles = app_role_rows[(app_role_rows["member_id"] == member_id) & app_role_rows["active"].map(is_active)]
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
