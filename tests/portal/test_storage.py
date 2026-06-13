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
