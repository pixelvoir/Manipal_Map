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
    get_flagged_locations,
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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700;800&display=swap');

    /* ── Light theme (default) ──────────────────────────── */
    :root {
        --bg:            #F0F4F1;
        --surface:       #FFFFFF;
        --surface-alt:   #F7FAF8;
        --surface-glass: rgba(255,255,255,0.82);
        --border:        #DCE5DE;
        --border-strong: #B8CEC0;
        --text:          #111816;
        --text-2:        #3D5047;
        --text-soft:     #6B8070;
        --text-3:        #8FA89A;
        --accent:        #16A34A;
        --accent-mid:    #22C55E;
        --accent-dark:   #15803D;
        --accent-pale:   #DCFCE7;
        --accent-line:   #BBF7D0;
        --accent-glow:   rgba(22,163,74,0.18);
        --shadow-sm:     0 1px 4px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
        --shadow-md:     0 4px 16px rgba(0,0,0,0.08), 0 2px 6px rgba(0,0,0,0.05);
        --shadow-lg:     0 12px 40px rgba(0,0,0,0.12), 0 4px 12px rgba(0,0,0,0.06);
        --r-sm:  8px;
        --r-md:  12px;
        --r-lg:  18px;
        --r-xl:  24px;
    }

    /* ── Dark theme ──────────────────────────────────────── */
    [data-theme="dark"] {
        --bg:            #0E1410;
        --surface:       #161D18;
        --surface-alt:   #1C2620;
        --surface-glass: rgba(22,29,24,0.88);
        --border:        #2A3830;
        --border-strong: #3D5045;
        --text:          #E8F0EA;
        --text-2:        #8EB09A;
        --text-soft:     #6A8A72;
        --text-3:        #4A6A54;
        --accent:        #22C55E;
        --accent-mid:    #4ADE80;
        --accent-dark:   #16A34A;
        --accent-pale:   rgba(34,197,94,0.12);
        --accent-line:   rgba(34,197,94,0.25);
        --accent-glow:   rgba(34,197,94,0.28);
        --shadow-sm:     0 1px 4px rgba(0,0,0,0.35), 0 1px 2px rgba(0,0,0,0.2);
        --shadow-md:     0 4px 20px rgba(0,0,0,0.5), 0 2px 8px rgba(0,0,0,0.3);
        --shadow-lg:     0 16px 48px rgba(0,0,0,0.65), 0 6px 16px rgba(0,0,0,0.4);
    }

    * { box-sizing: border-box; }

    .stApp {
        background: var(--bg);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: var(--text);
        font-size: 14px;
        line-height: 1.5;
        -webkit-font-smoothing: antialiased;
        transition: background 0.3s ease, color 0.3s ease;
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

    /* ── Star Rating ─────────────────────────────────────── */
    .star-row {
        display: flex;
        align-items: center;
        gap: 0.22rem;
        margin: 0.35rem 0;
    }
    .star-row svg { flex-shrink: 0; }
    .star-score {
        font-size: 0.82rem;
        font-weight: 700;
        color: var(--text);
        margin-left: 0.3rem;
    }
    .star-count {
        font-size: 0.76rem;
        color: var(--text-3);
        margin-left: 0.15rem;
    }

    /* ── Inspector card ──────────────────────────────────── */
    .inspector-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--r-lg);
        box-shadow: var(--shadow-md);
        overflow: hidden;
        margin-bottom: 0.9rem;
    }
    .inspector-header-bar {
        background: linear-gradient(145deg, #1a342a 0%, #274d3b 100%);
        padding: 1rem 1.1rem 0.85rem;
        position: relative;
    }
    [data-theme="dark"] .inspector-header-bar {
        background: linear-gradient(145deg, #0d1f16 0%, #1a3528 100%);
    }
    .inspector-header-bar .panel-kicker { color: rgba(200,230,215,0.72) !important; }
    .inspector-header-bar .inspector-title { color: #fff !important; }
    .inspector-header-bar .muted-copy { color: rgba(200,220,210,0.85) !important; }
    .inspector-body {
        padding: 0.9rem 1.1rem;
    }

    /* ── Dark mode toggle button ─────────────────────────── */
    .dm-toggle {
        position: fixed;
        bottom: 1.25rem;
        right: 1.25rem;
        z-index: 9999;
        width: 44px;
        height: 44px;
        border-radius: 50%;
        border: 1px solid var(--border-strong);
        background: var(--surface);
        box-shadow: var(--shadow-md);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
        transition: background 0.2s, transform 0.2s, box-shadow 0.2s;
    }
    .dm-toggle:hover {
        transform: scale(1.12);
        box-shadow: var(--shadow-lg);
        background: var(--accent-pale);
    }

    /* ── Accent glow on hover for feature cards ──────────── */
    .profile-card:hover, .metric-shell:hover {
        border-color: var(--accent-line) !important;
        box-shadow: var(--shadow-md), 0 0 0 3px var(--accent-glow) !important;
        transition: border-color 0.2s, box-shadow 0.2s;
    }

    /* ── Nav panel refinements ───────────────────────────── */
    .nav-user-chip {
        display: flex;
        align-items: center;
        gap: 0.55rem;
        padding: 0.5rem 0.65rem;
        background: var(--accent-pale);
        border: 1px solid var(--accent-line);
        border-radius: var(--r-md);
        margin-bottom: 0.75rem;
    }
    .nav-user-avatar {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: var(--accent);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7rem;
        font-weight: 700;
        color: #fff;
        flex-shrink: 0;
    }
    .nav-user-name {
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--text);
        line-height: 1.3;
    }
    .nav-user-status {
        font-size: 0.68rem;
        color: var(--accent);
        font-weight: 500;
    }

    /* ── Wordmark ────────────────────────────────────────── */
    .atlas-wordmark {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid var(--border);
    }
    .atlas-wordmark-text {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1rem;
        font-weight: 700;
        color: var(--text);
        letter-spacing: -0.01em;
    }
    .atlas-wordmark-sub {
        font-size: 0.65rem;
        color: var(--text-3);
        font-weight: 500;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    @media (max-width: 900px) {
        .hero-title { font-size: 1.05rem; }
        .inspector-meta { grid-template-columns: 1fr; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');

    .stApp,
    .stMarkdown,
    .stText,
    .stCaption,
    .stDataFrame,
    label,
    input,
    textarea,
    select,
    button {
        font-family: 'Inter', 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    }

    h1, h2, h3, h4, h5, h6,
    .surface-title,
    .inspector-title,
    .workspace-nav-title {
        font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
        letter-spacing: -0.01em;
    }

    .stApp {
        background:
            radial-gradient(1200px 460px at -8% -10%, rgba(22, 163, 74, 0.08), transparent 58%),
            radial-gradient(1000px 380px at 112% -12%, rgba(21, 128, 61, 0.06), transparent 56%),
            var(--bg);
        color: var(--text);
    }
    [data-theme="dark"] .stApp {
        background:
            radial-gradient(1200px 460px at -8% -10%, rgba(34, 197, 94, 0.1), transparent 58%),
            radial-gradient(1000px 380px at 112% -12%, rgba(16, 185, 129, 0.09), transparent 56%),
            var(--bg);
    }

    .map-caption {
        margin-top: 0.62rem;
        color: var(--text-soft);
        font-weight: 600;
    }

    .spotlight-shell,
    .review-shell,
    .profile-card,
    .metric-shell,
    .auth-panel,
    .transition-shell,
    .empty-shell {
        border-radius: 12px !important;
        border: 1px solid var(--border) !important;
        background: linear-gradient(180deg, var(--surface) 0%, var(--surface-alt) 100%) !important;
        box-shadow: var(--shadow-sm) !important;
        transition: transform 200ms ease, box-shadow 200ms ease, border-color 200ms ease;
    }

    .spotlight-shell:hover,
    .review-shell:hover,
    .profile-card:hover,
    .metric-shell:hover,
    .auth-panel:hover {
        transform: translateY(-1px);
        border-color: var(--border-strong) !important;
        box-shadow: var(--shadow-md) !important;
    }

    .metric-value {
        font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
    }

    .soft-chip {
        border-radius: 999px !important;
        border: 1px solid var(--border-strong) !important;
        background: var(--surface-alt) !important;
        color: var(--text-2) !important;
        font-weight: 700 !important;
    }

    .workspace-nav-kicker {
        margin: 0 0 0.3rem;
        font-size: 0.66rem;
        letter-spacing: 0.11em;
        text-transform: uppercase;
        color: var(--accent);
        font-weight: 800;
    }

    .workspace-nav-title {
        margin: 0 0 0.2rem;
        font-size: 1.04rem;
        color: var(--text);
        font-weight: 800;
    }

    .workspace-nav-copy {
        margin: 0 0 0.72rem;
        font-size: 0.82rem;
        color: var(--text-soft);
    }

    .workspace-chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
        margin-bottom: 0.7rem;
    }

    .workspace-chip {
        display: inline-flex;
        align-items: center;
        padding: 0.3rem 0.62rem;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 700;
        color: var(--text-2);
        border: 1px solid var(--border-strong);
        background: var(--surface-alt);
    }

    [data-testid="stButton"] > button,
    [data-testid="stFormSubmitButton"] > button {
        border-radius: 10px !important;
        border: 1px solid var(--border-strong) !important;
        background: var(--surface) !important;
        color: var(--text) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.84rem !important;
        font-weight: 700 !important;
        box-shadow: var(--shadow-sm) !important;
    }

    [data-testid="stButton"] > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover {
        border-color: var(--accent) !important;
        background: var(--surface-alt) !important;
    }

    [data-testid="stButton"] > button[kind="primary"],
    [data-testid="stFormSubmitButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent-dark) 0%, var(--accent) 100%) !important;
        border: none !important;
        color: #f8fffb !important;
    }

    [data-testid="stButton"] > button[kind="primary"]:hover,
    [data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-mid) 100%) !important;
    }

    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    div[data-baseweb="base-input"] > div,
    .stTextArea textarea,
    .stNumberInput input {
        border-radius: 10px !important;
        border: 1px solid var(--border) !important;
        background: var(--surface) !important;
    }

    .stTabs [data-baseweb="tab"] {
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
    }

    .stTabs [aria-selected="true"] {
        border-bottom-color: var(--accent) !important;
        color: var(--text) !important;
    }

    .element-container iframe {
        border-radius: 16px !important;
        border: 1px solid var(--border) !important;
        box-shadow: var(--shadow-md) !important;
    }

    .glow-shell {
        border-radius: 16px;
        overflow: hidden;
    }
    .glow-shell::after {
        content: "";
        position: absolute;
        inset: 0;
        pointer-events: none;
        background: linear-gradient(120deg, rgba(255,255,255,0) 35%, rgba(255,255,255,0.18) 50%, rgba(255,255,255,0) 65%);
        transform: translateX(-120%);
        animation: atlasSweep 7s ease-in-out infinite;
    }
    [data-theme="dark"] .glow-shell::after {
        background: linear-gradient(120deg, rgba(255,255,255,0) 35%, rgba(255,255,255,0.11) 50%, rgba(255,255,255,0) 65%);
    }

    .fade-slide {
        animation: atlasLiftIn 420ms cubic-bezier(0.22,1,0.36,1);
    }

    @keyframes atlasLiftIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes atlasSweep {
        0% { transform: translateX(-120%); }
        55% { transform: translateX(120%); }
        100% { transform: translateX(120%); }
    }

    [data-testid="stSidebar"] {
        background: var(--surface) !important;
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


def apply_theme_mode(theme_mode: str) -> None:
    theme_js = json.dumps(theme_mode if theme_mode in {"light", "dark"} else "light")
    components.html(
        f"""
        <script>
            const theme = {theme_js};
            const parentDoc = window.parent && window.parent.document ? window.parent.document : document;
            parentDoc.documentElement.setAttribute('data-theme', theme);
            parentDoc.body.setAttribute('data-theme', theme);
            const appRoot = parentDoc.querySelector('.stApp');
            if (appRoot) {{
                appRoot.setAttribute('data-theme', theme);
            }}
        </script>
        """,
        height=0,
    )


def render_theme_toggle(widget_key: str, *, label: str = "Dark mode") -> None:
    is_dark = st.session_state.get("ui_theme", "light") == "dark"
    toggled = st.toggle(label, value=is_dark, key=widget_key)
    next_theme = "dark" if toggled else "light"
    if next_theme != st.session_state.get("ui_theme", "light"):
        st.session_state.ui_theme = next_theme
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

def render_react_hero(
    title: str,
    subtitle: str,
    chips: list[str],
    *,
    background_image: str | None = None,
    badge: str = "Map-first experience",
    is_dark: bool = False,
    height: int = 236,
) -> None:
    hero_data_js = json.dumps(
        {
            "title": title,
            "subtitle": subtitle,
            "chips": chips,
            "background_image": background_image or "",
            "badge": badge,
            "is_dark": is_dark,
        }
    )
    container_id = f"atlas-react-hero-{secrets.token_hex(6)}"
    html_block = """
        <div id="__ID__"></div>
        <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
        <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
        <script>
            const e = React.createElement;
            const heroData = __HERO_DATA__;

            function Hero() {
                const [show, setShow] = React.useState(false);
                const [imgLoaded, setImgLoaded] = React.useState(!heroData.background_image);
                const [activeIdx, setActiveIdx] = React.useState(0);
                const [pointer, setPointer] = React.useState({x: 0, y: 0});
                const safeChips = (heroData.chips && heroData.chips.length ? heroData.chips : ['Ready']).slice(0, 6);

                React.useEffect(() => {
                    const timer = setTimeout(() => setShow(true), 40);
                    return () => clearTimeout(timer);
                }, []);

                React.useEffect(() => {
                    if (!heroData.background_image) {
                        setImgLoaded(true);
                        return;
                    }
                    const img = new Image();
                    img.onload = () => setImgLoaded(true);
                    img.onerror = () => setImgLoaded(true);
                    img.src = heroData.background_image;
                }, []);

                React.useEffect(() => {
                    if (safeChips.length <= 1) {
                        return;
                    }
                    const rotate = setInterval(() => {
                        setActiveIdx((prev) => (prev + 1) % safeChips.length);
                    }, 4000);
                    return () => clearInterval(rotate);
                }, [safeChips.length]);

                const shellBg = (heroData.background_image && imgLoaded)
                    ? (heroData.is_dark
                        ? 'linear-gradient(118deg, rgba(6,11,16,0.86) 0%, rgba(17,34,30,0.76) 58%, rgba(17,58,40,0.72) 100%), url(' + heroData.background_image + ')'
                        : 'linear-gradient(118deg, rgba(12,17,28,0.78) 0%, rgba(23,46,40,0.68) 58%, rgba(34,87,63,0.64) 100%), url(' + heroData.background_image + ')')
                    : (heroData.is_dark
                        ? 'linear-gradient(128deg, #0b1210 0%, #183126 58%, #225139 100%)'
                        : 'linear-gradient(128deg, #122033 0%, #1d3b32 58%, #2f6146 100%)');
                const contentTransform = 'translate3d(' + (pointer.x * 8) + 'px,' + (pointer.y * 6) + 'px,0)';
                const glowTransform = 'translate3d(' + (pointer.x * 14) + 'px,' + (pointer.y * 10) + 'px,0)';

                return e('section', {
                    className: 'atlas-hero-shell' + (show ? ' atlas-hero-show' : ''),
                    style: { backgroundImage: shellBg },
                    onMouseMove: (event) => {
                        const rect = event.currentTarget.getBoundingClientRect();
                        const relX = (event.clientX - rect.left) / Math.max(rect.width, 1);
                        const relY = (event.clientY - rect.top) / Math.max(rect.height, 1);
                        setPointer({
                            x: Math.max(-1, Math.min(1, (relX - 0.5) * 2)),
                            y: Math.max(-1, Math.min(1, (relY - 0.5) * 2))
                        });
                    },
                    onMouseLeave: () => setPointer({x: 0, y: 0})
                }, [
                    e('style', { key: 'hero-style' }, `
                        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');
                        * { box-sizing: border-box; }
                        body { margin: 0; }
                        .atlas-hero-shell {
                            position: relative;
                            overflow: hidden;
                            border-radius: 22px;
                            min-height: 196px;
                            padding: 1rem 1.15rem;
                            border: 1px solid rgba(173, 220, 194, 0.3);
                            box-shadow: 0 18px 44px rgba(8, 16, 31, 0.34);
                            background-size: 160% 160%;
                            background-position: center;
                            animation: atlasDrift 18s ease-in-out infinite alternate;
                            opacity: 0;
                            transform: translateY(8px);
                            transition: opacity 420ms ease, transform 460ms cubic-bezier(0.22,1,0.36,1);
                            font-family: 'Inter', 'Segoe UI', sans-serif;
                            will-change: transform, opacity;
                        }
                        .atlas-hero-show { opacity: 1; transform: translateY(0); }
                        .atlas-hero-top {
                            display: flex;
                            align-items: center;
                            justify-content: space-between;
                            gap: 0.6rem;
                            margin-bottom: 0.55rem;
                        }
                        .atlas-hero-badge {
                            display: inline-flex;
                            align-items: center;
                            height: 25px;
                            padding: 0 0.72rem;
                            border-radius: 999px;
                            border: 1px solid rgba(171, 224, 194, 0.46);
                            background: rgba(12, 22, 43, 0.42);
                            color: rgba(224, 242, 255, 0.95);
                            font-size: 0.69rem;
                            font-weight: 700;
                            letter-spacing: 0.08em;
                            text-transform: uppercase;
                        }
                        .atlas-context-label {
                            display: inline-flex;
                            align-items: center;
                            gap: 0.35rem;
                            color: rgba(214, 236, 255, 0.9);
                            font-size: 0.73rem;
                            font-weight: 600;
                        }
                        .atlas-context-dot {
                            width: 8px;
                            height: 8px;
                            border-radius: 999px;
                            background: #4ade80;
                            box-shadow: 0 0 0 rgba(74,222,128,0.42);
                            animation: atlasPulse 1.8s ease-out infinite;
                        }
                        .atlas-hero-title {
                            margin: 0;
                            color: #f8fbff;
                            font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
                            font-size: clamp(1.45rem, 3vw, 2rem);
                            font-weight: 800;
                            line-height: 1.08;
                            letter-spacing: -0.02em;
                        }
                        .atlas-hero-sub {
                            margin: 0.42rem 0 0;
                            max-width: 46rem;
                            color: rgba(225, 243, 255, 0.92);
                            font-size: 0.9rem;
                            line-height: 1.55;
                            font-weight: 500;
                        }
                        .atlas-highlight {
                            margin-top: 0.7rem;
                            border-radius: 12px;
                            border: 1px solid rgba(170, 222, 190, 0.42);
                            background: rgba(8, 23, 44, 0.36);
                            padding: 0.5rem 0.64rem;
                            color: rgba(236, 247, 255, 0.96);
                            font-size: 0.82rem;
                            font-weight: 600;
                            backdrop-filter: blur(3px);
                            animation: atlasContextFade 320ms ease;
                        }
                        .atlas-chip-row {
                            display: flex;
                            flex-wrap: wrap;
                            gap: 0.4rem;
                            margin-top: 0.62rem;
                        }
                        .atlas-chip {
                            display: inline-flex;
                            align-items: center;
                            padding: 0.3rem 0.65rem;
                            border-radius: 999px;
                            border: 1px solid rgba(173, 220, 194, 0.38);
                            background: rgba(12, 28, 49, 0.33);
                            color: rgba(232, 246, 255, 0.95);
                            font-size: 0.72rem;
                            font-weight: 600;
                        }
                        .atlas-chip-active {
                            border-color: rgba(158, 247, 183, 0.72);
                            background: rgba(22, 72, 45, 0.52);
                            color: #f8fdff;
                            transform: translateY(-1px);
                        }
                        .atlas-hero-glow {
                            position: absolute;
                            inset: auto -10% -36% auto;
                            width: 250px;
                            height: 250px;
                            border-radius: 999px;
                            background: radial-gradient(circle, rgba(74, 222, 128, 0.24) 0%, rgba(74, 222, 128, 0) 70%);
                            pointer-events: none;
                            z-index: 1;
                            transition: transform 280ms ease;
                        }
                        .atlas-progress {
                            margin-top: 0.52rem;
                            width: 100%;
                            height: 3px;
                            border-radius: 999px;
                            background: rgba(180, 214, 243, 0.22);
                            overflow: hidden;
                        }
                        .atlas-progress > span {
                            display: block;
                            height: 100%;
                            width: 100%;
                            transform-origin: left;
                            background: linear-gradient(90deg, rgba(134,239,172,0.94), rgba(52,211,153,0.92));
                            animation: atlasProgress 2.7s linear forwards;
                        }
                        .atlas-content {
                            position: relative;
                            z-index: 3;
                            transition: transform 280ms ease;
                        }
                        @keyframes atlasPulse {
                            0% { box-shadow: 0 0 0 0 rgba(74,222,128,0.42); }
                            100% { box-shadow: 0 0 0 8px rgba(74,222,128,0); }
                        }
                        @keyframes atlasProgress {
                            from { transform: scaleX(0); opacity: 0.9; }
                            to { transform: scaleX(1); opacity: 1; }
                        }
                        @keyframes atlasContextFade {
                            from { opacity: 0; transform: translateY(4px); }
                            to { opacity: 1; transform: translateY(0); }
                        }
                        @keyframes atlasDrift {
                            0% { background-position: 18% 35%; }
                            100% { background-position: 82% 64%; }
                        }
                        @media (max-width: 840px) {
                            .atlas-hero-shell { padding: 0.95rem; }
                            .atlas-hero-title { font-size: clamp(1.25rem, 4.8vw, 1.65rem); }
                            .atlas-hero-sub { font-size: 0.85rem; }
                        }
                    `),
                    e('div', { key: 'glow', className: 'atlas-hero-glow', style: { transform: glowTransform } }),
                    e('div', { key: 'content', className: 'atlas-content', style: { transform: contentTransform } }, [
                        e('div', { key: 'top', className: 'atlas-hero-top' }, [
                            e('span', { key: 'badge', className: 'atlas-hero-badge' }, heroData.badge)
                        ]),
                        e('h2', { key: 'title', className: 'atlas-hero-title' }, heroData.title),
                        e('p', { key: 'subtitle', className: 'atlas-hero-sub' }, heroData.subtitle),
                        e('div', { key: 'highlight-' + activeIdx, className: 'atlas-highlight' }, safeChips[activeIdx]),
                        e('div', { key: 'progress', className: 'atlas-progress' }, [
                            e('span', { key: 'progress-fill-' + activeIdx })
                        ]),
                        e('div', { key: 'chips', className: 'atlas-chip-row' },
                            safeChips.map((chip, idx) =>
                                e('span', {
                                    key: 'chip-' + idx,
                                    className: 'atlas-chip' + (idx === activeIdx ? ' atlas-chip-active' : '')
                                }, chip)
                            )
                        )
                    ])
                ]);
            }

            ReactDOM.createRoot(document.getElementById('__ID__')).render(e(Hero));
        </script>
    """
    html_block = html_block.replace("__ID__", container_id).replace("__HERO_DATA__", hero_data_js)
    components.html(html_block, height=height)


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

    if st.session_state.last_clicked_coords and st.session_state.show_add_location:
        pin_lat, pin_lng = st.session_state.last_clicked_coords
        folium.CircleMarker(
            location=[pin_lat, pin_lng],
            radius=12,
            color="#b45309",
            fill=True,
            fill_color="#f59e0b",
            fill_opacity=0.95,
            weight=3,
            tooltip="New location pin",
            popup=f"New location pin: {pin_lat:.6f}, {pin_lng:.6f}",
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
        is_dark=st.session_state.get("ui_theme") == "dark",
        height=236,
    )

    if show_welcome_transition:
        # Hold the welcome hero briefly, then move to the default map hero.
        time.sleep(1.0)
        st.session_state.just_signed_in = False
        st.session_state.just_signed_in_until = 0.0
        st.rerun()

    if st.session_state.selected_location_id:
        map_col, inspector_col = st.columns([2.5, 1], gap="large")
        with map_col:
            render_map(locations_df)
        with inspector_col:
            render_location_details()
    else:
        render_map(locations_df)
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
        is_dark=st.session_state.get("ui_theme") == "dark",
        height=226,
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
    top_left, _ = st.columns([1, 5])
    with top_left:
        render_theme_toggle("theme_toggle_auth")

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
            is_dark=st.session_state.get("ui_theme") == "dark",
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
                email = st.text_input("Email", key="login_email")
                password = st.text_input(
                    "Password",
                    type="password",
                    key="login_password",
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
                name = st.text_input("Name", key="reg_name")
                email = st.text_input("Email", key="reg_email")
                password = st.text_input(
                    "Password",
                    type="password",
                    key="reg_password",
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
        category_name = st.text_input("Category name")
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

    pin_is_set = bool(st.session_state.last_clicked_coords)
    if pin_is_set:
        pin_lat, pin_lng = st.session_state.last_clicked_coords
        add_location_desc = f"Pinned coordinate: {pin_lat:.6f}, {pin_lng:.6f}"
    else:
        add_location_desc = "Pinned coordinate: click on map to select"

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

    if st.session_state.last_clicked_coords:
        pin_lat, pin_lng = st.session_state.last_clicked_coords
    else:
        pin_lat, pin_lng = (None, None)

    if not st.session_state.last_clicked_coords:
        st.info("Click anywhere on the map to drop a pin, then save the location.")

    clear_pin_col, pin_hint_col = st.columns([1, 2])
    with clear_pin_col:
        if st.button("Clear pin", width="stretch", key="clear_add_location_pin"):
            st.session_state.last_clicked_coords = None
            st.rerun()
    with pin_hint_col:
        st.caption("Map click sets the exact coordinate for this new location.")

    with st.form("add_location_form"):
        name = st.text_input("Location name")
        category_id = st.selectbox(
            "Category",
            categories["category_id"].tolist(),
            format_func=lambda cid: f"{cid} - {categories.loc[categories['category_id'] == cid, 'category_name'].iloc[0]}",
        )
        address = st.text_input("Address")
        description = st.text_area("Description")
        coord_col1, coord_col2 = st.columns(2)
        with coord_col1:
            st.text_input(
                "Latitude (from map pin)",
                value=f"{pin_lat:.6f}" if pin_lat is not None else "Click map to set latitude",
                disabled=True,
            )
        with coord_col2:
            st.text_input(
                "Longitude (from map pin)",
                value=f"{pin_lng:.6f}" if pin_lng is not None else "Click map to set longitude",
                disabled=True,
            )
        submitted = st.form_submit_button("Save location", type="primary", width="stretch")

    if submitted:
        if not st.session_state.last_clicked_coords:
            st.error("Pick a point on the map first, then save location.")
            return

        latitude, longitude = st.session_state.last_clicked_coords
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
            st.session_state.last_clicked_coords = None
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

    review_log_df = get_review_logs()
    deleted_log_df = get_deleted_location_audit()

    render_react_hero(
        "System logs and audit trail",
        "Monitor trigger output and delete archives from one clean workspace.",
        [
            f"Review events: {len(review_log_df.index)}",
            f"Delete events: {len(deleted_log_df.index)}",
            f"Data version: {st.session_state.data_version}",
        ],
        badge="Operational insights",
        is_dark=st.session_state.get("ui_theme") == "dark",
        height=232,
    )

    refresh_col, ts_col = st.columns([1, 4])
    with refresh_col:
        if st.button("Refresh all data", key="analytics_refresh", type="primary", width="stretch"):
            st.session_state.data_version += 1
            st.rerun()
    with ts_col:
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        st.markdown(
            f'<p style="color:var(--text-soft);margin:0.75rem 0 0 0.5rem;font-size:0.88rem;">'
            f'Last refreshed at <strong>{now_str}</strong> | data version <strong>{st.session_state.data_version}</strong></p>',
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
                    <p class="surface-copy">Trigger-backed rating change records.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Refresh logs", key="refresh_review_logs_btn", width="stretch"):
            st.rerun()
        safe_df(review_log_df, "No trigger log entries yet. Add or edit a review to generate log rows.")

    with delete_logs_tab:
        st.markdown(
            """
            <div class="flat-section">
                <div class="surface-head">
                    <div class="panel-kicker">Logs</div>
                    <div class="surface-title">Deleted location archive log</div>
                    <p class="surface-copy">Records generated from archive-and-delete operations.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Refresh logs", key="refresh_deleted_logs_btn", width="stretch"):
            st.rerun()
        safe_df(deleted_log_df, "No locations have been deleted yet.")



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
        "ui_theme": "light",
        # Incremented after every write so analytics always shows fresh data.
        "data_version": 0,
        "query_log_reset_done": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_db()
init_state()
apply_theme_mode(st.session_state.ui_theme)
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
        render_theme_toggle("theme_toggle_nav")

        workspace_state = "Signed in" if st.session_state.logged_in_user else "Guest mode"
        st.markdown(
            f"""
            <p class="workspace-nav-kicker">Manipal Atlas</p>
            <p class="workspace-nav-title">Map control center</p>
            <p class="workspace-nav-copy">Use this panel to navigate views, filter places, and launch actions.</p>
            <div class="workspace-chip-row">
                <span class="workspace-chip">{esc(workspace_state)}</span>
                <span class="workspace-chip">Page: {esc(st.session_state.current_page.title())}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

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
            "Highly rated",
            "Highly reviewed",
            "Most favourited",
            "Category leaders",
            "Saved and reviewed",
            "Flagged locations",
        ]
        default_preset = st.session_state.get("selected_preset", "None")
        preset_index = preset_options.index(default_preset) if default_preset in preset_options else 0
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
            if st.session_state.show_add_location:
                st.session_state.current_page = "map"
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
        elif st.session_state.selected_preset == "Flagged locations":
            preset_df = get_flagged_locations()
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


