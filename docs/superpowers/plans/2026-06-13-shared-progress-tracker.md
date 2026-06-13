# Shared Progress Tracker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Streamlit prototype that tracks member milestones, experiments, Dropbox data links, and Lead/PI review state from a Google Sheet-compatible CSV ledger.

**Architecture:** Create a new `streamlit_app/` subproject. Keep domain logic in small Python modules under `streamlit_app/progress_tracker/`, keep sample ledger CSVs under `streamlit_app/data/sample/`, and keep Streamlit UI assembly in `streamlit_app/app.py`. The first version uses local CSV storage with interfaces that can be swapped for a Google Sheet adapter.

**Tech Stack:** Python 3, Streamlit, pandas, pytest, local CSV files.

---

## File Structure

- Create `requirements.txt`: Python dependencies for the prototype and tests.
- Create `streamlit_app/app.py`: Streamlit entrypoint and tab wiring.
- Create `streamlit_app/__init__.py`: package marker.
- Create `streamlit_app/progress_tracker/__init__.py`: package marker.
- Create `streamlit_app/progress_tracker/constants.py`: allowed statuses, review statuses, table names.
- Create `streamlit_app/progress_tracker/schema.py`: required columns and sample row builders.
- Create `streamlit_app/progress_tracker/storage.py`: CSV ledger reader/writer.
- Create `streamlit_app/progress_tracker/validation.py`: field validation for records and URLs.
- Create `streamlit_app/progress_tracker/services.py`: update, review, and history logic.
- Create `streamlit_app/progress_tracker/summary.py`: overview and grouped dashboard summaries.
- Create `streamlit_app/progress_tracker/views.py`: reusable Streamlit rendering helpers.
- Create `streamlit_app/data/sample/*.csv`: sample Members, Projects, Milestones, Experiments, Updates/Reviews tables.
- Create `tests/test_schema.py`: schema contract tests.
- Create `tests/test_storage.py`: local CSV storage tests.
- Create `tests/test_validation.py`: required-field and URL validation tests.
- Create `tests/test_services.py`: member update and review workflow tests.
- Create `tests/test_summary.py`: dashboard aggregation tests.
- Create `tests/test_app_smoke.py`: app import smoke test.

## Task 1: Scaffold Schema and Constants

**Files:**
- Create: `requirements.txt`
- Create: `streamlit_app/__init__.py`
- Create: `streamlit_app/progress_tracker/__init__.py`
- Create: `streamlit_app/progress_tracker/constants.py`
- Create: `streamlit_app/progress_tracker/schema.py`
- Test: `tests/test_schema.py`

- [ ] **Step 1: Write the failing schema tests**

Create `tests/test_schema.py`:

```python
from streamlit_app.progress_tracker.constants import REVIEW_STATUSES, STATUSES, TABLES
from streamlit_app.progress_tracker.schema import REQUIRED_COLUMNS, empty_ledger


def test_status_vocabularies_match_spec():
    assert STATUSES == [
        "Planned",
        "Preparing",
        "Running",
        "Data acquired",
        "Analyzing",
        "Review needed",
        "Completed",
        "Blocked",
    ]
    assert REVIEW_STATUSES == ["Pending", "Approved", "Needs revision"]


def test_required_columns_include_spec_fields():
    assert TABLES == ["Members", "Projects", "Milestones", "Experiments", "Updates_Reviews"]
    assert "experiment_data_link" in REQUIRED_COLUMNS["Experiments"]
    assert "analysis_folder_link" in REQUIRED_COLUMNS["Experiments"]
    assert "review_note" in REQUIRED_COLUMNS["Updates_Reviews"]


def test_empty_ledger_has_all_tables_and_columns():
    ledger = empty_ledger()
    assert set(ledger) == set(TABLES)
    for table_name, columns in REQUIRED_COLUMNS.items():
        assert list(ledger[table_name].columns) == columns
```

- [ ] **Step 2: Run the schema tests to verify they fail**

Run:

```bash
python -m pytest tests/test_schema.py -v
```

Expected: FAIL with `ModuleNotFoundError` because `streamlit_app.progress_tracker` does not exist yet.

- [ ] **Step 3: Add dependencies and schema implementation**

Create `requirements.txt`:

```text
pandas>=2.2
pytest>=8.2
streamlit>=1.35
```

Create `streamlit_app/__init__.py`:

```python
"""Streamlit prototype package for the shared progress tracker."""
```

Create `streamlit_app/progress_tracker/__init__.py`:

```python
"""Domain logic for the shared progress tracker."""
```

Create `streamlit_app/progress_tracker/constants.py`:

```python
STATUSES = [
    "Planned",
    "Preparing",
    "Running",
    "Data acquired",
    "Analyzing",
    "Review needed",
    "Completed",
    "Blocked",
]

REVIEW_STATUSES = ["Pending", "Approved", "Needs revision"]

TABLES = ["Members", "Projects", "Milestones", "Experiments", "Updates_Reviews"]
```

Create `streamlit_app/progress_tracker/schema.py`:

