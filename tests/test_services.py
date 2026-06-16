from pathlib import Path

import pytest

from streamlit_app.progress_tracker.services import (
    create_milestone,
    create_project,
    import_from_excel_bytes,
    import_from_docx_bytes,
    review_record,
    update_progress_record,
)
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


def test_member_update_preserves_blank_blocker_reason_validation():
    ledger = _sample_ledger()

    with pytest.raises(ValueError, match="Blocked records require blocker_reason."):
        update_progress_record(
            ledger,
            table_name="Experiments",
            record_id_column="experiment_id",
            record_id="EXP001",
            updated_by="M003",
            changes={"status": "Blocked", "blocker_reason": None},
            update_note="Blocked by missing reagent",
            timestamp="2026-06-13T10:15:00",
        )


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


def test_create_project_adds_project_row():
    ledger = _sample_ledger()
    created = create_project(
        ledger,
        project="Organoid interface",
        aim="Aim 3",
        owner_member_id="M002",
        start_date="2026-06-16",
        target_date="2026-12-31",
        notes="Manual entry",
    )

    assert "Organoid interface" in set(created["Projects"]["project"])


def test_create_milestone_requires_owner():
    ledger = _sample_ledger()

    with pytest.raises(ValueError, match="owner_member_id or member_id is required."):
        create_milestone(
            ledger,
            project_id="P001",
            project="Endometriosis-associated implantation failure on chip",
            aim="Aim 1",
            milestone="Missing owner",
            time_window="Months 0-1",
            owner_member_id="",
            start_date="2026-06-16",
            status="Planned",
            review_status="Pending",
            next_action="Assign owner",
            due_date="2026-07-01",
            blocker_reason="",
            help_needed_from="",
            updated_at="2026-06-16T09:00:00",
        )


def test_import_projects_from_excel_bytes_adds_project_and_milestone():
    ledger = _sample_ledger()
    import pandas as pd
    from io import BytesIO

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame(
            [
                {
                    "project": "Imported project",
                    "aim": "Aim X",
                    "owner_member_id": "M001",
                    "start_date": "2026-06-16",
                    "target_date": "2026-12-31",
                    "notes": "From Excel",
                }
            ]
        ).to_excel(writer, sheet_name="Projects", index=False)
        pd.DataFrame(
            [
                {
                    "project": "Imported project",
                    "aim": "Aim X",
                    "milestone": "Imported milestone",
                    "time_window": "Months 1-2",
                    "owner_member_id": "M002",
                    "start_date": "2026-06-16",
                    "status": "Planned",
                    "review_status": "Pending",
                    "next_action": "Review",
                    "due_date": "2026-07-01",
                    "blocker_reason": "",
                    "help_needed_from": "",
                    "updated_at": "2026-06-16T09:00:00",
                }
            ]
        ).to_excel(writer, sheet_name="Milestones", index=False)
    created = import_from_excel_bytes(ledger, buffer.getvalue())
    assert "Imported project" in set(created["Projects"]["project"])
    assert "Imported milestone" in set(created["Milestones"]["milestone"])


def test_import_projects_from_docx_bytes_adds_project():
    ledger = _sample_ledger()
    from docx import Document
    from io import BytesIO

    document = Document()
    table = document.add_table(rows=2, cols=6)
    headers = ["project", "aim", "owner_member_id", "start_date", "target_date", "notes"]
    for idx, header in enumerate(headers):
        table.rows[0].cells[idx].text = header
    values = ["Docx project", "Aim Y", "M003", "2026-06-16", "2026-12-31", "From Word"]
    for idx, value in enumerate(values):
        table.rows[1].cells[idx].text = value
    buffer = BytesIO()
    document.save(buffer)

    created = import_from_docx_bytes(ledger, buffer.getvalue())
    assert "Docx project" in set(created["Projects"]["project"])
