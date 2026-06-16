from __future__ import annotations

import pandas as pd


ALL_TEAMS_LABEL = "All teams"


def team_options(ledger: dict[str, pd.DataFrame]) -> list[str]:
    teams = ledger.get("Teams", pd.DataFrame(columns=["team_name", "active"])).copy()
    if teams.empty:
        fallback = ledger["Members"].get("team", pd.Series(dtype=str)).dropna().astype(str)
        names = [name for name in fallback.drop_duplicates().tolist() if name]
        return [ALL_TEAMS_LABEL, *names]

    active = teams[teams["active"].astype(str).str.upper().isin(["TRUE", "1", "YES", "Y"])]
    names = active["team_name"].dropna().astype(str).tolist()
    return [ALL_TEAMS_LABEL, *[name for name in names if name]]


def member_ids_for_team(ledger: dict[str, pd.DataFrame], team_name: str) -> set[str]:
    members = ledger["Members"]
    if team_name == ALL_TEAMS_LABEL:
        return set(members["member_id"].astype(str))

    teams = ledger.get("Teams", pd.DataFrame(columns=["team_id", "team_name"]))
    member_teams = ledger.get("Member_Teams", pd.DataFrame(columns=["member_id", "team_id"]))
    matching_team_ids = set(teams.loc[teams["team_name"] == team_name, "team_id"].astype(str))
    if matching_team_ids:
        return set(member_teams.loc[member_teams["team_id"].isin(matching_team_ids), "member_id"].astype(str))

    if "team" in members.columns:
        return set(members.loc[members["team"] == team_name, "member_id"].astype(str))
    return set()


def filter_ledger_by_team(ledger: dict[str, pd.DataFrame], team_name: str) -> dict[str, pd.DataFrame]:
    if team_name == ALL_TEAMS_LABEL:
        return {table_name: frame.copy() for table_name, frame in ledger.items()}

    member_ids = member_ids_for_team(ledger, team_name)
    filtered = {table_name: frame.copy() for table_name, frame in ledger.items()}
    filtered["Projects"] = ledger["Projects"][ledger["Projects"]["owner_member_id"].isin(member_ids)].copy()
    filtered["Members"] = ledger["Members"][ledger["Members"]["member_id"].isin(member_ids)].copy()
    filtered["Milestones"] = ledger["Milestones"][ledger["Milestones"]["owner_member_id"].isin(member_ids)].copy()
    filtered["Experiments"] = ledger["Experiments"][ledger["Experiments"]["member_id"].isin(member_ids)].copy()
    filtered["Member_Teams"] = ledger.get("Member_Teams", pd.DataFrame()).copy()
    if not filtered["Member_Teams"].empty:
        filtered["Member_Teams"] = filtered["Member_Teams"][filtered["Member_Teams"]["member_id"].isin(member_ids)].copy()
    return filtered


def overview_counts(ledger: dict[str, pd.DataFrame]) -> dict[str, int]:
    milestones = ledger["Milestones"]
    experiments = ledger["Experiments"]
    pending_review = int((milestones["review_status"] == "Pending").sum()) + int(
        (experiments["review_status"] == "Pending").sum()
    )
    blocked = int((milestones["status"] == "Blocked").sum()) + int((experiments["status"] == "Blocked").sum())
    return {
        "milestones_total": int(len(milestones)),
        "experiments_total": int(len(experiments)),
        "pending_review": pending_review,
        "blocked": blocked,
    }


def overview_summary_rows(ledger: dict[str, pd.DataFrame]) -> pd.DataFrame:
    counts = overview_counts(ledger)
    return pd.DataFrame(
        [
            {"metric": "Milestones", "value": counts["milestones_total"]},
            {"metric": "Experiments", "value": counts["experiments_total"]},
            {"metric": "Pending review", "value": counts["pending_review"]},
            {"metric": "Blocked", "value": counts["blocked"]},
        ]
    )


def records_by_member(ledger: dict[str, pd.DataFrame]) -> pd.DataFrame:
    members = ledger["Members"][["member_id", "name"]].rename(columns={"name": "member_name"})
    milestones = ledger["Milestones"].rename(
        columns={"owner_member_id": "member_id", "milestone": "title"}
    )[["member_id", "title", "status", "review_status", "next_action", "due_date"]]
    milestones["record_type"] = "Milestone"

    experiments = ledger["Experiments"].rename(columns={"experiment_title": "title"})[
        ["member_id", "title", "status", "review_status", "next_action", "due_date"]
    ]
    experiments["record_type"] = "Experiment"

    combined = pd.concat([milestones, experiments], ignore_index=True)
    return combined.merge(members, on="member_id", how="left")[
        ["member_name", "record_type", "title", "status", "review_status", "next_action", "due_date"]
    ]


