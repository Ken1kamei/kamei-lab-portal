from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import pandas as pd

from .constants import TABLES
from .schema import REQUIRED_COLUMNS, empty_registry


Registry = dict[str, pd.DataFrame]


class RegistryStore(Protocol):
    def load(self) -> Registry:
        ...

    def save(self, registry: Registry) -> None:
        ...


@dataclass(frozen=True)
class CsvRegistryStore:
    base_dir: Path

    def load(self) -> Registry:
        registry = empty_registry()
        for table_name in TABLES:
            path = self.base_dir / f"{table_name}.csv"
            if path.exists():
                registry[table_name] = pd.read_csv(path, dtype=str).fillna("")
            registry[table_name] = registry[table_name].reindex(columns=REQUIRED_COLUMNS[table_name], fill_value="")
        return registry

    def save(self, registry: Registry) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        for table_name in TABLES:
            frame = registry[table_name].reindex(columns=REQUIRED_COLUMNS[table_name], fill_value="")
            frame.to_csv(self.base_dir / f"{table_name}.csv", index=False)


@dataclass(frozen=True)
class GoogleSheetRegistryStore:
    spreadsheet: object

    def load(self) -> Registry:
        registry = empty_registry()
        for table_name in TABLES:
            worksheet = self.spreadsheet.worksheet(table_name)
            records = worksheet.get_all_records()
            frame = pd.DataFrame(records)
            registry[table_name] = frame.reindex(columns=REQUIRED_COLUMNS[table_name], fill_value="").astype(str)
        return registry

    def save(self, registry: Registry) -> None:
        for table_name in TABLES:
            worksheet = self.spreadsheet.worksheet(table_name)
            frame = registry[table_name].reindex(columns=REQUIRED_COLUMNS[table_name], fill_value="")
            rows = [list(frame.columns)] + frame.fillna("").astype(str).values.tolist()
            worksheet.clear()
            worksheet.update(rows)
