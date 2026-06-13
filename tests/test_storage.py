from pathlib import Path

import pandas as pd

from streamlit_app.progress_tracker.storage import CsvLedgerStore


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
