import importlib

from lab_portal.portal.auth import authenticated_email


def test_lab_portal_app_imports():
    module = importlib.import_module("lab_portal.app")

    assert module.APP_TITLE == "Kamei Lab Portal"
    assert module.VIEWS == ["Home", "Members", "Teams", "App Access", "Audit"]


def test_authenticated_email_uses_dev_environment(monkeypatch):
    monkeypatch.setenv("PORTAL_DEV_EMAIL", "dev@example.edu")

    assert authenticated_email() == "dev@example.edu"


def test_authenticated_email_returns_empty_without_login(monkeypatch):
    monkeypatch.delenv("PORTAL_DEV_EMAIL", raising=False)

    assert authenticated_email() == ""