```python
from __future__ import annotations

import pandas as pd

from .constants import TABLES


REQUIRED_COLUMNS = {
    "Members": ["member_id", "name", "email", "role", "team", "lead_id", "active"],
    "Projects": [
        "project_id",
        "project",
        "aim",
        "owner_member_id",
        "start_date",
        "target_date",
        "notes",
    ],
    "Milestones": [
        "milestone_id",
        "project_id",
        "project",
        "aim",
        "milestone",
        "time_window",
        "owner_member_id",
        "status",
        "review_status",
        "next_action",
        "due_date",
        "blocker_reason",
        "help_needed_from",
        "updated_at",
    ],
    "Experiments": [
        "experiment_id",
        "milestone_id",
        "project_id",
        "member_id",
        "experiment_title",
        "experiment_type",
        "status",
        "review_status",
        "next_action",
        "due_date",
        "experiment_data_link",
        "protocol_link",
        "analysis_folder_link",
        "blocker_reason",
        "help_needed_from",
        "updated_at",
    ],
    "Updates_Reviews": [
        "update_id",
        "record_type",
        "record_id",
        "updated_by",
        "update_note",
        "old_status",
        "new_status",
        "reviewed_by",
        "review_status",
        "review_note",
        "timestamp",
    ],
}


def empty_ledger() -> dict[str, pd.DataFrame]:
    return {table_name: pd.DataFrame(columns=REQUIRED_COLUMNS[table_name]) for table_name in TABLES}
```

- [ ] **Step 4: Run the schema tests to verify they pass**

Run:

```bash
python -m pytest tests/test_schema.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt streamlit_app/__init__.py streamlit_app/progress_tracker/__init__.py streamlit_app/progress_tracker/constants.py streamlit_app/progress_tracker/schema.py tests/test_schema.py
git commit -m "feat: scaffold progress tracker schema"
```

## Task 2: Add Sample Ledger and CSV Storage

**Files:**
- Create: `streamlit_app/progress_tracker/storage.py`
- Create: `streamlit_app/data/sample/Members.csv`
- Create: `streamlit_app/data/sample/Projects.csv`
- Create: `streamlit_app/data/sample/Milestones.csv`
- Create: `streamlit_app/data/sample/Experiments.csv`
- Create: `streamlit_app/data/sample/Updates_Reviews.csv`
- Test: `tests/test_storage.py`

- [ ] **Step 1: Write the failing storage tests**

Create `tests/test_storage.py`:

```python
from pathlib import Path

import pandas as pd

from streamlit_app.progress_tracker.storage import CsvLedgerStore


def test_csv_store_loads_all_sample_tables():
    store = CsvLedgerStore(Path("streamlit_app/data/sample"))
    ledger = store.load()

    assert set(ledger) == {"Members", "Projects", "Milestones", "Experiments", "Updates_Reviews"}
    assert ledger["Members"].loc[0, "name"] == "Ken Kamei"
    assert ledger["Experiments"].loc[0, "experiment_data_link"].startswith("https://www.dropbox.com/")


def test_csv_store_round_trip(tmp_path):
    store = CsvLedgerStore(Path("streamlit_app/data/sample"))
    ledger = store.load()
    output_store = CsvLedgerStore(tmp_path)

    output_store.save(ledger)
    reloaded = output_store.load()

    pd.testing.assert_frame_equal(reloaded["Milestones"], ledger["Milestones"])
    pd.testing.assert_frame_equal(reloaded["Updates_Reviews"], ledger["Updates_Reviews"])
```

- [ ] **Step 2: Run the storage tests to verify they fail**

Run:

```bash
python -m pytest tests/test_storage.py -v
```

Expected: FAIL with `ImportError` because `CsvLedgerStore` is not defined.

- [ ] **Step 3: Add sample CSV files**

Create `streamlit_app/data/sample/Members.csv`:

```csv
member_id,name,email,role,team,lead_id,active
M001,Ken Kamei,kk4801@nyu.edu,PI,Endometriosis,,TRUE
M002,Project Lead,lead@example.edu,Lead,Endometriosis,M001,TRUE
M003,Lab Member,member@example.edu,Member,Endometriosis,M002,TRUE
```

Create `streamlit_app/data/sample/Projects.csv`:

```csv
project_id,project,aim,owner_member_id,start_date,target_date,notes
P001,Endometriosis-associated implantation failure on chip,Aim 1,M001,2026-06-01,2026-12-31,Baseline receptive chip and attachment assay
```

Create `streamlit_app/data/sample/Milestones.csv`:

```csv
milestone_id,project_id,project,aim,milestone,time_window,owner_member_id,status,review_status,next_action,due_date,blocker_reason,help_needed_from,updated_at
MS001,P001,Endometriosis-associated implantation failure on chip,Aim 1,Healthy receptive chip setup,Months 0-3,M002,Preparing,Pending,Confirm hormone conditioning schedule,2026-07-15,,,2026-06-13T09:00:00
MS002,P001,Endometriosis-associated implantation failure on chip,Aim 1,Blastoid attachment assay,Months 0-3,M003,Planned,Pending,Prepare initial experiment sheet,2026-08-01,,,2026-06-13T09:00:00
```

