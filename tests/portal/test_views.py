from pathlib import Path

from lab_portal.portal.storage import CsvRegistryStore
from lab_portal.portal.views import app_cards, dashboard_header_html


def test_app_cards_marks_missing_url_as_disabled():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    cards = app_cards(registry)
    tracker = next(card for card in cards if card["app_id"] == "project_tracker")

    assert tracker["label"] == "Project Tracker"
    assert tracker["enabled"] is False
    assert tracker["status"] == "URL needed"


def test_app_cards_marks_active_url_as_enabled():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    cards = app_cards(registry)
    budget = next(card for card in cards if card["app_id"] == "budget")

    assert budget["enabled"] is True
    assert budget["status"] == "Active"


def test_dashboard_header_html_escapes_title():
    html = dashboard_header_html("Kamei <Portal>", "Shared apps")

    assert "Kamei &lt;Portal&gt;" in html
    assert "Shared apps" in html
