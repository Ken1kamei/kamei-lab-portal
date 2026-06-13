from __future__ import annotations

import streamlit as st


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
          --portal-bg: #151b32;
          --portal-surface: #242a46;
          --portal-surface-alt: #1d233b;
          --portal-text: #f7f8ff;
          --portal-muted: #c1c8e4;
          --portal-subtle: #8892bb;
          --portal-line: #37405f;
          --portal-cyan: #2ee6cf;
          --portal-danger: #ff4f80;
        }
        .stApp {
          background: linear-gradient(180deg, var(--portal-bg), var(--portal-bg));
          color: var(--portal-text);
        }
        section[data-testid="stSidebar"] {
          background: var(--portal-surface-alt);
          border-right: 1px solid var(--portal-line);
        }
        .main .block-container {
          max-width: 1440px;
          padding-top: 1rem;
        }
        .portal-header {
          border-bottom: 1px solid var(--portal-line);
          margin: 16px 0 28px;
          padding-bottom: 24px;
        }
        .portal-title {
          color: var(--portal-text);
          font-size: clamp(2.4rem, 4vw, 4rem);
          line-height: 1.05;
          font-weight: 900;
          letter-spacing: 0;
          margin: 0;
        }
        .portal-subtitle {
          color: var(--portal-muted);
          font-size: 1rem;
          margin-top: 12px;
        }
        .portal-card {
          display: block;
          border: 1px solid #425074;
          border-radius: 8px;
          background: linear-gradient(145deg, #303851, #202842);
          padding: 22px;
          min-height: 180px;
          text-decoration: none;
          transition: border-color .16s ease, box-shadow .16s ease, transform .16s ease;
        }
        .portal-card-link {
          cursor: pointer;
        }
        .portal-card-link:hover,
        .portal-card-link:focus {
          border-color: var(--portal-cyan);
          box-shadow: 0 16px 36px rgba(46, 230, 207, .14);
          outline: none;
          transform: translateY(-2px);
        }
        .portal-card-disabled {
          cursor: default;
          opacity: .7;
        }
        .portal-card-title {
          color: var(--portal-text);
          font-size: 1.2rem;
          font-weight: 900;
          margin-bottom: 8px;
        }
        .portal-card-muted {
          color: var(--portal-muted);
          font-size: .95rem;
          line-height: 1.35;
        }
        .portal-status {
          color: var(--portal-cyan);
          font-size: .78rem;
          text-transform: uppercase;
          font-weight: 900;
          letter-spacing: .04em;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
