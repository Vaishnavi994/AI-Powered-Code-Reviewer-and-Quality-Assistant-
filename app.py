import ast
import html
import json
import multiprocessing
import os
import subprocess
import tkinter as tk
from tkinter import filedialog
from textwrap import dedent
from string import Template
from typing import Dict, Optional, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from docstring_engine.docstring_generator import (
    generate_docstring,
    insert_docstring,
    remove_existing_docstring,
    update_function_in_file,
)
from parser.file_parser import get_function_node
from parser.findfunctions import extract_functions
from validation.code_analyzer import fix_docstrings, fix_source_code

APP_TITLE = "AI Python Code Studio"
DOC_PRESENT = "✅ Present"
DOC_MISSING = "❌ Missing"
ANALYSIS_COLUMNS = [
    "File",
    "Function",
    "Start Line",
    "End Line",
    "Complexity",
    "Violations",
    "Docstring",
]
NAV_ITEMS = {
    "overview": "Overview",
    "dashboard": "Dashboard",
    "functions": "Function Analysis",
    "docstrings": "Docstring Review",
    "quality": "Code Quality",
}
NAV_ICONS = {
    "overview": "🏠",
    "dashboard": "📊",
    "functions": "🔎",
    "docstrings": "✍️",
    "quality": "🛡️",
}
NAV_SEQUENCE = ["overview", "dashboard", "functions", "docstrings", "quality"]
DOC_STYLES = ["Google", "NumPy", "reST"]
CHART_SEQUENCE = ["#67e8f9", "#38bdf8", "#0891b2", "#14b8a6", "#0f766e", "#1d4ed8"]
CHATBOT_STORAGE_KEY = "ai_python_code_studio_chat_v1"
APP_FOOTER_COPY = "Fast Python analysis, docstring review, code-quality checks, and quick assistant help."
THEME_TOKENS = {
    "dark": {
        "bg": "#08111c",
        "bg_soft": "#0d1724",
        "panel": "rgba(9, 18, 31, 0.86)",
        "panel_strong": "rgba(8, 16, 28, 0.96)",
        "panel_alt": "rgba(15, 25, 40, 0.78)",
        "border": "rgba(148, 163, 184, 0.14)",
        "text": "#e5edf5",
        "muted": "#90a3b8",
        "primary": "#67e8f9",
        "accent": "#38bdf8",
        "accent_2": "#14b8a6",
        "success": "#22c55e",
        "warning": "#f59e0b",
        "danger": "#f43f5e",
        "shadow": "0 24px 60px rgba(2, 6, 23, 0.42)",
        "chart_template": "plotly_dark",
        "card_text": "#f8fafc",
        "sidebar_bg": "linear-gradient(180deg, rgba(5, 12, 21, 0.97), rgba(8, 16, 27, 0.94))",
        "sidebar_panel": "rgba(11, 22, 37, 0.88)",
        "sidebar_text": "#e5edf5",
        "sidebar_muted": "#93a7bc",
        "hero_start": "rgba(8, 15, 29, 0.94)",
        "hero_end": "rgba(11, 54, 72, 0.74)",
    },
    "light": {
        "bg": "#f7f9fc",
        "bg_soft": "#eef3f8",
        "panel": "#ffffff",
        "panel_strong": "#ffffff",
        "panel_alt": "#ffffff",
        "border": "#d7e0ea",
        "text": "#1f2937",
        "muted": "#5b6878",
        "primary": "#0f766e",
        "accent": "#1d4ed8",
        "accent_2": "#0891b2",
        "success": "#16a34a",
        "warning": "#d97706",
        "danger": "#e11d48",
        "shadow": "0 14px 32px rgba(15, 23, 42, 0.08)",
        "chart_template": "plotly_white",
        "card_text": "#111827",
        "sidebar_bg": "linear-gradient(180deg, #eef2f7, #e9eef5)",
        "sidebar_panel": "#ffffff",
        "sidebar_text": "#1f2937",
        "sidebar_muted": "#5b6878",
        "hero_start": "rgba(18, 35, 58, 0.96)",
        "hero_end": "rgba(15, 118, 110, 0.88)",
    },
}

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ----------------------------
# Native File/Folder Picker
# ----------------------------
def _picker_process(queue: multiprocessing.Queue, mode: str = "file") -> None:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    if mode == "folder":
        path = filedialog.askdirectory()
    else:
        path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])

    root.destroy()
    queue.put(path)


def get_path_safely(mode: str = "file") -> str:
    queue: multiprocessing.Queue = multiprocessing.Queue()
    process = multiprocessing.Process(target=_picker_process, args=(queue, mode))
    process.start()
    path = queue.get()
    process.join()
    return path


