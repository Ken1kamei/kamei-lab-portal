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
    html = dashboard_header_html("Kamei <Portal>", "Shared <apps>")

    assert "Kamei &lt;Portal&gt;" in html
    assert "Shared &lt;apps&gt;" in html


def test_app_cards_escapes_registry_text_fields():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()
    registry["Apps"].loc[0, "app_name"] = "Budget <script>"
    registry["Apps"].loc[0, "description"] = "Use <b>carefully</b>"

    budget = next(card for card in app_cards(registry) if card["app_id"] == "budget")

    assert budget["label"] == "Budget &lt;script&gt;"
    assert budget["description"] == "Use &lt;b&gt;carefully&lt;/b&gt;"


def test_app_cards_marks_inactive_app_with_url_as_inactive():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()
    registry["Apps"].loc[0, "active"] = "FALSE"

    budget = next(card for card in app_cards(registry) if card["app_id"] == "budget")

    assert budget["enabled"] is False
    assert budget["status"] == "Inactive"


def test_app_cards_handles_non_numeric_sort_order():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()
    registry["Apps"].loc[0, "sort_order"] = "not-a-number"

    cards = app_cards(registry)

    assert cards[-1]["app_id"] == "budget"
