# Kamei Lab Portal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a separate Streamlit Kamei Lab Portal that launches Budget, Notebooks/Protocols, and Project Tracker while centrally managing members, teams, app roles, and audit history through a Google Sheet-compatible registry.

**Architecture:** Keep the existing Project Tracker under `streamlit_app/` untouched and add a separate `lab_portal/` app. Put registry schema, storage adapters, validation, permissions, audit logic, and UI rendering in focused modules under `lab_portal/portal/`. Use local CSV sample data for tests and local development, with a Google Sheets adapter behind the same store interface for deployment.

**Tech Stack:** Python 3, Streamlit, pandas, pytest, gspread, Google service account credentials.

---

## File Structure

- Modify `requirements.txt`: add Google Sheets dependencies used by the portal.
- Create `lab_portal/__init__.py`: package marker for the portal app.
- Create `lab_portal/app.py`: Streamlit entrypoint for the portal.
- Create `lab_portal/portal/__init__.py`: package marker for portal domain code.
- Create `lab_portal/portal/constants.py`: table names, portal roles, app roles, and app ids.
- Create `lab_portal/portal/schema.py`: required columns, empty registry builder, and sample row helpers.
- Create `lab_portal/portal/storage.py`: CSV and Google Sheets registry stores behind a shared interface.
- Create `lab_portal/portal/config.py`: Streamlit secrets parsing and registry store selection.
- Create `lab_portal/portal/validation.py`: row validation and registry-level integrity checks.
- Create `lab_portal/portal/services.py`: member, team, app, app-role, and audit operations.
- Create `lab_portal/portal/permissions.py`: role resolution and admin access decisions.
- Create `lab_portal/portal/auth.py`: deployed login extraction plus local development fallback.
- Create `lab_portal/portal/theme.py`: shared Kamei Lab dark theme helpers for portal screens.
- Create `lab_portal/portal/views.py`: Streamlit rendering helpers for launcher and admin pages.
- Create `lab_portal/data/sample/*.csv`: sample registry worksheets.
- Create `tests/portal/test_schema.py`: registry schema tests.
- Create `tests/portal/test_storage.py`: CSV store and fake Google Sheets store tests.
- Create `tests/portal/test_config.py`: CSV-vs-Google-Sheets store selection tests.
- Create `tests/portal/test_validation.py`: registry validation tests.
- Create `tests/portal/test_services.py`: member/team/app/audit workflow tests.
- Create `tests/portal/test_permissions.py`: user and app-role resolution tests.
- Create `tests/portal/test_views.py`: HTML helper tests.
- Create `tests/portal/test_app_smoke.py`: portal import smoke test.
- Create `lab_portal/README.md`: local run, Google Sheet setup, and Streamlit Cloud setup notes.

## Task 1: Portal Schema and Constants

**Files:**
- Modify: `requirements.txt`
- Create: `lab_portal/__init__.py`
- Create: `lab_portal/portal/__init__.py`
- Create: `lab_portal/portal/constants.py`
- Create: `lab_portal/portal/schema.py`
- Test: `tests/portal/test_schema.py`

- [ ] **Step 1: Write the failing schema tests**

Create `tests/portal/test_schema.py`:

```python
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
```

- [ ] **Step 2: Run the schema tests to verify they fail**

Run:

```bash
python -m pytest tests/portal/test_schema.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'lab_portal'`.

- [ ] **Step 3: Add dependencies and schema implementation**

Modify `requirements.txt` so it contains:

```text
altair>=5
gspread>=6
pandas>=2.2
pytest>=8.2
streamlit>=1.35
```

Create `lab_portal/__init__.py`:

```python
"""Kamei Lab Portal Streamlit app."""
```

Create `lab_portal/portal/__init__.py`:

```python
"""Domain logic for the Kamei Lab Portal."""
```

Create `lab_portal/portal/constants.py`:

```python
TABLES = ["Members", "Teams", "Member_Teams", "Apps", "App_Roles", "Audit_Log"]

PORTAL_ROLES = ["pi", "admin", "lead", "member", "inactive"]
ADMIN_ROLES = ["pi", "admin"]
TEAM_ADMIN_ROLES = ["pi", "admin", "lead"]

APP_ROLES = ["owner", "manager", "lead", "editor", "viewer"]
APP_IDS = ["budget", "notebooks_protocols", "project_tracker"]
```

Create `lab_portal/portal/schema.py`:

```python
from __future__ import annotations

import pandas as pd

from .constants import TABLES


REQUIRED_COLUMNS = {
    "Members": [
        "member_id",
        "email",
        "name",
        "display_name",
        "global_role",
        "active",
        "start_date",
        "end_date",
        "notes",
    ],
    "Teams": ["team_id", "team_name", "description", "active"],
    "Member_Teams": [
        "member_team_id",
        "member_id",
        "team_id",
        "team_role",
        "active",
        "start_date",
        "end_date",
    ],
    "Apps": ["app_id", "app_name", "app_url", "description", "category", "active", "sort_order"],
    "App_Roles": [
        "app_role_id",
        "member_id",
        "app_id",
        "app_role",
        "scope_team_id",
        "active",
        "start_date",
        "end_date",
    ],
    "Audit_Log": ["audit_id", "timestamp", "actor_email", "action", "target_type", "target_id", "before", "after"],
}


def empty_registry() -> dict[str, pd.DataFrame]:
    return {table_name: pd.DataFrame(columns=REQUIRED_COLUMNS[table_name]) for table_name in TABLES}
```

