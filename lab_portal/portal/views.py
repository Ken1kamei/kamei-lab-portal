from __future__ import annotations

import html

from .permissions import is_active
from .storage import Registry


def dashboard_header_html(title: str, subtitle: str) -> str:
    return (
        '<div class="portal-header">'
        f'<h1 class="portal-title">{html.escape(title)}</h1>'
        f'<div class="portal-subtitle">{html.escape(subtitle)}</div>'
        "</div>"
    )


def app_cards(registry: Registry) -> list[dict[str, object]]:
    apps = registry["Apps"].fillna("").copy()
    if "sort_order" in apps:
        apps["sort_order_numeric"] = (
            apps["sort_order"].astype(str).str.extract(r"(\d+)", expand=False).fillna("999").astype(int)
        )
        apps = apps.sort_values(["sort_order_numeric", "app_name"])
    cards: list[dict[str, object]] = []
    for _, row in apps.iterrows():
        active = is_active(row["active"])
        has_url = bool(str(row["app_url"]).strip())
        enabled = active and has_url
        if not has_url:
            status = "URL needed"
        elif enabled:
            status = "Active"
        else:
            status = "Inactive"
        cards.append(
            {
                "app_id": html.escape(str(row["app_id"])),
                "label": html.escape(str(row["app_name"])),
                "url": html.escape(str(row["app_url"])),
                "description": html.escape(str(row["description"])),
                "category": html.escape(str(row["category"])),
                "enabled": enabled,
                "status": html.escape(status),
            }
        )
    return cards
