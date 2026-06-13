import importlib
import runpy


def test_streamlit_app_imports():
    module = importlib.import_module("streamlit_app.app")
    assert hasattr(module, "main")


def test_streamlit_app_loads_as_script():
    namespace = runpy.run_path("streamlit_app/app.py", run_name="__streamlit_test__")
    assert "main" in namespace
