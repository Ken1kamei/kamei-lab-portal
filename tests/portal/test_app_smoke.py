import importlib
import runpy
import sys
from pathlib import Path

from lab_portal.portal.auth import app_url_with_handoff, authenticated_email
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


def test_lab_portal_auth_configured_detects_default_provider(monkeypatch):
    module = importlib.import_module("lab_portal.app")
    monkeypatch.setattr(
        module.st,
        "secrets",
        {
            "auth": {
                "client_id": "client",
                "client_secret": "secret",
                "server_metadata_url": "https://accounts.google.com/.well-known/openid-configuration",
            }
        },
    )

    assert module.auth_configured() is True


def test_lab_portal_auth_configured_is_false_without_auth_secrets(monkeypatch):
    module = importlib.import_module("lab_portal.app")
    monkeypatch.setattr(module.st, "secrets", {})

    assert module.auth_configured() is False


def test_lab_portal_admin_passcode_configured(monkeypatch):
    module = importlib.import_module("lab_portal.app")
    monkeypatch.setattr(module.st, "secrets", {"PORTAL_ADMIN_PASSCODE": "let-me-in"})

    assert module.admin_passcode_configured() is True


def test_authenticated_email_uses_dev_environment(monkeypatch):
    monkeypatch.setenv("PORTAL_DEV_EMAIL", "dev@example.edu")

    assert authenticated_email() == "dev@example.edu"


def test_authenticated_email_uses_dev_secret(monkeypatch):
    import lab_portal.portal.auth as auth

    monkeypatch.delenv("PORTAL_DEV_EMAIL", raising=False)
    monkeypatch.setattr(auth.st, "secrets", {"PORTAL_DEV_EMAIL": "secret-admin@example.edu"})

    assert auth.authenticated_email() == "secret-admin@example.edu"


def test_authenticated_email_returns_empty_without_login(monkeypatch):
    monkeypatch.delenv("PORTAL_DEV_EMAIL", raising=False)

    assert authenticated_email() == ""


def test_authenticated_email_ignores_empty_dev_environment(monkeypatch):
    monkeypatch.setenv("PORTAL_DEV_EMAIL", "")

    assert authenticated_email() == ""


def test_authenticated_email_uses_verified_nyu_oidc_user(monkeypatch):
    import lab_portal.portal.auth as auth

    monkeypatch.delenv("PORTAL_DEV_EMAIL", raising=False)
    monkeypatch.setattr(auth.st, "secrets", {}, raising=False)
    monkeypatch.setattr(auth.st, "session_state", {}, raising=False)
    monkeypatch.setattr(
        auth.st,
        "user",
        {"is_logged_in": True, "email": "Lab.Member@nyu.edu", "email_verified": True},
        raising=False,
    )

    assert auth.authenticated_email() == "lab.member@nyu.edu"


def test_authenticated_email_rejects_non_nyu_oidc_user(monkeypatch):
    import lab_portal.portal.auth as auth

    monkeypatch.delenv("PORTAL_DEV_EMAIL", raising=False)
    monkeypatch.setattr(auth.st, "secrets", {}, raising=False)
    monkeypatch.setattr(auth.st, "session_state", {}, raising=False)
    monkeypatch.setattr(
        auth.st,
        "user",
        {"is_logged_in": True, "email": "person@example.com", "email_verified": True},
        raising=False,
    )

    assert auth.authenticated_email() == ""


def test_app_url_with_handoff_adds_signed_portal_token(monkeypatch):
    import lab_portal.portal.auth as auth

    monkeypatch.setattr(auth.st, "secrets", {"auth": {"cookie_secret": "shared-test-secret"}}, raising=False)

    url = app_url_with_handoff("https://example.streamlit.app/?theme=night", "Lab.Member@nyu.edu")

    assert url.startswith("https://example.streamlit.app/?theme=night&portal_token=")
    assert auth.verify_handoff_token(url.split("portal_token=", 1)[1]) == "lab.member@nyu.edu"


def test_authenticated_email_consumes_portal_handoff_token(monkeypatch):
    import lab_portal.portal.auth as auth

    monkeypatch.delenv("PORTAL_DEV_EMAIL", raising=False)
    monkeypatch.setattr(auth.st, "secrets", {"auth": {"cookie_secret": "shared-test-secret"}}, raising=False)
    monkeypatch.setattr(auth.st, "session_state", {}, raising=False)
    monkeypatch.setattr(auth.st, "user", {"is_logged_in": False}, raising=False)
    token = auth.make_handoff_token("Lab.Member@nyu.edu")
    monkeypatch.setattr(auth.st, "query_params", {"portal_token": token}, raising=False)

    assert auth.authenticated_email() == "lab.member@nyu.edu"
    assert auth.st.session_state[auth.SESSION_EMAIL_KEY] == "lab.member@nyu.edu"
    assert "portal_token" not in auth.st.query_params
