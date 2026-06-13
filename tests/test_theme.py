from streamlit_app.progress_tracker.theme import metric_card_html, sidebar_brand_html


def test_sidebar_brand_html_uses_lab_design_classes():
    html = sidebar_brand_html("Kamei Lab", "Progress Tracker", "Shared research portal")

    assert "lab-sidebar-brand" in html
    assert "Kamei Lab" in html
    assert "Progress Tracker" in html
    assert "Shared research portal" in html


def test_metric_card_html_uses_count_without_budget_currency_marker():
    html = metric_card_html("Milestones", "4", "active project milestones", accent="cyan")

    assert "lab-stat-card" in html
    assert "Milestones" in html
    assert "4" in html
    assert "$" not in html
