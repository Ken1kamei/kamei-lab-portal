from pathlib import Path

from lab_portal.portal.storage import CsvRegistryStore
from lab_portal.portal.views import app_card_html, app_cards, dashboard_header_html


def test_app_cards_marks_missing_url_as_disabled():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()
    registry["Apps"].loc[registry["Apps"]["app_id"] == "project_tracker", "app_url"] = ""
    registry["Apps"].loc[registry["Apps"]["app_id"] == "project_tracker", "active"] = "FALSE"

    cards = app_cards(registry)
    tracker = next(card for card in cards if card["app_id"] == "project_tracker")

    assert tracker["label"] == "Project Tracker"
    assert tracker["enabled"] is False
    assert tracker["status"] == "URL needed"


def test_app_cards_marks_project_tracker_implementation_url_as_enabled():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    cards = app_cards(registry)
    tracker = next(card for card in cards if card["app_id"] == "project_tracker")

    assert tracker["enabled"] is True
    assert tracker["status"] == "Active"
    assert tracker["url"] == "http://127.0.0.1:8502/"


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
    registry["Apps"].loc[0, "app_id"] = "budget<script>"
    registry["Apps"].loc[0, "app_name"] = "Budget <script>"
    registry["Apps"].loc[0, "app_url"] = "https://example.edu/?q=<bad>"
    registry["Apps"].loc[0, "description"] = "Use <b>carefully</b>"
    registry["Apps"].loc[0, "category"] = "Ops <Lab>"

    budget = next(card for card in app_cards(registry) if card["app_id"] == "budget&lt;script&gt;")

    assert budget["app_id"] == "budget&lt;script&gt;"
    assert budget["label"] == "Budget &lt;script&gt;"
    assert budget["url"] == "https://example.edu/?q=<bad>"
    assert budget["display_url"] == "https://example.edu/?q=&lt;bad&gt;"
    assert budget["description"] == "Use &lt;b&gt;carefully&lt;/b&gt;"
    assert budget["category"] == "Ops &lt;Lab&gt;"
    assert budget["status"] == "Active"


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


def test_app_card_html_makes_enabled_card_the_link_target():
    card = {
        "label": "Budget",
        "description": "Lab budget management",
        "display_url": "https://example.edu/budget",
        "enabled": True,
        "status": "Active",
    }

    html = app_card_html(card)

    assert html.startswith('<a class="portal-card portal-card-link"')
    assert 'href="https://example.edu/budget"' in html
    assert "Open Budget" not in html


def test_app_card_html_does_not_link_disabled_card():
    card = {
        "label": "Project Tracker",
        "description": "Milestones experiments and reviews",
        "display_url": "",
        "enabled": False,
        "status": "URL needed",
    }

    html = app_card_html(card)

    assert html.startswith('<div class="portal-card portal-card-disabled"')
    assert "href=" not in html