Create `streamlit_app/data/sample/Experiments.csv`:

```csv
experiment_id,milestone_id,project_id,member_id,experiment_title,experiment_type,status,review_status,next_action,due_date,experiment_data_link,protocol_link,analysis_folder_link,blocker_reason,help_needed_from,updated_at
EXP001,MS001,P001,M003,Hormone conditioning pilot,Chip setup,Running,Pending,Upload day 3 images and notes,2026-06-30,https://www.dropbox.com/s/example/endometriosis-chip-pilot-data,https://www.dropbox.com/s/example/protocol,https://www.dropbox.com/s/example/analysis,,,2026-06-13T09:00:00
```

Create `streamlit_app/data/sample/Updates_Reviews.csv`:

```csv
update_id,record_type,record_id,updated_by,update_note,old_status,new_status,reviewed_by,review_status,review_note,timestamp
UPD001,Experiment,EXP001,M003,Started hormone conditioning pilot,Preparing,Running,M002,Pending,,2026-06-13T09:00:00
```

- [ ] **Step 4: Add CSV storage implementation**

Create `streamlit_app/progress_tracker/storage.py`:

```python
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .schema import REQUIRED_COLUMNS


class CsvLedgerStore:
    def __init__(self, directory: Path | str):
        self.directory = Path(directory)

    def load(self) -> dict[str, pd.DataFrame]:
        ledger: dict[str, pd.DataFrame] = {}
        for table_name, columns in REQUIRED_COLUMNS.items():
            path = self.directory / f"{table_name}.csv"
            if path.exists():
                frame = pd.read_csv(path, dtype=str, keep_default_na=False)
            else:
                frame = pd.DataFrame(columns=columns)
            missing = [column for column in columns if column not in frame.columns]
            if missing:
                raise ValueError(f"{path} is missing required columns: {', '.join(missing)}")
            ledger[table_name] = frame[columns].copy()
        return ledger

    def save(self, ledger: dict[str, pd.DataFrame]) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        for table_name, columns in REQUIRED_COLUMNS.items():
            frame = ledger.get(table_name, pd.DataFrame(columns=columns)).copy()
            missing = [column for column in columns if column not in frame.columns]
            if missing:
                raise ValueError(f"{table_name} is missing required columns: {', '.join(missing)}")
            frame[columns].to_csv(self.directory / f"{table_name}.csv", index=False)
```

- [ ] **Step 5: Run storage tests to verify they pass**

Run:

```bash
python -m pytest tests/test_storage.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add streamlit_app/progress_tracker/storage.py streamlit_app/data/sample tests/test_storage.py
git commit -m "feat: add sample CSV ledger storage"
```

## Task 3: Implement Validation Rules

**Files:**
- Create: `streamlit_app/progress_tracker/validation.py`
- Test: `tests/test_validation.py`

- [ ] **Step 1: Write the failing validation tests**

Create `tests/test_validation.py`:

```python
from streamlit_app.progress_tracker.validation import validate_progress_record, validate_review


def test_blocked_requires_blocker_reason():
    errors = validate_progress_record(
        {"status": "Blocked", "review_status": "Pending", "next_action": "Ask core facility", "blocker_reason": ""}
    )
    assert errors == ["Blocked records require blocker_reason."]


def test_valid_dropbox_like_url_is_accepted():
    errors = validate_progress_record(
        {
            "status": "Running",
            "review_status": "Pending",
            "next_action": "Collect effluent",
            "experiment_data_link": "https://www.dropbox.com/s/example/data",
        }
    )
    assert errors == []


def test_invalid_url_is_rejected():
    errors = validate_progress_record(
        {
            "status": "Running",
            "review_status": "Pending",
            "next_action": "Collect effluent",
            "experiment_data_link": "dropbox folder",
        }
    )
    assert errors == ["experiment_data_link must be a valid http(s) URL."]


def test_needs_revision_requires_review_note():
    errors = validate_review({"review_status": "Needs revision", "review_note": ""})
    assert errors == ["Needs revision requires review_note."]
```

- [ ] **Step 2: Run validation tests to verify they fail**

Run:

```bash
python -m pytest tests/test_validation.py -v
```

Expected: FAIL with `ImportError` because `validation.py` is not defined.

- [ ] **Step 3: Add validation implementation**

Create `streamlit_app/progress_tracker/validation.py`:

