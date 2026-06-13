from __future__ import annotations

from collections import defaultdict

from .constants import ADMIN_ROLES
from .storage import Registry


def is_active(value: object) -> bool:
    return str(value).strip().upper() in {"TRUE", "1", "YES", "Y"}


def resolve_member_by_email(registry: Registry, email: str) -> dict[str, str] | None:
    members = registry["Members"].fillna("")
    normalized_email = str(email).strip().lower()
    matches = members[members["email"].astype(str).str.strip().str.lower() == normalized_email]
    active_matches = []
    for _, row in matches.iterrows():
        record = row.to_dict()
        if is_active(record.get("active", "")):
            active_matches.append({key: str(value) for key, value in record.items()})
    return active_matches[0] if len(active_matches) == 1 else None


def can_admin_portal(member: dict[str, str] | None) -> bool:
    if not member:
        return False
    return member.get("global_role") in ADMIN_ROLES


def resolve_app_roles(registry: Registry, member_id: str) -> dict[str, list[dict[str, str]]]:
    roles_by_app: dict[str, list[dict[str, str]]] = defaultdict(list)
    app_roles = registry["App_Roles"].fillna("")
    active_roles = app_roles[app_roles["active"].map(is_active)]
    for _, row in active_roles[active_roles["member_id"] == member_id].iterrows():
        roles_by_app[row["app_id"]].append({"role": row["app_role"], "scope_team_id": row["scope_team_id"]})
    return dict(roles_by_app)
