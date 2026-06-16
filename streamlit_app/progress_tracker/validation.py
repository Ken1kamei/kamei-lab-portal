from __future__ import annotations

from urllib.parse import urlparse

from .constants import REVIEW_STATUSES, STATUSES


URL_FIELDS = ["experiment_data_link", "protocol_link", "analysis_folder_link"]


def _blank(value: object) -> bool:
    return value is None or str(value).strip() == ""


def _valid_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_progress_record(record: dict[str, object]) -> list[str]:
    errors: list[str] = []
    status = str(record.get("status", "")).strip()
    review_status = str(record.get("review_status", "")).strip()

    if status not in STATUSES:
        errors.append(f"status must be one of: {', '.join(STATUSES)}.")
    if review_status and review_status not in REVIEW_STATUSES:
        errors.append(f"review_status must be one of: {', '.join(REVIEW_STATUSES)}.")
    if _blank(record.get("owner_member_id")) and _blank(record.get("member_id")):
        errors.append("owner_member_id or member_id is required.")
    if _blank(record.get("next_action")):
        errors.append("next_action is required.")
    if status == "Blocked" and _blank(record.get("blocker_reason")):
        errors.append("Blocked records require blocker_reason.")

    for field in URL_FIELDS:
        value = str(record.get(field, "")).strip()
        if value and not _valid_http_url(value):
            errors.append(f"{field} must be a valid http(s) URL.")

    return errors


def validate_project_record(record: dict[str, object]) -> list[str]:
    errors: list[str] = []
    if _blank(record.get("project")):
        errors.append("project is required.")
    if _blank(record.get("aim")):
        errors.append("aim is required.")
    if _blank(record.get("owner_member_id")):
        errors.append("owner_member_id is required.")
    if _blank(record.get("start_date")):
        errors.append("start_date is required.")
    return errors


def validate_review(record: dict[str, object]) -> list[str]:
    errors: list[str] = []
    review_status = str(record.get("review_status", "")).strip()
    if review_status not in REVIEW_STATUSES:
        errors.append(f"review_status must be one of: {', '.join(REVIEW_STATUSES)}.")
    if review_status == "Needs revision" and _blank(record.get("review_note")):
        errors.append("Needs revision requires review_note.")
    return errors
