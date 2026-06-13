from __future__ import annotations

import pandas as pd


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
