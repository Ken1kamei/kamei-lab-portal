from pathlib import Path

from streamlit_app.progress_tracker.storage import CsvLedgerStore
from streamlit_app.progress_tracker.summary import (
    completed_records,
    filter_ledger_by_team,
    milestone_gantt_data,
    overview_counts,
    overview_summary_rows,
    records_by_member,
    team_gantt_data,
    team_options,
)


def test_overview_counts_include_pending_and_blocked():
    ledger = CsvLedgerStore(Path("streamlit_app/data/sample")).load()
    counts = overview_counts(ledger)

    assert counts["milestones_total"] == 2
    assert counts["experiments_total"] == 1
    assert counts["pending_review"] == 3
    assert counts["blocked"] == 0


def test_overview_summary_rows_are_plain_table_data():
    ledger = CsvLedgerStore(Path("streamlit_app/data/sample")).load()
    rows = overview_summary_rows(ledger)

    assert list(rows.columns) == ["metric", "value"]
    assert rows.to_dict("records") == [
        {"metric": "Milestones", "value": 2},
        {"metric": "Experiments", "value": 1},
        {"metric": "Pending review", "value": 3},
        {"metric": "Blocked", "value": 0},
    ]


def test_records_by_member_includes_member_names():
    ledger = CsvLedgerStore(Path("streamlit_app/data/sample")).load()
    grouped = records_by_member(ledger)

    assert "Lab Member" in set(grouped["member_name"])
    lab_member_rows = grouped[grouped["member_name"] == "Lab Member"]
    assert "Hormone conditioning pilot" in set(lab_member_rows["title"])


def test_milestone_gantt_data_uses_start_and_due_dates():
    ledger = CsvLedgerStore(Path("streamlit_app/data/sample")).load()
    gantt = milestone_gantt_data(ledger)

    assert list(gantt.columns) == [
        "milestone_id",
        "project",
        "aim",
        "milestone",
        "time_window",
        "owner_member_id",
        "status",
        "review_status",
        "start_date",
        "end_date",
    ]
    first = gantt.loc[gantt["milestone_id"] == "MS001"].iloc[0]
    assert str(first["start_date"].date()) == "2026-06-01"
    assert str(first["end_date"].date()) == "2026-07-15"


def test_team_gantt_data_combines_member_milestones_and_experiments():
    ledger = CsvLedgerStore(Path("streamlit_app/data/sample")).load()
    gantt = team_gantt_data(ledger)

    assert list(gantt.columns) == [
        "record_type",
        "record_id",
        "team_member",
        "project",
        "aim",
        "title",
        "status",
        "review_status",
        "start_date",
        "end_date",
        "lane",
    ]
    assert {"Milestone", "Experiment"} == set(gantt["record_type"])
    assert "Project Lead / Healthy receptive chip setup" in set(gantt["lane"])
    assert "Lab Member / Hormone conditioning pilot" in set(gantt["lane"])


def test_completed_records_include_done_milestones_and_experiments():
    ledger = CsvLedgerStore(Path("streamlit_app/data/sample")).load()
    ledger["Milestones"].loc[ledger["Milestones"]["milestone_id"] == "MS001", "status"] = "Completed"
    ledger["Milestones"].loc[ledger["Milestones"]["milestone_id"] == "MS001", "review_status"] = "Approved"
    ledger["Experiments"].loc[ledger["Experiments"]["experiment_id"] == "EXP001", "status"] = "Completed"

    done = completed_records(ledger)

    assert list(done["record_type"]) == ["Milestone", "Experiment"]
    assert "Healthy receptive chip setup" in set(done["title"])
    assert "Hormone conditioning pilot" in set(done["title"])
    assert set(done["aim"]) == {"Aim 1"}


def test_team_options_include_all_and_active_teams():
    ledger = CsvLedgerStore(Path("streamlit_app/data/sample")).load()

    assert team_options(ledger) == ["All teams", "Endometriosis Core", "Assay Development", "Data Analysis"]


def test_filter_ledger_by_team_scopes_member_records_without_dropping_tables():
    ledger = CsvLedgerStore(Path("streamlit_app/data/sample")).load()
    filtered = filter_ledger_by_team(ledger, "Data Analysis")

    assert set(filtered) == set(ledger)
    assert set(filtered["Members"]["member_id"]) == {"M001", "M003"}
    assert list(filtered["Milestones"]["milestone_id"]) == ["MS002"]
    assert list(filtered["Experiments"]["experiment_id"]) == ["EXP001"]
    assert len(ledger["Milestones"]) == 2


def test_filter_ledger_by_all_teams_keeps_everything():
    ledger = CsvLedgerStore(Path("streamlit_app/data/sample")).load()
    filtered = filter_ledger_by_team(ledger, "All teams")

    assert len(filtered["Members"]) == len(ledger["Members"])
    assert len(filtered["Milestones"]) == len(ledger["Milestones"])
    assert len(filtered["Experiments"]) == len(ledger["Experiments"])
