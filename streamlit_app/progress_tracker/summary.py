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