- [ ] **Step 4: Run schema tests to verify they pass**

Run:

```bash
python -m pytest tests/portal/test_schema.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit schema scaffold**

Run:

```bash
git add requirements.txt lab_portal/__init__.py lab_portal/portal/__init__.py lab_portal/portal/constants.py lab_portal/portal/schema.py tests/portal/test_schema.py
git commit -m "feat: scaffold lab portal registry schema"
```

## Task 2: Local Sample Registry and Storage Adapters

**Files:**
- Create: `lab_portal/portal/storage.py`
- Create: `lab_portal/data/sample/Members.csv`
- Create: `lab_portal/data/sample/Teams.csv`
- Create: `lab_portal/data/sample/Member_Teams.csv`
- Create: `lab_portal/data/sample/Apps.csv`
- Create: `lab_portal/data/sample/App_Roles.csv`
- Create: `lab_portal/data/sample/Audit_Log.csv`
- Test: `tests/portal/test_storage.py`

- [ ] **Step 1: Write failing storage tests**

Create `tests/portal/test_storage.py`:

```python
from pathlib import Path

import pandas as pd

from lab_portal.portal.storage import CsvRegistryStore, GoogleSheetRegistryStore


def test_csv_registry_store_loads_sample_registry():
    store = CsvRegistryStore(Path("lab_portal/data/sample"))
    registry = store.load()

    assert registry["Members"].loc[0, "email"] == "kkamei@nyu.edu"
    assert set(registry["Apps"]["app_id"]) == {"budget", "notebooks_protocols", "project_tracker"}
    assert "Audit_Log" in registry


def test_csv_registry_store_round_trips_all_tables(tmp_path):
    source = CsvRegistryStore(Path("lab_portal/data/sample"))
    registry = source.load()
    output = CsvRegistryStore(tmp_path)

    output.save(registry)
    reloaded = output.load()

    for table_name in registry:
        pd.testing.assert_frame_equal(reloaded[table_name], registry[table_name])


class FakeWorksheet:
    def __init__(self, records):
        self.records = records
        self.updated_rows = None

    def get_all_records(self):
        return self.records

    def clear(self):
        self.updated_rows = []

    def update(self, rows):
        self.updated_rows = rows


class FakeSpreadsheet:
    def __init__(self, worksheets):
        self.worksheets = worksheets

    def worksheet(self, name):
        return self.worksheets[name]


def test_google_sheet_registry_store_uses_same_table_contract():
    spreadsheet = FakeSpreadsheet(
        {
            "Members": FakeWorksheet(
                [
                    {
                        "member_id": "M001",
                        "email": "kkamei@nyu.edu",
                        "name": "Ken Kamei",
                        "display_name": "Ken",
                        "global_role": "pi",
                        "active": "TRUE",
                        "start_date": "2026-01-01",
                        "end_date": "",
                        "notes": "PI",
                    }
                ]
            ),
            "Teams": FakeWorksheet([{"team_id": "T001", "team_name": "Core Lab", "description": "Lab-wide", "active": "TRUE"}]),
            "Member_Teams": FakeWorksheet(
                [
                    {
                        "member_team_id": "MT001",
                        "member_id": "M001",
                        "team_id": "T001",
                        "team_role": "lead",
                        "active": "TRUE",
                        "start_date": "2026-01-01",
                        "end_date": "",
                    }
                ]
            ),
            "Apps": FakeWorksheet(
                [
                    {
                        "app_id": "budget",
                        "app_name": "Budget",
                        "app_url": "https://kamei-lab-budget-qff7jmewjwgpft4qyhc7hb.streamlit.app/",
                        "description": "Lab budget management",
                        "category": "Operations",
                        "active": "TRUE",
                        "sort_order": 1,
                    }
                ]
            ),
            "App_Roles": FakeWorksheet(
                [
                    {
                        "app_role_id": "AR001",
                        "member_id": "M001",
                        "app_id": "budget",
                        "app_role": "owner",
                        "scope_team_id": "",
                        "active": "TRUE",
                        "start_date": "2026-01-01",
                        "end_date": "",
                    }
                ]
            ),
            "Audit_Log": FakeWorksheet([]),
        }
    )

    store = GoogleSheetRegistryStore(spreadsheet)
    registry = store.load()

    assert registry["Members"].loc[0, "member_id"] == "M001"
    assert list(registry["Apps"].columns)[0] == "app_id"
