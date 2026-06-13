from pathlib import Path

import json

import pandas as pd
import pytest

from lab_portal.portal.services import add_member, deactivate_member, grant_app_role
from lab_portal.portal.storage import CsvRegistryStore


def test_add_member_appends_member_and_audit_record():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    updated = add_member(
        registry,
        actor_email="kkamei@nyu.edu",
        email="new.member@example.edu",
        name="New Member",
        display_name="New Member",
        global_role="member",
        start_date="2026-06-13",
        notes="Joined portal pilot",
    )

    assert "new.member@example.edu" in set(updated["Members"]["email"])
    assert updated["Audit_Log"].iloc[-1]["action"] == "member.add"
    assert updated["Audit_Log"].iloc[-1]["actor_email"] == "kkamei@nyu.edu"
    assert "new.member@example.edu" not in set(registry["Members"]["email"])
    assert json.loads(updated["Audit_Log"].iloc[-1]["after"])["email"] == "new.member@example.edu"


def test_add_member_reports_invalid_global_role():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    with pytest.raises(ValueError, match="Invalid global_role invalid_role"):
        add_member(
            registry,
            actor_email="kkamei@nyu.edu",
            email="new.member@example.edu",
            name="New Member",
            display_name="New Member",
            global_role="invalid_role",
            start_date="2026-06-13",
            notes="Joined portal pilot",
        )


def test_add_member_reports_duplicate_active_email():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    with pytest.raises(ValueError, match="Duplicate active member email kkamei@nyu.edu"):
        add_member(
            registry,
            actor_email="kkamei@nyu.edu",
            email=" KKAMEI@NYU.EDU ",
            name="Duplicate Member",
            display_name="Duplicate Member",
            global_role="member",
            start_date="2026-06-13",
            notes="Duplicate",
        )


def test_deactivate_member_keeps_row_and_appends_audit_record():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    updated = deactivate_member(registry, actor_email="kkamei@nyu.edu", member_id="M003", end_date="2026-06-30")

    member = updated["Members"].set_index("member_id").loc["M003"]
    assert member["active"] == "FALSE"
    assert member["end_date"] == "2026-06-30"
    assert updated["Audit_Log"].iloc[-1]["action"] == "member.deactivate"
    assert registry["Members"].set_index("member_id").loc["M003", "active"] == "TRUE"
    assert json.loads(updated["Audit_Log"].iloc[-1]["before"])["active"] == "TRUE"
    assert json.loads(updated["Audit_Log"].iloc[-1]["after"])["active"] == "FALSE"


def test_deactivate_member_reports_unknown_member_id():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    with pytest.raises(ValueError, match="Unknown member_id M999"):
        deactivate_member(registry, actor_email="kkamei@nyu.edu", member_id="M999", end_date="2026-06-30")


def test_deactivate_member_reports_duplicate_member_id():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()
    duplicate = registry["Members"].iloc[[2]].copy()
    registry["Members"] = pd.concat([registry["Members"], duplicate], ignore_index=True)

    with pytest.raises(ValueError, match="Duplicate member_id M003"):
        deactivate_member(registry, actor_email="kkamei@nyu.edu", member_id="M003", end_date="2026-06-30")


def test_grant_app_role_adds_role_and_audit_record():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    updated = grant_app_role(
        registry,
        actor_email="kkamei@nyu.edu",
        member_id="M003",
        app_id="budget",
        app_role="viewer",
        scope_team_id="",
        start_date="2026-06-13",
    )

    matching = updated["App_Roles"][
        (updated["App_Roles"]["member_id"] == "M003")
        & (updated["App_Roles"]["app_id"] == "budget")
        & (updated["App_Roles"]["app_role"] == "viewer")
    ]
    assert len(matching) == 1
    assert updated["Audit_Log"].iloc[-1]["target_type"] == "App_Roles"
    assert json.loads(updated["Audit_Log"].iloc[-1]["after"])["app_role"] == "viewer"


def test_grant_app_role_reports_unknown_member_id():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    with pytest.raises(ValueError, match="Unknown member_id M999"):
        grant_app_role(
            registry,
            actor_email="kkamei@nyu.edu",
            member_id="M999",
            app_id="budget",
            app_role="viewer",
            scope_team_id="",
            start_date="2026-06-13",
        )


def test_grant_app_role_reports_unknown_app_id():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    with pytest.raises(ValueError, match="Unknown app_id missing_app"):
        grant_app_role(
            registry,
            actor_email="kkamei@nyu.edu",
            member_id="M003",
            app_id="missing_app",
            app_role="viewer",
            scope_team_id="",
            start_date="2026-06-13",
        )


def test_grant_app_role_reports_unknown_scope_team_id():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    with pytest.raises(ValueError, match="Unknown scope_team_id T999"):
        grant_app_role(
            registry,
            actor_email="kkamei@nyu.edu",
            member_id="M003",
            app_id="budget",
            app_role="viewer",
            scope_team_id="T999",
            start_date="2026-06-13",
        )


def test_grant_app_role_reports_invalid_app_role():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    with pytest.raises(ValueError, match="Invalid app_role invalid_role"):
        grant_app_role(
            registry,
            actor_email="kkamei@nyu.edu",
            member_id="M003",
            app_id="budget",
            app_role="invalid_role",
            scope_team_id="",
            start_date="2026-06-13",
        )
