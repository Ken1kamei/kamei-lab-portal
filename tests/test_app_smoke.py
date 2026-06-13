import importlib


def test_streamlit_app_imports():
    module = importlib.import_module("streamlit_app.app")
    assert hasattr(module, "main")
