from pathlib import Path

from streamlit_app.progress_tracker import views
from streamlit_app.progress_tracker.storage import CsvLedgerStore


def _sample_ledger():
    return CsvLedgerStore(Path("streamlit_app/data/sample")).load()


class _FakeStreamlit:
    def __init__(self):
        self.errors: list[str] = []

    def subheader(self, _label):
        pass

    def dataframe(self, *_args, **_kwargs):
        pass

    def info(self, _message):
        pass

    def selectbox(self, label, options, index=0, **_kwargs):
        if label == "Status":
            return "Blocked"
        if label == "Decision":
            return "Needs revision"
        return options[index]

    def text_input(self, label, value="", **_kwargs):
        if label == "Blocker reason":
            return ""
        return value

    def text_area(self, _label, **_kwargs):
        return ""

    def button(self, _label, **_kwargs):
        return True

    def error(self, message):
        self.errors.append(message)


def test_member_update_form_shows_validation_error_and_keeps_ledger(monkeypatch):
    ledger = _sample_ledger()
    fake_st = _FakeStreamlit()
    monkeypatch.setattr(views, "st", fake_st)

    result = views.render_member_update_form(ledger, "M003")

    assert result is ledger
    assert fake_st.errors == ["Blocked records require blocker_reason."]


def test_milestone_update_form_shows_validation_error_and_keeps_ledger(monkeypatch):
    ledger = _sample_ledger()
    fake_st = _FakeStreamlit()
    monkeypatch.setattr(views, "st", fake_st)

    result = views.render_milestone_update_form(ledger, "M002")

    assert result is ledger
    assert fake_st.errors == ["Blocked records require blocker_reason."]


def test_review_form_shows_validation_error_and_keeps_ledger(monkeypatch):
    ledger = _sample_ledger()
    fake_st = _FakeStreamlit()
    monkeypatch.setattr(views, "st", fake_st)

    result = views.render_review(ledger, "M002")

    assert result is ledger
    assert fake_st.errors == ["Needs revision requires review_note."]