# ----------------------------
# Session + Theme Helpers
# ----------------------------
def initialize_session_state() -> None:
    defaults = {
        "file_path": "",
        "analysis_done": False,
        "master_data": [],
        "project_errors": [],
        "file_contents": {},
        "selected_page": "overview",
        "ui_theme": "dark",
        "ui_feedback": None,
        "doc_style": "Google",
        "last_style": "Google",
        "doc_cache": {},
        "doc_review_panel": "compare",
        "dashboard_panel": "filters",
        "function_analysis_panel": "table",
        "quality_panel": "issues",
        "show_onboarding_hint": True,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_theme_tokens() -> Dict[str, str]:
    return THEME_TOKENS[st.session_state.get("ui_theme", "dark")]


def get_page_title(page_key: str) -> str:
    return NAV_ITEMS.get(page_key, "Overview")


def get_nav_label(page_key: str) -> str:
    return f"{NAV_ICONS.get(page_key, '•')} {get_page_title(page_key)}"


def set_feedback(message: str, level: str = "info") -> None:
    st.session_state.ui_feedback = {"message": message, "level": level}


def render_feedback() -> None:
    payload = st.session_state.get("ui_feedback")
    if not payload:
        return

    message = payload["message"]
    level = payload["level"]
    icon = {"success": "✅", "warning": "⚠️", "error": "🚨", "info": "ℹ️"}.get(level, "ℹ️")

    if hasattr(st, "toast"):
        try:
            st.toast(message, icon=icon)
        except TypeError:
            st.toast(f"{icon} {message}")
    else:
        getattr(st, level if level in {"success", "warning", "error", "info"} else "info")(message)

    st.session_state.ui_feedback = None


def inject_global_styles() -> None:
    theme = get_theme_tokens()
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

        :root {{
            --bg: {theme['bg']};
            --bg-soft: {theme['bg_soft']};
            --panel: {theme['panel']};
            --panel-strong: {theme['panel_strong']};
            --panel-alt: {theme['panel_alt']};
            --border: {theme['border']};
            --text: {theme['text']};
            --muted: {theme['muted']};
            --primary: {theme['primary']};
            --accent: {theme['accent']};
            --accent-2: {theme['accent_2']};
            --success: {theme['success']};
            --warning: {theme['warning']};
            --danger: {theme['danger']};
            --shadow: {theme['shadow']};
            --card-text: {theme['card_text']};
            --control-bg: {theme['panel_strong']};
            --control-bg-soft: {theme['panel_alt']};
            --sidebar-bg: {theme['sidebar_bg']};
            --sidebar-panel: {theme['sidebar_panel']};
            --sidebar-text: {theme['sidebar_text']};
            --sidebar-muted: {theme['sidebar_muted']};
            --hero-start: {theme['hero_start']};
            --hero-end: {theme['hero_end']};
        }}

        html, body, [class*="css"] {{
            font-family: 'Manrope', sans-serif;
        }}

        .stApp {{
            background:
                radial-gradient(circle at 18% 14%, rgba(103, 232, 249, 0.10), transparent 22%),
                radial-gradient(circle at 82% 8%, rgba(56, 189, 248, 0.09), transparent 18%),
                linear-gradient(180deg, var(--bg-soft) 0%, var(--bg) 100%);
            color: var(--text);
        }}

        .block-container {{
            padding-top: 1.25rem;
            padding-bottom: 2.5rem;
        }}

        @keyframes riseIn {{
            0% {{
                opacity: 0;
                transform: translateY(10px);
            }}
            100% {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .ambient-orb {{
            position: fixed;
            width: 18rem;
            height: 18rem;
            border-radius: 50%;
            filter: blur(88px);
            opacity: 0.10;
            pointer-events: none;
            animation: floatOrb 22s ease-in-out infinite;
            z-index: 0;
        }}

        .orb-one {{ top: -4rem; left: -4rem; background: var(--primary); }}
        .orb-two {{ top: 12rem; right: -5rem; background: var(--accent); animation-delay: -8s; }}
        .orb-three {{ display:none; }}

        @keyframes floatOrb {{
            0%, 100% {{ transform: translate3d(0, 0, 0) scale(1); }}
            50% {{ transform: translate3d(0, 18px, 0) scale(1.06); }}
        }}

        section[data-testid="stSidebar"] {{
            background: var(--sidebar-bg);
            border-right: 1px solid var(--border);
        }}

        section[data-testid="stSidebar"] * {{
            color: var(--sidebar-text);
        }}

        section[data-testid="stSidebar"] div[data-baseweb="select"] > div {{
            background: var(--sidebar-panel) !important;
            border: 1px solid rgba(148, 163, 184, 0.24) !important;
            border-radius: 16px !important;
            box-shadow: var(--shadow);
            transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
        }}

        section[data-testid="stSidebar"] div[data-baseweb="select"] > div:hover {{
            transform: translateY(-1px);
            border-color: rgba(56, 189, 248, 0.36) !important;
            box-shadow: 0 18px 30px rgba(2, 6, 23, 0.18);
        }}

        section[data-testid="stSidebar"] div.stButton > button {{
            width: 100%;
        }}

        section[data-testid="stSidebar"] div.stButton > button:hover {{
            transform: translateY(-1px) scale(1.01);
        }}

        .panel-card, .topbar-card, .hero-card {{
            background: var(--panel);
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
            backdrop-filter: blur(18px);
            transition: transform 0.22s ease, border-color 0.22s ease, box-shadow 0.22s ease;
            animation: riseIn 0.42s ease both;
        }}

        .panel-card:hover, .topbar-card:hover, .hero-card:hover {{
            transform: translateY(-2px);
            border-color: rgba(56, 189, 248, 0.24);
            box-shadow: 0 28px 52px rgba(2, 6, 23, 0.18);
        }}

        .sidebar-brand, .sidebar-card {{
            background: var(--sidebar-panel);
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
        }}

        .sidebar-brand {{
            border-radius: 24px;
            padding: 1.1rem 1rem;
            margin-bottom: 1rem;
        }}

        .sidebar-brand h2,
        .sidebar-value {{
            color: var(--sidebar-text);
        }}

        .sidebar-muted {{
            color: var(--sidebar-muted);
        }}

        .sidebar-card, .panel-card {{
            border-radius: 20px;
            padding: 1rem;
        }}

        .sidebar-hero {{
            min-height: 10rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            gap: 0.5rem;
            border-radius: 24px;
            padding: 1rem 1rem 1.1rem;
            background: linear-gradient(180deg, color-mix(in srgb, var(--sidebar-panel) 94%, transparent), var(--sidebar-panel));
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
            transition: transform 0.22s ease, border-color 0.22s ease, box-shadow 0.22s ease;
        }}

        .sidebar-hero:hover {{
            transform: translateY(-2px);
            border-color: rgba(56, 189, 248, 0.26);
            box-shadow: 0 26px 44px rgba(2, 6, 23, 0.16);
        }}

        .sidebar-hero-title {{
            color: var(--sidebar-text);
            font-size: 1.18rem;
            font-weight: 800;
            margin-top: 0.3rem;
            line-height: 1.15;
        }}

        .sidebar-hero-copy {{
            color: var(--sidebar-muted);
            line-height: 1.6;
            font-size: 0.92rem;
        }}

        .sidebar-hero-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-top: 0.35rem;
        }}

        .sidebar-chip {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.38rem 0.7rem;
            border-radius: 999px;
            background: rgba(56, 189, 248, 0.10);
            border: 1px solid rgba(56, 189, 248, 0.18);
            color: var(--sidebar-text);
            font-size: 0.78rem;
            font-weight: 700;
            transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
        }}

        .sidebar-chip:hover {{
            transform: translateY(-1px);
            border-color: rgba(56, 189, 248, 0.34);
            box-shadow: 0 14px 22px rgba(2, 6, 23, 0.12);
        }}

        .status-chip {{
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.42rem 0.78rem;
            border-radius: 999px;
            background: var(--control-bg-soft);
            border: 1px solid rgba(148, 163, 184, 0.20);
            color: var(--text);
            font-size: 0.85rem;
            font-weight: 700;
        }}

        .topbar-grid {{
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            align-items: center;
            flex-wrap: wrap;
        }}

        .topbar-title {{
            margin: 0.12rem 0 0.2rem;
            color: var(--text);
            font-size: 1.42rem;
            font-weight: 800;
            line-height: 1.15;
        }}

        .topbar-subtitle {{
            color: var(--muted);
            line-height: 1.55;
            font-size: 0.91rem;
        }}

        .toolbar-copy {{
            color: var(--muted);
            font-size: 0.92rem;
            line-height: 1.5;
            padding-top: 0.25rem;
        }}

        .topbar-card {{
            min-height: auto;
            border-radius: 24px;
            padding: 0.8rem 1rem;
            margin-bottom: 0.7rem;
            position: sticky;
            top: 0.85rem;
            z-index: 28;
            background: color-mix(in srgb, var(--panel) 88%, transparent);
        }}

        .topbar-card::before {{
            content: "";
            display: block;
            width: 3.5rem;
            height: 0.22rem;
            border-radius: 999px;
            margin-bottom: 0.65rem;
            background: linear-gradient(90deg, var(--primary), var(--accent), var(--accent-2));
            opacity: 0.75;
        }}

        .hero-card {{
            border-radius: 26px;
            padding: 1.2rem 1.3rem;
            background:
                linear-gradient(135deg, var(--hero-start), var(--hero-end)),
                var(--panel);
            margin-bottom: 0.9rem;
        }}

        .hero-kicker, .section-kicker, .mini-label {{
            font-size: 0.76rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            font-weight: 800;
            color: var(--primary);
        }}

        .hero-title {{
            font-size: 2.2rem;
            font-weight: 800;
            color: #f8fafc;
            margin: 0.35rem 0 0.55rem;
        }}

        .hero-copy, .section-copy, .soft-copy {{
            color: var(--muted);
            line-height: 1.65;
        }}

        .hero-pill {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.45rem 0.7rem;
            margin: 0.2rem 0.3rem 0 0;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.07);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: #f8fafc;
            font-size: 0.86rem;
            font-weight: 700;
        }}

        .workflow-loop {{
            position: relative;
            overflow: hidden;
            margin-top: 1rem;
            padding: 1rem 0.7rem;
            border-radius: 24px;
            background:
                linear-gradient(180deg, rgba(15, 23, 42, 0.72), rgba(15, 23, 42, 0.42)),
                var(--panel);
            border: 1px solid rgba(148, 163, 184, 0.16);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
            -webkit-mask-image: linear-gradient(90deg, transparent 0%, black 7%, black 93%, transparent 100%);
            mask-image: linear-gradient(90deg, transparent 0%, black 7%, black 93%, transparent 100%);
        }}

        .workflow-loop::before {{
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(90deg, transparent 0%, rgba(103, 232, 249, 0.18) 50%, transparent 100%);
            opacity: 0.55;
            animation: loopShine 7s linear infinite;
            pointer-events: none;
        }}

        .workflow-loop-track {{
            position: relative;
            z-index: 1;
            display: flex;
            align-items: stretch;
            width: max-content;
            --loop-gap: 0.85rem;
            gap: var(--loop-gap);
            animation: loopScroll 18s linear infinite;
        }}

        .workflow-loop-group {{
            display: flex;
            align-items: stretch;
            gap: 0.85rem;
        }}

        .workflow-loop-item {{
            width: 132px;
            min-height: 88px;
            padding: 0.72rem 0.75rem;
            border-radius: 18px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            gap: 0.18rem;
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.09), rgba(255, 255, 255, 0.03)),
                var(--panel);
            border: 1px solid rgba(148, 163, 184, 0.18);
            box-shadow: 0 16px 28px rgba(2, 6, 23, 0.12);
            transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
        }}

        .workflow-loop-item:hover {{
            transform: translateY(-2px);
            border-color: rgba(103, 232, 249, 0.30);
            box-shadow: 0 20px 34px rgba(2, 6, 23, 0.16);
        }}

        .workflow-loop-index {{
            width: 1.65rem;
            height: 1.65rem;
            border-radius: 50%;
            display: grid;
            place-items: center;
            background: linear-gradient(135deg, rgba(103, 232, 249, 0.95), rgba(20, 184, 166, 0.95));
            color: #ffffff;
            font-size: 0.7rem;
            font-weight: 800;
            box-shadow: 0 10px 18px rgba(8, 145, 178, 0.22);
        }}

        .workflow-loop-label {{
            color: var(--text);
            font-size: 0.82rem;
            font-weight: 800;
            line-height: 1.2;
        }}

        .workflow-loop-copy {{
            color: var(--muted);
            font-size: 0.7rem;
            line-height: 1.25;
        }}

        .section-header {{
            margin-bottom: 0.85rem;
        }}

        .section-title {{
            margin: 0.2rem 0 0.15rem;
            color: var(--text);
            font-size: 1.45rem;
            font-weight: 800;
        }}

        .info-card {{
            height: 100%;
            border-radius: 22px;
            padding: 0.95rem 1rem;
            background: var(--panel-alt);
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
            transition: transform 0.18s ease, border-color 0.18s ease;
            animation: riseIn 0.46s ease both;
        }}

        .feature-panel {{
            background: linear-gradient(180deg, var(--panel-strong), var(--panel));
            border: 1px solid var(--border);
            border-radius: 22px;
            padding: 1rem 1.05rem;
            box-shadow: var(--shadow);
            margin-bottom: 0.9rem;
            transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
            animation: riseIn 0.48s ease both;
        }}

        .feature-panel--soft {{
            background: linear-gradient(180deg, var(--panel-alt), var(--panel));
        }}

        .surface-tag {{
            font-size: 0.72rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            font-weight: 800;
            color: var(--muted);
        }}

        .surface-title {{
            color: var(--text);
            font-size: 1.08rem;
            font-weight: 800;
            margin-top: 0.28rem;
        }}

        .surface-copy {{
            color: var(--muted);
            line-height: 1.6;
            margin-top: 0.25rem;
        }}

        .info-card:hover, div[data-testid="metric-container"]:hover {{
            transform: translateY(-2px);
            border-color: rgba(56, 189, 248, 0.34);
        }}

        .feature-panel:hover {{
            transform: translateY(-2px);
            border-color: rgba(56, 189, 248, 0.30);
            box-shadow: 0 22px 38px rgba(15, 23, 42, 0.14);
        }}

        .info-value {{
            font-size: 1.65rem;
            font-weight: 800;
            color: var(--text);
            margin: 0.35rem 0 0.25rem;
        }}

        div[data-testid="metric-container"] {{
            background: var(--panel-alt);
            border: 1px solid var(--border);
            border-radius: 20px;
            box-shadow: var(--shadow);
            padding: 1rem;
        }}

        [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {{
            color: var(--text);
        }}

        section[data-testid="stSidebar"] [data-testid="stMetricLabel"],
        section[data-testid="stSidebar"] [data-testid="stMetricValue"] {{
            color: var(--sidebar-text);
        }}

        div.stButton > button, div.stDownloadButton > button {{
            border-radius: 16px;
            border: 1px solid rgba(148, 163, 184, 0.26);
            font-weight: 700;
            min-height: 2.9rem;
            position: relative;
            overflow: hidden;
            isolation: isolate;
            letter-spacing: 0.01em;
            background: linear-gradient(180deg, var(--control-bg-soft), var(--control-bg));
            color: var(--text);
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,0.16),
                0 10px 20px rgba(15, 23, 42, 0.08);
            transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease, background 0.18s ease, filter 0.18s ease;
        }}

        div.stButton > button[kind="primary"] {{
            animation: primaryGlow 3.8s ease-in-out infinite;
        }}

        div.stDownloadButton > button {{
            animation: downloadGlow 4.8s ease-in-out infinite;
        }}

        div.stButton > button::after, div.stDownloadButton > button::after {{
            content: "";
            position: absolute;
            inset: -30%;
            background: linear-gradient(115deg, transparent 34%, rgba(255,255,255,0.20) 50%, transparent 66%);
            transform: translateX(-140%) rotate(8deg);
            transition: transform 0.55s ease;
            z-index: 0;
            pointer-events: none;
        }}

        div.stButton > button > div, div.stDownloadButton > button > div,
        div.stButton > button p, div.stDownloadButton > button p,
        div.stButton > button span, div.stDownloadButton > button span {{
            position: relative;
            z-index: 1;
            color: inherit !important;
        }}

        div.stButton > button:hover, div.stDownloadButton > button:hover {{
            transform: translateY(-2px) scale(1.01);
            box-shadow: 0 18px 30px rgba(2, 6, 23, 0.18);
            border-color: rgba(56, 189, 248, 0.42);
            filter: saturate(1.08);
        }}

        div.stButton > button:hover::after, div.stDownloadButton > button:hover::after {{
            transform: translateX(140%) rotate(8deg);
        }}

        div.stButton > button:active, div.stDownloadButton > button:active {{
            transform: translateY(0) scale(0.995);
        }}

        div.stButton > button:focus-visible, div.stDownloadButton > button:focus-visible {{
            outline: none;
            box-shadow:
                0 0 0 3px rgba(56, 189, 248, 0.22),
                0 18px 30px rgba(2, 6, 23, 0.18);
        }}

        button[kind="primary"] {{
            background: linear-gradient(135deg, var(--primary), var(--accent-2) 52%, var(--accent));
            color: white;
            border-color: rgba(103, 232, 249, 0.40);
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,0.16),
                0 16px 28px rgba(8, 145, 178, 0.24);
        }}

        button[kind="primary"]:hover {{
            background: linear-gradient(135deg, var(--accent-2), var(--primary) 54%, var(--accent));
            border-color: rgba(103, 232, 249, 0.58);
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,0.16),
                0 20px 36px rgba(8, 145, 178, 0.30);
        }}

        button[kind="secondary"] {{
            background:
                linear-gradient(135deg, rgba(56, 189, 248, 0.14), rgba(20, 184, 166, 0.10)),
                linear-gradient(180deg, var(--control-bg-soft), var(--control-bg));
            color: var(--text);
            border-color: rgba(56, 189, 248, 0.28);
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,0.16),
                0 12px 22px rgba(15, 23, 42, 0.08);
        }}

        button[kind="secondary"]:hover {{
            background:
                linear-gradient(135deg, rgba(59, 130, 246, 0.18), rgba(20, 184, 166, 0.14)),
                linear-gradient(180deg, var(--control-bg-soft), var(--control-bg));
            border-color: rgba(20, 184, 166, 0.42);
        }}

        div.stDownloadButton > button {{
            background: linear-gradient(135deg, rgba(34, 197, 94, 0.96), rgba(13, 148, 136, 0.96));
            color: #ffffff;
            border-color: rgba(34, 197, 94, 0.34);
            box-shadow: 0 14px 24px rgba(21, 128, 61, 0.20);
        }}

        div.stDownloadButton > button:hover {{
            background: linear-gradient(135deg, rgba(22, 163, 74, 1), rgba(15, 118, 110, 1));
            border-color: rgba(16, 185, 129, 0.44);
            box-shadow: 0 18px 30px rgba(21, 128, 61, 0.26);
        }}

        .stButton button[data-testid*="run_analysis"] {{
            min-height: 3.1rem;
        }}

        button[data-baseweb="tab"] {{
            font-weight: 700;
            background: transparent;
            color: var(--muted);
            border-radius: 12px;
        }}

        button[data-baseweb="tab"][aria-selected="true"] {{
            background: var(--control-bg);
            color: var(--text);
            border: 1px solid rgba(103, 232, 249, 0.24);
        }}

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        .stTextInput input,
        .stTextArea textarea {{
            background: var(--control-bg) !important;
            color: var(--text) !important;
            border: 1px solid rgba(148, 163, 184, 0.22) !important;
            border-radius: 14px !important;
            transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease, background 0.18s ease;
        }}

        div[data-baseweb="select"] > div:hover,
        div[data-baseweb="input"] > div:hover,
        .stTextInput input:hover,
        .stTextArea textarea:hover {{
            border-color: rgba(56, 189, 248, 0.38) !important;
        }}

        div[data-baseweb="select"] > div:focus-within,
        div[data-baseweb="input"] > div:focus-within,
        .stTextInput input:focus,
        .stTextArea textarea:focus {{
            box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.14);
        }}

        div[data-baseweb="select"] svg,
        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder {{
            color: var(--muted) !important;
        }}

        div[role="radiogroup"] > label {{
            background: var(--sidebar-panel);
            border: 1px solid rgba(148, 163, 184, 0.20);
            border-radius: 14px;
            padding: 0.6rem 0.8rem;
            margin-bottom: 0.4rem;
            transition: background 0.18s ease, border-color 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease;
        }}

        div[role="radiogroup"] > label:hover {{
            border-color: rgba(56, 189, 248, 0.34);
            transform: translateX(2px);
        }}

        div[role="radiogroup"] > label:has(input:checked) {{
            background:
                linear-gradient(135deg, rgba(56, 189, 248, 0.16), rgba(20, 184, 166, 0.10)),
                var(--control-bg);
            border-color: rgba(103, 232, 249, 0.36);
            box-shadow: 0 12px 22px rgba(2, 6, 23, 0.12);
        }}

        div[role="radiogroup"] > label > div {{
            color: inherit !important;
            font-weight: 700;
        }}

        div[data-testid="stDataFrame"] {{
            background: var(--panel-strong);
            border: 1px solid var(--border);
            border-radius: 18px;
            overflow: hidden;
            animation: riseIn 0.5s ease both;
        }}

        div[data-testid="stDataFrame"] * {{
            color: var(--text);
        }}

        div[data-testid="stCodeBlock"],
        div[data-testid="stJson"] {{
            border-radius: 18px;
            overflow: hidden;
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
            background: var(--panel-strong);
            animation: riseIn 0.5s ease both;
        }}

        div[data-testid="stExpander"] {{
            background: var(--panel-alt);
            border: 1px solid var(--border);
            border-radius: 18px;
            box-shadow: var(--shadow);
            overflow: hidden;
        }}

        div[data-testid="stExpander"] summary {{
            color: var(--text);
            font-weight: 700;
        }}

        div[data-testid="stAlert"] {{
            border-radius: 18px;
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
            backdrop-filter: blur(16px);
            background: color-mix(in srgb, var(--panel) 92%, var(--bg-soft) 8%);
            color: var(--text);
        }}

        div[data-testid="stAlert"] * {{
            color: inherit;
        }}

        @media (max-width: 900px) {{
            .topbar-card {{
                position: static;
            }}
        }}

        @keyframes loopScroll {{
            from {{ transform: translateX(0); }}
            to {{ transform: translateX(calc(-50% - (var(--loop-gap) / 2))); }}
        }}

        @keyframes loopShine {{
            0% {{ transform: translateX(-40%); opacity: 0.25; }}
            50% {{ opacity: 0.7; }}
            100% {{ transform: translateX(40%); opacity: 0.25; }}
        }}

        @keyframes primaryGlow {{
            0%, 100% {{ box-shadow: inset 0 1px 0 rgba(255,255,255,0.16), 0 16px 28px rgba(8, 145, 178, 0.24); }}
            50% {{ box-shadow: inset 0 1px 0 rgba(255,255,255,0.18), 0 18px 34px rgba(8, 145, 178, 0.34); }}
        }}

        @keyframes downloadGlow {{
            0%, 100% {{ box-shadow: 0 14px 24px rgba(21, 128, 61, 0.20); }}
            50% {{ box-shadow: 0 18px 30px rgba(21, 128, 61, 0.28); }}
        }}

        @media (prefers-reduced-motion: reduce) {{
            *, *::before, *::after {{
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
                scroll-behavior: auto !important;
            }}
        }}

        div[data-testid="stCodeBlock"] pre,
        div[data-testid="stJson"] > div {{
            background: var(--panel-strong) !important;
            color: var(--text) !important;
        }}

        header[data-testid="stHeader"] {{
            background: transparent;
        }}

        #MainMenu,
        footer {{
            visibility: hidden;
            height: 0;
        }}

        .block-container {{
            padding-top: 0.95rem;
            padding-bottom: 4.5rem;
        }}

        .workspace-footer {{
            margin-top: 1rem;
            padding: 0.95rem 1rem;
            border-radius: 18px;
            border: 1px solid var(--border);
            background: var(--panel-alt);
            box-shadow: var(--shadow);
            color: var(--muted);
            font-size: 0.88rem;
            line-height: 1.5;
        }}

        .workspace-footer strong {{
            color: var(--text);
        }}

        .issue-card {{
            background: color-mix(in srgb, var(--danger) 10%, var(--panel) 90%);
            border: 1px solid color-mix(in srgb, var(--danger) 28%, var(--border) 72%);
            border-left: 4px solid var(--danger);
            color: var(--text);
            font-weight: 600;
            line-height: 1.45;
            padding: 0.8rem 0.9rem;
            border-radius: 16px;
            margin-bottom: 0.65rem;
        }}

        ::-webkit-scrollbar {{ width: 8px; }}
        ::-webkit-scrollbar-thumb {{
            background: rgba(148, 163, 184, 0.35);
            border-radius: 999px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_background_layer() -> None:
    st.markdown(
        """
        <div class="ambient-orb orb-one"></div>
        <div class="ambient-orb orb-two"></div>
        """,
        unsafe_allow_html=True,
    )


def build_analysis_dataframe() -> pd.DataFrame:
    return pd.DataFrame(st.session_state.master_data, columns=ANALYSIS_COLUMNS)


def clean_dataframe_for_display(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned = cleaned.replace(r"^\s*$", pd.NA, regex=True)
    cleaned = cleaned.dropna(how="all").reset_index(drop=True)
    return cleaned


def dataframe_height(df: pd.DataFrame, min_rows: int = 1, max_rows: int = 12) -> int:
    row_count = 0 if df is None else len(df)
    visible_rows = max(min_rows, min(max_rows, row_count if row_count > 0 else min_rows))
    return 44 + (visible_rows * 35)


def color_docstring(value: str) -> str:
    if value == DOC_PRESENT:
        return "background-color: rgba(34,197,94,0.18); color: #16a34a; font-weight: 700;"
    return "background-color: rgba(244,63,94,0.18); color: #e11d48; font-weight: 700;"


def get_project_status(df: pd.DataFrame) -> Tuple[str, str]:
    if df.empty:
        return "No Data", "#94a3b8"

    doc_percent = (len(df[df["Docstring"] == DOC_PRESENT]) / len(df)) * 100
    avg_complexity = df["Complexity"].mean()
    total_violations = df["Violations"].sum()
    score = doc_percent - (avg_complexity * 2) - (total_violations * 3)

    if score >= 60:
        return "Healthy", get_theme_tokens()["success"]
    if score >= 30:
        return "Needs Attention", get_theme_tokens()["warning"]
    return "High Risk", get_theme_tokens()["danger"]


def get_docstring_percentage(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0
    return float(df["Docstring"].eq(DOC_PRESENT).mean() * 100)


def build_file_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["File", "Functions", "Missing Docstrings", "Avg Complexity", "Violations"])

    summary = (
        df.groupby("File")
        .agg(
            Functions=("Function", "count"),
            Violations=("Violations", "sum"),
            Avg_Complexity=("Complexity", "mean"),
            Missing_Docstrings=("Docstring", lambda values: int((values == DOC_MISSING).sum())),
        )
        .reset_index()
        .rename(columns={"Avg_Complexity": "Avg Complexity", "Missing_Docstrings": "Missing Docstrings"})
    )
    summary["Avg Complexity"] = summary["Avg Complexity"].round(1)
    return summary.sort_values(by=["Violations", "Missing Docstrings", "Avg Complexity"], ascending=[False, False, False])


def apply_chart_layout(fig: go.Figure, title: str, xaxis_title: str = "", yaxis_title: str = "", height: int = 380, tickangle: int = 0) -> go.Figure:
    theme = get_theme_tokens()
    fig.update_layout(
        title=title,
        template=theme["chart_template"],
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=24, r=24, t=56, b=24),
        font=dict(color=theme["text"]),
        legend_title_text="",
        hoverlabel=dict(bgcolor=theme["panel_strong"]),
    )
    fig.update_xaxes(title=xaxis_title, tickangle=tickangle, showgrid=False)
    fig.update_yaxes(title=yaxis_title, gridcolor="rgba(148,163,184,0.16)")
    return fig


def render_section_header(title: str, subtitle: str, kicker: str = "Workspace") -> None:
    st.markdown(
        f"""
        <div class="section-header">
            <div class="section-kicker">{html.escape(kicker)}</div>
            <div class="section-title">{html.escape(title)}</div>
            <div class="section-copy">{html.escape(subtitle)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_info_card(label: str, value: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="info-card">
            <div class="mini-label">{html.escape(label)}</div>
            <div class="info-value">{html.escape(value)}</div>
            <div class="soft-copy">{html.escape(description)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_feature_panel(tag: str, title: str, description: str, accent: Optional[str] = None, soft: bool = False) -> None:
    accent_color = accent or get_theme_tokens()["primary"]
    panel_class = "feature-panel feature-panel--soft" if soft else "feature-panel"
    st.markdown(
        f"""
        <div class="{panel_class}" style="border-top:3px solid {accent_color};">
            <div class="surface-tag">{html.escape(tag)}</div>
            <div class="surface-title">{html.escape(title)}</div>
            <div class="surface-copy">{html.escape(description)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_data_table(
    title: str,
    description: str,
    df: pd.DataFrame,
    max_rows: int = 12,
    style_docstring_col: bool = False,
) -> None:
    display_df = clean_dataframe_for_display(df)
    render_feature_panel("Data View", title, f"{description} Showing {len(display_df)} row(s).", soft=True)
    dataframe_payload = display_df
    if style_docstring_col and "Docstring" in display_df.columns:
        dataframe_payload = display_df.style.applymap(color_docstring, subset=["Docstring"])
    st.dataframe(
        dataframe_payload,
        use_container_width=True,
        height=dataframe_height(display_df, max_rows=max_rows),
        hide_index=True,
    )


def render_json_panel(title: str, description: str, payload, download_name: str) -> None:
    render_feature_panel("JSON View", title, description, accent=get_theme_tokens()["accent"], soft=True)
    json_string = payload if isinstance(payload, str) else json.dumps(payload, indent=2)
    st.code(json_string, language="json")
    st.download_button(
        "⬇ Download JSON",
        json_string,
        download_name,
        "application/json",
        use_container_width=True,
        help="Download the current JSON payload.",
    )


def render_button_selector(options, session_key: str, button_prefix: str) -> str:
    valid_values = [value for value, _ in options]
    current_value = st.session_state.get(session_key, options[0][0])
    if current_value not in valid_values:
        current_value = options[0][0]
    cols = st.columns(len(options))
    changed = False

    for col, (value, label) in zip(cols, options):
        with col:
            if st.button(
                label,
                key=f"{button_prefix}_{value}",
                use_container_width=True,
                type="primary" if current_value == value else "secondary",
                help=f"Switch to {label}.",
            ):
                if current_value != value:
                    current_value = value
                    changed = True

    st.session_state[session_key] = current_value
    if changed:
        st.rerun()
    return current_value


def render_workspace_snapshot(df: pd.DataFrame, subtitle: str = "Current workspace snapshot") -> None:
    if df.empty:
        return

    status, status_color = get_project_status(df)
    st.markdown(
        f"""
        <div class="panel-card" style="border-left:4px solid {status_color};margin-bottom:0.85rem;">
            <div class="mini-label">Snapshot</div>
            <div class="surface-title">{html.escape(subtitle)}</div>
            <div class="surface-copy">{html.escape(status)} workspace state. Use this summary before filtering, editing, or exporting.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    snapshot_col1, snapshot_col2, snapshot_col3, snapshot_col4 = st.columns(4)
    with snapshot_col1:
        st.metric("Functions", len(df))
    with snapshot_col2:
        st.metric("Violations", int(df["Violations"].sum()))
    with snapshot_col3:
        st.metric("Docstrings", f"{get_docstring_percentage(df):.0f}%")
    with snapshot_col4:
        st.metric("Avg Complexity", f"{df['Complexity'].mean():.1f}")


def render_source_workflow(title: str, description: str) -> None:
    steps = [
        ("01", "Select", "Pick a file or folder"),
        ("02", "Analyze", "Run the analyzer"),
        ("03", "Review", "Inspect the dashboard"),
        ("04", "Improve", "Update docs and fixes"),
        ("05", "Export", "Share results"),
    ]
    step_markup = "".join(
        f"""
        <div class="workflow-loop-item">
            <div class="workflow-loop-index">{html.escape(step[0])}</div>
            <div class="workflow-loop-label">{html.escape(step[1])}</div>
            <div class="workflow-loop-copy">{html.escape(step[2])}</div>
        </div>
        """
        for step in steps
    )
    loop_markup = "".join(
        (
            f'<div class="workflow-loop-group">{step_markup}</div>'
            if repeat_index == 0
            else f'<div class="workflow-loop-group" aria-hidden="true">{step_markup}</div>'
        )
        for repeat_index in range(2)
    )

    st.markdown(
        f"""
        <div class="panel-card" style="margin-bottom:0.9rem;">
            <div class="mini-label">Workflow</div>
            <div class="surface-title">{html.escape(title)}</div>
            <div class="surface-copy">{html.escape(description)}</div>
            <div class="workflow-loop" aria-label="Animated workflow loop">
                <div class="workflow-loop-track">
                    {loop_markup}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard_help() -> None:
    render_feature_panel(
        "Help",
        "How to use the workspace",
        "A quick guide to search, filters, tests, and export.",
        accent=get_theme_tokens()["primary"],
        soft=True,
    )
    help_rows = st.columns(2)
    help_cards = [
        ("Filters", "Narrow the dataset by complexity, docstrings, and file scope."),
        ("Search", "Find analyzed functions by name without leaving the dashboard."),
        ("Tests", "Run `pytest` only and review the latest test report."),
        ("Export", "Save the current analysis as CSV or JSON for sharing."),
    ]
    for index, (tag, description) in enumerate(help_cards):
        with help_rows[index % 2]:
            render_feature_panel(tag, tag, description, soft=True)


def render_function_change_preview(function_code: str, generated_doc: str, current_doc: Optional[str], current_style: str) -> None:
    clean_code = remove_existing_docstring(function_code)
    updated_preview = insert_docstring(clean_code, generated_doc)
    change_summary = (
        f"Added a new {current_style} docstring."
        if current_doc is None
        else f"Updated the existing docstring to the {current_style} style."
    )

    render_feature_panel(
        "Preview",
        "Before code vs after code",
        "Compare the selected function before applying the generated docstring.",
        accent=get_theme_tokens()["accent"],
        soft=True,
    )

    before_col, after_col = st.columns(2)
    with before_col:
        st.markdown("#### Before")
        st.code(function_code or "No source available.", language="python")
    with after_col:
        st.markdown("#### After")
        st.code(updated_preview or "No preview available.", language="python")

    change_col1, change_col2 = st.columns(2)
    with change_col1:
        render_info_card("What Changed", change_summary, "The function body and signature stay the same.")
    with change_col2:
        render_info_card("Scope", "Docstring only", "No executable logic changes until you confirm the update.")


def resolve_selected_file_path(selected_file: str) -> Optional[str]:
    return next(
        (
            file_path
            for file_path in st.session_state.file_contents
            if os.path.basename(file_path) == selected_file
        ),
        None,
    )


def choose_source(mode: str) -> bool:
    selected_path = get_path_safely(mode)
    if not selected_path:
        return False

    st.session_state.file_path = selected_path
    st.session_state.analysis_done = False
    st.session_state.doc_cache = {}
    st.session_state.master_data = []
    st.session_state.project_errors = []
    st.session_state.file_contents = {}
    set_feedback(f"{'File' if mode == 'file' else 'Folder'} selected. Run analysis to refresh the workspace.", "info")
    return True


def run_analysis_with_feedback() -> bool:
    if not st.session_state.file_path:
        set_feedback("Choose a file or folder first.", "warning")
        return False

    with st.spinner("Analyzing project..."):
        run_full_analysis()
    set_feedback("Analysis complete.", "success")
    return True


def reset_workspace() -> None:
    st.session_state.file_path = ""
    st.session_state.analysis_done = False
    st.session_state.master_data = []
    st.session_state.project_errors = []
    st.session_state.file_contents = {}
    st.session_state.doc_cache = {}
    st.session_state.selected_page = "overview"
    st.session_state.dashboard_panel = "filters"
    st.session_state.function_analysis_panel = "table"
    st.session_state.quality_panel = "issues"
    st.session_state.doc_review_panel = "compare"
    set_feedback("Workspace reset.", "info")


# ----------------------------
# Full Analysis
# ----------------------------
def run_full_analysis() -> None:
    files = []
    if os.path.isdir(st.session_state.file_path):
        for root_dir, _, file_names in os.walk(st.session_state.file_path):
            for file_name in file_names:
                if file_name.endswith(".py"):
                    files.append(os.path.join(root_dir, file_name))
    elif st.session_state.file_path:
        files.append(st.session_state.file_path)

    files.sort()
    master_data = []
    project_errors = []
    file_contents = {}

    for file_path in files:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            file_contents[file_path] = content

        errors, _ = fix_source_code(content, os.path.basename(file_path))
        raw_functions = extract_functions(file_path, original_name=os.path.basename(file_path))

        for result in raw_functions:
            master_data.append(
                {
                    "File": result["file_name"],
                    "Function": result["function_name"],
                    "Start Line": result.get("start_line"),
                    "End Line": result.get("end_line"),
                    "Complexity": result["cyclomatic_complexity"],
                    "Violations": len(result["errors"]),
                    "Docstring": DOC_PRESENT if result["has_docstring"] else DOC_MISSING,
                }
            )

        if errors:
            project_errors.extend((os.path.basename(file_path), error) for error in errors)

        for result in raw_functions:
            for error in result["errors"]:
                if "Missing Docstring" in error:
                    continue
                project_errors.append((result["file_name"], f"{result['function_name']}: {error}"))

    st.session_state.master_data = master_data
    st.session_state.project_errors = project_errors
    st.session_state.file_contents = file_contents
    st.session_state.analysis_done = True


# ----------------------------
# Global Layout
# ----------------------------
def render_sidebar(df: pd.DataFrame) -> str:
    nav_options = NAV_SEQUENCE
    current_page = st.session_state.get("selected_page", nav_options[0])
    if current_page not in nav_options:
        current_page = nav_options[0]
        st.session_state.selected_page = current_page
    file_selected = bool(st.session_state.file_path)
    target_name = os.path.basename(st.session_state.file_path) if file_selected else "Nothing selected"
    sidebar_copy = (
        f"Working on {target_name}. Run analysis to refresh the workspace."
        if file_selected
        else "No source selected yet. Choose a file or folder to start the animated workflow."
    )
    sidebar_chips = (
        [("Source ready", "Current file or folder is loaded"), ("Review", "Open dashboard pages"), ("Export", "Save results")]
        if file_selected
        else [("Select source", "Pick a file or folder"), ("Analyze", "Unlock the workspace"), ("Review", "See results")]
    )

    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-hero">
                <div>
                    <div class="mini-label">Workspace</div>
                    <div class="sidebar-hero-title">✨ AI Python Code Studio</div>
                    <div class="sidebar-hero-copy">%s</div>
                </div>
                <div class="sidebar-hero-meta">
                    %s
                </div>
            </div>
            """ % (
                html.escape(sidebar_copy),
                "".join(
                    f'<span class="sidebar-chip">{html.escape(label)}</span>'
                    for label, _ in sidebar_chips
                ),
            ),
            unsafe_allow_html=True,
        )

        st.markdown('<div class="mini-label" style="margin-top:0.95rem;">Theme</div>', unsafe_allow_html=True)
        theme_label = "Switch to Light" if st.session_state.ui_theme == "dark" else "Switch to Dark"
        if st.button(f"🌓 {theme_label}", use_container_width=True, help="Toggle the interface theme."):
            st.session_state.ui_theme = "light" if st.session_state.ui_theme == "dark" else "dark"
            set_feedback(f"Theme switched to {st.session_state.ui_theme.title()}.", "success")
            st.rerun()

        st.markdown('<div class="mini-label" style="margin-top:0.95rem;">Source</div>', unsafe_allow_html=True)
        source_col1, source_col2 = st.columns(2)
        with source_col1:
            if st.button("📄 File", use_container_width=True, help="Select a single Python file."):
                if choose_source("file"):
                    st.rerun()

        with source_col2:
            if st.button("📁 Folder", use_container_width=True, help="Select a Python project folder."):
                if choose_source("folder"):
                    st.rerun()

        st.markdown(
            f"""
            <div class="sidebar-card">
                <div class="mini-label">Current Target</div>
                <div class="sidebar-value" style="font-size:1rem;font-weight:800;margin-top:0.35rem;">{html.escape(target_name)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="mini-label" style="margin-top:1rem;">Navigation</div>', unsafe_allow_html=True)
        st.selectbox(
            "Page",
            nav_options,
            format_func=get_nav_label,
            key="selected_page",
            label_visibility="collapsed",
            help="Jump between the workspace sections.",
        )

        st.markdown('<div class="mini-label" style="margin-top:0.95rem;">Run</div>', unsafe_allow_html=True)
        analyze_label = "🚀 Refresh Analysis" if st.session_state.analysis_done else "🚀 Run Analysis"
        if st.button(
            analyze_label,
            key="run_analysis_sidebar",
            use_container_width=True,
            type="primary",
            help="Run or refresh analysis for the selected source.",
        ):
            if st.session_state.file_path:
                run_analysis_with_feedback()
                st.rerun()
            else:
                set_feedback("Choose a file or folder first.", "warning")
                st.rerun()

        if st.session_state.analysis_done and not df.empty and st.session_state.selected_page in {"dashboard", "functions", "docstrings"}:
            st.markdown('<div class="mini-label" style="margin-top:1rem;">Snapshot</div>', unsafe_allow_html=True)
            snapshot_col1, snapshot_col2 = st.columns(2)
            with snapshot_col1:
                st.metric("Functions", len(df))
                st.metric("Docstrings", f"{get_docstring_percentage(df):.0f}%")
            with snapshot_col2:
                st.metric("Violations", int(df["Violations"].sum()))
                st.metric("Avg Complexity", f"{df['Complexity'].mean():.1f}")

    return st.session_state.selected_page


def render_action_bar() -> None:
    page_key = st.session_state.get("selected_page", "overview")
    page_title = get_page_title(page_key)
    page_icon = NAV_ICONS.get(page_key, "•")
    target_name = os.path.basename(st.session_state.file_path) if st.session_state.file_path else "No source selected"
    status_label = "Analysis ready" if st.session_state.analysis_done else "Awaiting analysis"
    status_color = get_theme_tokens()["success"] if st.session_state.analysis_done else get_theme_tokens()["warning"]

    st.markdown(
        f"""
        <div class="topbar-card">
            <div class="topbar-grid">
                <div>
                    <div class="mini-label">Workspace</div>
                    <div class="topbar-title">{html.escape(page_icon)} {html.escape(page_title)}</div>
                    <div class="topbar-subtitle">Target: {html.escape(target_name)} • {html.escape(status_label)}</div>
                </div>
                <div class="status-chip" style="border-color:{status_color}40;color:{status_color};">
                    <span style="width:0.55rem;height:0.55rem;border-radius:50%;background:{status_color};display:inline-block;"></span>
                    {html.escape(status_label)}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(has_source: bool = False) -> None:
    if not has_source:
        render_source_workflow(
            "AI Python Code Studio Workflow",
            "A clean loop keeps moving until you select a source from the sidebar.",
        )
        return

    render_section_header(
        "Source Ready",
        "A source is selected. Run analysis from the sidebar to unlock the dashboard pages.",
        "Getting Started",
    )
    st.markdown(
        """
        <div class="panel-card">
            <div class="mini-label">Ready State</div>
            <div class="surface-title">The workflow is waiting for analysis.</div>
            <div class="surface-copy">Once you run analysis, the dashboard, docstring review, and code quality views will fill with live project data.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_chatbot_context(df: pd.DataFrame) -> Dict[str, object]:
    target_name = os.path.basename(st.session_state.file_path) if st.session_state.file_path else "No source selected"
    analysis_ready = st.session_state.analysis_done and not df.empty
    return {
        "app_title": APP_TITLE,
        "target_name": target_name,
        "selected_page": get_page_title(st.session_state.get("selected_page", "overview")),
        "analysis_ready": analysis_ready,
        "functions": int(len(df)) if analysis_ready else 0,
        "violations": int(df["Violations"].sum()) if analysis_ready else 0,
        "docstrings": f"{get_docstring_percentage(df):.0f}%" if analysis_ready else "0%",
    }


def build_chatbot_html(df: pd.DataFrame) -> str:
    theme = get_theme_tokens()
    context = build_chatbot_context(df)
    # Keep the embedded assistant state machine lightweight and self-contained.
    context_json = json.dumps(context).replace("</", "<\\/")
    title = html.escape(APP_TITLE)
    template = Template(
        dedent(
            """
            <style>
            :root {
                --bg: $bg;
                --panel: $panel;
                --panel-alt: $panel_alt;
                --border: $border;
                --text: $text;
                --muted: $muted;
                --primary: $primary;
                --accent: $accent;
                --accent-2: $accent_2;
                --shadow: $shadow;
            }
            html, body {
                margin: 0;
                width: 100%;
                height: 100%;
                background: transparent;
                overflow: hidden;
                font-family: "Manrope", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            }
            * { box-sizing: border-box; }
            .chat-root {
                width: 100%;
                height: 100%;
                position: relative;
                pointer-events: none;
            }
            .chat-fab {
                position: absolute;
                right: 0;
                bottom: 0;
                width: 3.45rem;
                height: 3.45rem;
                border: 0;
                border-radius: 999px;
                color: #fff;
                background: linear-gradient(135deg, var(--primary), var(--accent-2) 52%, var(--accent));
                box-shadow: 0 18px 34px rgba(8, 145, 178, 0.30);
                cursor: pointer;
                font-size: 1.1rem;
                font-weight: 800;
                pointer-events: auto;
                transition: transform 0.2s ease, opacity 0.2s ease, box-shadow 0.2s ease;
            }
            .chat-shell {
                position: absolute;
                inset: 0;
            }
            .chat-panel {
                position: absolute;
                inset: 0;
                display: flex;
                flex-direction: column;
                border-radius: 22px;
                border: 1px solid var(--border);
                background: color-mix(in srgb, var(--panel) 96%, transparent);
                backdrop-filter: blur(18px);
                box-shadow: var(--shadow);
                opacity: 0;
                transform: translateY(16px) scale(0.96);
                pointer-events: none;
                overflow: hidden;
                transition: opacity 0.22s ease, transform 0.22s ease;
            }
            .chat-shell.open .chat-panel {
                opacity: 1;
                transform: translateY(0) scale(1);
                pointer-events: auto;
            }
            .chat-shell.open .chat-fab {
                opacity: 0;
                transform: translateY(8px) scale(0.8);
                pointer-events: none;
            }
            .chat-header {
                display: flex;
                justify-content: space-between;
                gap: 0.75rem;
                padding: 0.9rem 1rem;
                border-bottom: 1px solid color-mix(in srgb, var(--border) 84%, transparent);
                background: linear-gradient(135deg, color-mix(in srgb, var(--panel-alt) 72%, transparent), var(--panel));
            }
            .chat-kicker {
                color: var(--muted);
                font-size: 0.7rem;
                font-weight: 800;
                letter-spacing: 0.16em;
                text-transform: uppercase;
            }
            .chat-title {
                margin-top: 0.2rem;
                color: var(--text);
                font-size: 1rem;
                font-weight: 800;
            }
            .chat-subtitle {
                margin-top: 0.2rem;
                color: var(--muted);
                font-size: 0.8rem;
                line-height: 1.4;
            }
            .chat-close {
                width: 2.05rem;
                height: 2.05rem;
                border: 1px solid var(--border);
                border-radius: 999px;
                background: var(--panel-alt);
                color: var(--text);
                cursor: pointer;
            }
            .chat-pills, .chat-suggestions {
                display: flex;
                flex-wrap: wrap;
                gap: 0.35rem;
                padding: 0.75rem 1rem 0;
            }
            .chat-pill, .chat-suggestion {
                border: 1px solid color-mix(in srgb, var(--border) 84%, transparent);
                border-radius: 999px;
                background: var(--panel-alt);
                color: var(--text);
                font-size: 0.72rem;
                font-weight: 700;
                padding: 0.38rem 0.68rem;
            }
            .chat-suggestion {
                cursor: pointer;
                transition: transform 0.18s ease, border-color 0.18s ease;
            }
            .chat-suggestion:hover {
                transform: translateY(-1px);
                border-color: rgba(56, 189, 248, 0.42);
            }
            .chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 0.8rem 1rem 0.9rem;
                display: flex;
                flex-direction: column;
                gap: 0.65rem;
            }
            .row {
                display: flex;
                align-items: flex-end;
                gap: 0.5rem;
            }
            .row.user { flex-direction: row-reverse; }
            .avatar {
                width: 1.6rem;
                height: 1.6rem;
                border-radius: 999px;
                display: grid;
                place-items: center;
                color: #fff;
                font-size: 0.63rem;
                font-weight: 800;
                flex: 0 0 auto;
            }
            .avatar.bot { background: linear-gradient(135deg, var(--primary), var(--accent)); }
            .avatar.user { background: linear-gradient(135deg, var(--accent-2), var(--accent)); }
            .bubble {
                max-width: 82%;
                padding: 0.68rem 0.8rem;
                border-radius: 16px;
                border: 1px solid color-mix(in srgb, var(--border) 84%, transparent);
                white-space: pre-wrap;
                word-break: break-word;
                line-height: 1.45;
                font-size: 0.86rem;
            }
            .row.bot .bubble {
                background: var(--panel-alt);
                border-top-left-radius: 8px;
            }
            .row.user .bubble {
                background: linear-gradient(135deg, rgba(56, 189, 248, 0.18), rgba(20, 184, 166, 0.18));
                border-top-right-radius: 8px;
            }
            .chat-form {
                display: flex;
                gap: 0.5rem;
                padding: 0.85rem 1rem 1rem;
                border-top: 1px solid color-mix(in srgb, var(--border) 84%, transparent);
                background: var(--panel);
            }
            .chat-input {
                flex: 1;
                min-width: 0;
                border: 1px solid color-mix(in srgb, var(--border) 84%, transparent);
                border-radius: 14px;
                background: var(--panel-alt);
                color: var(--text);
                padding: 0.7rem 0.8rem;
                font: inherit;
                font-size: 0.86rem;
                outline: none;
            }
            .chat-send {
                border: 0;
                border-radius: 14px;
                padding: 0 0.95rem;
                min-width: 4.5rem;
                color: #fff;
                background: linear-gradient(135deg, var(--primary), var(--accent-2) 52%, var(--accent));
                font-weight: 800;
                cursor: pointer;
            }
            @media (max-width: 640px) {
                .chat-root { width: 100%; height: 100%; }
            }
            </style>
            <div class="chat-root">
                <button class="chat-fab" id="chat-fab" type="button" aria-label="Open assistant" title="Open assistant">💬</button>
                <div class="chat-shell" id="chat-shell">
                    <div class="chat-panel">
                        <div class="chat-header">
                            <div>
                                <div class="chat-kicker">Assistant</div>
                                <div class="chat-title">$title</div>
                                <div class="chat-subtitle">Quick answers for the project, Python basics, and syntax help.</div>
                            </div>
                            <button class="chat-close" id="chat-close" type="button" aria-label="Close assistant" title="Close assistant">×</button>
                        </div>
                        <div class="chat-pills" id="chat-pills"></div>
                        <div class="chat-suggestions">
                            <button class="chat-suggestion" type="button" data-suggestion="What does this project do?">Project help</button>
                            <button class="chat-suggestion" type="button" data-suggestion="Explain Python list syntax.">Python basics</button>
                            <button class="chat-suggestion" type="button" data-suggestion="Show function syntax in Python.">Syntax help</button>
                        </div>
                        <div class="chat-messages" id="chat-messages"></div>
                        <form class="chat-form" id="chat-form">
                            <input class="chat-input" id="chat-input" type="text" placeholder="Ask about the project or Python..." autocomplete="off" />
                            <button class="chat-send" type="submit">Send</button>
                        </form>
                    </div>
                </div>
            </div>
            <script id="chat-context-data" type="application/json">$context_json</script>
            <script>
            (function () {
                const context = JSON.parse(document.getElementById("chat-context-data").textContent);
                const storageKey = "$storage_key";
                const shell = document.getElementById("chat-shell");
                const fab = document.getElementById("chat-fab");
                const closeButton = document.getElementById("chat-close");
                const form = document.getElementById("chat-form");
                const input = document.getElementById("chat-input");
                const messages = document.getElementById("chat-messages");
                const pills = document.getElementById("chat-pills");
                const suggestions = Array.from(document.querySelectorAll("[data-suggestion]"));

                function loadState() {
                    try {
                        const raw = window.localStorage.getItem(storageKey);
                        if (!raw) { return { open: false, messages: [] }; }
                        const parsed = JSON.parse(raw);
                        return { open: Boolean(parsed.open), messages: Array.isArray(parsed.messages) ? parsed.messages : [] };
                    } catch (error) {
                        return { open: false, messages: [] };
                    }
                }

                let state = loadState();
                if (!Array.isArray(state.messages)) { state.messages = []; }

                function saveState() {
                    try { window.localStorage.setItem(storageKey, JSON.stringify(state)); } catch (error) {}
                }

                function summaryLine() {
                    if (context.analysis_ready) {
                        return "Workspace stats: " + context.functions + " functions, " + context.docstrings + " docstrings, and " + context.violations + " violations.";
                    }
                    return "Run analysis after selecting a file or folder to unlock live project stats.";
                }

                function greeting() {
                    const sourceLine = context.target_name !== "No source selected" ? "Current source: " + context.target_name + "." : "No source selected yet.";
                    return "Hi, I’m your workspace assistant. Ask me about the project, Python syntax, or docstrings. " + sourceLine + " " + summaryLine();
                }

                function replyFor(text) {
                    const query = String(text || "").toLowerCase();
                    if (query.includes("project") || query.includes("app") || query.includes("what does this do") || query.includes("what can you do")) {
                        return "This Streamlit app analyzes Python files, extracts functions, reviews docstrings, checks quality issues, and helps you export or fix supported results. " + summaryLine();
                    }
                    if (query.includes("docstring")) { return "A docstring is a short description placed at the top of a function, class, or module. The Docstring Review page lets you generate and insert them quickly."; }
                    if (query.includes("class")) { return "A class groups data and behavior. Example:\n\nclass Demo:\n    def __init__(self, value):\n        self.value = value"; }
                    if (query.includes("list")) { return "A list is ordered and mutable. Example:\n\nitems = [1, 2, 3]\nitems.append(4)"; }
                    if (query.includes("dict")) { return "A dictionary stores key-value pairs. Example:\n\nuser = {\"name\": \"Ava\", \"role\": \"admin\"}"; }
                    if (query.includes("loop")) { return "A for-loop repeats over items. Example:\n\nfor item in items:\n    print(item)"; }
                    if (query.includes("syntax") || query.includes("function") || query.includes("python")) { return "A basic Python function looks like this:\n\ndef greet(name):\n    return f\"Hello, {name}\"\n\nIf you want, I can also explain loops, dictionaries, classes, or docstrings."; }
                    if (query.includes("error") || query.includes("traceback") || query.includes("bug")) { return "Share the error message or code snippet and I’ll help narrow it down."; }
                    return "I can help with the project, Python basics, or syntax examples. Try: “What does this project do?”, “Explain a list”, or “Show class syntax.”";
                }

                function renderPills() {
                    const items = [];
                    if (context.target_name) { items.push("Source: " + context.target_name); }
                    items.push(context.analysis_ready ? "Analysis ready" : "Ready to analyze");
                    if (context.analysis_ready) {
                        items.push(context.functions + " functions");
                        items.push(context.docstrings + " docstrings");
                    }
                    pills.innerHTML = "";
                    items.forEach((label) => {
                        const pill = document.createElement("span");
                        pill.className = "chat-pill";
                        pill.textContent = label;
                        pills.appendChild(pill);
                    });
                }

                function renderMessages() {
                    messages.innerHTML = "";
                    const items = state.messages.length ? state.messages : [{ role: "bot", text: greeting() }];
                    items.forEach((entry) => {
                        const row = document.createElement("div");
                        row.className = "row " + (entry.role === "user" ? "user" : "bot");
                        const avatar = document.createElement("div");
                        avatar.className = "avatar " + (entry.role === "user" ? "user" : "bot");
                        avatar.textContent = entry.role === "user" ? "You" : "AI";
                        const bubble = document.createElement("div");
                        bubble.className = "bubble";
                        bubble.textContent = entry.text;
                        row.appendChild(avatar);
                        row.appendChild(bubble);
                        messages.appendChild(row);
                    });
                    if (!state.messages.length) { saveState(); }
                    messages.scrollTop = messages.scrollHeight;
                }

                function setOpen(nextOpen) {
                    state.open = nextOpen;
                    saveState();
                    shell.classList.toggle("open", state.open);
                    fab.setAttribute("aria-expanded", String(state.open));
                    if (state.open) { setTimeout(() => input.focus({ preventScroll: true }), 0); }
                }

                fab.addEventListener("click", () => setOpen(true));
                closeButton.addEventListener("click", () => setOpen(false));
                form.addEventListener("submit", (event) => {
                    event.preventDefault();
                    const value = input.value.trim();
                    if (!value) { return; }
                    state.messages.push({ role: "user", text: value });
                    state.messages.push({ role: "bot", text: replyFor(value) });
                    input.value = "";
                    saveState();
                    renderMessages();
                    setOpen(true);
                });
                suggestions.forEach((button) => {
                    button.addEventListener("click", () => {
                        input.value = button.getAttribute("data-suggestion") || "";
                        input.focus({ preventScroll: true });
                    });
                });
                window.addEventListener("keydown", (event) => { if (event.key === "Escape") { setOpen(false); } });

                renderPills();
                if (!state.messages.length) { state.messages.push({ role: "bot", text: greeting() }); saveState(); }
                renderMessages();
                setOpen(Boolean(state.open));

                function sizeFrame() {
                    try {
                        const frame = window.frameElement;
                        if (!frame) { return; }
                        let vw = window.innerWidth;
                        let vh = window.innerHeight;
                        try { vw = window.parent.innerWidth; vh = window.parent.innerHeight; } catch (error) {}
                        frame.style.position = "fixed";
                        frame.style.right = "1rem";
                        frame.style.bottom = "1rem";
                        frame.style.width = Math.max(300, Math.min(380, vw - 16)) + "px";
                        frame.style.height = Math.max(360, Math.min(560, vh - 16)) + "px";
                        frame.style.maxWidth = "calc(100vw - 1rem)";
                        frame.style.maxHeight = "calc(100vh - 1rem)";
                        frame.style.border = "0";
                        frame.style.zIndex = "9999";
                        frame.style.borderRadius = "24px";
                        frame.style.background = "transparent";
                        frame.style.boxShadow = "0 28px 60px rgba(2, 6, 23, 0.28)";
                    } catch (error) {}
                }

                sizeFrame();
                window.addEventListener("resize", sizeFrame);
            })();
            </script>
            """
        )
    )

    return template.substitute(
        bg=theme["bg"],
        panel=theme["panel"],
        panel_alt=theme["panel_alt"],
        border=theme["border"],
        text=theme["text"],
        muted=theme["muted"],
        primary=theme["primary"],
        accent=theme["accent"],
        accent_2=theme["accent_2"],
        shadow=theme["shadow"],
        context_json=context_json,
        storage_key=CHATBOT_STORAGE_KEY,
        title=title,
    )


def render_chatbot_assistant(df: pd.DataFrame) -> None:
    components.html(build_chatbot_html(df), height=1, scrolling=False)


def render_footer(df: pd.DataFrame) -> None:
    target_name = os.path.basename(st.session_state.file_path) if st.session_state.file_path else "No source selected"
    status_label = "Analysis ready" if st.session_state.analysis_done else "Waiting for source"
    docstring_label = f"{get_docstring_percentage(df):.0f}%" if not df.empty else "0%"
    st.markdown(
        f"""
        <div class="workspace-footer">
            <strong>{html.escape(APP_TITLE)}</strong> {html.escape(APP_FOOTER_COPY)}<br />
            Source: {html.escape(target_name)} &nbsp;•&nbsp; Status: {html.escape(status_label)} &nbsp;•&nbsp; Docstrings: {html.escape(docstring_label)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_test_results(report: Dict[str, object]) -> None:
    summary = report.get("summary", {})
    total_tests = summary.get("total", 0)
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)

    metric1, metric2, metric3 = st.columns(3)
    metric1.metric("Total Tests", total_tests)
    metric2.metric("Passed", passed)
    metric3.metric("Failed", failed)

    file_results = {}
    for test in report.get("tests", []):
        file_name = test["nodeid"].split("::")[0]
        if file_name not in file_results:
            file_results[file_name] = {"passed": 0, "failed": 0}
        if test.get("outcome") == "passed":
            file_results[file_name]["passed"] += 1
        else:
            file_results[file_name]["failed"] += 1

    if not file_results:
        return

    results_df = pd.DataFrame(
        [
            {"File": file_name, "Passed": values["passed"], "Failed": values["failed"]}
            for file_name, values in file_results.items()
        ]
    )

    chart = go.Figure()
    chart.add_trace(go.Bar(x=results_df["File"], y=results_df["Passed"], name="Passed", marker_color="#22c55e"))
    chart.add_trace(go.Bar(x=results_df["File"], y=results_df["Failed"], name="Failed", marker_color="#f43f5e"))
    chart.update_layout(barmode="group")
    apply_chart_layout(chart, "Test Results by File", "File", "Tests", tickangle=-25)
    st.plotly_chart(chart, use_container_width=True)

    for _, row in results_df.iterrows():
        total = int(row["Passed"] + row["Failed"])
        status_color = "#0f766e" if int(row["Failed"]) == 0 else "#9f1239"
        st.markdown(
            f"""
            <div style="background:{status_color};padding:0.9rem 1rem;border-radius:16px;color:white;margin-bottom:0.7rem;display:flex;justify-content:space-between;">
                <span>{html.escape(str(row['File']))}</span>
                <span>{int(row['Passed'])}/{total} passed</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_tests_panel() -> None:
    os.makedirs("storage", exist_ok=True)
    report_path = "storage/test_report.json"
    latest_run = None

    st.caption("This action runs `pytest` only. It does not refresh analysis or change source files.")
    if st.button("🧪 Run Tests", type="primary", use_container_width=True, help="Run the project test suite and generate a fresh report."):
        with st.spinner("Running tests..."):
            latest_run = subprocess.run(
                ["pytest", "--json-report", "--json-report-file=storage/test_report.json"],
                capture_output=True,
                text=True,
            )
        set_feedback("Tests completed.", "success" if latest_run.returncode in (0, 1) else "error")

    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as file:
            report = json.load(file)
        render_test_results(report)
    else:
        st.info("Run the suite to generate a test report.")

    if latest_run and (latest_run.stdout or latest_run.stderr):
        with st.expander("Latest pytest output"):
            if latest_run.stdout:
                st.code(latest_run.stdout, language="bash")
            if latest_run.stderr:
                st.code(latest_run.stderr, language="bash")


def render_export_panel(df: pd.DataFrame) -> None:
    os.makedirs("storage", exist_ok=True)
    csv_path = os.path.join("storage", "analysis_report.csv")
    json_path = os.path.join("storage", "analysis_report.json")
    csv_data = df.to_csv(index=False)
    json_data = df.to_json(orient="records", indent=2)

    with open(csv_path, "w", encoding="utf-8") as file:
        file.write(csv_data)
    with open(json_path, "w", encoding="utf-8") as file:
        file.write(json_data)

    st.success("Latest analysis was saved to the storage folder.")
    download_col1, download_col2 = st.columns(2)
    with download_col1:
        st.download_button("⬇ Download CSV", csv_data, "analysis_report.csv", "text/csv", use_container_width=True, help="Download the analysis as CSV.")
    with download_col2:
        st.download_button("⬇ Download JSON", json_data, "analysis_report.json", "application/json", use_container_width=True, help="Download the analysis as JSON.")


def render_dashboard(df: pd.DataFrame) -> None:
    render_section_header(
        "Dashboard",
        "Filter, search, test, and export from one place.",
        "Operations",
    )
    dashboard_panel = render_button_selector(
        [
            ("filters", "Filters"),
            ("search", "Search"),
            ("tests", "Tests"),
            ("export", "Export"),
            ("help", "Help"),
        ],
        "dashboard_panel",
        "dashboard_panel_selector",
    )

    if dashboard_panel == "filters":
        if df.empty:
            st.warning("No function data available. Run analysis on Python files with functions first.")
            return
        render_feature_panel(
            "Filters",
            "Refine the visible function set",
            "Filter by complexity, docstrings, and file.",
            soft=True,
        )
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        with filter_col1:
            max_complexity = st.slider("Maximum Complexity", 0, int(df["Complexity"].max()), int(df["Complexity"].max()), help="Filter out functions above this complexity score.")
        with filter_col2:
            doc_filter = st.selectbox("Docstring Status", ["All", "Present", "Missing"], help="Limit results by docstring coverage.")
        with filter_col3:
            selected_file = st.selectbox("File", ["All"] + sorted(df["File"].unique().tolist()), help="Focus on one analyzed file.")

        filtered_df = df[df["Complexity"] <= max_complexity].copy()
        if doc_filter == "Present":
            filtered_df = filtered_df[filtered_df["Docstring"] == DOC_PRESENT]
        elif doc_filter == "Missing":
            filtered_df = filtered_df[filtered_df["Docstring"] == DOC_MISSING]
        if selected_file != "All":
            filtered_df = filtered_df[filtered_df["File"] == selected_file]

        filtered_df = clean_dataframe_for_display(filtered_df.drop(columns=["Violations"]))
        summary_col1, summary_col2, summary_col3 = st.columns(3)
        with summary_col1:
            render_info_card("Matches", str(len(filtered_df)), "Functions matching the active filter rules.")
        with summary_col2:
            render_info_card("Scope", doc_filter, "Current documentation filter applied to the dataset.")
        with summary_col3:
            render_info_card("File Focus", selected_file, "Current file scope for the filtered results.")
        render_data_table(
            "Filtered Function Results",
            "Clean filtered results.",
            filtered_df,
            max_rows=10,
        )

    elif dashboard_panel == "search":
        if df.empty:
            st.warning("No function data available to search.")
            return
        render_feature_panel(
            "Search",
            "Locate functions instantly",
            "Search by function name.",
            soft=True,
        )
        query = st.text_input("Search Function Name", placeholder="Type a function name...", help="Search analyzed functions by name.")
        if query:
            results = clean_dataframe_for_display(df[df["Function"].str.contains(query, case=False, na=False)].drop(columns=["Violations"]))
            result_col1, result_col2 = st.columns(2)
            with result_col1:
                render_info_card("Results", str(len(results)), "Functions matched by the current search query.")
            with result_col2:
                render_info_card("Query", query, "Active keyword used to scan analyzed functions.")
            render_data_table(
                "Search Results",
                "Matching functions in the current target.",
                results,
                max_rows=10,
            )
        else:
            st.info("Search across analyzed functions by name.")

    elif dashboard_panel == "tests":
        render_feature_panel(
            "Tests",
            "Run validation without leaving the workspace",
            "Run pytest and review the latest report.",
            soft=True,
        )
        render_tests_panel()

    elif dashboard_panel == "export":
        render_feature_panel(
            "Export",
            "Save sharable analysis snapshots",
            "Download the current analysis as CSV or JSON.",
            soft=True,
        )
        render_export_panel(df)

    elif dashboard_panel == "help":
        render_dashboard_help()


def render_overview(df: pd.DataFrame) -> None:
    if df.empty:
        render_section_header(
            "Overview",
            "Analysis completed, but there are no function-level records to summarize yet.",
            "Summary",
        )
        st.info("No function data available.")
        return

    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-kicker">AI Python Code Studio</div>
            <div class="hero-title">{APP_TITLE}</div>
            <div class="hero-copy">Analyze, document, test, and improve Python code from one polished control center.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_section_header(
        "Overview",
        "Project health, risk, and documentation at a glance.",
        "Summary",
    )
    summary_df = clean_dataframe_for_display(build_file_summary(df))
    target_name = os.path.basename(st.session_state.file_path) if st.session_state.file_path else "No source selected"
    render_workspace_snapshot(df, subtitle=f"Workspace snapshot for {target_name}")

    highlight_col1, highlight_col2 = st.columns([1.1, 0.9])
    with highlight_col1:
        render_feature_panel(
            "Current Target",
            target_name,
            "Active analysis source.",
            accent=get_theme_tokens()["primary"],
        )
    with highlight_col2:
        review_target = df.sort_values(by=["Violations", "Complexity"], ascending=[False, False]).head(1)
        focus_name = review_target.iloc[0]["Function"] if not review_target.empty else "No hotspot detected"
        render_feature_panel(
            "Priority Review",
            focus_name,
            "Best place to start cleanup.",
            accent=get_theme_tokens()["warning"],
        )

    insight1, insight2, insight3 = st.columns(3)
    with insight1:
        render_info_card("Coverage", f"{get_docstring_percentage(df):.0f}%", "Functions that already contain docstrings.")
    with insight2:
        render_info_card("Files", str(summary_df["File"].nunique() if not summary_df.empty else 0), "Python files included in the current target.")
    with insight3:
        hotspot_row = df.sort_values(by=["Violations", "Complexity"], ascending=[False, False]).head(1)
        hotspot_name = hotspot_row.iloc[0]["Function"] if not hotspot_row.empty else "None"
        render_info_card("Hotspot", hotspot_name, "Highest-priority function based on violations and complexity.")

    detail_col1, detail_col2 = st.columns([1.15, 1])
    with detail_col1:
        render_feature_panel(
            "File Summary",
            "Per-file health snapshot",
            "Key file metrics side by side.",
            soft=True,
        )
        st.dataframe(
            summary_df,
            use_container_width=True,
            height=dataframe_height(summary_df, max_rows=9),
            hide_index=True,
        )
    with detail_col2:
        priority_df = clean_dataframe_for_display(
            df.sort_values(by=["Violations", "Complexity"], ascending=[False, False]).head(10)[
                ["File", "Function", "Complexity", "Violations", "Docstring"]
            ]
        )
        render_feature_panel(
            "Priority Queue",
            "Highest-risk functions first",
            "Focus on the riskiest functions first.",
            soft=True,
        )
        st.dataframe(
            priority_df,
            use_container_width=True,
            height=dataframe_height(priority_df, max_rows=10),
            hide_index=True,
        )


def render_function_analysis(df: pd.DataFrame) -> None:
    if df.empty:
        render_section_header(
            "Function Analysis",
            "No function-level records are available for the current analysis.",
            "Inspection",
        )
        st.info("No functions found to display.")
        return

    render_section_header(
        "Function Analysis",
        "Inspect the analyzed function list in table or JSON.",
        "Inspection",
    )
    df_display = df.drop(columns=["Violations"])
    render_feature_panel(
        "Function Views",
        "Switch between table and JSON",
        "Same data, two clean formats.",
        accent=get_theme_tokens()["accent_2"],
    )
    function_analysis_panel = render_button_selector(
        [("table", "Table View"), ("json", "JSON View")],
        "function_analysis_panel",
        "function_analysis_panel_selector",
    )

    if function_analysis_panel == "table":
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            selected_file = st.selectbox("File Filter", ["All"] + sorted(df_display["File"].unique().tolist()), help="Limit the table to a specific file.")
        with filter_col2:
            doc_filter = st.selectbox("Docstring Filter", ["All", DOC_PRESENT, DOC_MISSING], help="Filter rows by docstring status.")
        filtered_df = df_display.copy()
        if selected_file != "All":
            filtered_df = filtered_df[filtered_df["File"] == selected_file]
        if doc_filter != "All":
            filtered_df = filtered_df[filtered_df["Docstring"] == doc_filter]
        table_col1, table_col2, table_col3 = st.columns(3)
        with table_col1:
            render_info_card("Rows", str(len(filtered_df)), "Functions visible in the current filtered table.")
        with table_col2:
            render_info_card("File Scope", selected_file, "Current file filter applied to the table view.")
        with table_col3:
            render_info_card("Docstrings", doc_filter, "Current documentation filter applied to the table view.")
        render_data_table(
            "Function Inventory",
            "Clean function table.",
            filtered_df,
            max_rows=12,
            style_docstring_col=True,
        )

    else:
        render_json_panel(
            "Function Analysis JSON",
            "Formatted JSON for the current function analysis.",
            df_display.to_dict(orient="records"),
            "function_analysis.json",
        )


def render_docstring_review(df: pd.DataFrame) -> None:
    if df.empty:
        render_section_header(
            "Docstring Review",
            "Run analysis on a Python file that contains functions before opening the docstring workspace.",
            "Documentation",
        )
        st.warning("No function data available. Run analysis first.")
        return

    render_section_header(
        "Docstring Review",
        "Review and update docstrings.",
        "Documentation",
    )
    render_feature_panel(
        "Style",
        "Choose a docstring standard",
        "Switch between Google, NumPy, and reST without changing the review flow.",
        accent=get_theme_tokens()["primary"],
        soft=True,
    )
    current_style = render_button_selector(
        [(style, style) for style in DOC_STYLES],
        "doc_style",
        "doc_style_selector",
    )

    if st.session_state.last_style != current_style:
        st.session_state.doc_cache = {}
        st.session_state.last_style = current_style
    st.session_state.doc_style = current_style

    file_groups = df.groupby("File")
    picker_col1, picker_col2 = st.columns([1, 1.3])
    theme = get_theme_tokens()
    with picker_col1:
        selected_file = st.selectbox("Select File", list(file_groups.groups.keys()), help="Pick the file you want to review.")
        file_df = file_groups.get_group(selected_file)
        missing_count = int(file_df["Docstring"].eq(DOC_MISSING).sum())
        st.markdown(
            f"""
            <div class="panel-card" style="border-color:{theme['primary']}66;border-left:4px solid {theme['primary']};background:linear-gradient(180deg, rgba(103,232,249,0.08), rgba(15,23,42,0.02));">
                <div class="mini-label">File</div>
                <div style="font-size:1.15rem;font-weight:800;color:var(--text);margin-top:0.35rem;">{html.escape(selected_file)}</div>
                <div class="soft-copy">Functions: {len(file_df)} • Missing docstrings: {missing_count}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with picker_col2:
        selected_function = st.selectbox("Select Function", file_df["Function"].tolist(), help="Choose the function to inspect or rewrite.")
        function_row = file_df[file_df["Function"] == selected_function].iloc[0]
        documented = function_row["Docstring"] == DOC_PRESENT
        st.markdown(
            f"""
            <div class="panel-card" style="border-color:{theme['accent']}66;border-left:4px solid {theme['accent']};background:linear-gradient(180deg, rgba(20,184,166,0.08), rgba(15,23,42,0.02));">
                <div class="mini-label">Function</div>
                <div style="font-size:1.15rem;font-weight:800;color:var(--text);">{html.escape(selected_function)}</div>
                <div class="soft-copy">Status: {"Documented" if documented else "Missing"} • Style: {html.escape(current_style)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    file_path = resolve_selected_file_path(selected_file)
    if not file_path:
        st.error("Unable to resolve the selected file.")
        return

    with open(file_path, "r", encoding="utf-8") as file:
        source_code = file.read()
    try:
        tree = ast.parse(source_code)
    except SyntaxError as error:
        st.error(f"Unable to parse the selected file: {error}")
        return
    node = get_function_node(tree, selected_function)
    current_doc = ast.get_docstring(node) if node else None
    try:
        function_code = ast.get_source_segment(source_code, node) or ""
    except Exception:
        function_code = ""

    cache_key = f"{selected_file}_{selected_function}_{current_style}"
    if cache_key not in st.session_state.doc_cache:
        with st.spinner("Generating docstring..."):
            st.session_state.doc_cache[cache_key] = generate_docstring(function_code, current_style)
    generated_doc = st.session_state.doc_cache[cache_key]

    doc_review_panel = render_button_selector(
        [("compare", "Before / After"), ("source", "Function Source")],
        "doc_review_panel",
        "doc_review_panel_selector",
    )

    if doc_review_panel == "compare":
        render_function_change_preview(function_code, generated_doc, current_doc, current_style)
    else:
        st.code(function_code, language="python")

    action_col1, action_col2 = st.columns(2)
    with action_col1:
        if st.button("💾 Insert / Update Docstring", use_container_width=True, type="primary", help="Write the generated docstring back into the selected function."):
            clean_code = remove_existing_docstring(function_code)
            final_doc = st.session_state.doc_cache.get(cache_key) or generate_docstring(clean_code, current_style)
            new_function = insert_docstring(clean_code, final_doc)
            update_function_in_file(file_path, selected_function, new_function)
            run_full_analysis()
            set_feedback(f"Docstring updated for {selected_function}.", "success")
            st.rerun()

    with action_col2:
        if st.button("🚀 Update All Functions", use_container_width=True, help="Generate and insert docstrings for every function in the selected file."):
            df_file = df[df["File"] == selected_file]
            progress = st.progress(0)
            for index, function_name in enumerate(df_file["Function"].tolist(), start=1):
                with open(file_path, "r", encoding="utf-8") as file:
                    src = file.read()
                tree = ast.parse(src)
                node = get_function_node(tree, function_name)
                if node:
                    function_src = ast.get_source_segment(src, node) or ""
                    cleaned = remove_existing_docstring(function_src)
                    bulk_cache_key = f"{selected_file}_{function_name}_{current_style}"
                    if bulk_cache_key not in st.session_state.doc_cache:
                        st.session_state.doc_cache[bulk_cache_key] = generate_docstring(cleaned, current_style)
                    updated_doc = st.session_state.doc_cache[bulk_cache_key]
                    updated_function = insert_docstring(cleaned, updated_doc)
                    update_function_in_file(file_path, function_name, updated_function)
                progress.progress(index / len(df_file))
            run_full_analysis()
            st.balloons()
            set_feedback(f"Docstrings updated for functions in {selected_file}.", "success")
            st.rerun()


def render_code_quality_dashboard(df: pd.DataFrame) -> None:
    render_section_header(
        "Code Quality",
        "Review issues, fix supported errors, and inspect quality charts.",
        "Quality",
    )
    render_feature_panel(
        "Quality Center",
        "Issue review and visual insights",
        "Switch between fixes and chart-driven review.",
        accent=get_theme_tokens()["warning"],
    )
    quality_panel = render_button_selector(
        [("issues", "Errors & Fix Code"), ("charts", "Graph Insights")],
        "quality_panel",
        "quality_panel_selector",
    )

    if quality_panel == "issues":
        if st.session_state.project_errors:
            grouped = {}
            for file_name, error in st.session_state.project_errors:
                grouped.setdefault(file_name, []).append(error)

            issue_count = len(st.session_state.project_errors)
            file_count = len(grouped)
            quality_col1, quality_col2, quality_col3 = st.columns(3)
            with quality_col1:
                render_info_card("Issues", str(issue_count), "Total project issues currently detected by the analysis.")
            with quality_col2:
                render_info_card("Files Affected", str(file_count), "Files that currently contain tracked issues.")
            with quality_col3:
                most_affected = max(grouped.items(), key=lambda item: len(item[1]))[0]
                render_info_card("Top File", most_affected, "File with the highest number of grouped issues.")

            render_feature_panel(
                "Fix Workflow",
                "Apply supported fixes with one action",
                "Apply supported fixes and refresh analysis.",
                accent=get_theme_tokens()["danger"],
                soft=True,
            )
            if st.button("🔥 Fix Errors", use_container_width=True, type="primary", help="Apply supported code fixes across the current project."):
                progress = st.progress(0)
                total_files = len(st.session_state.file_contents)
                for index, file_path in enumerate(st.session_state.file_contents, start=1):
                    original = st.session_state.file_contents[file_path]
                    _, fixed = fix_source_code(original, os.path.basename(file_path))
                    fixed = fix_docstrings(fixed)
                    with open(file_path, "w", encoding="utf-8") as file:
                        file.write(fixed)
                    progress.progress(index / total_files)
                run_full_analysis()
                st.balloons()
                set_feedback("Errors fixed and dashboard refreshed.", "success")
                st.rerun()

            for file_name, errors in grouped.items():
                with st.expander(f"{file_name} ({len(errors)} issues)"):
                    for error in errors:
                        st.markdown(f'<div class="issue-card">❌ {html.escape(error)}</div>', unsafe_allow_html=True)
        else:
            st.success("✨ No issues found.")

    else:
        if df.empty:
            st.info("No function-level chart data is available for the current analysis.")
            return
        chart_metrics = st.columns(4)
        chart_metrics[0].metric("Files", df["File"].nunique())
        chart_metrics[1].metric("Functions", len(df))
        chart_metrics[2].metric("Violations", int(df["Violations"].sum()))
        chart_metrics[3].metric("Docstrings", f"{get_docstring_percentage(df):.0f}%")
        render_feature_panel(
            "Graph Insights",
            "Understand where quality work matters most",
            "Charts for complexity, violations, coverage, file hotspots, and trend shape.",
            accent=get_theme_tokens()["accent"],
            soft=True,
        )
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            complexity_chart = px.bar(
                df,
                x="Function",
                y="Complexity",
                color="Complexity",
                color_continuous_scale=["#155e75", "#67e8f9"],
                text="Complexity",
            )
            complexity_chart.update_traces(textposition="outside")
            apply_chart_layout(complexity_chart, "Function Complexity", "Function", "Complexity", tickangle=-35)
            st.plotly_chart(complexity_chart, use_container_width=True)
        with chart_col2:
            violation_chart = px.bar(
                df,
                x="Function",
                y="Violations",
                color="Violations",
                color_continuous_scale=["#f59e0b", "#f43f5e"],
                text="Violations",
            )
            violation_chart.update_traces(textposition="outside")
            apply_chart_layout(violation_chart, "Function Violations", "Function", "Violations", tickangle=-35)
            st.plotly_chart(violation_chart, use_container_width=True)

        trend_df = df.sort_values(by=["Complexity", "Violations"], ascending=[False, False]).reset_index(drop=True)
        if not trend_df.empty:
            trend_df["Rank"] = trend_df.index + 1
            area_chart = px.area(
                trend_df,
                x="Rank",
                y="Violations",
                markers=True,
            )
            area_chart.update_traces(
                line=dict(color="#f59e0b", width=3),
                fillcolor="rgba(245,158,11,0.24)",
                hovertemplate="Rank %{x}<br>Violations %{y}<extra></extra>",
            )
            apply_chart_layout(area_chart, "Violation Trend Area", "Function Rank", "Violations", height=340)
            st.plotly_chart(area_chart, use_container_width=True)

        pie_col1, pie_col2 = st.columns(2)
        with pie_col1:
            coverage_df = pd.DataFrame(
                {
                    "Status": [DOC_PRESENT, DOC_MISSING],
                    "Count": [
                        int(df["Docstring"].eq(DOC_PRESENT).sum()),
                        int(df["Docstring"].eq(DOC_MISSING).sum()),
                    ],
                }
            )
            coverage_chart = px.pie(
                coverage_df,
                names="Status",
                values="Count",
                hole=0.5,
                color="Status",
                color_discrete_map={DOC_PRESENT: "#22c55e", DOC_MISSING: "#f43f5e"},
            )
            apply_chart_layout(coverage_chart, "Docstring Coverage", height=360)
            st.plotly_chart(coverage_chart, use_container_width=True)
        with pie_col2:
            violation_share = df.groupby("File", as_index=False)["Violations"].sum()
            file_chart = px.pie(
                violation_share,
                names="File",
                values="Violations",
                hole=0.5,
                color_discrete_sequence=CHART_SEQUENCE,
            )
            apply_chart_layout(file_chart, "Violation Share by File", height=360)
            st.plotly_chart(file_chart, use_container_width=True)


def main() -> None:
    initialize_session_state()
    inject_global_styles()
    render_background_layer()
    render_feedback()

    if st.session_state.analysis_done:
        df = build_analysis_dataframe()
    else:
        df = pd.DataFrame(columns=ANALYSIS_COLUMNS)

    selected_page = render_sidebar(df)
    render_action_bar()

    if not st.session_state.analysis_done:
        render_empty_state(has_source=bool(st.session_state.file_path))
    else:
        if selected_page == "overview":
            render_overview(df)
        elif selected_page == "dashboard":
            render_dashboard(df)
        elif selected_page == "functions":
            render_function_analysis(df)
        elif selected_page == "docstrings":
            render_docstring_review(df)
        elif selected_page == "quality":
            render_code_quality_dashboard(df)

    # Persistent UI chrome stays visible across every workspace state.
    render_footer(df)
    render_chatbot_assistant(df)


if __name__ == "__main__":
    main()