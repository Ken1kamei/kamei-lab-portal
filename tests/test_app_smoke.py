import importlib
import runpy


def test_streamlit_app_imports():
    module = importlib.import_module("streamlit_app.app")
    assert hasattr(module, "main")
    assert hasattr(module, "save_ledger")
    assert module.APP_TITLE == "Project Tracker"


def test_streamlit_app_script_path_loads_without_running_main():
    result = runpy.run_path("streamlit_app/app.py", run_name="__streamlit_test__")
    assert "main" in result