```python
from __future__ import annotations

from urllib.parse import urlparse

from .constants import REVIEW_STATUSES, STATUSES


URL_FIELDS = ["experiment_data_link", "protocol_link", "analysis_folder_link"]


def _blank(value: object) -> bool:
    return value is None or str(value).strip() == ""


def _valid_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_progress_record(record: dict[str, object]) -> list[str]:
    errors: list[str] = []
    status = str(record.get("status", "")).strip()
    review_status = str(record.get("review_status", "")).strip()

    if status not in STATUSES:
        errors.append(f"status must be one of: {', '.join(STATUSES)}.")
    if review_status and review_status not in REVIEW_STATUSES:
        errors.append(f"review_status must be one of: {', '.join(REVIEW_STATUSES)}.")
    if _blank(record.get("next_action")):
        errors.append("next_action is required.")
    if status == "Blocked" and _blank(record.get("blocker_reason")):
        errors.append("Blocked records require blocker_reason.")

    for field in URL_FIELDS:
        value = str(record.get(field, "")).strip()
        if value and not _valid_http_url(value):
            errors.append(f"{field} must be a valid http(s) URL.")

    return errors


def validate_review(record: dict[str, object]) -> list[str]:
    errors: list[str] = []
    review_status = str(record.get("review_status", "")).strip()
    if review_status not in REVIEW_STATUSES:
        errors.append(f"review_status must be one of: {', '.join(REVIEW_STATUSES)}.")
    if review_status == "Needs revision" and _blank(record.get("review_note")):
        errors.append("Needs revision requires review_note.")
    return errors
```

- [ ] **Step 4: Run validation tests to verify they pass**

Run:

```bash
python -m pytest tests/test_validation.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add streamlit_app/progress_tracker/validation.py tests/test_validation.py
git commit -m "feat: add progress validation rules"
```

## Task 4: Implement Member Update and Lead/PI Review Services

**Files:**
- Create: `streamlit_app/progress_tracker/services.py`
- Test: `tests/test_services.py`

- [ ] **Step 1: Write the failing service tests**

Create `tests/test_services.py`:

```python
from pathlib import Path

from streamlit_app.progress_tracker.services import review_record, update_progress_record
from streamlit_app.progress_tracker.storage import CsvLedgerStore


def _sample_ledger():
    return CsvLedgerStore(Path("streamlit_app/data/sample")).load()


def test_member_update_sets_pending_and_writes_history():
    ledger = _sample_ledger()
    updated = update_progress_record(
        ledger,
        table_name="Experiments",
        record_id_column="experiment_id",
        record_id="EXP001",
        updated_by="M003",
        changes={"status": "Data acquired", "next_action": "Start image analysis"},
        update_note="Images collected and uploaded",
        timestamp="2026-06-13T10:00:00",
    )

    row = updated["Experiments"].loc[updated["Experiments"]["experiment_id"] == "EXP001"].iloc[0]
    assert row["status"] == "Data acquired"
    assert row["review_status"] == "Pending"
    assert row["next_action"] == "Start image analysis"
    assert len(updated["Updates_Reviews"]) == 2
    assert updated["Updates_Reviews"].iloc[-1]["update_note"] == "Images collected and uploaded"


def test_lead_review_approves_record_and_writes_history():
    ledger = _sample_ledger()
    reviewed = review_record(
        ledger,
        table_name="Experiments",
        record_id_column="experiment_id",
        record_id="EXP001",
        reviewed_by="M002",
        review_status="Approved",
        review_note="Looks ready for analysis",
        timestamp="2026-06-13T10:30:00",
    )

    row = reviewed["Experiments"].loc[reviewed["Experiments"]["experiment_id"] == "EXP001"].iloc[0]
    assert row["review_status"] == "Approved"
    assert reviewed["Updates_Reviews"].iloc[-1]["reviewed_by"] == "M002"
    assert reviewed["Updates_Reviews"].iloc[-1]["review_status"] == "Approved"
```

- [ ] **Step 2: Run service tests to verify they fail**

Run:

```bash
python -m pytest tests/test_services.py -v
```

Expected: FAIL with `ImportError` because `services.py` is not defined.

- [ ] **Step 3: Add service implementation**

Create `streamlit_app/progress_tracker/services.py`:

