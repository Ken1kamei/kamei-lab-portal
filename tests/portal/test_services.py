from pathlib import Path

import json

import pandas as pd
import pytest

from lab_portal.portal.services import add_member, add_team, deactivate_member, grant_app_role, update_app_url, update_member
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
        password="initial-pass-123",
        notes="Joined portal pilot",
    )

    assert "new.member@example.edu" in set(updated["Members"]["email"])
    assert updated["Audit_Log"].iloc[-1]["action"] == "member.add"
    assert updated["Audit_Log"].iloc[-1]["actor_email"] == "kkamei@nyu.edu"
    assert "new.member@example.edu" not in set(registry["Members"]["email"])
    member = updated["Members"].set_index("email").loc["new.member@example.edu"]
    assert member["password_hash"].startswith("pbkdf2_sha256$")
    assert member["password_hash"] != "initial-pass-123"
    assert member["password_must_change"] == "TRUE"
    assert json.loads(updated["Audit_Log"].iloc[-1]["after"])["email"] == "new.member@example.edu"
    assert json.loads(updated["Audit_Log"].iloc[-1]["after"])["password_hash"] == "<redacted>"


def test_add_member_can_assign_teams_and_app_access_for_shared_registry():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    updated = add_member(
        registry,
        actor_email="kkamei@nyu.edu",
        email="shared.member@example.edu",
        name="Shared Member",
        display_name="Shared Member",
        global_role="member",
        start_date="2026-06-18",
        password="initial-pass-123",
        notes="Visible across apps",
        team_ids=["T001", "T002"],
        team_role="member",
        app_ids=["budget", "notebooks_protocols", "project_tracker"],
        app_role="viewer",
    )

    member = updated["Members"].set_index("email").loc["shared.member@example.edu"]
    member_id = member["member_id"]
    member_team_rows = updated["Member_Teams"][updated["Member_Teams"]["member_id"] == member_id]
    app_role_rows = updated["App_Roles"][updated["App_Roles"]["member_id"] == member_id]

    assert set(member_team_rows["team_id"]) == {"T001", "T002"}
    assert set(app_role_rows["app_id"]) == {"budget", "notebooks_protocols", "project_tracker"}
    assert set(app_role_rows["app_role"]) == {"viewer"}
    assert "member_team.assign" in set(updated["Audit_Log"]["action"])
    assert "app_role.grant" in set(updated["Audit_Log"]["action"])


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
            password="initial-pass-123",
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
            password="initial-pass-123",
            notes="Duplicate",
        )


def test_add_member_requires_initial_password():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    with pytest.raises(ValueError, match="password must be at least 8 characters"):
        add_member(
            registry,
            actor_email="kkamei@nyu.edu",
            email="new.member@example.edu",
            name="New Member",
            display_name="New Member",
            global_role="member",
            start_date="2026-06-13",
            password="short",
            notes="Joined portal pilot",
        )


def test_update_member_changes_profile_and_can_reset_password():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    updated = update_member(
        registry,
        actor_email="kkamei@nyu.edu",
        member_id="M003",
        email="updated.member@example.edu",
        name="Updated Member",
        display_name="Updated",
        global_role="lead",
        active="TRUE",
        start_date="2026-02-01",
        end_date="",
        notes="Updated profile",
        password="updated-pass-123",
        password_must_change="FALSE",
    )

    member = updated["Members"].set_index("member_id").loc["M003"]
    assert member["email"] == "updated.member@example.edu"
    assert member["display_name"] == "Updated"
    assert member["global_role"] == "lead"
    assert member["password_hash"].startswith("pbkdf2_sha256$")
    assert member["password_hash"] != "updated-pass-123"
    assert member["password_must_change"] == "TRUE"
    assert updated["Audit_Log"].iloc[-1]["action"] == "member.update"
    assert json.loads(updated["Audit_Log"].iloc[-1]["after"])["password_hash"] == "<redacted>"


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


def test_grant_app_role_reports_inactive_member_id():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()
    registry["Members"].loc[registry["Members"]["member_id"] == "M003", "active"] = "FALSE"

    with pytest.raises(ValueError, match="Inactive member_id M003"):
        grant_app_role(
            registry,
            actor_email="kkamei@nyu.edu",
            member_id="M003",
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


def test_grant_app_role_reports_duplicate_active_role():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    with pytest.raises(ValueError, match="Duplicate active app_role M003 project_tracker viewer"):
        grant_app_role(
            registry,
            actor_email="kkamei@nyu.edu",
            member_id="M003",
            app_id="project_tracker",
            app_role="viewer",
            scope_team_id="T002",
            start_date="2026-06-13",
        )


def test_add_team_appends_team_and_audit_record():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    updated = add_team(
        registry,
        actor_email="kkamei@nyu.edu",
        team_name="Digital Twin",
        description="Digital twin projects",
    )

    assert "Digital Twin" in set(updated["Teams"]["team_name"])
    assert updated["Audit_Log"].iloc[-1]["action"] == "team.add"
    assert updated["Audit_Log"].iloc[-1]["target_type"] == "Teams"
    assert "Digital Twin" not in set(registry["Teams"]["team_name"])


def test_add_team_reports_blank_team_name():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    with pytest.raises(ValueError, match="team_name is required"):
        add_team(registry, actor_email="kkamei@nyu.edu", team_name="  ", description="Missing")


def test_add_team_reports_duplicate_active_team_name():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    with pytest.raises(ValueError, match="Duplicate active team_name endometriosis project"):
        add_team(
            registry,
            actor_email="kkamei@nyu.edu",
            team_name=" Endometriosis Project ",
            description="Duplicate",
        )


def test_update_app_url_updates_launcher_and_audit_record():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    updated = update_app_url(
        registry,
        actor_email="kkamei@nyu.edu",
        app_id="project_tracker",
        app_url="https://kamei-lab-project-tracker.streamlit.app/",
        active="TRUE",
    )

    app = updated["Apps"].set_index("app_id").loc["project_tracker"]
    assert app["app_url"] == "https://kamei-lab-project-tracker.streamlit.app/"
    assert app["active"] == "TRUE"
    assert updated["Audit_Log"].iloc[-1]["action"] == "app.update_url"
    assert json.loads(updated["Audit_Log"].iloc[-1]["before"])["app_url"] == "http://127.0.0.1:8502/"
    assert json.loads(updated["Audit_Log"].iloc[-1]["after"])["active"] == "TRUE"
    assert registry["Apps"].set_index("app_id").loc["project_tracker", "app_url"] == "http://127.0.0.1:8502/"


def test_update_app_url_reports_unknown_app_id():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    with pytest.raises(ValueError, match="Unknown app_id missing_app"):
        update_app_url(
            registry,
            actor_email="kkamei@nyu.edu",
            app_id="missing_app",
            app_url="https://example.streamlit.app/",
            active="TRUE",
        )


def test_update_app_url_reports_invalid_active_value():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    with pytest.raises(ValueError, match="Invalid active maybe"):
        update_app_url(
            registry,
            actor_email="kkamei@nyu.edu",
            app_id="project_tracker",
            app_url="https://example.streamlit.app/",
            active="maybe",
        )


def test_update_app_url_reports_invalid_url_scheme():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    with pytest.raises(ValueError, match="app_url must start with http:// or https://"):
        update_app_url(
            registry,
            actor_email="kkamei@nyu.edu",
            app_id="project_tracker",
            app_url="javascript:alert(1)",
            active="TRUE",
        )
