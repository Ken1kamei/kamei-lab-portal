import importlib
import runpy
import sys
from pathlib import Path

from lab_portal.portal.storage import CsvRegistryStore
from streamlit_app.progress_tracker.storage import SharedRegistryLedgerStore


def test_streamlit_app_imports():
    module = importlib.import_module("streamlit_app.app")
    assert hasattr(module, "main")
    assert hasattr(module, "save_ledger")
    assert module.APP_TITLE == "Project Tracker"


def test_streamlit_app_uses_shared_registry_store_without_sheet_secrets(monkeypatch):
    module = importlib.import_module("streamlit_app.app")
    monkeypatch.setattr(module.st, "secrets", {})

    store = module.get_ledger_store()

    assert isinstance(store, SharedRegistryLedgerStore)
    assert isinstance(store.registry_store, CsvRegistryStore)


def test_streamlit_app_script_path_loads_without_running_main():
    result = runpy.run_path("streamlit_app/app.py", run_name="__streamlit_test__")
    assert "main" in result


def test_streamlit_app_script_path_loads_without_package_path(monkeypatch):
    project_root = str(Path.cwd())
    script_dir = str(Path.cwd() / "streamlit_app")
    monkeypatch.setattr(sys, "path", [script_dir, *[path for path in sys.path if path not in {"", project_root}]])

    result = runpy.run_path("streamlit_app/app.py", run_name="__streamlit_test__")

    assert "main" in result
