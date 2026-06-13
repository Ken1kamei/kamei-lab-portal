from streamlit_app.progress_tracker.validation import validate_progress_record, validate_review


def test_blocked_requires_blocker_reason():
    errors = validate_progress_record(
        {
            "owner_member_id": "M002",
            "status": "Blocked",
            "review_status": "Pending",
            "next_action": "Ask core facility",
            "blocker_reason": "",
        }
    )
    assert errors == ["Blocked records require blocker_reason."]


def test_progress_record_requires_owner_or_member():
    errors = validate_progress_record(
        {
            "status": "Running",
            "review_status": "Pending",
            "next_action": "Collect effluent",
        }
    )
    assert errors == ["owner_member_id or member_id is required."]


def test_valid_experiment_member_is_accepted():
    errors = validate_progress_record(
        {
            "member_id": "M003",
            "status": "Running",
            "review_status": "Pending",
            "next_action": "Collect effluent",
        }
    )
    assert errors == []


def test_valid_milestone_owner_is_accepted():
    errors = validate_progress_record(
        {
            "owner_member_id": "M002",
            "status": "Preparing",
            "review_status": "Pending",
            "next_action": "Confirm schedule",
        }
    )
    assert errors == []


def test_valid_dropbox_like_url_is_accepted():
    errors = validate_progress_record(
        {
            "member_id": "M003",
            "status": "Running",
            "review_status": "Pending",
            "next_action": "Collect effluent",
            "experiment_data_link": "https://www.dropbox.com/s/example/data",
        }
    )
    assert errors == []


def test_invalid_url_is_rejected():
    errors = validate_progress_record(
        {
            "member_id": "M003",
            "status": "Running",
            "review_status": "Pending",
            "next_action": "Collect effluent",
            "experiment_data_link": "dropbox folder",
        }
    )
    assert errors == ["experiment_data_link must be a valid http(s) URL."]


def test_needs_revision_requires_review_note():
    errors = validate_review({"review_status": "Needs revision", "review_note": ""})
    assert errors == ["Needs revision requires review_note."]
