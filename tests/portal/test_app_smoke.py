import importlib


def test_lab_portal_app_imports():
    module = importlib.import_module("lab_portal.app")

    assert module.APP_TITLE == "Kamei Lab Portal"
    assert module.VIEWS == ["Home", "Members", "Teams", "App Access", "Audit"]