```python
from __future__ import annotations

import uuid

import pandas as pd

from .validation import validate_progress_record, validate_review


def _append_history(
    ledger: dict[str, pd.DataFrame],
    *,
    record_type: str,
    record_id: str,
    updated_by: str = "",
    update_note: str = "",
    old_status: str = "",
    new_status: str = "",
    reviewed_by: str = "",
    review_status: str = "",
    review_note: str = "",
    timestamp: str,
) -> None:
    history_row = {
        "update_id": f"UPD-{uuid.uuid4().hex[:10]}",
        "record_type": record_type,
        "record_id": record_id,
        "updated_by": updated_by,
        "update_note": update_note,
        "old_status": old_status,
        "new_status": new_status,
        "reviewed_by": reviewed_by,
        "review_status": review_status,
        "review_note": review_note,
        "timestamp": timestamp,
    }
    ledger["Updates_Reviews"] = pd.concat(
        [ledger["Updates_Reviews"], pd.DataFrame([history_row])], ignore_index=True
    )


def update_progress_record(
    ledger: dict[str, pd.DataFrame],
    *,
    table_name: str,
    record_id_column: str,
    record_id: str,
    updated_by: str,
    changes: dict[str, object],
    update_note: str,
    timestamp: str,
) -> dict[str, pd.DataFrame]:
    output = {name: frame.copy() for name, frame in ledger.items()}
    table = output[table_name].copy()
    mask = table[record_id_column] == record_id
    if not mask.any():
        raise ValueError(f"{table_name} record not found: {record_id}")

    index = table.index[mask][0]
    old_status = str(table.at[index, "status"])
    for key, value in changes.items():
        table.at[index, key] = str(value)
    table.at[index, "review_status"] = "Pending"
    table.at[index, "updated_at"] = timestamp

    errors = validate_progress_record(table.loc[index].to_dict())
    if errors:
        raise ValueError(" ".join(errors))

    output[table_name] = table
    _append_history(
        output,
        record_type=table_name[:-1],
        record_id=record_id,
        updated_by=updated_by,
        update_note=update_note,
        old_status=old_status,
        new_status=str(table.at[index, "status"]),
        review_status="Pending",
        timestamp=timestamp,
    )
    return output


def review_record(
    ledger: dict[str, pd.DataFrame],
    *,
    table_name: str,
    record_id_column: str,
    record_id: str,
    reviewed_by: str,
    review_status: str,
    review_note: str,
    timestamp: str,
) -> dict[str, pd.DataFrame]:
    output = {name: frame.copy() for name, frame in ledger.items()}
    table = output[table_name].copy()
    mask = table[record_id_column] == record_id
    if not mask.any():
        raise ValueError(f"{table_name} record not found: {record_id}")

    errors = validate_review({"review_status": review_status, "review_note": review_note})
    if errors:
        raise ValueError(" ".join(errors))

    index = table.index[mask][0]
    table.at[index, "review_status"] = review_status
    table.at[index, "updated_at"] = timestamp
    output[table_name] = table
    _append_history(
        output,
        record_type=table_name[:-1],
        record_id=record_id,
        reviewed_by=reviewed_by,
        review_status=review_status,
        review_note=review_note,
        timestamp=timestamp,
    )
    return output
```

- [ ] **Step 4: Run service tests to verify they pass**

Run:

```bash
python -m pytest tests/test_services.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add streamlit_app/progress_tracker/services.py tests/test_services.py
git commit -m "feat: add progress update review services"
```

## Task 5: Implement Dashboard Summaries

**Files:**
- Create: `streamlit_app/progress_tracker/summary.py`
- Test: `tests/test_summary.py`

- [ ] **Step 1: Write the failing summary tests**

Create `tests/test_summary.py`:

```python
from pathlib import Path

from streamlit_app.progress_tracker.storage import CsvLedgerStore
from streamlit_app.progress_tracker.summary import overview_counts, records_by_member


def test_overview_counts_include_pending_and_blocked():
    ledger = CsvLedgerStore(Path("streamlit_app/data/sample")).load()
    counts = overview_counts(ledger)

    assert counts["milestones_total"] == 2
    assert counts["experiments_total"] == 1
    assert counts["pending_review"] == 3
    assert counts["blocked"] == 0


def test_records_by_member_includes_member_names():
    ledger = CsvLedgerStore(Path("streamlit_app/data/sample")).load()
    grouped = records_by_member(ledger)

    assert "Lab Member" in set(grouped["member_name"])
    lab_member_rows = grouped[grouped["member_name"] == "Lab Member"]
    assert "Hormone conditioning pilot" in set(lab_member_rows["title"])
```

- [ ] **Step 2: Run summary tests to verify they fail**

Run:

```bash
python -m pytest tests/test_summary.py -v
```

Expected: FAIL with `ImportError` because `summary.py` is not defined.

- [ ] **Step 3: Add summary implementation**

Create `streamlit_app/progress_tracker/summary.py`:

```python
from __future__ import annotations

import pandas as pd


def overview_counts(ledger: dict[str, pd.DataFrame]) -> dict[str, int]:
    milestones = ledger["Milestones"]
    experiments = ledger["Experiments"]
    pending_review = int((milestones["review_status"] == "Pending").sum()) + int(
        (experiments["review_status"] == "Pending").sum()
    )
    blocked = int((milestones["status"] == "Blocked").sum()) + int((experiments["status"] == "Blocked").sum())
    return {
        "milestones_total": int(len(milestones)),
        "experiments_total": int(len(experiments)),
        "pending_review": pending_review,
        "blocked": blocked,
    }


def records_by_member(ledger: dict[str, pd.DataFrame]) -> pd.DataFrame:
    members = ledger["Members"][["member_id", "name"]].rename(columns={"name": "member_name"})
    milestones = ledger["Milestones"].rename(
        columns={"owner_member_id": "member_id", "milestone": "title"}
    )[["member_id", "title", "status", "review_status", "next_action", "due_date"]]
    milestones["record_type"] = "Milestone"

    experiments = ledger["Experiments"].rename(columns={"experiment_title": "title"})[
        ["member_id", "title", "status", "review_status", "next_action", "due_date"]
    ]
    experiments["record_type"] = "Experiment"

    combined = pd.concat([milestones, experiments], ignore_index=True)
    return combined.merge(members, on="member_id", how="left")[
        ["member_name", "record_type", "title", "status", "review_status", "next_action", "due_date"]
    ]
```

- [ ] **Step 4: Run summary tests to verify they pass**

Run:

