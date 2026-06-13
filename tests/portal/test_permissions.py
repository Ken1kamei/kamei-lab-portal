from pathlib import Path

import pandas as pd

from lab_portal.portal.permissions import can_admin_portal, resolve_app_roles, resolve_member_by_email
from lab_portal.portal.storage import CsvRegistryStore


def test_resolve_member_by_email_returns_active_member():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    member = resolve_member_by_email(registry, "kkamei@nyu.edu")

    assert member["member_id"] == "M001"
    assert member["global_role"] == "pi"


def test_resolve_member_by_email_strips_and_normalizes_case():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    member = resolve_member_by_email(registry, " KKAMEI@NYU.EDU ")

    assert member["member_id"] == "M001"


def test_resolve_member_by_email_rejects_inactive_member():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()
    registry["Members"].loc[0, "active"] = "FALSE"

    assert resolve_member_by_email(registry, "kkamei@nyu.edu") is None


def test_resolve_member_by_email_rejects_duplicate_active_members():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()
    duplicate = registry["Members"].iloc[[0]].copy()
    duplicate.loc[duplicate.index[0], "member_id"] = "M999"
    registry["Members"] = pd.concat([registry["Members"], duplicate], ignore_index=True)

    assert resolve_member_by_email(registry, "kkamei@nyu.edu") is None


def test_can_admin_portal_for_pi_and_admin_only():
    assert can_admin_portal({"global_role": "pi"})
    assert can_admin_portal({"global_role": "admin"})
    assert not can_admin_portal({"global_role": "lead"})
    assert not can_admin_portal({"global_role": "member"})


def test_resolve_app_roles_returns_active_roles_for_member():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    roles = resolve_app_roles(registry, "M001")

    assert roles["budget"] == [{"role": "owner", "scope_team_id": ""}]
    assert roles["project_tracker"] == [{"role": "owner", "scope_team_id": ""}]
