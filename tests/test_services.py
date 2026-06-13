from pathlib import Path

import pytest

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
