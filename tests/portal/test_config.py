from pathlib import Path

from lab_portal.portal.config import PortalSettings, registry_store_from_settings, settings_from_mapping
from lab_portal.portal.storage import CsvRegistryStore, GoogleSheetRegistryStore


class FakeClient:
    def __init__(self):
        self.opened_key = None

    def open_by_key(self, key):
        self.opened_key = key
        return {"spreadsheet_key": key}


def test_settings_from_mapping_reads_registry_values():
    settings = settings_from_mapping(
        {
            "REGISTRY_SPREADSHEET_ID": "sheet-123",
            "PROGRESS_SPREADSHEET_ID": "progress-456",
            "gcp_service_account": {"client_email": "service@example.iam.gserviceaccount.com"},
        }
    )

    assert settings.registry_spreadsheet_id == "sheet-123"
    assert settings.progress_spreadsheet_id == "progress-456"
    assert settings.service_account_info == {"client_email": "service@example.iam.gserviceaccount.com"}


def test_settings_from_mapping_defaults_missing_values():
    settings = settings_from_mapping({})

    assert settings == PortalSettings()


def test_registry_store_uses_csv_when_sheet_settings_are_missing():
    store = registry_store_from_settings(PortalSettings(), Path("lab_portal/data/sample"), lambda info: FakeClient())

    assert isinstance(store, CsvRegistryStore)


def test_registry_store_uses_google_sheet_when_sheet_settings_exist():
    fake_client = FakeClient()
    store = registry_store_from_settings(
        PortalSettings(
            registry_spreadsheet_id="sheet-123",
            service_account_info={"client_email": "service@example.iam.gserviceaccount.com"},
        ),
        Path("lab_portal/data/sample"),
        lambda info: fake_client,
    )

    assert isinstance(store, GoogleSheetRegistryStore)
    assert fake_client.opened_key == "sheet-123"