```bash
python -m pytest tests/test_summary.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add streamlit_app/progress_tracker/summary.py tests/test_summary.py
git commit -m "feat: add dashboard summaries"
```

## Task 6: Build Streamlit Views and App Entrypoint

**Files:**
- Create: `streamlit_app/progress_tracker/views.py`
- Create: `streamlit_app/app.py`
- Test: `tests/test_app_smoke.py`

- [ ] **Step 1: Write the failing app smoke test**

Create `tests/test_app_smoke.py`:

```python
import importlib


def test_streamlit_app_imports():
    module = importlib.import_module("streamlit_app.app")
    assert hasattr(module, "main")
```

- [ ] **Step 2: Run app smoke test to verify it fails**

Run:

```bash
python -m pytest tests/test_app_smoke.py -v
```

Expected: FAIL with `ModuleNotFoundError` or missing `main`.

- [ ] **Step 3: Add reusable Streamlit view helpers**

Create `streamlit_app/progress_tracker/views.py`:

```python
from __future__ import annotations

import pandas as pd
import streamlit as st

from .constants import REVIEW_STATUSES, STATUSES
from .summary import overview_counts, records_by_member


def render_overview(ledger: dict[str, pd.DataFrame]) -> None:
    counts = overview_counts(ledger)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Milestones", counts["milestones_total"])
    col2.metric("Experiments", counts["experiments_total"])
    col3.metric("Pending review", counts["pending_review"])
    col4.metric("Blocked", counts["blocked"])

    blocked = pd.concat(
        [
            ledger["Milestones"].assign(record_type="Milestone", title=ledger["Milestones"]["milestone"]),
            ledger["Experiments"].assign(record_type="Experiment", title=ledger["Experiments"]["experiment_title"]),
        ],
        ignore_index=True,
    )
    blocked = blocked[blocked["status"] == "Blocked"]
    st.subheader("Blocked items")
    st.dataframe(blocked[["record_type", "title", "blocker_reason", "help_needed_from"]], use_container_width=True)


def render_members(ledger: dict[str, pd.DataFrame]) -> None:
    st.subheader("Progress by member")
    st.dataframe(records_by_member(ledger), use_container_width=True)


def render_milestones(ledger: dict[str, pd.DataFrame]) -> None:
    st.subheader("Milestones")
    frame = ledger["Milestones"]
    st.dataframe(
        frame[["project", "aim", "milestone", "time_window", "owner_member_id", "status", "review_status", "next_action"]],
        use_container_width=True,
    )


def render_experiments(ledger: dict[str, pd.DataFrame]) -> None:
    st.subheader("Experiments")
    frame = ledger["Experiments"].copy()
    for field in ["experiment_data_link", "protocol_link", "analysis_folder_link"]:
        frame[field] = frame[field].apply(lambda value: value if str(value).startswith("http") else "")
    st.dataframe(
        frame[
            [
                "experiment_title",
                "experiment_type",
                "member_id",
                "status",
                "review_status",
                "next_action",
                "due_date",
                "experiment_data_link",
                "analysis_folder_link",
            ]
        ],
        use_container_width=True,
        column_config={
            "experiment_data_link": st.column_config.LinkColumn("Data"),
            "analysis_folder_link": st.column_config.LinkColumn("Analysis"),
        },
    )


def render_review(ledger: dict[str, pd.DataFrame]) -> None:
    st.subheader("Review queue")
    review_items = pd.concat(
        [
            ledger["Milestones"].assign(record_type="Milestone", title=ledger["Milestones"]["milestone"]),
            ledger["Experiments"].assign(record_type="Experiment", title=ledger["Experiments"]["experiment_title"]),
        ],
        ignore_index=True,
    )
    review_items = review_items[review_items["review_status"].isin(["Pending", "Needs revision"])]
    st.dataframe(review_items[["record_type", "title", "status", "review_status", "next_action"]], use_container_width=True)


def render_member_update_form() -> None:
    st.subheader("Prototype update form")
    st.selectbox("Status", STATUSES)
    st.selectbox("Review status", REVIEW_STATUSES, index=0, disabled=True)
    st.text_input("Next action")
    st.text_area("Update note")
    st.text_input("Dropbox data link")
    st.info("The first prototype screen shows the form shape. Persistence is covered by service tests and can be wired to this form in the next task.")
```

- [ ] **Step 4: Add the Streamlit app entrypoint**

Create `streamlit_app/app.py`:

