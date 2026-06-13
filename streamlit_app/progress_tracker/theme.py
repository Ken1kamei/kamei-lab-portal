from __future__ import annotations

import html

import streamlit as st


def apply_theme() -> str:
    """Apply the shared Kamei Lab app styling and return the selected mode."""
    selected = "Night"
    st.session_state.theme_mode = selected
    st.session_state._theme_mode_widget = selected
    if st.query_params.get("theme") != "night":
        st.query_params["theme"] = "night"

    colors = {
        "bg": "#151b32",
        "surface": "#242a46",
        "surface_alt": "#1d233b",
        "text": "#f7f8ff",
        "muted": "#c1c8e4",
        "subtle": "#8892bb",
        "line": "#37405f",
        "grid": "#303858",
        "cyan": "#2ee6cf",
        "green": "#7cff6b",
        "amber": "#ffd335",
        "violet": "#a86cff",
        "danger": "#ff4f80",
        "shadow": "0 18px 44px rgba(5, 8, 20, .38)",
    }
    st.session_state["_theme_colors"] = colors

    st.markdown(
        f"""
        <style>
        :root {{
          --lab-bg: {colors["bg"]};
          --lab-surface: {colors["surface"]};
          --lab-surface-alt: {colors["surface_alt"]};
          --lab-text: {colors["text"]};
          --lab-muted: {colors["muted"]};
          --lab-subtle: {colors["subtle"]};
          --lab-line: {colors["line"]};
          --lab-grid: {colors["grid"]};
          --lab-cyan: {colors["cyan"]};
          --lab-green: {colors["green"]};
          --lab-amber: {colors["amber"]};
          --lab-violet: {colors["violet"]};
          --lab-danger: {colors["danger"]};
          --lab-shadow: {colors["shadow"]};
        }}
        .stApp {{
          background:
            radial-gradient(circle at 12% 0%, rgba(46, 230, 207, .12), transparent 24rem),
            radial-gradient(circle at 82% 8%, rgba(168, 108, 255, .12), transparent 22rem),
            linear-gradient(180deg, var(--lab-bg), var(--lab-bg));
          color: var(--lab-text);
        }}
        header[data-testid="stHeader"] {{
          background: var(--lab-bg);
          color: var(--lab-text);
        }}
        header[data-testid="stHeader"] * {{
          color: var(--lab-text);
        }}
        section[data-testid="stSidebar"] {{
          background: var(--lab-surface-alt);
          border-right: 1px solid var(--lab-line);
        }}
        section[data-testid="stSidebar"] * {{
          color: var(--lab-text);
        }}
        .main .block-container {{
          padding-top: 1rem;
          max-width: 1480px;
        }}
        h1, h2, h3, p, label {{
          color: var(--lab-text);
        }}
        .lab-sidebar-brand {{
          padding: 12px 8px 22px;
        }}
        .lab-sidebar-title {{
          color: var(--lab-text);
          font-size: 1.55rem;
          font-weight: 900;
          margin-bottom: 22px;
        }}
        .lab-sidebar-muted {{
          color: var(--lab-subtle);
          font-size: .96rem;
          font-weight: 700;
          margin-bottom: 22px;
        }}
        .lab-sidebar-card {{
          background: linear-gradient(135deg, rgba(47,140,255,.24), rgba(46,230,207,.08));
          border: 1px solid rgba(47,140,255,.24);
          border-radius: 10px;
          padding: 18px 18px;
          color: var(--lab-text);
          font-size: 1.08rem;
          font-weight: 800;
          margin-bottom: 28px;
        }}
        .lab-sidebar-rule {{
          height: 1px;
          background: var(--lab-line);
          margin: 8px 0 24px;
        }}
        .lab-dashboard-top {{
          display: grid;
          grid-template-columns: minmax(320px, 1fr) minmax(480px, 1.1fr);
          gap: 34px;
          align-items: end;
          padding-bottom: 26px;
          border-bottom: 1px solid var(--lab-line);
          margin: 20px 0 28px;
        }}
        .lab-title {{
          color: var(--lab-text);
          font-size: clamp(2.4rem, 4vw, 4.1rem);
          line-height: 1.05;
          font-weight: 800;
          letter-spacing: 0;
          margin: 0;
        }}
        .lab-subtitle {{
          color: var(--lab-muted);
          font-size: 1rem;
          margin-top: 12px;
        }}
        .lab-top-tabs {{
          display: flex;
          gap: 26px;
          flex-wrap: wrap;
          align-items: center;
          justify-content: flex-end;
        }}
        .lab-top-tab {{
          color: var(--lab-subtle);
          font-size: .82rem;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: .04em;
          padding: 8px 0;
        }}
        .lab-top-tab-active {{
          color: var(--lab-cyan);
          border-bottom: 3px solid var(--lab-cyan);
          text-shadow: 0 0 18px rgba(46, 230, 207, .38);
        }}
        .lab-stat-grid {{
          display: grid;
          grid-template-columns: repeat(4, minmax(210px, 1fr));
          gap: 18px;
          margin-bottom: 24px;
        }}
        .lab-stat-card {{
          min-height: 190px;
          padding: 24px 24px 22px;
          border-radius: 8px;
          border: 1px solid #425074;
          background: linear-gradient(145deg, #303851, #202842);
          box-shadow: 0 18px 46px rgba(4, 7, 18, .35);
          border-top: 4px solid var(--lab-cyan);
          display: flex;
          flex-direction: column;
        }}
        .lab-stat-card-cyan {{
          border-top-color: var(--lab-cyan);
        }}
        .lab-stat-card-green {{
          border-top-color: var(--lab-green);
        }}
        .lab-stat-card-amber {{
          border-top-color: var(--lab-amber);
        }}
        .lab-stat-card-violet {{
          border-top-color: var(--lab-violet);
        }}
        .lab-stat-card-danger {{
          border-top-color: var(--lab-danger);
        }}
        .lab-stat-title {{
          color: var(--lab-text);
          font-size: .88rem;
          font-weight: 900;
          text-transform: uppercase;
          letter-spacing: .04em;
          margin-bottom: 18px;
        }}
        .lab-stat-value {{
          color: var(--lab-text);
          font-size: clamp(2.4rem, 3.35vw, 4.15rem);
          line-height: 1;
          font-weight: 900;
          letter-spacing: 0;
          margin-bottom: 16px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: clip;
        }}
        .lab-stat-value-cyan {{
          color: var(--lab-cyan);
        }}
        .lab-stat-value-amber {{
          color: var(--lab-amber);
        }}
        .lab-stat-caption {{
          color: var(--lab-muted);
          font-size: .95rem;
          line-height: 1.32;
          margin-top: auto;
        }}
        .lab-card-title,
        .lab-chart-title {{
          display: flex;
          gap: 12px;
          align-items: center;
          color: var(--lab-text);
          font-size: .95rem;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: .04em;
          margin: 8px 8px 12px;
        }}
        .lab-gantt {{
          display: grid;
          gap: 10px;
          background: linear-gradient(145deg, rgba(48,56,81,.92), rgba(32,40,66,.92));
          border: 1px solid var(--lab-line);
          border-radius: 8px;
          padding: 18px;
          box-shadow: var(--lab-shadow);
          margin-bottom: 22px;
        }}
        .lab-gantt-scale {{
          display: flex;
          justify-content: space-between;
          color: var(--lab-subtle);
          font-size: .78rem;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: .04em;
          padding-left: min(32vw, 320px);
        }}
        .lab-gantt-row {{
          display: grid;
          grid-template-columns: minmax(180px, 320px) 1fr;
          gap: 16px;
          align-items: center;
        }}
        .lab-gantt-label {{
          color: var(--lab-text);
          font-size: .9rem;
          font-weight: 800;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }}
        .lab-gantt-meta {{
          color: var(--lab-muted);
          font-size: .74rem;
          font-weight: 700;
          margin-top: 3px;
          text-transform: uppercase;
          letter-spacing: .04em;
        }}
        .lab-gantt-track {{
          position: relative;
          height: 36px;
          border-radius: 6px;
          background:
            repeating-linear-gradient(
              90deg,
              rgba(255,255,255,.055) 0,
              rgba(255,255,255,.055) 1px,
              transparent 1px,
              transparent 12.5%
            ),
            var(--lab-surface-alt);
          border: 1px solid var(--lab-line);
          overflow: hidden;
        }}
        .lab-gantt-bar {{
          position: absolute;
          top: 7px;
          height: 20px;
          min-width: 10px;
          border-radius: 5px;
          box-shadow: 0 0 18px rgba(46, 230, 207, .18);
        }}
        .lab-gantt-bar-milestone {{
          background: linear-gradient(90deg, var(--lab-cyan), #2f8cff);
        }}
        .lab-gantt-bar-experiment {{
          background: linear-gradient(90deg, var(--lab-amber), var(--lab-green));
        }}
        @media (max-width: 900px) {{
          .lab-gantt-scale {{
            padding-left: 0;
          }}
          .lab-gantt-row {{
            grid-template-columns: 1fr;
            gap: 8px;
          }}
        }}
        .lab-handle {{
          color: var(--lab-muted);
          line-height: .75;
          font-weight: 700;
        }}
        [data-testid="stMetric"],
        div[data-testid="stForm"],
        div[data-testid="stDataFrame"] {{
          border-radius: 8px;
        }}
        div[data-testid="stDataFrame"] {{
          border: 1px solid var(--lab-line);
          box-shadow: var(--lab-shadow);
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] {{
          background: var(--lab-surface);
          border-color: var(--lab-line);
          border-radius: 4px;
          box-shadow: var(--lab-shadow);
          min-height: 320px;
        }}
        .stButton > button,
        .stDownloadButton > button {{
          border-radius: 8px;
          border: 1px solid var(--lab-line);
          background: var(--lab-surface);
          color: var(--lab-text);
          box-shadow: 0 8px 22px rgba(0,0,0,.04);
        }}
        .stButton > button[kind="primary"],
        .stFormSubmitButton > button[kind="primary"],
        button[data-testid="stBaseButton-primary"],
        button[data-testid="stBaseButton-primary"] * {{
          background: var(--lab-text);
          color: var(--lab-bg) !important;
          border-color: var(--lab-text);
        }}
        .stTabs [data-baseweb="tab-list"] {{
          gap: 22px;
          border-bottom: 1px solid var(--lab-line);
        }}
        .stTabs [data-baseweb="tab"] {{
          color: var(--lab-subtle);
          font-weight: 800;
          letter-spacing: .02em;
        }}
        .stTabs [aria-selected="true"] {{
          color: var(--lab-cyan);
        }}
        @media (max-width: 900px) {{
          .lab-dashboard-top {{
            grid-template-columns: 1fr;
          }}
          .lab-top-tabs {{
            justify-content: flex-start;
          }}
          .lab-stat-grid {{
            grid-template-columns: 1fr;
          }}
        }}
        @media (min-width: 901px) and (max-width: 1320px) {{
          .lab-stat-grid {{
            grid-template-columns: repeat(2, minmax(260px, 1fr));
          }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    return selected


def chart_theme() -> dict[str, str]:
    colors = st.session_state.get("_theme_colors", {})
    return {
        "text": colors.get("text", "#f7f8ff"),
        "muted": colors.get("muted", "#c1c8e4"),
        "grid": colors.get("grid", "#303858"),
        "surface": colors.get("surface", "#242a46"),
        "bg": colors.get("bg", "#151b32"),
        "line": colors.get("line", "#37405f"),
    }


def sidebar_brand_html(title: str, subtitle: str, card_text: str) -> str:
    return f"""
    <div class="lab-sidebar-brand">
      <div class="lab-sidebar-title">{html.escape(title)}</div>
      <div class="lab-sidebar-muted">{html.escape(subtitle)}</div>
      <div class="lab-sidebar-card">{html.escape(card_text)}</div>
      <div class="lab-sidebar-rule"></div>
    </div>
    """


def dashboard_header_html(title: str, subtitle: str, active_tab: str = "Overview") -> str:
    tabs = ["Overview", "Members", "Milestones", "Experiments", "Review"]
    tab_html = "\n".join(
        f'<span class="lab-top-tab{" lab-top-tab-active" if tab == active_tab else ""}">{html.escape(tab)}</span>'
        for tab in tabs
    )
    return f"""
    <div class="lab-dashboard-top">
      <div>
        <h1 class="lab-title">{html.escape(title)}</h1>
        <div class="lab-subtitle">{html.escape(subtitle)}</div>
      </div>
      <div class="lab-top-tabs">
        {tab_html}
      </div>
    </div>
    """


def metric_card_html(title: str, value: str, caption: str = "", accent: str = "cyan") -> str:
    accent_class = {
        "cyan": "lab-stat-card-cyan",
        "green": "lab-stat-card-green",
        "amber": "lab-stat-card-amber",
        "violet": "lab-stat-card-violet",
        "danger": "lab-stat-card-danger",
    }.get(accent, "lab-stat-card-cyan")
    value_class = "lab-stat-value-cyan" if accent == "cyan" else "lab-stat-value-amber" if accent == "amber" else ""
    return f"""
    <div class="lab-stat-card {accent_class}">
      <div class="lab-stat-title">{html.escape(title)}</div>
      <div class="lab-stat-value {value_class}">{html.escape(str(value))}</div>
      <div class="lab-stat-caption">{html.escape(caption)}</div>
    </div>
    """


def metric_grid_html(cards: list[str]) -> str:
    return f"""
    <div class="lab-stat-grid">
      {''.join(cards)}
    </div>
    """
