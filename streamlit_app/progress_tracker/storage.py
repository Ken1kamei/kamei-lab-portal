from __future__ import annotations

from pathlib import Path

import pandas as pd

from .schema import REQUIRED_COLUMNS


SHARED_REGISTRY_TABLES = {"Members", "Teams", "Member_Teams"}
PROJECT_TRACKER_APP_IDS = {"project_tracker", "progress_tracker"}
PROGRESS_TABLES = tuple(table_name for table_name in REQUIRED_COLUMNS if table_name not in SHARED_REGISTRY_TABLES)


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

    def save(self, ledger: dict[str, pd.DataFrame], table_names: tuple[str, ...] | None = None) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        selected_tables = table_names or tuple(REQUIRED_COLUMNS)
        for table_name in selected_tables:
            columns = REQUIRED_COLUMNS[table_name]
            frame = ledger.get(table_name, pd.DataFrame(columns=columns)).copy()
            missing = [column for column in columns if column not in frame.columns]
            if missing:
                raise ValueError(f"{table_name} is missing required columns: {', '.join(missing)}")
            frame[columns].to_csv(self.directory / f"{table_name}.csv", index=False)


class GoogleSheetLedgerStore:
    def __init__(self, spreadsheet):
        self.spreadsheet = spreadsheet

    def load(self) -> dict[str, pd.DataFrame]:
        ledger: dict[str, pd.DataFrame] = {}
        for table_name, columns in REQUIRED_COLUMNS.items():
            if table_name in SHARED_REGISTRY_TABLES:
                ledger[table_name] = pd.DataFrame(columns=columns)
                continue
            worksheet = self.spreadsheet.worksheet(table_name)
            records = worksheet.get_all_records()
            frame = pd.DataFrame(records)
            ledger[table_name] = frame.reindex(columns=columns, fill_value="").astype(str)
        return ledger

    def save(self, ledger: dict[str, pd.DataFrame], table_names: tuple[str, ...] | None = None) -> None:
        selected_tables = table_names or PROGRESS_TABLES
        for table_name in selected_tables:
            if table_name in SHARED_REGISTRY_TABLES:
                continue
            columns = REQUIRED_COLUMNS[table_name]
            worksheet = self.spreadsheet.worksheet(table_name)
            frame = ledger.get(table_name, pd.DataFrame(columns=columns)).reindex(columns=columns, fill_value="")
            rows = [list(frame.columns)] + frame.fillna("").astype(str).values.tolist()
            worksheet.clear()
            worksheet.update(rows)


class SharedRegistryLedgerStore:
    def __init__(self, progress_store: CsvLedgerStore, registry_store):
        self.progress_store = progress_store
        self.registry_store = registry_store

    def load(self) -> dict[str, pd.DataFrame]:
        ledger = self.progress_store.load()
        registry = self.registry_store.load()
        shared_tables = _project_tracker_shared_tables(registry)
        ledger.update(shared_tables)
        return {table_name: ledger[table_name].reindex(columns=columns, fill_value="") for table_name, columns in REQUIRED_COLUMNS.items()}

    def save(self, ledger: dict[str, pd.DataFrame]) -> None:
        self.progress_store.save(ledger, table_names=PROGRESS_TABLES)


def _is_active(value: object) -> bool:
    return str(value).strip().upper() in {"TRUE", "1", "YES", "Y"}


def _project_tracker_shared_tables(registry: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    members = registry["Members"].fillna("").copy()
    teams = registry["Teams"].fillna("").copy()
    member_teams = registry["Member_Teams"].fillna("").copy()
    app_roles = registry.get("App_Roles", pd.DataFrame()).fillna("").copy()

    active_members = members[members["active"].map(_is_active)].copy()
    active_teams = teams[teams["active"].map(_is_active)].copy()
    active_member_teams = member_teams[member_teams["active"].map(_is_active)].copy()
    active_project_roles = _active_project_tracker_roles(app_roles)
    members_with_project_roles = set(active_project_roles["member_id"].astype(str))

    active_member_ids = set(active_members["member_id"])
    active_team_ids = set(active_teams["team_id"])
    active_member_teams = active_member_teams[
        active_member_teams["member_id"].isin(active_member_ids) & active_member_teams["team_id"].isin(active_team_ids)
    ]

    team_names = active_teams.set_index("team_id")["team_name"].to_dict()
    first_team_by_member = (
        active_member_teams.assign(team_name=active_member_teams["team_id"].map(team_names))
        .sort_values(["member_id", "team_name"])
        .drop_duplicates("member_id")
        .set_index("member_id")["team_name"]
        .to_dict()
    )

    tracker_members = pd.DataFrame(
        [
            {
                "member_id": row["member_id"],
                "name": row["display_name"] or row["name"],
                "email": row["email"],
                "role": _project_tracker_role_for_member(row, active_project_roles, members_with_project_roles),
                "team": first_team_by_member.get(row["member_id"], ""),
                "lead_id": "",
                "active": "TRUE",
            }
            for _, row in active_members.iterrows()
        ],
        columns=REQUIRED_COLUMNS["Members"],
    )
    tracker_teams = active_teams.rename(columns={"description": "_description"}).reindex(columns=REQUIRED_COLUMNS["Teams"], fill_value="")
    tracker_member_teams = active_member_teams.reindex(columns=REQUIRED_COLUMNS["Member_Teams"], fill_value="")
    return {
        "Members": tracker_members,
        "Teams": tracker_teams,
        "Member_Teams": tracker_member_teams,
    }


def _active_project_tracker_roles(app_roles: pd.DataFrame) -> pd.DataFrame:
    required_columns = {"member_id", "app_id", "active"}
    if app_roles.empty or not required_columns.issubset(set(app_roles.columns)):
        return pd.DataFrame(columns=["member_id", "app_id", "active"])
    return app_roles[
        app_roles["active"].map(_is_active) & app_roles["app_id"].astype(str).isin(PROJECT_TRACKER_APP_IDS)
    ].copy()


def _project_tracker_role_for_member(
    member: pd.Series,
    active_project_roles: pd.DataFrame,
    members_with_project_roles: set[str],
) -> str:
    member_id = str(member.get("member_id", ""))
    if member_id in members_with_project_roles:
        role = str(
            active_project_roles.loc[
                active_project_roles["member_id"].astype(str) == member_id,
                "app_role",
            ].iloc[0]
        ).strip()
        if role:
            return role
    return str(member.get("global_role", "") or "member")