```python
from __future__ import annotations

from pathlib import Path

import streamlit as st

from .progress_tracker.storage import CsvLedgerStore
from .progress_tracker.views import (
    render_experiments,
    render_member_update_form,
    render_members,
    render_milestones,
    render_overview,
    render_review,
)


SAMPLE_LEDGER_DIR = Path(__file__).parent / "data" / "sample"


def load_ledger():
    return CsvLedgerStore(SAMPLE_LEDGER_DIR).load()


def main() -> None:
    st.set_page_config(page_title="Endometriosis Progress Tracker", layout="wide")
    st.title("Endometriosis Project Progress Tracker")
    st.caption("Prototype: local CSV ledger with Dropbox links")

    ledger = load_ledger()
    member_names = ledger["Members"]["name"].tolist()
    st.sidebar.selectbox("Member", member_names)
    st.sidebar.info("Prototype mode: member-name selection. Login roles are planned for Streamlit Cloud.")

    tabs = st.tabs(["Overview", "Members", "Milestones", "Experiments", "Review"])
    with tabs[0]:
        render_overview(ledger)
    with tabs[1]:
        render_members(ledger)
        render_member_update_form()
    with tabs[2]:
        render_milestones(ledger)
    with tabs[3]:
        render_experiments(ledger)
    with tabs[4]:
        render_review(ledger)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run app smoke test to verify it passes**

Run:

```bash
python -m pytest tests/test_app_smoke.py -v
```

Expected: PASS.

- [ ] **Step 6: Run all tests**

Run:

```bash
python -m pytest tests -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add streamlit_app/progress_tracker/views.py streamlit_app/app.py tests/test_app_smoke.py
git commit -m "feat: add streamlit progress tracker UI"
```

## Task 7: Wire Persistent Prototype Updates

**Files:**
- Modify: `streamlit_app/app.py`
- Modify: `streamlit_app/progress_tracker/views.py`
- Test: `tests/test_app_smoke.py`

- [ ] **Step 1: Extend the smoke test for app helper imports**

Modify `tests/test_app_smoke.py`:

```python
import importlib


def test_streamlit_app_imports():
    module = importlib.import_module("streamlit_app.app")
    assert hasattr(module, "main")
    assert hasattr(module, "save_ledger")
```

- [ ] **Step 2: Run the smoke test to verify it fails**

Run:

```bash
python -m pytest tests/test_app_smoke.py -v
```

Expected: FAIL because `save_ledger` is not defined.

- [ ] **Step 3: Add a save helper to the app**

Modify `streamlit_app/app.py`:

```python
from __future__ import annotations

from pathlib import Path

import streamlit as st

from .progress_tracker.storage import CsvLedgerStore
from .progress_tracker.views import (
    render_experiments,
    render_member_update_form,
    render_members,
    render_milestones,
    render_overview,
    render_review,
)


SAMPLE_LEDGER_DIR = Path(__file__).parent / "data" / "sample"


def load_ledger():
    return CsvLedgerStore(SAMPLE_LEDGER_DIR).load()


def save_ledger(ledger) -> None:
    CsvLedgerStore(SAMPLE_LEDGER_DIR).save(ledger)


def main() -> None:
    st.set_page_config(page_title="Endometriosis Progress Tracker", layout="wide")
    st.title("Endometriosis Project Progress Tracker")
    st.caption("Prototype: local CSV ledger with Dropbox links")

    ledger = load_ledger()
    member_names = ledger["Members"]["name"].tolist()
    selected_member = st.sidebar.selectbox("Member", member_names)
    selected_member_id = ledger["Members"].set_index("name").loc[selected_member, "member_id"]
    st.sidebar.info("Prototype mode: member-name selection. Login roles are planned for Streamlit Cloud.")

    tabs = st.tabs(["Overview", "Members", "Milestones", "Experiments", "Review"])
    with tabs[0]:
        render_overview(ledger)
    with tabs[1]:
        render_members(ledger)
    with tabs[2]:
        render_milestones(ledger)
    with tabs[3]:
        updated_ledger = render_member_update_form(ledger, selected_member_id)
        if updated_ledger is not ledger:
            save_ledger(updated_ledger)
            st.success("Progress update saved.")
            st.rerun()
        render_experiments(ledger)
    with tabs[4]:
        reviewed_ledger = render_review(ledger, selected_member_id)
        if reviewed_ledger is not ledger:
            save_ledger(reviewed_ledger)
            st.success("Review saved.")
            st.rerun()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Replace view form stubs with service-backed forms**

Modify the bottom of `streamlit_app/progress_tracker/views.py` so `render_review` and `render_member_update_form` are:

