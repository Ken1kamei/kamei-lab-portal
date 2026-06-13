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
