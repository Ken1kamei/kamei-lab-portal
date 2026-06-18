from lab_portal.portal.constants import APP_IDS, APP_ROLES, PORTAL_ROLES, TABLES
from lab_portal.portal.schema import REQUIRED_COLUMNS, empty_registry


def test_registry_tables_match_design_spec():
    assert TABLES == ["Members", "Teams", "Member_Teams", "Apps", "App_Roles", "Audit_Log"]


def test_roles_and_initial_app_ids_match_design_spec():
    assert PORTAL_ROLES == ["pi", "admin", "lead", "member", "inactive"]
    assert APP_ROLES == ["owner", "manager", "lead", "editor", "viewer"]
    assert APP_IDS == ["budget", "notebooks_protocols", "project_tracker"]


def test_required_columns_include_all_registry_fields():
    assert REQUIRED_COLUMNS["Members"] == [
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
    ]
    assert REQUIRED_COLUMNS["Teams"] == ["team_id", "team_name", "description", "active"]
    assert REQUIRED_COLUMNS["Member_Teams"] == [
        "member_team_id",
        "member_id",
        "team_id",
        "team_role",
        "active",
        "start_date",
        "end_date",
    ]
    assert REQUIRED_COLUMNS["Apps"] == [
        "app_id",
        "app_name",
        "app_url",
        "description",
        "category",
        "active",
        "sort_order",
    ]
    assert REQUIRED_COLUMNS["App_Roles"] == [
        "app_role_id",
        "member_id",
        "app_id",
        "app_role",
        "scope_team_id",
        "active",
        "start_date",
        "end_date",
    ]
    assert REQUIRED_COLUMNS["Audit_Log"] == [
        "audit_id",
        "timestamp",
        "actor_email",
        "action",
        "target_type",
        "target_id",
        "before",
        "after",
    ]


def test_empty_registry_has_all_tables_and_columns():
    registry = empty_registry()
    assert set(registry) == set(TABLES)
    for table_name, columns in REQUIRED_COLUMNS.items():
        assert list(registry[table_name].columns) == columns
