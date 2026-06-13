import importlib
import runpy
import sys
from pathlib import Path

from lab_portal.portal.auth import authenticated_email
from lab_portal.portal.storage import CsvRegistryStore


def test_lab_portal_app_imports():
    module = importlib.import_module("lab_portal.app")

    assert module.APP_TITLE == "Kamei Lab Portal"
    assert module.VIEWS == ["Home", "Members", "Teams", "App Access", "Audit"]


def test_lab_portal_uses_csv_store_without_sheet_secrets(monkeypatch):
    module = importlib.import_module("lab_portal.app")
    monkeypatch.setattr(module.st, "secrets", {})

    assert isinstance(module.get_registry_store(), CsvRegistryStore)


def test_lab_portal_uses_csv_store_when_secrets_file_is_missing(monkeypatch):
    module = importlib.import_module("lab_portal.app")

    class MissingSecrets:
        def get(self, _key, _default=None):
            raise module.StreamlitSecretNotFoundError("No secrets found")

    monkeypatch.setattr(module.st, "secrets", MissingSecrets())

    assert isinstance(module.get_registry_store(), CsvRegistryStore)


def test_lab_portal_app_script_path_loads_without_package_path(monkeypatch):
    project_root = str(Path.cwd())
    script_dir = str(Path.cwd() / "lab_portal")
    monkeypatch.setattr(sys, "path", [script_dir, *[path for path in sys.path if path not in {"", project_root}]])

    result = runpy.run_path("lab_portal/app.py", run_name="__streamlit_test__")

    assert "main" in result


def test_authenticated_email_uses_dev_environment(monkeypatch):
    monkeypatch.setenv("PORTAL_DEV_EMAIL", "dev@example.edu")

    assert authenticated_email() == "dev@example.edu"


def test_authenticated_email_returns_empty_without_login(monkeypatch):
    monkeypatch.delenv("PORTAL_DEV_EMAIL", raising=False)

    assert authenticated_email() == ""


def test_authenticated_email_ignores_empty_dev_environment(monkeypatch):
    monkeypatch.setenv("PORTAL_DEV_EMAIL", "")

    assert authenticated_email() == ""