def milestone_gantt_data(ledger: dict[str, pd.DataFrame]) -> pd.DataFrame:
    frame = ledger["Milestones"][
        [
            "milestone_id",
            "project",
            "aim",
            "milestone",
            "time_window",
            "owner_member_id",
            "status",
            "review_status",
            "start_date",
            "due_date",
        ]
    ].copy()
    frame["start_date"] = pd.to_datetime(frame["start_date"], errors="coerce")
    frame["end_date"] = pd.to_datetime(frame["due_date"], errors="coerce")
    frame = frame.drop(columns=["due_date"])
    return frame.dropna(subset=["start_date", "end_date"])


def team_gantt_data(ledger: dict[str, pd.DataFrame]) -> pd.DataFrame:
    members = ledger["Members"][["member_id", "name"]].rename(columns={"name": "team_member"})
    milestones = ledger["Milestones"][
        [
            "milestone_id",
            "project",
            "aim",
            "milestone",
            "owner_member_id",
            "status",
            "review_status",
            "start_date",
            "due_date",
        ]
    ].rename(
        columns={
            "milestone_id": "record_id",
            "milestone": "title",
            "owner_member_id": "member_id",
        }
    )
    milestones["record_type"] = "Milestone"

    experiment_context = ledger["Milestones"][["milestone_id", "project", "aim", "start_date"]].rename(
        columns={"start_date": "milestone_start_date"}
    )
    experiments = ledger["Experiments"][
        [
            "experiment_id",
            "milestone_id",
            "member_id",
            "experiment_title",
            "status",
            "review_status",
            "due_date",
        ]
    ].rename(columns={"experiment_id": "record_id", "experiment_title": "title"})
    experiments = experiments.merge(experiment_context, on="milestone_id", how="left")
    experiments["start_date"] = experiments["milestone_start_date"]
    experiments = experiments.drop(columns=["milestone_id", "milestone_start_date"])
    experiments["record_type"] = "Experiment"

    combined = pd.concat([milestones, experiments], ignore_index=True, sort=False)
    combined = combined.merge(members, on="member_id", how="left")
    combined["start_date"] = combined["start_date"].replace("", pd.NA).fillna(combined["due_date"])
    combined["start_date"] = pd.to_datetime(combined["start_date"], errors="coerce")
    combined["end_date"] = pd.to_datetime(combined["due_date"], errors="coerce")
    combined = combined.dropna(subset=["start_date", "end_date", "team_member"])
    combined["lane"] = combined["team_member"] + " / " + combined["title"]
    return combined[
        [
            "record_type",
            "record_id",
            "team_member",
            "project",
            "aim",
            "title",
            "status",
            "review_status",
            "start_date",
            "end_date",
            "lane",
        ]
    ]


def completed_records(ledger: dict[str, pd.DataFrame]) -> pd.DataFrame:
    milestones = ledger["Milestones"][
        [
            "milestone_id",
            "project",
            "aim",
            "milestone",
            "owner_member_id",
            "status",
            "review_status",
            "updated_at",
        ]
    ].rename(
        columns={
            "milestone_id": "record_id",
            "milestone": "title",
            "owner_member_id": "owner_id",
        }
    )
    milestones["record_type"] = "Milestone"

    experiments = ledger["Experiments"][
        [
            "experiment_id",
            "milestone_id",
            "member_id",
            "experiment_title",
            "status",
            "review_status",
            "updated_at",
        ]
    ].rename(
        columns={
            "experiment_id": "record_id",
            "experiment_title": "title",
            "member_id": "owner_id",
        }
    )
    experiment_context = ledger["Milestones"][["milestone_id", "project", "aim"]]
    experiments = experiments.merge(experiment_context, on="milestone_id", how="left").drop(columns=["milestone_id"])
    experiments["record_type"] = "Experiment"

    combined = pd.concat([milestones, experiments], ignore_index=True, sort=False)
    completed = combined[combined["status"] == "Completed"].copy()
    return completed[
        [
            "record_type",
            "record_id",
            "project",
            "aim",
            "title",
            "owner_id",
            "status",
            "review_status",
            "updated_at",
        ]
    ]
