from pathlib import Path

import pandas as pd

from lab_portal.portal.storage import CsvRegistryStore
from streamlit_app.progress_tracker.storage import CsvLedgerStore, GoogleSheetLedgerStore, SharedRegistryLedgerStore


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


def test_csv_store_loads_all_sample_tables():
    store = CsvLedgerStore(Path("streamlit_app/data/sample"))
    ledger = store.load()

    assert set(ledger) == {
        "Members",
        "Teams",
        "Member_Teams",
        "Projects",
        "Milestones",
        "Experiments",
        "Updates_Reviews",
    }
    assert ledger["Members"].loc[0, "name"] == "Ken Kamei"
    assert "Assay Development" in set(ledger["Teams"]["team_name"])
    assert {"M002", "M003"}.issubset(set(ledger["Member_Teams"]["member_id"]))
    assert ledger["Experiments"].loc[0, "experiment_data_link"].startswith("https://www.dropbox.com/")


def test_csv_store_round_trip(tmp_path):
    store = CsvLedgerStore(Path("streamlit_app/data/sample"))
    ledger = store.load()
    output_store = CsvLedgerStore(tmp_path)

    output_store.save(ledger)
    reloaded = output_store.load()

    pd.testing.assert_frame_equal(reloaded["Milestones"], ledger["Milestones"])
    pd.testing.assert_frame_equal(reloaded["Teams"], ledger["Teams"])
    pd.testing.assert_frame_equal(reloaded["Member_Teams"], ledger["Member_Teams"])
    pd.testing.assert_frame_equal(reloaded["Updates_Reviews"], ledger["Updates_Reviews"])


def test_shared_registry_store_loads_members_and_teams_from_portal_registry():
    store = SharedRegistryLedgerStore(
        CsvLedgerStore(Path("streamlit_app/data/sample")),
        CsvRegistryStore(Path("lab_portal/data/sample")),
    )

    ledger = store.load()

    assert ledger["Members"].set_index("member_id").loc["M001", "email"] == "kkamei@nyu.edu"
    assert ledger["Members"].set_index("member_id").loc["M001", "name"] == "Ken"
    assert set(ledger["Teams"]["team_name"]) == {"Core Lab", "Endometriosis Project"}
    assert set(ledger["Member_Teams"]["member_id"]) == {"M001", "M002", "M003"}
    assert "Projects" in ledger


def test_shared_registry_store_saves_progress_tables_without_overwriting_member_registry(tmp_path):
    source = CsvLedgerStore(Path("streamlit_app/data/sample"))
    progress_store = CsvLedgerStore(tmp_path)
    progress_store.save(source.load())
    store = SharedRegistryLedgerStore(progress_store, CsvRegistryStore(Path("lab_portal/data/sample")))
    ledger = store.load()
    ledger["Updates_Reviews"].loc[len(ledger["Updates_Reviews"])] = {
        "update_id": "UP999",
        "record_type": "Experiment",
        "record_id": "EXP001",
        "updated_by": "M003",
        "update_note": "Shared registry save test",
        "old_status": "Running",
        "new_status": "Analyzing",
        "reviewed_by": "",
        "review_status": "Pending",
        "review_note": "",
        "timestamp": "2026-06-14T00:00:00+00:00",
    }

    store.save(ledger)
    raw_reloaded = CsvLedgerStore(tmp_path).load()

    assert "UP999" in set(raw_reloaded["Updates_Reviews"]["update_id"])
    assert raw_reloaded["Members"].set_index("member_id").loc["M001", "email"] == "kk4801@nyu.edu"


def test_google_sheet_ledger_store_loads_progress_tables_and_leaves_shared_tables_empty():
    spreadsheet = FakeSpreadsheet(
        {
            "Projects": FakeWorksheet(
                [
                    {
                        "project_id": "P001",
                        "project": "Endometriosis",
                        "aim": "Aim 1",
                        "owner_member_id": "M001",
                        "start_date": "2026-06-01",
                        "target_date": "2026-08-01",
                        "notes": "Pilot",
                    }
                ]
            ),
            "Milestones": FakeWorksheet([]),
            "Experiments": FakeWorksheet([]),
            "Updates_Reviews": FakeWorksheet([]),
        }
    )

    ledger = GoogleSheetLedgerStore(spreadsheet).load()

    assert ledger["Members"].empty
    assert ledger["Projects"].loc[0, "project_id"] == "P001"


def test_google_sheet_ledger_store_saves_only_progress_tables():
    spreadsheet = FakeSpreadsheet(
        {
            "Projects": FakeWorksheet([]),
            "Milestones": FakeWorksheet([]),
            "Experiments": FakeWorksheet([]),
            "Updates_Reviews": FakeWorksheet([]),
        }
    )
    ledger = CsvLedgerStore(Path("streamlit_app/data/sample")).load()

    GoogleSheetLedgerStore(spreadsheet).save(ledger)

    assert spreadsheet.worksheets["Milestones"].updated_rows[0] == list(ledger["Milestones"].columns)
    assert "Members" not in spreadsheet.worksheets
