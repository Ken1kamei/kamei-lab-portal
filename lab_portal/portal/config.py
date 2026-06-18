from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from .storage import CsvRegistryStore, GoogleSheetRegistryStore, RegistryStore


@dataclass(frozen=True)
class PortalSettings:
    registry_spreadsheet_id: str = ""
    progress_spreadsheet_id: str = ""
    portal_app_url: str = "https://kamei-lab-tools.streamlit.app/"
    service_account_info: dict[str, Any] = field(default_factory=dict)


def settings_from_mapping(values: Mapping[str, Any]) -> PortalSettings:
    service_account_info = values.get("gcp_service_account", {})
    return PortalSettings(
        registry_spreadsheet_id=str(values.get("REGISTRY_SPREADSHEET_ID", "")).strip(),
        progress_spreadsheet_id=str(values.get("PROGRESS_SPREADSHEET_ID", "")).strip(),
        portal_app_url=str(values.get("PORTAL_APP_URL", "https://kamei-lab-tools.streamlit.app/")).strip(),
        service_account_info=dict(service_account_info) if service_account_info else {},
    )


def registry_store_from_settings(
    settings: PortalSettings,
    sample_dir: Path,
    spreadsheet_factory: Callable[[dict[str, Any]], Any],
) -> RegistryStore:
    if settings.registry_spreadsheet_id and settings.service_account_info:
        client = spreadsheet_factory(settings.service_account_info)
        spreadsheet = client.open_by_key(settings.registry_spreadsheet_id)
        return GoogleSheetRegistryStore(spreadsheet)
    return CsvRegistryStore(sample_dir)