```

- [ ] **Step 2: Run storage tests to verify they fail**

Run:

```bash
python -m pytest tests/portal/test_storage.py -v
```

Expected: FAIL with `ModuleNotFoundError` or `ImportError` for `lab_portal.portal.storage`.

- [ ] **Step 3: Add sample registry CSVs**

Create `lab_portal/data/sample/Members.csv`:

```csv
member_id,email,name,display_name,global_role,active,start_date,end_date,notes
M001,kkamei@nyu.edu,Ken Kamei,Ken,pi,TRUE,2026-01-01,,PI
M002,lead@example.edu,Assay Lead,Assay Lead,lead,TRUE,2026-01-15,,Example lead
M003,member@example.edu,Research Member,Research Member,member,TRUE,2026-02-01,,Example member
```

Create `lab_portal/data/sample/Teams.csv`:

```csv
team_id,team_name,description,active
T001,Core Lab,Lab-wide operations,TRUE
T002,Endometriosis Project,Endometriosis project team,TRUE
```

Create `lab_portal/data/sample/Member_Teams.csv`:

```csv
member_team_id,member_id,team_id,team_role,active,start_date,end_date
MT001,M001,T001,lead,TRUE,2026-01-01,
MT002,M002,T002,lead,TRUE,2026-01-15,
MT003,M003,T002,member,TRUE,2026-02-01,
```

Create `lab_portal/data/sample/Apps.csv`:

```csv
app_id,app_name,app_url,description,category,active,sort_order
budget,Budget,https://kamei-lab-budget-qff7jmewjwgpft4qyhc7hb.streamlit.app/,Lab budget management,Operations,TRUE,1
notebooks_protocols,Notebooks/Protocols,https://kamei-lab-notebooks-protocols.streamlit.app/,Lab notebooks and protocols,Knowledge,TRUE,2
project_tracker,Project Tracker,,Milestones experiments and reviews,Research,FALSE,3
```

Create `lab_portal/data/sample/App_Roles.csv`:

```csv
app_role_id,member_id,app_id,app_role,scope_team_id,active,start_date,end_date
AR001,M001,budget,owner,,TRUE,2026-01-01,
AR002,M001,notebooks_protocols,owner,,TRUE,2026-01-01,
AR003,M001,project_tracker,owner,,TRUE,2026-01-01,
AR004,M002,project_tracker,lead,T002,TRUE,2026-01-15,
AR005,M003,project_tracker,viewer,T002,TRUE,2026-02-01,
```

Create `lab_portal/data/sample/Audit_Log.csv`:

```csv
audit_id,timestamp,actor_email,action,target_type,target_id,before,after
```

- [ ] **Step 4: Implement storage adapters**

Create `lab_portal/portal/storage.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import pandas as pd

from .constants import TABLES
from .schema import REQUIRED_COLUMNS, empty_registry


Registry = dict[str, pd.DataFrame]


class RegistryStore(Protocol):
    def load(self) -> Registry:
        ...

    def save(self, registry: Registry) -> None:
        ...


@dataclass(frozen=True)
class CsvRegistryStore:
    base_dir: Path

    def load(self) -> Registry:
        registry = empty_registry()
        for table_name in TABLES:
            path = self.base_dir / f"{table_name}.csv"
            if path.exists():
                registry[table_name] = pd.read_csv(path, dtype=str).fillna("")
            registry[table_name] = registry[table_name].reindex(columns=REQUIRED_COLUMNS[table_name], fill_value="")
        return registry

    def save(self, registry: Registry) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        for table_name in TABLES:
            frame = registry[table_name].reindex(columns=REQUIRED_COLUMNS[table_name], fill_value="")
            frame.to_csv(self.base_dir / f"{table_name}.csv", index=False)


@dataclass(frozen=True)
class GoogleSheetRegistryStore:
    spreadsheet: object

    def load(self) -> Registry:
        registry = empty_registry()
        for table_name in TABLES:
            worksheet = self.spreadsheet.worksheet(table_name)
            records = worksheet.get_all_records()
            frame = pd.DataFrame(records)
            registry[table_name] = frame.reindex(columns=REQUIRED_COLUMNS[table_name], fill_value="").astype(str)
        return registry

    def save(self, registry: Registry) -> None:
        for table_name in TABLES:
            worksheet = self.spreadsheet.worksheet(table_name)
            frame = registry[table_name].reindex(columns=REQUIRED_COLUMNS[table_name], fill_value="")
            rows = [list(frame.columns)] + frame.fillna("").astype(str).values.tolist()
            worksheet.clear()
            worksheet.update(rows)
```

- [ ] **Step 5: Run storage tests to verify they pass**

Run:

```bash
python -m pytest tests/portal/test_storage.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit storage adapters**

Run:

```bash
git add lab_portal/data/sample lab_portal/portal/storage.py tests/portal/test_storage.py
git commit -m "feat: add portal registry storage"
```

## Task 3: Registry Validation and Permission Resolution

**Files:**
- Create: `lab_portal/portal/validation.py`
- Create: `lab_portal/portal/permissions.py`
- Test: `tests/portal/test_validation.py`
- Test: `tests/portal/test_permissions.py`

- [ ] **Step 1: Write failing validation tests**

Create `tests/portal/test_validation.py`:

