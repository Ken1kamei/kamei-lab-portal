from streamlit_app.progress_tracker.theme import dashboard_header_html, metric_card_html, sidebar_brand_html


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


def test_dashboard_header_view_tabs_are_links():
    html = dashboard_header_html("Project Tracker", "All teams overview", active_tab="Milestones")

    assert 'href="?view=Overview&amp;theme=night"' in html
    assert 'href="?view=Milestones&amp;theme=night"' in html
    assert "lab-top-tab-active" in html
