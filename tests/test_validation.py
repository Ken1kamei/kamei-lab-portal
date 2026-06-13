from streamlit_app.progress_tracker.validation import validate_progress_record, validate_review


def test_blocked_requires_blocker_reason():
    errors = validate_progress_record(
        {"status": "Blocked", "review_status": "Pending", "next_action": "Ask core facility", "blocker_reason": ""}
    )
    assert errors == ["Blocked records require blocker_reason."]


def test_valid_dropbox_like_url_is_accepted():
    errors = validate_progress_record(
        {
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