```python
from pathlib import Path

import pandas as pd

from lab_portal.portal.storage import CsvRegistryStore
from lab_portal.portal.validation import validate_registry


def test_valid_sample_registry_has_no_errors():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    assert validate_registry(registry) == []


def test_duplicate_active_email_is_reported():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()
    duplicate = registry["Members"].iloc[[0]].copy()
    duplicate.loc[duplicate.index[0], "member_id"] = "M999"
    registry["Members"] = pd.concat([registry["Members"], duplicate], ignore_index=True)

    errors = validate_registry(registry)

    assert "Duplicate active member email: kkamei@nyu.edu" in errors


def test_unknown_app_role_reference_is_reported():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()
    registry["App_Roles"].loc[0, "app_id"] = "missing_app"

    errors = validate_registry(registry)

    assert "App_Roles AR001 references unknown app_id missing_app" in errors
```

- [ ] **Step 2: Write failing permission tests**

Create `tests/portal/test_permissions.py`:

```python
from pathlib import Path

from lab_portal.portal.permissions import can_admin_portal, resolve_app_roles, resolve_member_by_email
from lab_portal.portal.storage import CsvRegistryStore


def test_resolve_member_by_email_returns_active_member():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    member = resolve_member_by_email(registry, "kkamei@nyu.edu")

    assert member["member_id"] == "M001"
    assert member["global_role"] == "pi"


def test_resolve_member_by_email_rejects_inactive_member():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()
    registry["Members"].loc[0, "active"] = "FALSE"

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
```

- [ ] **Step 3: Run validation and permission tests to verify they fail**

Run:

```bash
python -m pytest tests/portal/test_validation.py tests/portal/test_permissions.py -v
```

Expected: FAIL with imports missing for `validation` and `permissions`.

- [ ] **Step 4: Implement validation**

Create `lab_portal/portal/validation.py`:

```python
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
```

- [ ] **Step 5: Implement permissions**

Create `lab_portal/portal/permissions.py`:

```python
from __future__ import annotations

from collections import defaultdict

from .constants import ADMIN_ROLES
from .storage import Registry


def is_active(value: object) -> bool:
    return str(value).strip().upper() in {"TRUE", "1", "YES", "Y"}


def resolve_member_by_email(registry: Registry, email: str) -> dict[str, str] | None:
    members = registry["Members"].fillna("")
    matches = members[members["email"].str.lower() == email.lower()]
    for _, row in matches.iterrows():
        record = row.to_dict()
        if is_active(record.get("active", "")):
            return {key: str(value) for key, value in record.items()}
    return None


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
```

- [ ] **Step 6: Run validation and permission tests to verify they pass**

Run:

```bash
python -m pytest tests/portal/test_validation.py tests/portal/test_permissions.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit validation and permissions**

Run:

```bash
git add lab_portal/portal/validation.py lab_portal/portal/permissions.py tests/portal/test_validation.py tests/portal/test_permissions.py
git commit -m "feat: add portal registry validation"
```

## Task 4: Audit and Registry Mutation Services

**Files:**
- Create: `lab_portal/portal/services.py`
- Test: `tests/portal/test_services.py`

- [ ] **Step 1: Write failing service tests**

Create `tests/portal/test_services.py`:

```python
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
```

- [ ] **Step 2: Run service tests to verify they fail**

Run:

```bash
python -m pytest tests/portal/test_services.py -v
```

Expected: FAIL with `ModuleNotFoundError` or missing functions in `lab_portal.portal.services`.

- [ ] **Step 3: Implement services**

Create `lab_portal/portal/services.py`:

```python
from __future__ import annotations

import json
from datetime import UTC, datetime

import pandas as pd

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
```

- [ ] **Step 4: Run service tests to verify they pass**

Run:

```bash
python -m pytest tests/portal/test_services.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit services**

Run:

```bash
git add lab_portal/portal/services.py tests/portal/test_services.py
git commit -m "feat: add portal member access services"
```

## Task 5: Theme and View Helpers

**Files:**
- Create: `lab_portal/portal/theme.py`
- Create: `lab_portal/portal/views.py`
- Test: `tests/portal/test_views.py`

- [ ] **Step 1: Write failing view helper tests**

Create `tests/portal/test_views.py`:

```python
from pathlib import Path

from lab_portal.portal.storage import CsvRegistryStore
from lab_portal.portal.views import app_cards, dashboard_header_html


def test_app_cards_marks_missing_url_as_disabled():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    cards = app_cards(registry)
    tracker = next(card for card in cards if card["app_id"] == "project_tracker")

    assert tracker["label"] == "Project Tracker"
    assert tracker["enabled"] is False
    assert tracker["status"] == "URL needed"


def test_app_cards_marks_active_url_as_enabled():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    cards = app_cards(registry)
    budget = next(card for card in cards if card["app_id"] == "budget")

    assert budget["enabled"] is True
    assert budget["status"] == "Active"


def test_dashboard_header_html_escapes_title():
    html = dashboard_header_html("Kamei <Portal>", "Shared apps")

    assert "Kamei &lt;Portal&gt;" in html
    assert "Shared apps" in html
```

- [ ] **Step 2: Run view tests to verify they fail**

Run:

```bash
python -m pytest tests/portal/test_views.py -v
```

Expected: FAIL with missing `views` module.

- [ ] **Step 3: Implement portal theme**

Create `lab_portal/portal/theme.py`:

