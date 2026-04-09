"""Map-first Streamlit app for the Manipal Location & Review Management System."""

from __future__ import annotations

from datetime import date
import hashlib
import html
import json
import os
import secrets
import time

import folium
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit_folium import st_folium

from db import init_db, reset_query_log
from queries import (
    active_but_not_top_rated,
    add_category,
    add_favorite,
    add_image,
    add_location,
    add_review,
    archive_delete_location_transaction,
    average_rating_per_location,
    best_per_category_correlated,
    common_favorites_and_reviewed,
    delete_location,
    delete_review,
    demo_savepoint_transaction,
    flag_low_rated_locations,
    get_category_activity_summary,
    get_categories,
    get_deleted_location_audit,
    get_images_uploaded_by_user,
    get_images_for_location,
    get_favorite_location_ids,
    get_location_details,
    get_location_spotlight_insights,
    get_location_status,
    get_locations,
    get_locations_added_by_user,
    get_reviews_by_user,
    get_review_logs,
    get_reviews_for_location,
    get_user_by_email,
    get_user_contribution_summary,
    location_rating_bands,
    locations_above_all_in_category,
    locations_union_high_activity,
    most_favorited_locations,
    most_reviewed_locations,
    parameterized_category_cursor,
    remove_favorite,
    register_user,
    search_locations_by_category,
    top_rated_locations,
    update_location,
    update_review,
    users_who_reviewed_all_categories,
    users_with_five_star_review,
    users_with_most_reviews,
)
from sample_data import insert_sample_data

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_images")
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.set_page_config(page_title="Manipal Atlas", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');

    :root {
        --bg:            #F4F5F2;
        --surface:       #FFFFFF;
        --surface-alt:   #F9FAF8;
        --border:        #E0E5DF;
        --border-strong: #C8D0C6;
        --text:          #16201A;
        --text-2:        #4A5750;
        --text-3:        #8A9590;
        --accent:        #1B6840;
        --accent-mid:    #2E8A5A;
        --accent-pale:   #EAF3EE;
        --accent-line:   #C6DDD0;
        --shadow-sm:     0 1px 3px rgba(0,0,0,0.07),0 1px 2px rgba(0,0,0,0.04);
        --shadow-md:     0 4px 12px rgba(0,0,0,0.08),0 2px 4px rgba(0,0,0,0.04);
        --r-sm:  6px;
        --r-md:  10px;
        --r-lg:  14px;
    }

    * { box-sizing: border-box; }

    .stApp {
        background: var(--bg);
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
        color: var(--text);
        font-size: 14px;
        line-height: 1.5;
        -webkit-font-smoothing: antialiased;
    }
    section.main > div.block-container,
    div[data-testid="stMainBlockContainer"],
    [data-testid="stMain"] > div,
    [data-testid="stMain"] > div > div,
    [data-testid="stMain"] .block-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
        padding-bottom: 2rem;
        max-width: 1480px;
    }
    #MainMenu, footer, header[data-testid="stHeader"], [data-testid="stAppHeader"] { display: none !important; }
    [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none; }
    [data-testid="stAppViewContainer"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    [data-testid="stAppViewContainer"] > .main {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    [data-testid="stAppViewContainer"] > .main > div {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    [data-testid="stAppViewContainer"] .main .block-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    [data-testid="stAppViewContainer"] [data-testid="stMain"] {
        padding-top: 0 !important;
        margin-top: -0.35rem !important;
    }

    /* ── Sidebar ─────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: var(--surface) !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebar"] > div { padding-top: 0.75rem; }

    /* ── Page Banner ─────────────────────────────────────── */
    .hero-banner {
        display: block;
        padding: 0.9rem 1.2rem;
        background: var(--surface);
        border: 1px solid var(--border);
        border-left: 3px solid var(--accent);
        border-radius: var(--r-md);
        margin-bottom: 1rem;
        box-shadow: var(--shadow-sm);
    }
    .panel-kicker, .app-kicker {
        font-size: 0.67rem;
        font-weight: 700;
        color: var(--accent);
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 0.2rem;
    }
    .hero-title, .panel-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: var(--text);
        margin: 0;
        letter-spacing: -0.01em;
        line-height: 1.3;
        font-family: 'Space Grotesk', sans-serif;
    }
    .hero-copy, .panel-copy, .muted-copy {
        font-size: 0.82rem;
        color: var(--text-2);
        margin: 0.3rem 0 0;
        line-height: 1.55;
    }
    .hero-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
        margin-top: 0.6rem;
    }
    .soft-chip {
        display: inline-flex;
        align-items: center;
        height: 22px;
        padding: 0 0.55rem;
        background: var(--accent-pale);
        border: 1px solid var(--accent-line);
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 600;
        color: var(--accent);
    }

    /* ── Metric Cards ────────────────────────────────────── */
    .metric-shell {
        background: var(--surface);
        border: 1px solid var(--border);
        border-top: 2px solid var(--accent);
        border-radius: var(--r-md);
        padding: 0.8rem 1rem;
        box-shadow: var(--shadow-sm);
        margin-bottom: 0.75rem;
    }
    .metric-label {
        font-size: 0.67rem;
        font-weight: 700;
        color: var(--text-3);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.25rem;
    }
    .metric-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--text);
        line-height: 1;
        margin: 0;
        letter-spacing: -0.02em;
        font-family: 'Inter', sans-serif;
    }
    .metric-detail {
        font-size: 0.78rem;
        color: var(--text-2);
        margin-top: 0.3rem;
    }

    /* ── Section headers ─────────────────────────────────── */
    .surface-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: var(--text);
        margin: 0;
        font-family: 'Space Grotesk', sans-serif;
    }
    .surface-copy {
        font-size: 0.8rem;
        color: var(--text-2);
        margin: 0.2rem 0 0;
        line-height: 1.5;
    }
    .panel-divider {
        height: 1px;
        border: none;
        background: var(--border);
        margin: 0.9rem 0;
    }
    .flat-section { margin-bottom: 0.9rem; }
    .surface-head { margin-bottom: 0.75rem; }
    .map-caption, .section-label {
        font-size: 0.78rem;
        color: var(--text-3);
        margin-bottom: 0.5rem;
    }

    /* ── Inspector / location detail ────────────────────── */
    .inspector-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: var(--text);
        margin: 0.1rem 0 0;
        line-height: 1.3;
        font-family: 'Space Grotesk', sans-serif;
    }
    .inspector-meta {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 0.5rem;
        margin-top: 0.75rem;
    }
    .meta-block {
        background: var(--surface-alt);
        border: 1px solid var(--border);
        border-radius: var(--r-sm);
        padding: 0.6rem 0.75rem;
    }
    .meta-label {
        font-size: 0.64rem;
        font-weight: 700;
        color: var(--text-3);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.2rem;
    }
    .meta-value {
        font-size: 0.84rem;
        font-weight: 600;
        color: var(--text);
        line-height: 1.4;
    }

    /* ── Empty states ────────────────────────────────────── */
    .empty-shell {
        background: var(--surface);
        border: 1px dashed var(--border-strong);
        border-radius: var(--r-md);
        padding: 1.25rem;
        text-align: center;
    }
    .empty-title {
        font-size: 0.92rem;
        font-weight: 600;
        color: var(--text);
        margin-bottom: 0.3rem;
    }
    .empty-copy {
        font-size: 0.82rem;
        color: var(--text-2);
        line-height: 1.5;
        margin-bottom: 0.75rem;
    }

    /* ── Review cards ────────────────────────────────────── */
    .review-shell {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--r-md);
        padding: 0.75rem 0.9rem;
        margin-bottom: 0.6rem;
        box-shadow: var(--shadow-sm);
    }
    .review-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.5rem;
        margin-bottom: 0.3rem;
    }
    .review-author { font-weight: 600; font-size: 0.86rem; color: var(--text); }
    .review-date   { font-size: 0.78rem; color: var(--text-3); }
    .review-comment { font-size: 0.84rem; color: var(--text-2); margin: 0.25rem 0 0; line-height: 1.5; }

    .spotlight-shell {
        border: 1px solid var(--accent-line);
        background: linear-gradient(165deg, #ffffff 0%, #f4fbf6 100%);
        border-radius: var(--r-md);
        box-shadow: var(--shadow-md);
        padding: 0.9rem 0.95rem;
        margin-bottom: 0.9rem;
    }

    .spotlight-topline {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 0.75rem;
        margin-bottom: 0.75rem;
    }
    .spotlight-badges {
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
        margin-top: 0.6rem;
    }
    .insight-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.55rem;
        margin: 0.8rem 0 0.2rem;
    }
    .insight-card {
        background: rgba(255,255,255,0.84);
        border: 1px solid var(--border);
        border-radius: var(--r-sm);
        padding: 0.65rem 0.7rem;
    }
    .insight-label {
        font-size: 0.64rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--text-3);
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .insight-value {
        font-size: 0.92rem;
        font-weight: 700;
        color: var(--text);
        line-height: 1.25;
    }
    .insight-note {
        font-size: 0.76rem;
        color: var(--text-2);
        margin-top: 0.2rem;
    }
    .insight-card-wide {
        grid-column: 1 / -1;
    }
    .inline-feedback {
        margin: 0.35rem 0 0.6rem;
        padding: 0.5rem 0.65rem;
        border-radius: var(--r-sm);
        border: 1px solid var(--border);
        font-size: 0.81rem;
        font-weight: 600;
    }
    .inline-feedback.success {
        background: #eaf6ee;
        border-color: #bfdcc8;
        color: #1d6a41;
    }
    .inline-feedback.error {
        background: #fbecec;
        border-color: #edc1c1;
        color: #8d1f1f;
    }

    .profile-shell {
        display: grid;
        grid-template-columns: 1.1fr 1.3fr;
        gap: 1rem;
        align-items: start;
    }
    .profile-stack {
        display: grid;
        gap: 0.8rem;
    }
    .profile-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--r-md);
        box-shadow: var(--shadow-sm);
        padding: 0.85rem 0.95rem;
    }
    .profile-card-title {
        font-size: 0.9rem;
        font-weight: 700;
        color: var(--text);
        margin: 0 0 0.35rem;
    }
    .profile-card-copy {
        font-size: 0.82rem;
        color: var(--text-2);
        margin: 0;
    }
    .gallery-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.65rem;
    }
    .gallery-placeholder {
        border: 1px dashed var(--border-strong);
        border-radius: var(--r-md);
        background: var(--surface-alt);
        min-height: 160px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--text-2);
        font-size: 0.82rem;
        padding: 0.8rem;
        text-align: center;
    }

    .auth-shell {
        display: grid;
        grid-template-columns: 1.05fr 0.95fr;
        gap: 1rem;
        align-items: stretch;
    }
    .auth-visual {
        min-height: 640px;
        border-radius: 22px;
        overflow: hidden;
        box-shadow: var(--shadow-md);
    }
    .auth-panel {
        background: rgba(255,255,255,0.92);
        border: 1px solid var(--border);
        border-radius: 22px;
        box-shadow: var(--shadow-md);
        padding: 1rem;
        backdrop-filter: blur(8px);
    }
    .auth-panel-inner {
        display: grid;
        gap: 0.75rem;
    }
    .auth-mini {
        font-size: 0.78rem;
        color: var(--text-2);
        margin: 0;
    }
    .transition-shell {
        background: linear-gradient(145deg, rgba(255,255,255,0.95), rgba(234,243,238,0.95));
        border: 1px solid var(--border);
        border-radius: 22px;
        box-shadow: var(--shadow-md);
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .preset-bar {
        display: grid;
        gap: 0.5rem;
    }

    .glow-shell {
        position: relative;
        overflow: hidden;
        border-radius: var(--r-md);
    }
    .glow-shell::before {
        content: "";
        position: absolute;
        inset: -60% auto auto -40%;
        width: 220px;
        height: 220px;
        border-radius: 999px;
        background: radial-gradient(circle, rgba(46, 138, 90, 0.2) 0%, rgba(46, 138, 90, 0) 65%);
        pointer-events: none;
        animation: driftGlow 9s ease-in-out infinite;
    }
    .fade-slide {
        animation: fadeSlide 450ms ease-out;
    }

    /* ── Auth pages ──────────────────────────────────────── */
    .auth-hero, .auth-title, .auth-copy { display: none; }
    .auth-panel {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--r-lg);
        padding: 1.25rem;
        box-shadow: var(--shadow-sm);
    }
    .auth-panel-title { font-size: 1rem; font-weight: 700; color: var(--text); margin: 0; }
    .auth-panel-copy  { font-size: 0.82rem; color: var(--text-2); margin: 0.35rem 0 0.9rem; }
    .auth-feature-list {
        padding-left: 1.1rem;
        color: var(--text-2);
        font-size: 0.84rem;
        line-height: 1.7;
        margin: 0.75rem 0 0;
    }
    .auth-feature-list li { margin-bottom: 0.3rem; }

    /* ── Sidebar text ────────────────────────────────────── */
    .nav-title {
        font-size: 0.67rem;
        font-weight: 700;
        color: var(--text-3);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin: 0 0 0.3rem;
    }
    .nav-copy { font-size: 0.82rem; color: var(--text-2); line-height: 1.5; margin-bottom: 0.9rem; }

    /* ── Tabs ────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        border-bottom: 1px solid var(--border);
        margin-bottom: 1rem;
        background: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        border-radius: 0;
        padding: 0.5rem 0.85rem;
        font-size: 0.84rem;
        font-weight: 500;
        color: var(--text-2);
        margin-bottom: -1px;
        font-family: 'Inter', sans-serif;
    }
    .stTabs [aria-selected="true"] {
        background: transparent !important;
        border-bottom: 2px solid var(--accent) !important;
        color: var(--text) !important;
        font-weight: 600;
    }

    /* ── Expanders ───────────────────────────────────────── */
    .stExpander {
        border: 1px solid var(--border) !important;
        border-radius: var(--r-md) !important;
        background: var(--surface) !important;
        box-shadow: none !important;
    }

    /* ── DataFrames ──────────────────────────────────────── */
    .stDataFrame, div[data-testid="stTable"] {
        border-radius: var(--r-md);
        overflow: hidden;
        border: 1px solid var(--border);
    }

    /* ── Map iframe ──────────────────────────────────────── */
    .element-container iframe {
        border-radius: var(--r-md) !important;
        border: 1px solid var(--border) !important;
        box-shadow: var(--shadow-md);
    }

    /* ── Buttons ─────────────────────────────────────────── */
    div[data-testid="stButton"] > button,
    div[data-testid="stFormSubmitButton"] > button {
        background: var(--surface);
        border: 1px solid var(--border-strong);
        border-radius: var(--r-sm);
        color: var(--text);
        font-family: 'Outfit', sans-serif;
        font-size: 0.84rem;
        font-weight: 600;
        min-height: 2.35rem;
        box-shadow: var(--shadow-sm);
        transition: background 0.15s, border-color 0.15s, transform 0.15s, box-shadow 0.15s;
        letter-spacing: 0;
    }
    div[data-testid="stButton"] > button:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {
        background: var(--surface-alt);
        border-color: var(--accent);
        transform: translateY(-1px);
        box-shadow: var(--shadow-md);
    }
    div[data-testid="stButton"] > button[kind="primary"],
    div[data-testid="stFormSubmitButton"] > button[kind="primary"] {
        background: var(--accent);
        color: #fff;
        border-color: var(--accent);
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover,
    div[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {
        background: var(--accent-mid);
        border-color: var(--accent-mid);
    }
    div[data-testid="stButton"] > button p,
    div[data-testid="stFormSubmitButton"] > button p { font-size: 0.84rem; }

    /* ── Form inputs ─────────────────────────────────────── */
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    div[data-baseweb="base-input"] > div,
    .stTextArea textarea,
    .stNumberInput input {
        border-radius: var(--r-sm) !important;
        border: 1px solid var(--border-strong) !important;
        background: var(--surface) !important;
        box-shadow: none !important;
        color: var(--text) !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 0.84rem !important;
    }
    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea,
    div[data-baseweb="input"] input,
    div[data-baseweb="base-input"] input,
    div[data-baseweb="select"] input,
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div,
    div[data-baseweb="select"] * {
        color: var(--text) !important;
        -webkit-text-fill-color: var(--text) !important;
        caret-color: var(--accent) !important;
        opacity: 1 !important;
        background: var(--surface) !important;
    }
    .stTextInput input::placeholder,
    .stNumberInput input::placeholder,
    .stTextArea textarea::placeholder,
    div[data-baseweb="input"] input::placeholder,
    div[data-baseweb="base-input"] input::placeholder,
    div[data-baseweb="select"] input::placeholder {
        color: var(--text-3) !important;
        opacity: 1 !important;
    }
    div[data-baseweb="select"] svg, .stNumberInput button svg { fill: var(--text-2) !important; }
    .stNumberInput button { background: transparent !important; border: 0 !important; box-shadow: none !important; }
    .stSelectbox div[data-baseweb="select"] > div,
    .stNumberInput div[data-baseweb="base-input"] > div,
    .stTextInput div[data-baseweb="input"] > div { min-height: 2.5rem; }

    label[data-testid="stWidgetLabel"] p,
    .stSelectbox label p,
    .stNumberInput label p,
    .stTextInput label p,
    .stTextArea label p,
    .stSlider label p {
        color: var(--text) !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        font-family: 'Outfit', sans-serif !important;
    }

    .main-title {
        margin: 0.18rem 0 0;
        font-size: 1.65rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: var(--text);
        font-family: 'Space Grotesk', sans-serif;
    }
    .title-support {
        margin: 0.35rem 0 0;
        color: var(--text-2);
        font-size: 0.86rem;
        max-width: 76ch;
    }
    .status-text {
        margin: 0.35rem 0 0;
        color: var(--text-2);
        font-size: 0.8rem;
    }

    @keyframes fadeSlide {
        from { opacity: 0; transform: translateY(6px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes driftGlow {
        0% { transform: translateX(0px) translateY(0px); }
        50% { transform: translateX(14px) translateY(8px); }
        100% { transform: translateX(0px) translateY(0px); }
    }
    @keyframes heroLift {
        from { opacity: 0; transform: translateY(10px) scale(0.99); }
        to { opacity: 1; transform: translateY(0) scale(1); }
    }

    /* ── Misc ────────────────────────────────────────────── */
    .stFileUploader {
        border-radius: var(--r-md);
        background: var(--surface);
        border: 1px dashed var(--border-strong);
        padding: 0.2rem;
    }
    .stAlert { border-radius: var(--r-md); }

    /* status-pill kept for compatibility */
    .status-pill {
        display: inline-flex;
        align-items: center;
        height: 22px;
        padding: 0 0.55rem;
        background: var(--accent-pale);
        border: 1px solid var(--accent-line);
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 600;
        color: var(--accent);
    }

    @media (max-width: 900px) {
        .hero-title { font-size: 1.05rem; }
        .inspector-meta { grid-template-columns: 1fr; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def esc(value: object, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    return html.escape(text)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str | None) -> bool:
    if not stored or "$" not in stored:
        return False
    salt, expected = stored.split("$", 1)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
    return digest.hex() == expected


def require_login(action_text: str) -> bool:
    if st.session_state.logged_in_user is None:
        st.warning(f"Please sign in to {action_text}.")
        st.session_state.current_page = "auth"
        st.rerun()
        return False
    return True


def safe_df(df: pd.DataFrame, message: str = "No records found.") -> None:
    if df.empty:
        st.info(message)
        return
    st.dataframe(df, width="stretch", hide_index=True)


def closeable_card_header(title: str, state_key: str) -> None:
    head_col, close_col = st.columns([12, 1])
    with head_col:
        st.markdown(f"#### {title}")
    with close_col:
        if st.button("Close", key=f"close_{state_key}"):
            st.session_state[state_key] = False
            st.rerun()


def render_section_header(title: str, *, kicker: str | None = None, description: str | None = None, state_key: str | None = None) -> None:
    if state_key:
        title_col, action_col = st.columns([12, 1])
    else:
        title_col, action_col = st.container(), None

    with title_col:
        if kicker:
            st.markdown(f'<div class="panel-kicker">{esc(kicker)}</div>', unsafe_allow_html=True)
        st.markdown(f'<p class="surface-title">{esc(title)}</p>', unsafe_allow_html=True)
        if description:
            st.markdown(f'<p class="surface-copy">{esc(description)}</p>', unsafe_allow_html=True)

    if action_col is not None:
        with action_col:
            if st.button("Close", key=f"close_{state_key}"):
                st.session_state[state_key] = False
                st.rerun()


def render_page_banner(title: str, description: str, *, kicker: str, chips: list[str] | None = None) -> None:
    chip_html = ""
    if chips:
        chip_html = '<div class="hero-meta">' + "".join(
            f'<span class="soft-chip">{esc(chip)}</span>' for chip in chips
        ) + "</div>"

    st.markdown(
        f"""
        <section class="hero-banner">
            <div class="panel-kicker">{esc(kicker)}</div>
            <h2 class="hero-title">{esc(title)}</h2>
            <p class="hero-copy">{esc(description)}</p>
            {chip_html}
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_react_hero(
        title: str,
        subtitle: str,
        chips: list[str],
        *,
        background_image: str | None = None,
        badge: str = "Map-first experience",
    height: int = 320,
) -> None:
        title_js = json.dumps(title)
        subtitle_js = json.dumps(subtitle)
        chips_js = json.dumps(chips)
        bg_js = json.dumps(background_image or "")
        badge_js = json.dumps(badge)
        components.html(
                f"""
                <div id="atlas-react-hero"></div>
                <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
                <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
                <script>
                    const e = React.createElement;
                    const chips = {chips_js};
                    const bg = {bg_js};
                    const badge = {badge_js};
                    function Hero() {{
                        const [imgLoaded, setImgLoaded] = React.useState(!bg);
                        React.useEffect(() => {{
                            if (!bg) {{
                                setImgLoaded(true);
                                return;
                            }}
                            const img = new Image();
                            img.onload = () => setImgLoaded(true);
                            img.onerror = () => setImgLoaded(true);
                            img.src = bg;
                        }}, []);

                        const style = {{
                            position: 'relative',
                            overflow: 'hidden',
                            borderRadius: '22px',
                            minHeight: '280px',
                            padding: '22px',
                            color: '#fff',
                            backgroundImage: (bg && imgLoaded)
                                ? 'linear-gradient(135deg, rgba(11,28,22,0.82), rgba(11,28,22,0.44)), url(' + bg + ')'
                                : 'linear-gradient(135deg, #143126 0%, #2d6448 100%)',
                            backgroundSize: 'cover',
                            backgroundPosition: 'center, center',
                            backgroundRepeat: 'no-repeat, no-repeat',
                            boxShadow: '0 18px 40px rgba(0,0,0,0.15)',
                            animation: 'heroLift 480ms ease-out'
                        }};
                        return e('section', {{ style }}, [
                            e('style', {{key: 'style'}}, '@keyframes heroLift {{ from {{ opacity: 0; transform: translateY(10px) scale(0.99); }} to {{ opacity: 1; transform: translateY(0) scale(1); }} }} @keyframes heroShimmer {{ 0% {{ transform: translateX(-120%); }} 100% {{ transform: translateX(120%); }} }}'),
                            (!imgLoaded && bg) ? e('div', {{
                                key: 'loader',
                                style: {{
                                    position: 'absolute',
                                    inset: 0,
                                    background: 'linear-gradient(120deg, rgba(255,255,255,0.06), rgba(255,255,255,0.18), rgba(255,255,255,0.06))',
                                    backdropFilter: 'blur(2px)',
                                    overflow: 'hidden'
                                }}
                            }}, [
                                e('div', {{
                                    key: 'bar',
                                    style: {{
                                        position: 'absolute',
                                        top: 0,
                                        left: '-35%',
                                        width: '35%',
                                        height: '100%',
                                        background: 'linear-gradient(90deg, rgba(255,255,255,0), rgba(255,255,255,0.32), rgba(255,255,255,0))',
                                        animation: 'heroShimmer 1.15s ease-in-out infinite'
                                    }}
                                }})
                            ]) : null,
                            e('div', {{key: 'badge', style: {{fontSize: '11px', fontWeight: 700, letterSpacing: '0.16em', textTransform: 'uppercase', color: '#d7f0e2'}}}}, badge),
                            e('h2', {{key: 'title', style: {{margin: '0.55rem 0 0.35rem', fontFamily: 'Space Grotesk, sans-serif', fontSize: '2rem', lineHeight: 1.05}}}}, {title_js}),
                            e('p', {{key: 'subtitle', style: {{margin: 0, maxWidth: '42rem', color: 'rgba(255,255,255,0.9)', fontSize: '0.96rem', lineHeight: 1.55}}}}, {subtitle_js}),
                            e('div', {{key: 'chips', style: {{display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '1rem'}}}},
                                chips.map((chip, index) => e('span', {{key: index, style: {{padding: '0.42rem 0.72rem', borderRadius: '999px', background: 'rgba(255,255,255,0.14)', border: '1px solid rgba(255,255,255,0.2)', fontSize: '0.76rem', fontWeight: 600}}}}, chip))
                            )
                        ]);
                    }}
                    ReactDOM.createRoot(document.getElementById('atlas-react-hero')).render(e(Hero));
                </script>
                """,
                height=height,
        )


def render_metric_row(metrics: list[tuple[str, str, str]]) -> None:
    cols = st.columns(len(metrics))
    for col, (label, value, detail) in zip(cols, metrics):
        with col:
            st.markdown(
                f"""
                <div class="metric-shell">
                    <div class="metric-label">{esc(label)}</div>
                    <p class="metric-value">{esc(value)}</p>
                    <p class="metric-detail">{esc(detail)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_data_panel(title: str, description: str, df: pd.DataFrame, message: str = "No records found.") -> None:
    st.markdown(
        f"""
        <div class="flat-section">
            <div class="surface-head">
                <div class="panel-kicker">Data panel</div>
                <div class="surface-title">{esc(title)}</div>
                <p class="surface-copy">{esc(description)}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    safe_df(df, message)


def render_map(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No locations match the current filter.")
        return

    valid = df.dropna(subset=["latitude", "longitude"])
    if valid.empty:
        st.info("Locations are available, but they are missing coordinates.")
        return

    center = [valid["latitude"].mean(), valid["longitude"].mean()]
    fmap = folium.Map(location=center, zoom_start=15, tiles="CartoDB positron", control_scale=True)

    selected_id = st.session_state.selected_location_id
    for _, row in valid.iterrows():
        row_id = int(row["location_id"])
        is_selected = selected_id == row_id
        tooltip = f"ID:{row_id} | {row['name']}"
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=10 if is_selected else 8,
            color="#103b2f" if is_selected else "#1f6a52",
            fill=True,
            fill_color="#103b2f" if is_selected else "#2e8a6b",
            fill_opacity=0.95,
            weight=3 if is_selected else 2,
            tooltip=tooltip,
            popup=row["name"],
        ).add_to(fmap)

    st.markdown('<div class="glow-shell fade-slide">', unsafe_allow_html=True)
    result = st_folium(fmap, width=None, height=760, key="map_view")
    st.markdown('</div>', unsafe_allow_html=True)

    last_clicked = result.get("last_clicked") if result else None
    if last_clicked:
        st.session_state.last_clicked_coords = (
            float(last_clicked["lat"]),
            float(last_clicked["lng"]),
        )

    marker_tip = result.get("last_object_clicked_tooltip") if result else None
    if marker_tip and marker_tip.startswith("ID:"):
        loc_id = marker_tip.split("|")[0].replace("ID:", "").strip()
        if loc_id.isdigit():
            st.session_state.selected_location_id = int(loc_id)
            st.session_state.show_manage_loc = False

    if st.session_state.last_clicked_coords:
        lat, lng = st.session_state.last_clicked_coords
        st.markdown(
            f'<p class="map-caption">Pinned coordinate: {lat:.6f}, {lng:.6f}</p>',
            unsafe_allow_html=True,
        )


def render_map_page(locations_df: pd.DataFrame, all_locations_df: pd.DataFrame, categories_df: pd.DataFrame) -> None:
    selected_name = "No selection"
    if st.session_state.selected_location_id:
        match = all_locations_df.loc[
            all_locations_df["location_id"] == int(st.session_state.selected_location_id), "name"
        ]
        if not match.empty:
            selected_name = str(match.iloc[0])

    current_filter = "All categories"
    if st.session_state.selected_category_id is not None:
        match = categories_df.loc[
            categories_df["category_id"] == int(st.session_state.selected_category_id), "category_name"
        ]
        if not match.empty:
            current_filter = str(match.iloc[0])

    preset_label = st.session_state.get("selected_preset", "All places")
    show_welcome_transition = bool(st.session_state.get("just_signed_in"))

    title = (
        f"Welcome back, {esc(st.session_state.logged_in_user['name'])}"
        if show_welcome_transition
        else "Discover Manipal, one place at a time"
    )
    subtitle = (
        "Your map is ready. Explore places, save favourites, and open a spotlight for reviews, photos, and insights."
        if show_welcome_transition
        else "Explore, filter, and contribute from a cleaner map-first workspace with fewer distractions."
    )
    render_react_hero(
        title,
        subtitle,
        [
            f"Category: {current_filter}",
            f"Preset: {preset_label}",
            f"Selection: {selected_name}",
            "Tap a marker to open the spotlight",
        ],
        badge="Map workspace",
        height=220,
    )

    if show_welcome_transition:
        # Hold the welcome hero briefly, then move to the default map hero.
        time.sleep(1.0)
        st.session_state.just_signed_in = False
        st.session_state.just_signed_in_until = 0.0
        st.rerun()

    map_col, inspector_col = st.columns([2.45, 1], gap="large")
    with map_col:
        render_map(locations_df)
    with inspector_col:
        render_location_details()


def render_profile_page() -> None:
    if not st.session_state.logged_in_user:
        st.session_state.current_page = "auth"
        st.rerun()

    user = st.session_state.logged_in_user
    summary_df = get_user_contribution_summary(int(user["user_id"]))
    summary = summary_df.iloc[0] if not summary_df.empty else None
    locations_df = get_locations_added_by_user(int(user["user_id"]))
    reviews_df = get_reviews_by_user(int(user["user_id"]))
    images_df = get_images_uploaded_by_user(int(user["user_id"]))
    review_rank_text = "Unranked"
    reviewers_df = users_with_most_reviews()
    if not reviewers_df.empty:
        ranked = reviewers_df.reset_index(drop=True)
        user_match = ranked[ranked["user_id"] == int(user["user_id"])]
        if not user_match.empty:
            user_pos = int(user_match.index[0]) + 1
            user_reviews = int(user_match.iloc[0]["total_reviews"])
            review_rank_text = f"#{user_pos} by reviews ({user_reviews})"

    render_react_hero(
        f"{esc(user['name'])}'s profile",
        "A quick view of the places you added, the reviews you wrote, and the images you uploaded.",
        [
            f"Locations: {int(summary['locations_added']) if summary is not None else 0}",
            f"Reviews: {int(summary['reviews_written']) if summary is not None else 0}",
            f"Images: {int(summary['images_uploaded']) if summary is not None else 0}",
            f"Review rank: {review_rank_text}",
        ],
        badge="Contribution hub",
        height=240,
    )

    st.markdown(
        f'<span class="soft-chip">Review leaderboard: {esc(review_rank_text)}</span>',
        unsafe_allow_html=True,
    )

    metric_cols = st.columns(4)
    stats = [
        ("Locations added", int(summary["locations_added"]) if summary is not None else 0, "places created by you"),
        ("Reviews written", int(summary["reviews_written"]) if summary is not None else 0, "community feedback"),
        ("Images uploaded", int(summary["images_uploaded"]) if summary is not None else 0, "photos shared"),
        ("Favorites saved", int(summary["favorites_saved"]) if summary is not None else 0, "places bookmarked"),
    ]
    for col, (label, value, detail) in zip(metric_cols, stats):
        with col:
            st.markdown(
                f"""
                <div class="metric-shell">
                    <div class="metric-label">{esc(label)}</div>
                    <p class="metric-value">{value}</p>
                    <p class="metric-detail">{esc(detail)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    left_col, right_col = st.columns([1, 1], gap="large")
    with left_col:
        st.markdown('<div class="profile-card">', unsafe_allow_html=True)
        st.markdown('<div class="profile-card-title">Locations added</div>', unsafe_allow_html=True)
        if locations_df.empty:
            st.info("No locations added yet.")
        else:
            for _, row in locations_df.iterrows():
                st.markdown(
                    f"""
                    <div class="review-shell">
                        <div class="review-header">
                            <div>
                                <div class="review-author">{esc(row['location_name'])}</div>
                                <div class="review-date">{esc(row['category_name'], 'Uncategorized')} · {esc(row['created_at'], 'Recently added')}</div>
                            </div>
                            <span class="soft-chip">ID {int(row['location_id'])}</span>
                        </div>
                        <p class="review-comment">{esc(row['address'], 'No address saved.')}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="profile-card" style="margin-top:0.8rem;">', unsafe_allow_html=True)
        st.markdown('<div class="profile-card-title">Images uploaded</div>', unsafe_allow_html=True)
        if images_df.empty:
            st.info("No images uploaded yet.")
        else:
            image_cols = st.columns(2)
            rendered = False
            for idx, row in images_df.iterrows():
                with image_cols[idx % len(image_cols)]:
                    image_path = str(row["image_url"])
                    try:
                        if image_path.startswith("http://") or image_path.startswith("https://"):
                            st.image(image_path, use_container_width=True)
                            rendered = True
                        elif os.path.exists(image_path):
                            st.image(image_path, use_container_width=True)
                            rendered = True
                    except Exception:
                        continue
            if not rendered:
                st.info("No images uploaded yet.")
        st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="profile-card">', unsafe_allow_html=True)
        st.markdown('<div class="profile-card-title">Reviews written</div>', unsafe_allow_html=True)
        if reviews_df.empty:
            st.info("No reviews written yet.")
        else:
            for _, row in reviews_df.iterrows():
                comment_text = esc(row["comment"], "No comment provided.").replace("\n", "<br>")
                st.markdown(
                    f"""
                    <div class="review-shell">
                        <div class="review-header">
                            <div>
                                <div class="review-author">{esc(row['location_name'])}</div>
                                <div class="review-date">{esc(row['date'], 'Unknown date')}</div>
                            </div>
                            <span class="soft-chip">{int(row['rating'])}/5</span>
                        </div>
                        <p class="review-comment">{comment_text}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        st.markdown('</div>', unsafe_allow_html=True)


def render_auth_page() -> None:
    if st.session_state.logged_in_user:
        st.markdown(
            f"""
            <div class="transition-shell">
                <div class="panel-kicker">Signed in already</div>
                <h3 class="surface-title">Welcome back, {esc(st.session_state.logged_in_user['name'])}</h3>
                <p class="surface-copy">Continue to the map, profile, or sign out if you want to switch accounts.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        action_col1, action_col2 = st.columns(2)
        with action_col1:
            if st.button("Continue to map", type="primary", width="stretch", key="auth_go_map"):
                st.session_state.current_page = "map"
                st.rerun()
        with action_col2:
            if st.button("Sign out", width="stretch", key="auth_sign_out"):
                st.session_state.logged_in_user = None
                st.session_state.current_page = "auth"
                st.success("Signed out.")
                st.rerun()
        return

    left_col, right_col = st.columns([1.08, 0.92], gap="large")

    with left_col:
        render_react_hero(
            "Discover Manipal, one place at a time",
            "Sign in to explore the map, save favourites, write reviews, and add new places. Registration is available if you are new here.",
            ["Map-first", "Favourites", "Reviews", "Photos"],
            background_image="https://images.unsplash.com/photo-1516834611397-8d633eaec5d0?auto=format&fit=crop&w=1600&q=80",
            badge="Manipal Atlas",
        )
        st.markdown(
            """
            <div style="margin-top:0.9rem; display:grid; gap:0.55rem;">
                <div class="profile-card">
                    <div class="profile-card-title">Map-first workflow</div>
                    <p class="profile-card-copy">Browse places on the map, then open one spotlight panel for reviews, favourites, and photos.</p>
                </div>
                <div class="profile-card">
                    <div class="profile-card-title">Clean contribution flow</div>
                    <p class="profile-card-copy">Add a location, category, review, or image without exposing backend noise in the interface.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right_col:
        st.markdown('<div class="auth-panel">', unsafe_allow_html=True)
        st.markdown('<div class="auth-panel-inner">', unsafe_allow_html=True)
        st.markdown('<div class="panel-kicker">Secure access</div>', unsafe_allow_html=True)
        st.markdown('<p class="surface-title">Sign in to continue</p>', unsafe_allow_html=True)
        st.markdown('<p class="auth-mini">Create an account if you are new, then return to the map with your contributions saved.</p>', unsafe_allow_html=True)

        sign_in_tab, register_tab = st.tabs(["Sign in", "Register"])

        with sign_in_tab:
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email", placeholder="name@example.com")
                password = st.text_input(
                    "Password",
                    type="password",
                    key="login_password",
                    placeholder="Enter your password",
                )
                login_submit = st.form_submit_button("Sign in", type="primary", width="stretch")

            if login_submit:
                user = get_user_by_email(email)
                if user and verify_password(password, user.get("password_hash")):
                    st.session_state.logged_in_user = {
                        "user_id": int(user["user_id"]),
                        "name": user["name"],
                        "email": user["email"],
                    }
                    st.session_state.current_page = "map"
                    st.session_state.just_signed_in = True
                    st.session_state.just_signed_in_until = time.time() + 1.0
                    st.success("Signed in successfully.")
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

        with register_tab:
            with st.form("register_form"):
                name = st.text_input("Name", key="reg_name", placeholder="Your full name")
                email = st.text_input("Email", key="reg_email", placeholder="name@example.com")
                password = st.text_input(
                    "Password",
                    type="password",
                    key="reg_password",
                    placeholder="Create a secure password",
                )
                register_submit = st.form_submit_button("Create account", type="primary", width="stretch")

            if register_submit:
                try:
                    register_user(name, email, hash_password(password))
                    st.success("Registration successful. You can sign in now.")
                except Exception as ex:
                    st.error(f"Registration failed: {ex}")

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
def render_add_category_card() -> None:
    if not st.session_state.show_add_category:
        return

    render_section_header(
        "Add new category",
        kicker="Contribution studio",
        description="Create a category.",
        state_key="show_add_category",
    )
    with st.form("add_category_form", clear_on_submit=True):
        category_name = st.text_input("Category name", placeholder="e.g. Restaurant, Hostel, Academic Block")
        submitted = st.form_submit_button("Save category", type="primary", width="stretch")
    if submitted:
        try:
            add_category(category_name)
            st.success("Category added.")
            st.session_state.show_add_category = False
            st.session_state.data_version += 1
            st.rerun()
        except Exception as ex:
            st.error(f"Could not add category: {ex}")


def render_add_location_card() -> None:
    if not st.session_state.show_add_location:
        return

    if st.session_state.last_clicked_coords:
        pin_lat, pin_lng = st.session_state.last_clicked_coords
        add_location_desc = f"Pinned coordinate: {pin_lat:.6f}, {pin_lng:.6f}"
    else:
        add_location_desc = "Pinned coordinate: none selected"

    render_section_header(
        "Add new location",
        kicker="Contribution studio",
        description=add_location_desc,
        state_key="show_add_location",
    )
    if not require_login("add a location"):
        return

    categories = get_categories()
    if categories.empty:
        st.info("Create at least one category first.")
        return

    default_lat = 13.3520
    default_lng = 74.7920
    if st.session_state.last_clicked_coords:
        default_lat, default_lng = st.session_state.last_clicked_coords

    with st.form("add_location_form"):
        name = st.text_input("Location name", placeholder="e.g. Innovation Center")
        category_id = st.selectbox(
            "Category",
            categories["category_id"].tolist(),
            format_func=lambda cid: f"{cid} - {categories.loc[categories['category_id'] == cid, 'category_name'].iloc[0]}",
        )
        address = st.text_input("Address", placeholder="Street, block, or nearby landmark")
        description = st.text_area("Description", placeholder="What should someone know before visiting this location?")
        coord_col1, coord_col2 = st.columns(2)
        with coord_col1:
            latitude = st.number_input("Latitude", value=float(default_lat), format="%.6f")
        with coord_col2:
            longitude = st.number_input("Longitude", value=float(default_lng), format="%.6f")
        submitted = st.form_submit_button("Save location", type="primary", width="stretch")

    if submitted:
        try:
            add_location(
                name,
                int(category_id),
                address,
                description,
                float(latitude),
                float(longitude),
                created_by=int(st.session_state.logged_in_user["user_id"]),
            )
            st.success("Location added.")
            st.session_state.show_add_location = False
            st.session_state.data_version += 1
            st.rerun()
        except Exception as ex:
            st.error(f"Could not add location: {ex}")


def render_location_details() -> None:
    if not st.session_state.selected_location_id:
        st.markdown(
            """
            <section class="empty-shell">
                <div class="panel-kicker">Inspector</div>
                <div class="empty-title">Select a place on the map</div>
                <p class="empty-copy">Open any marker to see a clearer spotlight with insights, favourites, reviews, and photos.</p>
            </section>
            """,
            unsafe_allow_html=True,
        )
        return

    loc_id = int(st.session_state.selected_location_id)
    details_df = get_location_details(loc_id)
    if details_df.empty:
        st.warning("Selected location could not be found. It may have been deleted.")
        st.session_state.selected_location_id = None
        return

    loc = details_df.iloc[0]
    avg_text = f"{float(loc['avg_rating']):.1f}" if pd.notna(loc["avg_rating"]) else "N/A"
    review_total = int(loc["review_count"]) if pd.notna(loc["review_count"]) else 0
    favorite_total = int(loc["favorite_count"]) if pd.notna(loc.get("favorite_count")) else 0
    category_name = esc(loc["category_name"], "Uncategorized")
    address_text = esc(loc["address"], "Address not added yet.")
    description_text = esc(loc["description"], "No description has been provided for this location yet.")
    loc_name = esc(loc["name"], "Unknown location")
    insights_df = get_location_spotlight_insights(loc_id)
    insight = insights_df.iloc[0] if not insights_df.empty else None
    rank_text = f"#{int(insight['category_rank'])}" if insight is not None and pd.notna(insight["category_rank"]) else "N/A"
    is_favorited = False
    if st.session_state.logged_in_user:
        current_user_id = int(st.session_state.logged_in_user["user_id"])
        is_favorited = loc_id in get_favorite_location_ids(current_user_id)

    st.markdown(
        f"""
        <div class="spotlight-shell fade-slide">
            <div class="spotlight-topline">
                <div>
                    <div class="panel-kicker">Location spotlight</div>
                    <h3 class="inspector-title">{loc_name}</h3>
                    <p class="muted-copy">{description_text}</p>
                </div>
                <span class="soft-chip">{category_name}</span>
            </div>
            <div class="spotlight-badges">
                <span class="soft-chip">Avg {esc(avg_text)}</span>
                <span class="soft-chip">{review_total} reviews</span>
            </div>
            <div class="insight-grid">
                <div class="insight-card">
                    <div class="insight-label">Category rank</div>
                    <div class="insight-value">{rank_text}</div>
                    <div class="insight-note">Compared with places in {category_name.lower()}.</div>
                </div>
                <div class="insight-card">
                    <div class="insight-label">Favourite count</div>
                    <div class="insight-value">{favorite_total}</div>
                    <div class="insight-note">Saved by the community.</div>
                </div>
                <div class="insight-card insight-card-wide">
                    <div class="insight-label">Address</div>
                    <div class="insight-value" style="font-size:0.84rem; line-height:1.35;">{address_text}</div>
                    <div class="insight-note">Use manage location to edit details.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    overview_tab, gallery_tab, reviews_tab = st.tabs(["Overview", "Gallery", "Reviews"])

    with overview_tab:
        st.markdown('<p class="section-label">Quick actions</p>', unsafe_allow_html=True)
        fav_label = "Remove favourite" if is_favorited else "Save favourite"
        fav_type = "secondary" if is_favorited else "primary"
        if st.button(fav_label, key="toggle_fav_btn", width="stretch", type=fav_type):
            if require_login("manage favourites"):
                try:
                    user_id = int(st.session_state.logged_in_user["user_id"])
                    if is_favorited:
                        remove_favorite(user_id, loc_id)
                        st.session_state.spotlight_feedback = ("success", "Removed from favourites.")
                    else:
                        add_favorite(user_id, loc_id)
                        st.session_state.spotlight_feedback = ("success", "Added to favourites.")
                    st.session_state.data_version += 1
                    st.rerun()
                except Exception as ex:
                    st.session_state.spotlight_feedback = ("error", f"Could not update favourite: {ex}")

        feedback = st.session_state.get("spotlight_feedback")
        if feedback:
            fb_type, fb_text = feedback
            safe_type = "success" if fb_type == "success" else "error"
            st.markdown(
                f'<div class="inline-feedback {safe_type}">{esc(str(fb_text))}</div>',
                unsafe_allow_html=True,
            )

        if st.session_state.logged_in_user:
            if st.button("Manage location", key="toggle_manage_loc", width="stretch"):
                st.session_state.show_manage_loc = not st.session_state.get("show_manage_loc", False)

        st.markdown('<hr class="panel-divider">', unsafe_allow_html=True)

        if st.session_state.get("show_manage_loc", False) and st.session_state.logged_in_user:
            with st.expander("Update or delete this location", expanded=True):
                st.warning("Updates write directly to the database. Deleting a location also removes its images and reviews.")
                categories = get_categories()
                category_options = categories["category_id"].tolist()
                if not category_options:
                    st.info("Add a category before editing this location.")
                    category_index = 0
                    current_category_id = None
                else:
                    current_category_id = int(loc["category_id"]) if pd.notna(loc["category_id"]) else category_options[0]
                    category_index = category_options.index(current_category_id) if current_category_id in category_options else 0

                if category_options:
                    with st.form("update_loc_form"):
                        u_name = st.text_input("Name", value=str(loc["name"]))
                        u_cat_col, u_add_col = st.columns(2)
                        with u_cat_col:
                            u_cat = st.selectbox(
                                "Category",
                                category_options,
                                index=category_index,
                                format_func=lambda cid: f"{cid} - {categories.loc[categories['category_id'] == cid, 'category_name'].iloc[0]}",
                            )
                        with u_add_col:
                            u_addr = st.text_input("Address", value=str(loc["address"]) if pd.notna(loc["address"]) else "")

                        u_desc = st.text_area("Description", value=str(loc["description"]) if pd.notna(loc["description"]) else "")
                        update_coords = st.checkbox("Update coordinates", value=False)
                        u_lat = None
                        u_lng = None
                        if update_coords:
                            coord_col1, coord_col2 = st.columns(2)
                            with coord_col1:
                                u_lat = st.number_input(
                                    "Latitude",
                                    value=float(loc["latitude"]) if pd.notna(loc["latitude"]) else 13.3520,
                                    format="%.6f",
                                )
                            with coord_col2:
                                u_lng = st.number_input(
                                    "Longitude",
                                    value=float(loc["longitude"]) if pd.notna(loc["longitude"]) else 74.7920,
                                    format="%.6f",
                                )
                        sub_upd = st.form_submit_button("Save changes", type="primary")

                    if sub_upd:
                        update_location(loc_id, u_name, int(u_cat), u_addr, u_desc, u_lat, u_lng)
                        st.success("Location updated successfully.")
                        st.session_state.data_version += 1
                        st.rerun()

                if st.button("Delete location", key="delete_location_btn", type="primary", width="stretch"):
                    delete_location(loc_id)
                    st.session_state.selected_location_id = None
                    st.session_state.show_manage_loc = False
                    st.session_state.data_version += 1
                    st.success("Location completely deleted.")
                    st.rerun()

    with gallery_tab:
        st.markdown('<p class="section-label">Gallery</p>', unsafe_allow_html=True)
        if st.session_state.logged_in_user:
            upl_file = st.file_uploader(
                "Upload an image",
                type=["png", "jpg", "jpeg"],
                key="loc_img_upload",
            )
            if upl_file is not None and st.button("Save uploaded image", key="save_uploaded_image", width="stretch", type="primary"):
                filepath = os.path.join(UPLOAD_DIR, upl_file.name)
                with open(filepath, "wb") as file_obj:
                    file_obj.write(upl_file.getbuffer())
                add_image(loc_id, filepath, uploaded_by=int(st.session_state.logged_in_user["user_id"]))
                st.success(f"Image {upl_file.name} uploaded successfully.")
                st.session_state.data_version += 1
                st.rerun()
        else:
            st.info("Sign in to upload photos for this location.")

        images_df = get_images_for_location(loc_id)
        if not images_df.empty:
            img_cols = st.columns(min(len(images_df), 2))
            rendered = False
            for idx, row in images_df.iterrows():
                with img_cols[idx % max(len(img_cols), 1)]:
                    image_url = str(row["image_url"])
                    try:
                        if image_url.startswith("http://") or image_url.startswith("https://"):
                            st.image(image_url, use_container_width=True)
                            rendered = True
                        elif os.path.exists(image_url):
                            st.image(image_url, use_container_width=True)
                            rendered = True
                    except Exception:
                        continue
            if not rendered:
                st.info("No images uploaded yet.")
        else:
            st.info("No images uploaded yet.")

    with reviews_tab:
        st.markdown('<p class="section-label">Community reviews</p>', unsafe_allow_html=True)

        if st.session_state.logged_in_user:
            if st.button("Write a review", key="open_review_in_reviews_tab", width="stretch", type="primary"):
                st.session_state.show_add_review_for_selected = True
                st.rerun()

        if st.session_state.get("show_add_review_for_selected", False) and st.session_state.logged_in_user:
            with st.form("add_review_for_selected"):
                rating = st.slider("Rating", 1, 5, 4)
                comment = st.text_area("Comment")
                review_form_col1, review_form_col2 = st.columns(2)
                with review_form_col1:
                    submitted = st.form_submit_button("Submit review", type="primary")
                with review_form_col2:
                    cancel = st.form_submit_button("Cancel")

            if cancel:
                st.session_state.show_add_review_for_selected = False
                st.rerun()

            if submitted:
                try:
                    avg_rating = add_review(
                        int(st.session_state.logged_in_user["user_id"]),
                        loc_id,
                        int(rating),
                        comment,
                        date.today(),
                    )
                    st.success(f"Review added. New average rating: {avg_rating}")
                    st.session_state.show_add_review_for_selected = False
                    st.session_state.data_version += 1
                    st.rerun()
                except Exception as ex:
                    st.error(f"Could not add review: {ex}")

        reviews_df = get_reviews_for_location(loc_id)
        if reviews_df.empty:
            st.info("No reviews yet for this location.")
        else:
            for _, r_row in reviews_df.iterrows():
                r_id = int(r_row["review_id"])
                author = esc(r_row["user_name"], "Anonymous")
                review_date = esc(r_row["date"], "Unknown date")
                comment_html = esc(r_row["comment"], "No comment provided.").replace("\n", "<br>")
                st.markdown(
                    f"""
                    <div class="review-shell">
                        <div class="review-header">
                            <div>
                                <div class="review-author">{author}</div>
                                <div class="review-date">{review_date}</div>
                            </div>
                            <span class="soft-chip">Rating {int(r_row['rating'])}/5</span>
                        </div>
                        <p class="review-comment">{comment_html}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.session_state.logged_in_user and st.session_state.logged_in_user["user_id"] == int(r_row["user_id"]):
                    edit_col, delete_col = st.columns(2)
                    with edit_col:
                        if st.button("Edit review", key=f"edit_rev_{r_id}", width="stretch"):
                            st.session_state[f"editing_review_{r_id}"] = True
                    with delete_col:
                        if st.button("Delete review", key=f"del_rev_{r_id}", width="stretch"):
                            delete_review(r_id)
                            st.session_state.data_version += 1
                            st.rerun()

                    if st.session_state.get(f"editing_review_{r_id}", False):
                        with st.form(f"update_review_form_{r_id}"):
                            new_r = st.slider("New rating", 1, 5, int(r_row["rating"]), key=f"nr_{r_id}")
                            new_c = st.text_area("New comment", value=str(r_row["comment"]), key=f"nc_{r_id}")
                            upd_col1, upd_col2 = st.columns(2)
                            with upd_col1:
                                if st.form_submit_button("Save review", type="primary"):
                                    update_review(r_id, new_r, new_c)
                                    st.session_state[f"editing_review_{r_id}"] = False
                                    st.session_state.data_version += 1
                                    st.rerun()
                            with upd_col2:
                                if st.form_submit_button("Cancel"):
                                    st.session_state[f"editing_review_{r_id}"] = False
                                    st.rerun()


def build_coverage_audit_df() -> pd.DataFrame:
    return pd.DataFrame()


def build_substitution_df() -> pd.DataFrame:
    return pd.DataFrame()


def build_improvement_df() -> pd.DataFrame:
    return pd.DataFrame()


def render_db_runtime_sections() -> None:
    txn_col, cursor_col = st.columns(2, gap="large")
    with txn_col:
        st.markdown(
            """
            <div class="flat-section">
                <div class="surface-head">
                    <div class="panel-kicker">Runtime demo</div>
                    <div class="surface-title">Transaction control</div>
                    <p class="surface-copy">Run a SAVEPOINT transaction demo and observe commit versus rollback behavior.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        all_reviews = _to_df_for_ui(
            "SELECT review_id, user_id, location_id, rating, comment FROM Reviews ORDER BY review_id"
        )
        if all_reviews.empty:
            st.info("No reviews yet. Load sample data first.")
        else:
            safe_df(all_reviews)
            select_col, input_col = st.columns(2)
            with select_col:
                review_ids = all_reviews["review_id"].tolist()
                review_lookup = {
                    int(row["review_id"]): f"Review {int(row['review_id'])} - current rating {int(row['rating'])}"
                    for _, row in all_reviews.iterrows()
                }
                selected_rid = st.selectbox(
                    "Review to update",
                    review_ids,
                    format_func=lambda rid: review_lookup[int(rid)],
                    key="txn_review_id",
                )
            with input_col:
                rating_choices = list(range(0, 7))
                new_rating_input = st.selectbox(
                    "New rating",
                    rating_choices,
                    index=4,
                    format_func=lambda rating: (
                        f"{rating} - rollback case"
                        if int(rating) in {0, 6}
                        else f"{rating} - commit normally"
                    ),
                    key="txn_new_rating",
                )
            st.caption(f"Selected review: {review_lookup[int(selected_rid)]}. New rating: {int(new_rating_input)}.")
            st.caption("Ratings 0 and 6 intentionally trigger the SAVEPOINT rollback path for the demo.")
            if st.button("Execute transaction", key="run_txn", type="primary", width="stretch"):
                res = demo_savepoint_transaction(int(selected_rid), int(new_rating_input))
                if res["status"] == "committed":
                    st.success(f"Committed: {res['message']}")
                elif res["status"] == "rolled_back":
                    st.warning(f"Rolled back: {res['message']}")
                else:
                    st.error(f"Error: {res['message']}")

    with cursor_col:
        st.markdown(
            """
            <div class="flat-section">
                <div class="surface-head">
                    <div class="panel-kicker">Runtime demo</div>
                    <div class="surface-title">Cursor routine</div>
                    <p class="surface-copy">Run the Python-level cursor loop that flags low-rated locations into the LocationStatus table.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        threshold_val = st.slider("Flag threshold", min_value=1.0, max_value=5.0, value=3.5, step=0.5, key="cursor_threshold")
        if st.button("Run cursor flagging routine", key="run_cursor", type="primary", width="stretch"):
            with st.spinner("Running cursor loop..."):
                status_df = flag_low_rated_locations(threshold=float(threshold_val))
            st.success("Cursor routine complete.")
            safe_df(status_df)
        else:
            existing = get_location_status()
            if not existing.empty:
                st.markdown("**Current LocationStatus table**")
                safe_df(existing)
            else:
                st.info("Run the cursor routine to populate status results.")

    archive_col, param_cursor_col = st.columns(2, gap="large")
    with archive_col:
        st.markdown(
            """
            <div class="flat-section">
                <div class="surface-head">
                    <div class="panel-kicker">Runtime demo</div>
                    <div class="surface-title">Archive-and-delete transaction</div>
                    <p class="surface-copy">Run a richer transactional workflow that deletes a location and captures a trigger-backed archive record.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        locations_df = get_locations()
        if locations_df.empty:
            st.info("No locations are available.")
        else:
            location_ids = locations_df["location_id"].tolist()
            location_lookup = {
                int(row["location_id"]): f"{int(row['location_id'])} - {row['name']}"
                for _, row in locations_df.iterrows()
            }
            archive_location_id = st.selectbox(
                "Location to archive and delete",
                location_ids,
                format_func=lambda lid: location_lookup[int(lid)],
                key="archive_delete_location_id",
            )
            st.caption(f"Selected location: {location_lookup[int(archive_location_id)]}.")
            st.caption("This demo uses a SAVEPOINT and the delete-archive trigger.")
            if st.button("Archive and delete location", key="run_archive_delete", type="primary", width="stretch"):
                result = archive_delete_location_transaction(int(archive_location_id))
                if result["status"] == "committed":
                    st.session_state.data_version += 1
                    st.success(result["message"])
                    st.rerun()
                elif result["status"] == "rolled_back":
                    st.warning(result["message"])
                else:
                    st.error(result["message"])
            audit_df = get_deleted_location_audit()
            if not audit_df.empty:
                safe_df(audit_df)

    with param_cursor_col:
        st.markdown(
            """
            <div class="flat-section">
                <div class="surface-head">
                    <div class="panel-kicker">Runtime demo</div>
                    <div class="surface-title">Parameterized cursor analogue</div>
                    <p class="surface-copy">Run a category-scoped explicit cursor loop analogue with an adjustable threshold.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        categories_df = get_categories()
        if categories_df.empty:
            st.info("No categories are available.")
        else:
            category_options = categories_df["category_id"].tolist()
            category_lookup = {
                int(row["category_id"]): f"{int(row['category_id'])} - {row['category_name']}"
                for _, row in categories_df.iterrows()
            }
            selected_category_id = st.selectbox(
                "Category scope",
                category_options,
                format_func=lambda cid: category_lookup[int(cid)],
                key="param_cursor_category",
            )
            cursor_threshold = st.slider(
                "Highlight threshold",
                min_value=1.0,
                max_value=5.0,
                value=4.0,
                step=0.5,
                key="param_cursor_threshold",
            )
            st.caption(
                f"Showing locations from {category_lookup[int(selected_category_id)]} with emphasis on averages at or above {cursor_threshold:.1f}."
            )
            cursor_df = parameterized_category_cursor(int(selected_category_id), float(cursor_threshold))
            safe_df(cursor_df, "No locations found for the selected category.")


def render_analytics_page() -> None:
    import datetime

    render_page_banner(
        "Logs",
        "Trigger-backed audit logs.",
        kicker="Logs",
        chips=["Review logs", "Delete logs"],
    )

    refresh_col, ts_col = st.columns([1, 4])
    with refresh_col:
        if st.button("↻  Refresh all data", key="analytics_refresh", type="primary", width="stretch"):
            st.session_state.data_version += 1
            st.rerun()
    with ts_col:
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        st.markdown(
            f'<p style="color:var(--text-soft);margin:0.75rem 0 0 0.5rem;font-size:0.88rem;">'
            f'Last refreshed at <strong>{now_str}</strong> &nbsp;·&nbsp; data version <strong>{st.session_state.data_version}</strong></p>',
            unsafe_allow_html=True,
        )

    st.markdown('<hr class="panel-divider">', unsafe_allow_html=True)

    review_logs_tab, delete_logs_tab = st.tabs(
        ["Review Audit Logs", "Deleted Location Logs"]
    )

    with review_logs_tab:
        st.markdown(
            """
            <div class="flat-section">
                <div class="surface-head">
                    <div class="panel-kicker">Logs</div>
                    <div class="surface-title">Review audit log</div>
                    <p class="surface-copy">Trigger-backed audit logs.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Refresh logs", key="refresh_review_logs_btn", width="stretch"):
            st.rerun()
        safe_df(get_review_logs(), "No trigger log entries yet. Add or edit a review to generate log rows.")

    with delete_logs_tab:
        st.markdown(
            """
            <div class="flat-section">
                <div class="surface-head">
                    <div class="panel-kicker">Logs</div>
                    <div class="surface-title">Deleted location archive log</div>
                    <p class="surface-copy">Trigger-backed audit logs.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Refresh logs", key="refresh_deleted_logs_btn", width="stretch"):
            st.rerun()
        safe_df(get_deleted_location_audit(), "No locations have been deleted yet.")



def _to_df_for_ui(sql: str) -> pd.DataFrame:
    from db import get_conn
    conn = get_conn()
    try:
        cursor = conn.execute(sql)
        cols = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return pd.DataFrame([dict(zip(cols, row)) for row in rows], columns=cols)
    finally:
        conn.close()


def init_state() -> None:
    defaults = {
        "logged_in_user": None,
        "selected_location_id": None,
        "last_clicked_coords": None,
        "show_add_category": False,
        "show_add_location": False,
        "show_manage_loc": False,
        "show_add_review_for_selected": False,
        "show_upload_image_for_selected": False,
        "show_favorites_only": False,
        "selected_preset": "None",
        "spotlight_section": "Overview",
        "spotlight_feedback": None,
        "just_signed_in": False,
        "just_signed_in_until": 0.0,
        "current_page": "auth",
        "selected_category_id": None,
        # Incremented after every write so analytics always shows fresh data.
        "data_version": 0,
        "query_log_reset_done": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_db()
init_state()
if not st.session_state.query_log_reset_done:
    reset_query_log()
    st.session_state.query_log_reset_done = True

if not st.session_state.logged_in_user and st.session_state.current_page not in {"auth"}:
    st.session_state.current_page = "auth"
    st.rerun()

if st.session_state.logged_in_user and st.session_state.current_page not in {"map", "profile", "analytics", "auth"}:
    st.session_state.current_page = "map"
    st.rerun()

if st.session_state.current_page == "auth":
    render_auth_page()
else:
    if not st.session_state.logged_in_user and st.session_state.current_page not in {"auth"}:
        st.session_state.current_page = "auth"
    if st.session_state.logged_in_user and st.session_state.current_page not in {"map", "profile", "analytics"}:
        st.session_state.current_page = "map"

    nav_col, content_col = st.columns([1.08, 3.92], gap="large")

    with nav_col:
        if st.session_state.logged_in_user:
            st.markdown(
                f"<p class='status-text' style='margin:0 0 0.45rem;'>Signed in as {esc(st.session_state.logged_in_user['name'])}</p>",
                unsafe_allow_html=True,
            )
            if st.button("Sign out", icon=":material/logout:", width="stretch", key="nav_signout"):
                st.session_state.logged_in_user = None
                st.session_state.current_page = "auth"
                st.success("Signed out.")
                st.rerun()

        st.markdown('<div class="panel-kicker">Workspace</div>', unsafe_allow_html=True)
        st.markdown('<p class="nav-title">Navigation</p>', unsafe_allow_html=True)

        if st.button("Map View", icon=":material/map:", type="primary" if st.session_state.current_page == "map" else "secondary", width="stretch", key="nav_map"):
            st.session_state.current_page = "map"
        if st.session_state.logged_in_user and st.button("Profile", icon=":material/person:", type="primary" if st.session_state.current_page == "profile" else "secondary", width="stretch", key="nav_profile"):
            st.session_state.current_page = "profile"
        if st.session_state.logged_in_user and st.button("Logs", icon=":material/analytics:", type="primary" if st.session_state.current_page == "analytics" else "secondary", width="stretch", key="nav_analytics"):
            st.session_state.current_page = "analytics"

        st.markdown('<hr class="panel-divider">', unsafe_allow_html=True)
        st.markdown('<p class="nav-title">Filters</p>', unsafe_allow_html=True)

        categories_df = get_categories()
        options = ["All"]
        category_map: dict[str, int] = {}
        for _, row in categories_df.iterrows():
            label = f"{row['category_name']}"
            options.append(label)
            category_map[label] = int(row["category_id"])

        current_label = "All"
        if st.session_state.selected_category_id is not None:
            for label, cid in category_map.items():
                if cid == st.session_state.selected_category_id:
                    current_label = label
                    break

        selected_label = st.selectbox("Filter by category", options, index=options.index(current_label))
        st.session_state.selected_category_id = category_map.get(selected_label)
        preset_options = [
            "None",
            "All places",
            "Highly rated",
            "Highly reviewed",
            "Most favourited",
            "Category leaders",
            "Saved and reviewed",
        ]
        preset_index = preset_options.index(st.session_state.get("selected_preset", "All places")) if st.session_state.get("selected_preset", "All places") in preset_options else 0
        st.session_state.selected_preset = st.selectbox("Quick preset", preset_options, index=preset_index)
        st.session_state.show_favorites_only = st.checkbox(
            "Show only favorites",
            value=bool(st.session_state.show_favorites_only),
            help="Requires sign in.",
        )

        st.markdown('<hr class="panel-divider">', unsafe_allow_html=True)
        st.markdown('<p class="nav-title">Actions</p>', unsafe_allow_html=True)
        if st.button("Add new category", icon=":material/category:", width="stretch", key="nav_add_category"):
            st.session_state.show_add_category = not st.session_state.show_add_category
            st.session_state.show_add_location = False
        if st.button("Add new location", icon=":material/add_location_alt:", width="stretch", key="nav_add_location"):
            st.session_state.show_add_location = not st.session_state.show_add_location
            st.session_state.show_add_category = False
        if st.button("Load sample data", width="stretch", key="nav_load_sample"):
            try:
                insert_sample_data()
                st.success("Sample data loaded.")
                st.session_state.data_version += 1
                st.rerun()
            except Exception as ex:
                st.error(f"Could not load sample data: {ex}")

    with content_col:
        render_add_category_card()
        render_add_location_card()
        all_locations_df = get_locations()
        locations_df = search_locations_by_category(st.session_state.selected_category_id)

        if st.session_state.selected_preset == "Highly rated":
            preset_df = top_rated_locations(min_reviews=2)
            locations_df = locations_df[locations_df["location_id"].isin(preset_df["location_id"].tolist())]
        elif st.session_state.selected_preset == "Highly reviewed":
            preset_df = most_reviewed_locations()
            locations_df = locations_df[locations_df["location_id"].isin(preset_df["location_id"].tolist())]
        elif st.session_state.selected_preset == "Most favourited":
            preset_df = most_favorited_locations(min_favorites=1)
            locations_df = locations_df[locations_df["location_id"].isin(preset_df["location_id"].tolist())]
        elif st.session_state.selected_preset == "Category leaders":
            preset_df = locations_above_all_in_category()
            locations_df = locations_df[locations_df["location_id"].isin(preset_df["location_id"].tolist())]
        elif st.session_state.selected_preset == "Saved and reviewed":
            preset_df = common_favorites_and_reviewed()
            locations_df = locations_df[locations_df["location_id"].isin(preset_df["location_id"].tolist())]

        if st.session_state.show_favorites_only:
            if st.session_state.logged_in_user:
                favorite_ids = set(get_favorite_location_ids(int(st.session_state.logged_in_user["user_id"])))
                locations_df = locations_df[locations_df["location_id"].isin(favorite_ids)]
            else:
                locations_df = locations_df.iloc[0:0]
                st.info("Sign in to view favorite locations.")
        if st.session_state.current_page == "profile" and st.session_state.logged_in_user:
            render_profile_page()
        elif st.session_state.current_page == "analytics" and st.session_state.logged_in_user:
            render_analytics_page()
        elif st.session_state.current_page == "auth":
            render_auth_page()
        else:
            render_map_page(locations_df, all_locations_df, categories_df)