```python
from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from .constants import REVIEW_STATUSES, STATUSES
from .services import review_record, update_progress_record
from .summary import overview_counts, records_by_member


def render_review(ledger: dict[str, pd.DataFrame], reviewer_member_id: str) -> dict[str, pd.DataFrame]:
    st.subheader("Review queue")
    review_items = pd.concat(
        [
            ledger["Milestones"].assign(record_type="Milestones", record_id=ledger["Milestones"]["milestone_id"], title=ledger["Milestones"]["milestone"]),
            ledger["Experiments"].assign(record_type="Experiments", record_id=ledger["Experiments"]["experiment_id"], title=ledger["Experiments"]["experiment_title"]),
        ],
        ignore_index=True,
    )
    review_items = review_items[review_items["review_status"].isin(["Pending", "Needs revision"])]
    st.dataframe(review_items[["record_type", "record_id", "title", "status", "review_status", "next_action"]], use_container_width=True)

    if review_items.empty:
        return ledger

    choices = [f"{row.record_type}:{row.record_id} - {row.title}" for row in review_items.itertuples()]
    selected = st.selectbox("Review item", choices)
    record_type, rest = selected.split(":", 1)
    record_id = rest.split(" - ", 1)[0]
    review_status = st.selectbox("Decision", REVIEW_STATUSES, index=1)
    review_note = st.text_area("Review note")
    if st.button("Save review"):
        record_id_column = "milestone_id" if record_type == "Milestones" else "experiment_id"
        return review_record(
            ledger,
            table_name=record_type,
            record_id_column=record_id_column,
            record_id=record_id,
            reviewed_by=reviewer_member_id,
            review_status=review_status,
            review_note=review_note,
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )
    return ledger


def render_member_update_form(ledger: dict[str, pd.DataFrame], member_id: str) -> dict[str, pd.DataFrame]:
    st.subheader("Update my experiment")
    experiments = ledger["Experiments"]
    mine = experiments[experiments["member_id"] == member_id]
    if mine.empty:
        st.info("No experiments assigned to this member.")
        return ledger

    choices = [f"{row.experiment_id} - {row.experiment_title}" for row in mine.itertuples()]
    selected = st.selectbox("Experiment", choices)
    experiment_id = selected.split(" - ", 1)[0]
    current = mine[mine["experiment_id"] == experiment_id].iloc[0]
    status = st.selectbox("Status", STATUSES, index=STATUSES.index(current["status"]))
    next_action = st.text_input("Next action", value=current["next_action"])
    blocker_reason = st.text_input("Blocker reason", value=current["blocker_reason"])
    experiment_data_link = st.text_input("Dropbox data link", value=current["experiment_data_link"])
    update_note = st.text_area("Update note")

    if st.button("Save progress update"):
        return update_progress_record(
            ledger,
            table_name="Experiments",
            record_id_column="experiment_id",
            record_id=experiment_id,
            updated_by=member_id,
            changes={
                "status": status,
                "next_action": next_action,
                "blocker_reason": blocker_reason,
                "experiment_data_link": experiment_data_link,
            },
            update_note=update_note,
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )
    return ledger
```

Keep the existing `render_overview`, `render_members`, `render_milestones`, and `render_experiments` functions above these replacements.

- [ ] **Step 5: Run smoke test and all unit tests**

Run:

```bash
python -m pytest tests -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add streamlit_app/app.py streamlit_app/progress_tracker/views.py tests/test_app_smoke.py
git commit -m "feat: wire prototype progress persistence"
```

## Task 8: Add README and Manual Smoke Test

**Files:**
- Create: `streamlit_app/README.md`

- [ ] **Step 1: Create run documentation**

Create `streamlit_app/README.md`:

```markdown
# Endometriosis Project Progress Tracker

This is a local Streamlit prototype for shared milestone and experiment progress tracking.

## Data Model

The prototype reads and writes CSV files in `streamlit_app/data/sample/`. These CSV files mirror the planned Google Sheet tabs:

- `Members.csv`
- `Projects.csv`
- `Milestones.csv`
- `Experiments.csv`
- `Updates_Reviews.csv`

Dropbox experiment folders are stored as URL fields. The app does not store raw experimental data.

## Run Locally

```bash
python -m streamlit run streamlit_app/app.py
```

## Test

```bash
python -m pytest tests -v
```

## Prototype Workflow

1. Select a member name in the sidebar.
2. Open the Experiments tab.
3. Update an assigned experiment status, next action, and Dropbox data link.
4. Save the update.
5. Open the Review tab.
6. Approve the pending item or request revision with a review note.

## Shared Version Direction

After the workflow stabilizes, deploy to Streamlit Cloud and add login-based PI, Lead, and Member permissions. The local CSV adapter should be replaced or complemented by a Google Sheet adapter using the same logical table structure.
```

- [ ] **Step 2: Run the full test suite**

Run:

```bash
python -m pytest tests -v
```

Expected: PASS.

- [ ] **Step 3: Launch the app locally**

Run:

```bash
python -m streamlit run streamlit_app/app.py
```

Expected: Streamlit prints a local URL such as `http://localhost:8501`.

- [ ] **Step 4: Manual smoke test in the browser**

Open the Streamlit URL and verify:

- Overview shows milestone, experiment, pending review, and blocked counts.
- Members tab shows "Lab Member" and the assigned experiment.
- Milestones tab shows `Healthy receptive chip setup`.
- Experiments tab renders Dropbox links as clickable links.
- Experiment update form saves a changed status and sets `review_status` to `Pending`.
- Review tab shows the pending item and can save `Approved`.
- `Updates_Reviews.csv` gains a new history row after update and review actions.

- [ ] **Step 5: Commit**

```bash
git add streamlit_app/README.md
git commit -m "docs: add progress tracker runbook"
```

## Final Verification

- [ ] Run all tests:

```bash
python -m pytest tests -v
```

Expected: PASS.

- [ ] Run the Streamlit app:

```bash
python -m streamlit run streamlit_app/app.py
```

Expected: app opens locally and renders the five tabs.

- [ ] Check git status:

```bash
git status --short
```

Expected: no unexpected tracked changes. Existing untracked research artifacts may remain if they predated this work.
