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
    assert TABLES == ["Members", "Teams", "Member_Teams", "Projects", "Milestones", "Experiments", "Updates_Reviews"]
    assert REQUIRED_COLUMNS["Teams"] == ["team_id", "team_name", "active"]
    assert REQUIRED_COLUMNS["Member_Teams"] == ["member_id", "team_id"]
    assert "start_date" in REQUIRED_COLUMNS["Milestones"]
    assert "experiment_data_link" in REQUIRED_COLUMNS["Experiments"]
    assert "analysis_folder_link" in REQUIRED_COLUMNS["Experiments"]
    assert "review_note" in REQUIRED_COLUMNS["Updates_Reviews"]


def test_empty_ledger_has_all_tables_and_columns():
    ledger = empty_ledger()
    assert set(ledger) == set(TABLES)
    for table_name, columns in REQUIRED_COLUMNS.items():
        assert list(ledger[table_name].columns) == columns