```python
from __future__ import annotations

import streamlit as st


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
          --portal-bg: #151b32;
          --portal-surface: #242a46;
          --portal-surface-alt: #1d233b;
          --portal-text: #f7f8ff;
          --portal-muted: #c1c8e4;
          --portal-subtle: #8892bb;
          --portal-line: #37405f;
          --portal-cyan: #2ee6cf;
          --portal-danger: #ff4f80;
        }
        .stApp {
          background: linear-gradient(180deg, var(--portal-bg), var(--portal-bg));
          color: var(--portal-text);
        }
        section[data-testid="stSidebar"] {
          background: var(--portal-surface-alt);
          border-right: 1px solid var(--portal-line);
        }
        .main .block-container {
          max-width: 1440px;
          padding-top: 1rem;
        }
        .portal-header {
          border-bottom: 1px solid var(--portal-line);
          margin: 16px 0 28px;
          padding-bottom: 24px;
        }
        .portal-title {
          color: var(--portal-text);
          font-size: clamp(2.4rem, 4vw, 4rem);
          line-height: 1.05;
          font-weight: 900;
          letter-spacing: 0;
          margin: 0;
        }
        .portal-subtitle {
          color: var(--portal-muted);
          font-size: 1rem;
          margin-top: 12px;
        }
        .portal-card {
          border: 1px solid #425074;
          border-radius: 8px;
          background: linear-gradient(145deg, #303851, #202842);
          padding: 22px;
          min-height: 180px;
        }
        .portal-card-title {
          color: var(--portal-text);
          font-size: 1.2rem;
          font-weight: 900;
          margin-bottom: 8px;
        }
        .portal-card-muted {
          color: var(--portal-muted);
          font-size: .95rem;
          line-height: 1.35;
        }
        .portal-status {
          color: var(--portal-cyan);
          font-size: .78rem;
          text-transform: uppercase;
          font-weight: 900;
          letter-spacing: .04em;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
```

- [ ] **Step 4: Implement view helpers**

Create `lab_portal/portal/views.py`:

```python
from __future__ import annotations

import html

from .permissions import is_active
from .storage import Registry


def dashboard_header_html(title: str, subtitle: str) -> str:
    return (
        '<div class="portal-header">'
        f'<h1 class="portal-title">{html.escape(title)}</h1>'
        f'<div class="portal-subtitle">{html.escape(subtitle)}</div>'
        "</div>"
    )


def app_cards(registry: Registry) -> list[dict[str, object]]:
    apps = registry["Apps"].fillna("").copy()
    if "sort_order" in apps:
        apps["sort_order_numeric"] = (
            apps["sort_order"].astype(str).str.extract(r"(\\d+)", expand=False).fillna("999").astype(int)
        )
        apps = apps.sort_values(["sort_order_numeric", "app_name"])
    cards: list[dict[str, object]] = []
    for _, row in apps.iterrows():
        active = is_active(row["active"])
        has_url = bool(str(row["app_url"]).strip())
        enabled = active and has_url
        if enabled:
            status = "Active"
        elif active:
            status = "URL needed"
        else:
            status = "Inactive"
        cards.append(
            {
                "app_id": row["app_id"],
                "label": row["app_name"],
                "url": row["app_url"],
                "description": row["description"],
                "category": row["category"],
                "enabled": enabled,
                "status": status,
            }
        )
    return cards
```

- [ ] **Step 5: Run view helper tests to verify they pass**

Run:

```bash
python -m pytest tests/portal/test_views.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit theme and views**

Run:

```bash
git add lab_portal/portal/theme.py lab_portal/portal/views.py tests/portal/test_views.py
git commit -m "feat: add portal theme and launcher views"
```

## Task 6: Portal Streamlit App

**Files:**
- Create: `lab_portal/app.py`
- Create: `lab_portal/portal/auth.py`
- Test: `tests/portal/test_app_smoke.py`

- [ ] **Step 1: Write failing app smoke test**

Create `tests/portal/test_app_smoke.py`:

```python
import importlib


def test_lab_portal_app_imports():
    module = importlib.import_module("lab_portal.app")

    assert module.APP_TITLE == "Kamei Lab Portal"
    assert module.VIEWS == ["Home", "Members", "Teams", "App Access", "Audit"]
```

- [ ] **Step 2: Run app smoke test to verify it fails**

Run:

```bash
python -m pytest tests/portal/test_app_smoke.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'lab_portal.app'`.

- [ ] **Step 3: Implement local/deployed auth helper**

Create `lab_portal/portal/auth.py`:

```python
from __future__ import annotations

import os

import streamlit as st


def authenticated_email() -> str:
    if "PORTAL_DEV_EMAIL" in os.environ:
        return os.environ["PORTAL_DEV_EMAIL"]

    user = getattr(st, "user", None)
    if user and getattr(user, "is_logged_in", False):
        email = user.get("email") if hasattr(user, "get") else None
        if email:
            return str(email)

    return "kkamei@nyu.edu"
```

- [ ] **Step 4: Implement portal app entrypoint**

Create `lab_portal/app.py`:

```python
from __future__ import annotations

from pathlib import Path

import streamlit as st

