import importlib
import runpy
import sys
from pathlib import Path

from lab_portal.portal.storage import CsvRegistryStore
from streamlit_app.progress_tracker.storage import GoogleSheetLedgerStore, SharedRegistryLedgerStore


def test_streamlit_app_imports():
    module = importlib.import_module("streamlit_app.app")
    assert hasattr(module, "main")
    assert hasattr(module, "save_ledger")
    assert module.APP_TITLE == "Project Tracker"
    assert "Projects" in module.VIEWS


def test_streamlit_app_uses_shared_registry_store_without_sheet_secrets(monkeypatch):
    module = importlib.import_module("streamlit_app.app")
    monkeypatch.setattr(module.st, "secrets", {})

    store = module.get_ledger_store()

    assert isinstance(store, SharedRegistryLedgerStore)
    assert isinstance(store.registry_store, CsvRegistryStore)


def test_streamlit_app_uses_google_sheet_progress_store_with_progress_secret(monkeypatch):
    module = importlib.import_module("streamlit_app.app")

    class FakeClient:
        def __init__(self):
            self.opened_key = None

        def open_by_key(self, key):
            self.opened_key = key
            return {"spreadsheet_key": key}

    fake_client = FakeClient()
    monkeypatch.setattr(
        module.st,
        "secrets",
        {
            "PROGRESS_SPREADSHEET_ID": "progress-sheet-123",
            "gcp_service_account": {"client_email": "service@example.iam.gserviceaccount.com"},
        },
    )
    monkeypatch.setattr(module, "_gspread_service_account_from_dict", lambda _info: fake_client)

    store = module.get_ledger_store()

    assert isinstance(store.progress_store, GoogleSheetLedgerStore)
    assert fake_client.opened_key == "progress-sheet-123"


def test_streamlit_app_reports_shared_data_sources():
    module = importlib.import_module("streamlit_app.app")
    settings = module.PortalSettings(
        registry_spreadsheet_id="registry-sheet-123",
        progress_spreadsheet_id="progress-sheet-456",
        service_account_info={"client_email": "service@example.iam.gserviceaccount.com"},
    )

    assert module.shared_data_source_labels(settings) == ("Google Sheet", "Google Sheet")
    assert module.shared_data_source_labels(module.PortalSettings()) == ("Sample CSV", "Sample CSV")


def test_streamlit_app_script_path_loads_without_running_main():
    result = runpy.run_path("streamlit_app/app.py", run_name="__streamlit_test__")
    assert "main" in result


def test_streamlit_app_script_path_loads_without_package_path(monkeypatch):
    project_root = str(Path.cwd())
    script_dir = str(Path.cwd() / "streamlit_app")
    monkeypatch.setattr(sys, "path", [script_dir, *[path for path in sys.path if path not in {"", project_root}]])

    result = runpy.run_path("streamlit_app/app.py", run_name="__streamlit_test__")

    assert "main" in result
