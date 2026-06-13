from pathlib import Path

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


def test_deactivate_member_keeps_row_and_appends_audit_record():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    updated = deactivate_member(registry, actor_email="kkamei@nyu.edu", member_id="M003", end_date="2026-06-30")

    member = updated["Members"].set_index("member_id").loc["M003"]
    assert member["active"] == "FALSE"
    assert member["end_date"] == "2026-06-30"
    assert updated["Audit_Log"].iloc[-1]["action"] == "member.deactivate"


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