from lab_portal.portal.auth import authenticated_email
from lab_portal.portal.permissions import can_admin_portal, resolve_member_by_email
from lab_portal.portal.storage import CsvRegistryStore
from lab_portal.portal.theme import apply_theme
from lab_portal.portal.views import app_cards, dashboard_header_html


APP_TITLE = "Kamei Lab Portal"
VIEWS = ["Home", "Members", "Teams", "App Access", "Audit"]
SAMPLE_REGISTRY_DIR = Path(__file__).parent / "data" / "sample"


def load_registry():
    return CsvRegistryStore(SAMPLE_REGISTRY_DIR).load()


def render_home(registry) -> None:
    st.html(dashboard_header_html(APP_TITLE, "Shared entry point for Kamei Reverse Bioengineering Lab apps"))
    cards = app_cards(registry)
    columns = st.columns(3)
    for index, card in enumerate(cards):
        with columns[index % 3]:
            st.markdown(
                f"""
                <div class="portal-card">
                  <div class="portal-status">{card['status']}</div>
                  <div class="portal-card-title">{card['label']}</div>
                  <div class="portal-card-muted">{card['description']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if card["enabled"]:
                st.link_button(f"Open {card['label']}", str(card["url"]))
            else:
                st.button(f"{card['label']} unavailable", disabled=True)


def render_table_page(title: str, subtitle: str, frame) -> None:
    st.html(dashboard_header_html(title, subtitle))
    st.dataframe(frame, use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="K", layout="wide", initial_sidebar_state="expanded")
    apply_theme()

    registry = load_registry()
    email = authenticated_email()
    member = resolve_member_by_email(registry, email)
    is_admin = can_admin_portal(member)

    with st.sidebar:
        st.title("Kamei Lab")
        st.caption("Portal")
        st.caption(f"Signed in as `{email}`")
        visible_views = VIEWS if is_admin else ["Home"]
        view = st.radio("View", visible_views)

    if view == "Home":
        render_home(registry)
    elif view == "Members":
        render_table_page("Members", "Central lab member registry", registry["Members"])
    elif view == "Teams":
        render_table_page("Teams", "Lab teams and working groups", registry["Teams"])
    elif view == "App Access":
        render_table_page("App Access", "Per-app member roles", registry["App_Roles"])
    elif view == "Audit":
        render_table_page("Audit", "Append-only administrative history", registry["Audit_Log"])


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run app smoke test to verify it passes**

Run:

```bash
python -m pytest tests/portal/test_app_smoke.py -v
```

Expected: PASS.

- [ ] **Step 6: Run portal locally for visual verification**

Run:

```bash
streamlit_app/.venv/bin/streamlit run lab_portal/app.py --server.port 8503
```

Expected: the app starts at `http://localhost:8503` and shows launcher cards for Budget, Notebooks/Protocols, and a disabled Project Tracker card with URL-needed state.

- [ ] **Step 7: Commit portal app**

Run:

```bash
git add lab_portal/app.py lab_portal/portal/auth.py tests/portal/test_app_smoke.py
git commit -m "feat: add kamei lab portal app"
```

## Task 7: Admin Forms and Write Flow

**Files:**
- Modify: `lab_portal/app.py`
- Modify: `lab_portal/portal/services.py`
- Test: `tests/portal/test_services.py`

- [ ] **Step 1: Add failing service tests for team and app URL changes**

Append to `tests/portal/test_services.py`:

```python
from lab_portal.portal.services import add_team, update_app_url


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
```

- [ ] **Step 2: Run service tests to verify new tests fail**

Run:

```bash
python -m pytest tests/portal/test_services.py -v
```

Expected: FAIL with missing `add_team` and `update_app_url`.

- [ ] **Step 3: Extend service module**

Append to `lab_portal/portal/services.py`:

```python

def add_team(registry: Registry, *, actor_email: str, team_name: str, description: str) -> Registry:
    updated = {table: frame.copy() for table, frame in registry.items()}
    teams = updated["Teams"]
    row = {
        "team_id": _next_id(teams, "team_id", "T"),
        "team_name": team_name,
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


def update_app_url(registry: Registry, *, actor_email: str, app_id: str, app_url: str, active: str) -> Registry:
    updated = {table: frame.copy() for table, frame in registry.items()}
    apps = updated["Apps"].copy()
    mask = apps["app_id"] == app_id
    before = apps.loc[mask].iloc[0].to_dict()
    apps.loc[mask, "app_url"] = app_url
    apps.loc[mask, "active"] = active
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
```

- [ ] **Step 4: Run service tests to verify they pass**

Run:

```bash
python -m pytest tests/portal/test_services.py -v
```

Expected: PASS.

- [ ] **Step 5: Add minimal admin forms to `lab_portal/app.py`**

Modify `lab_portal/app.py` so it imports the store and services:

```python
from lab_portal.portal.services import add_member, add_team, grant_app_role, update_app_url
from lab_portal.portal.storage import CsvRegistryStore
```

Replace `load_registry()` with:

```python
def registry_store():
    return CsvRegistryStore(SAMPLE_REGISTRY_DIR)


def load_registry():
    return registry_store().load()


def save_registry(registry) -> None:
    registry_store().save(registry)
```

Add form handlers above `main()`:

```python
def render_member_admin(registry, actor_email: str) -> None:
    render_table_page("Members", "Central lab member registry", registry["Members"])
    with st.form("add_member"):
        st.subheader("Add member")
        email = st.text_input("Email")
        name = st.text_input("Name")
        display_name = st.text_input("Display name")
        global_role = st.selectbox("Global role", ["member", "lead", "admin", "pi"])
        start_date = st.text_input("Start date", value="2026-06-13")
        notes = st.text_input("Notes")
        if st.form_submit_button("Add member"):
            updated = add_member(
                registry,
                actor_email=actor_email,
                email=email,
                name=name,
                display_name=display_name,
                global_role=global_role,
                start_date=start_date,
                notes=notes,
            )
            save_registry(updated)
            st.success("Member added.")
            st.rerun()


def render_team_admin(registry, actor_email: str) -> None:
    render_table_page("Teams", "Lab teams and working groups", registry["Teams"])
    with st.form("add_team"):
        st.subheader("Add team")
        team_name = st.text_input("Team name")
        description = st.text_input("Description")
        if st.form_submit_button("Add team"):
            save_registry(add_team(registry, actor_email=actor_email, team_name=team_name, description=description))
            st.success("Team added.")
            st.rerun()


def render_app_access_admin(registry, actor_email: str) -> None:
    render_table_page("App Access", "Per-app member roles", registry["App_Roles"])
    with st.form("update_app_url"):
        st.subheader("Update app URL")
        app_id = st.selectbox("App", registry["Apps"]["app_id"].tolist())
        app_url = st.text_input("App URL")
        active = st.selectbox("Active", ["TRUE", "FALSE"])
        if st.form_submit_button("Update app"):
            save_registry(update_app_url(registry, actor_email=actor_email, app_id=app_id, app_url=app_url, active=active))
            st.success("App updated.")
            st.rerun()
    with st.form("grant_app_role"):
        st.subheader("Grant app role")
        member_id = st.selectbox("Member ID", registry["Members"]["member_id"].tolist())
        role_app_id = st.selectbox("Role app", registry["Apps"]["app_id"].tolist())
        app_role = st.selectbox("App role", ["viewer", "editor", "lead", "manager", "owner"])
        scope_team_id = st.selectbox("Scope team", [""] + registry["Teams"]["team_id"].tolist())
        start_date = st.text_input("Role start date", value="2026-06-13")
        if st.form_submit_button("Grant role"):
            updated = grant_app_role(
                registry,
                actor_email=actor_email,
                member_id=member_id,
                app_id=role_app_id,
                app_role=app_role,
                scope_team_id=scope_team_id,
                start_date=start_date,
            )
            save_registry(updated)
            st.success("App role granted.")
            st.rerun()
```

Then in `main()`, replace the admin page branches with:

```python
    elif view == "Members":
        render_member_admin(registry, email)
    elif view == "Teams":
        render_team_admin(registry, email)
    elif view == "App Access":
        render_app_access_admin(registry, email)
```

- [ ] **Step 6: Run focused tests**

Run:

```bash
python -m pytest tests/portal/test_services.py tests/portal/test_app_smoke.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit admin write flow**

Run:

```bash
git add lab_portal/app.py lab_portal/portal/services.py tests/portal/test_services.py
git commit -m "feat: add portal admin write flow"
```

## Task 8: Google Sheets Configuration Path

**Files:**
- Create: `lab_portal/portal/config.py`
- Modify: `lab_portal/app.py`
- Test: `tests/portal/test_config.py`

- [x] **Step 1: Write failing config tests**

Create `tests/portal/test_config.py`:

```python
from pathlib import Path

from lab_portal.portal.config import PortalSettings, registry_store_from_settings, settings_from_mapping
from lab_portal.portal.storage import CsvRegistryStore, GoogleSheetRegistryStore


class FakeClient:
    def __init__(self):
        self.opened_key = None

    def open_by_key(self, key):
        self.opened_key = key
        return {"spreadsheet_key": key}


def test_settings_from_mapping_reads_registry_values():
    settings = settings_from_mapping(
        {
            "REGISTRY_SPREADSHEET_ID": "sheet-123",
            "gcp_service_account": {"client_email": "service@example.iam.gserviceaccount.com"},
        }
    )

    assert settings.registry_spreadsheet_id == "sheet-123"
    assert settings.service_account_info == {"client_email": "service@example.iam.gserviceaccount.com"}


def test_registry_store_uses_csv_when_sheet_settings_are_missing():
    store = registry_store_from_settings(PortalSettings(), Path("lab_portal/data/sample"), lambda info: FakeClient())

    assert isinstance(store, CsvRegistryStore)


def test_registry_store_uses_google_sheet_when_sheet_settings_exist():
    fake_client = FakeClient()
    store = registry_store_from_settings(
        PortalSettings(
            registry_spreadsheet_id="sheet-123",
            service_account_info={"client_email": "service@example.iam.gserviceaccount.com"},
        ),
        Path("lab_portal/data/sample"),
        lambda info: fake_client,
    )

    assert isinstance(store, GoogleSheetRegistryStore)
    assert fake_client.opened_key == "sheet-123"
```

- [x] **Step 2: Run config tests to verify they fail**

Run:

```bash
python -m pytest tests/portal/test_config.py -v
```

Expected: FAIL with missing `lab_portal.portal.config`.

- [x] **Step 3: Implement config-driven store selection**

Create `lab_portal/portal/config.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from .storage import CsvRegistryStore, GoogleSheetRegistryStore, RegistryStore


@dataclass(frozen=True)
class PortalSettings:
    registry_spreadsheet_id: str = ""
    service_account_info: dict[str, Any] = field(default_factory=dict)


def settings_from_mapping(values: Mapping[str, Any]) -> PortalSettings:
    service_account_info = values.get("gcp_service_account", {})
    return PortalSettings(
        registry_spreadsheet_id=str(values.get("REGISTRY_SPREADSHEET_ID", "")),
        service_account_info=dict(service_account_info) if service_account_info else {},
    )


def registry_store_from_settings(
    settings: PortalSettings,
    sample_dir: Path,
    spreadsheet_factory: Callable[[dict[str, Any]], Any],
) -> RegistryStore:
    if settings.registry_spreadsheet_id and settings.service_account_info:
        client = spreadsheet_factory(settings.service_account_info)
        spreadsheet = client.open_by_key(settings.registry_spreadsheet_id)
        return GoogleSheetRegistryStore(spreadsheet)
    return CsvRegistryStore(sample_dir)
```

- [x] **Step 4: Run config tests to verify they pass**

Run:

```bash
python -m pytest tests/portal/test_config.py -v
```

Expected: PASS.

- [x] **Step 5: Wire config into the Streamlit app**

Modify imports in `lab_portal/app.py`:

```python
import gspread
import streamlit as st

from lab_portal.portal.config import registry_store_from_settings, settings_from_mapping
```

Replace `registry_store()` in `lab_portal/app.py` with:

```python
def registry_store():
    settings = settings_from_mapping(st.secrets)
    return registry_store_from_settings(settings, SAMPLE_REGISTRY_DIR, gspread.service_account_from_dict)
```

- [x] **Step 6: Run config and app smoke tests**

Run:

```bash
python -m pytest tests/portal/test_config.py tests/portal/test_app_smoke.py -v
```

Expected: PASS.

- [x] **Step 7: Commit Google Sheets configuration path**

Run:

```bash
git add lab_portal/app.py lab_portal/portal/config.py tests/portal/test_config.py
git commit -m "feat: add portal google sheets configuration"
```

## Task 9: Documentation and Full Verification

**Files:**
- Create: `lab_portal/README.md`
- Modify: `docs/superpowers/plans/2026-06-13-kamei-lab-portal.md`

- [x] **Step 1: Create portal README**

Create `lab_portal/README.md`:

````markdown
# Kamei Lab Portal

Kamei Lab Portal is a Streamlit app for launching lab apps and centrally managing lab members, teams, app roles, and audit history.

## Local Run

```bash
streamlit_app/.venv/bin/streamlit run lab_portal/app.py --server.port 8503
```

Local development reads and writes CSV files in `lab_portal/data/sample`.

## Registry Worksheets

The deployed registry Google Sheet must contain these worksheets with the headers defined in `lab_portal/portal/schema.py`:

- `Members`
- `Teams`
- `Member_Teams`
- `Apps`
- `App_Roles`
- `Audit_Log`

## Streamlit Cloud Setup

Configure the portal app with:

- `REGISTRY_SPREADSHEET_ID`
- Google service account credentials with edit access to the registry Sheet
- Streamlit OIDC authentication matching the Budget app authentication direction

## First Apps

The initial launcher apps are:

- Budget
- Notebooks/Protocols
- Project Tracker

Project Tracker can remain inactive or URL-disabled in the registry until its production deployment URL is ready.
````

- [x] **Step 2: Run all tests**

Run:

```bash
python -m pytest -v
```

Expected: all existing Project Tracker tests and new portal tests pass.

- [x] **Step 3: Run portal manually**

Run:

```bash
streamlit_app/.venv/bin/streamlit run lab_portal/app.py --server.port 8503
```

Expected:

- Home shows Budget, Notebooks/Protocols, and Project Tracker cards.
- Budget and Notebooks/Protocols cards have active launch buttons.
- Project Tracker card is disabled until a URL is entered.
- Members, Teams, App Access, and Audit pages are visible for `kkamei@nyu.edu`.
- Adding a member writes to `Members.csv` and appends to `Audit_Log.csv`.

- [x] **Step 4: Check git status**

Run:

```bash
git status --short
```

Expected: only the intentional README and any sample CSV changes from manual form testing are shown. Revert manual sample CSV edits by editing the CSVs back to their committed sample state before the final commit.

- [ ] **Step 5: Commit documentation**

Run:

```bash
git add lab_portal/README.md
git commit -m "docs: add lab portal setup guide"
```

## Final Handoff

After all tasks are complete:

- Run `python -m pytest -v`.
- Run the portal on port `8503`.
- Report the local URL.
- Report whether the Project Tracker production URL is still missing from `Apps.csv`.
- Report the latest commit hash.
