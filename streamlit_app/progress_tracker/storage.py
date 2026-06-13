from __future__ import annotations

from pathlib import Path

import pandas as pd

from .schema import REQUIRED_COLUMNS


class CsvLedgerStore:
    def __init__(self, directory: Path | str):
        self.directory = Path(directory)

    def load(self) -> dict[str, pd.DataFrame]:
        ledger: dict[str, pd.DataFrame] = {}
        for table_name, columns in REQUIRED_COLUMNS.items():
            path = self.directory / f"{table_name}.csv"
            if path.exists():
                frame = pd.read_csv(path, dtype=str, keep_default_na=False)
            else:
                frame = pd.DataFrame(columns=columns)
            missing = [column for column in columns if column not in frame.columns]
            if missing:
                raise ValueError(f"{path} is missing required columns: {', '.join(missing)}")
            ledger[table_name] = frame[columns].copy()
        return ledger

    def save(self, ledger: dict[str, pd.DataFrame]) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        for table_name, columns in REQUIRED_COLUMNS.items():
            frame = ledger.get(table_name, pd.DataFrame(columns=columns)).copy()
            missing = [column for column in columns if column not in frame.columns]
            if missing:
                raise ValueError(f"{table_name} is missing required columns: {', '.join(missing)}")
            frame[columns].to_csv(self.directory / f"{table_name}.csv", index=False)
