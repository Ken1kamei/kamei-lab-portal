from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import time
from typing import Any, Callable, Mapping

from .storage import CsvRegistryStore, GoogleSheetRegistryStore, RegistryStore


DEFAULT_REGISTRY_SPREADSHEET_ID = "1gZU_0tG10O2JuliAq6Hdy3GONVCSBAAuiQAKXNug2Lk"
DEFAULT_PROGRESS_SPREADSHEET_ID = DEFAULT_REGISTRY_SPREADSHEET_ID
STREAMLIT_CLOUD_HOME = "/home/adminuser"
STREAMLIT_CLOUD_SOURCE_ROOT = "/mount/src"


@dataclass(frozen=True)
class PortalSettings:
    registry_spreadsheet_id: str = ""
    progress_spreadsheet_id: str = ""
    portal_app_url: str = "https://kamei-lab-tools.streamlit.app/"
    service_account_info: dict[str, Any] = field(default_factory=dict)


def settings_from_mapping(values: Mapping[str, Any]) -> PortalSettings:
    service_account_info = values.get("gcp_service_account", {})
    has_service_account = bool(service_account_info)
    registry_spreadsheet_id = str(values.get("REGISTRY_SPREADSHEET_ID", "")).strip()
    if has_service_account and not registry_spreadsheet_id:
        registry_spreadsheet_id = DEFAULT_REGISTRY_SPREADSHEET_ID
    progress_spreadsheet_id = str(values.get("PROGRESS_SPREADSHEET_ID", "")).strip()
    if has_service_account and not progress_spreadsheet_id:
        progress_spreadsheet_id = registry_spreadsheet_id or DEFAULT_PROGRESS_SPREADSHEET_ID
    return PortalSettings(
        registry_spreadsheet_id=registry_spreadsheet_id,
        progress_spreadsheet_id=progress_spreadsheet_id,
        portal_app_url=str(values.get("PORTAL_APP_URL", "https://kamei-lab-tools.streamlit.app/")).strip(),
        service_account_info=dict(service_account_info) if service_account_info else {},
    )


def running_on_streamlit_cloud() -> bool:
    return os.environ.get("HOME") == STREAMLIT_CLOUD_HOME or str(Path.cwd()).startswith(STREAMLIT_CLOUD_SOURCE_ROOT)


def shared_registry_ready(settings: PortalSettings) -> bool:
    return bool(settings.registry_spreadsheet_id and settings.service_account_info)


def shared_registry_required() -> bool:
    return running_on_streamlit_cloud()


def shared_registry_configuration_message() -> str:
    return (
        "The shared Kamei Lab registry is required on Streamlit Cloud. "
        "Set REGISTRY_SPREADSHEET_ID and [gcp_service_account] in this app's Streamlit Cloud secrets, "
        "and share the central Google Sheet with the service account as an editor."
    )


def registry_store_from_settings(
    settings: PortalSettings,
    sample_dir: Path,
    spreadsheet_factory: Callable[[dict[str, Any]], Any],
) -> RegistryStore:
    if settings.registry_spreadsheet_id and settings.service_account_info:
        client = spreadsheet_factory(settings.service_account_info)
        spreadsheet = open_spreadsheet_by_key_with_retry(client, settings.registry_spreadsheet_id)
        return GoogleSheetRegistryStore(spreadsheet)
    if shared_registry_required():
        raise RuntimeError(shared_registry_configuration_message())
    return CsvRegistryStore(sample_dir)


def open_spreadsheet_by_key_with_retry(client: Any, spreadsheet_id: str, attempts: int = 3, delay_seconds: float = 0.8) -> Any:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return client.open_by_key(spreadsheet_id)
        except Exception as error:
            last_error = error
            if attempt == attempts - 1:
                break
            time.sleep(delay_seconds * (attempt + 1))
    if last_error is not None:
        raise last_error
    raise ValueError("Spreadsheet id is required.")
