"""Map-first Streamlit app for the Manipal Location & Review Management System."""

from __future__ import annotations

from datetime import date
import hashlib
import html
import os
import secrets

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from db import init_db
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
    get_images_for_location,
    get_location_details,
    get_location_status,
    get_locations,
    get_review_logs,
    get_reviews_for_location,
    get_user_by_email,
    location_rating_bands,
    locations_above_all_in_category,
    locations_union_high_activity,
    most_reviewed_locations,
    parameterized_category_cursor,
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
    @import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400;14..32,500;14..32,600;14..32,700&display=swap');

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
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: var(--text);
        font-size: 14px;
        line-height: 1.5;
        -webkit-font-smoothing: antialiased;
    }
    section.main > div.block-container {
        padding-top: 1.25rem;
        padding-bottom: 2rem;
        max-width: 1480px;
    }
    #MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; }

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
        font-family: 'Inter', sans-serif;
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
        font-family: 'Inter', sans-serif;
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
        font-family: 'Inter', sans-serif;
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
        font-family: 'Inter', sans-serif;
        font-size: 0.84rem;
        font-weight: 600;
        min-height: 2.35rem;
        box-shadow: var(--shadow-sm);
        transition: background 0.1s, border-color 0.1s;
        letter-spacing: 0;
    }
    div[data-testid="stButton"] > button:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {
        background: var(--surface-alt);
        border-color: var(--accent);
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
        font-family: 'Inter', sans-serif !important;
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
        font-family: 'Inter', sans-serif !important;
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
    st.markdown(
        """
        <div class="flat-section">
            <div class="surface-head">
                <div class="panel-kicker">Live map</div>
                <div class="surface-title">Campus and town map</div>
                <p class="surface-copy">Select a marker to inspect the location, or click anywhere on the map to capture coordinates for a new place.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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

    result = st_folium(fmap, width=None, height=620, key="map_view")

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
    rating_df = average_rating_per_location()
    total_reviews = int(rating_df["review_count"].fillna(0).sum()) if not rating_df.empty else 0
    best_avg = (
        f"{float(rating_df['avg_rating'].dropna().max()):.1f}"
        if not rating_df.empty and not rating_df["avg_rating"].dropna().empty
        else "N/A"
    )
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

    render_page_banner(
        "Map workspace",
        "A cleaner front end for exploring places, managing locations, and reviewing spots around Manipal without leaving the map flow.",
        kicker="Manipal Atlas",
        chips=[
            f"Filter: {current_filter}",
            f"Selection: {selected_name}",
            "Click map to stage coordinates",
        ],
    )
    render_metric_row(
        [
            ("Locations", str(len(all_locations_df)), "total mapped places"),
            ("Visible", str(len(locations_df)), "currently in view"),
            ("Categories", str(len(categories_df)), "organized location types"),
            ("Best rating", best_avg, f"{total_reviews} reviews captured"),
        ]
    )

    map_col, inspector_col = st.columns([1.7, 1], gap="large")
    with map_col:
        render_map(locations_df)
    with inspector_col:
        render_location_details()


def render_auth_page() -> None:
    render_page_banner(
        "Account access",
        "Sign in to contribute to the map or register a new account to manage reviews, favorites, and place details from one clean workspace.",
        kicker="Manipal Atlas",
        chips=["Dedicated auth page", "Map contributions", "Review management"],
    )

    if st.session_state.logged_in_user:
        st.success(f"You are already signed in as {st.session_state.logged_in_user['name']}.")
        action_col1, action_col2 = st.columns(2)
        with action_col1:
            if st.button("Go to map", type="primary", width="stretch", key="auth_go_map"):
                st.session_state.current_page = "map"
                st.rerun()
        with action_col2:
            if st.button("Sign out", width="stretch", key="auth_sign_out"):
                st.session_state.logged_in_user = None
                st.success("Signed out.")
                st.rerun()
        return

    info_col, form_col = st.columns([1.05, 1], gap="large")

    with info_col:
        render_section_header(
            "Your map account",
            kicker="Why sign in",
            description="Accounts keep editing tools separate from the public map so the main workspace stays focused while contribution tools stay one click away.",
        )
        st.markdown(
            """
            <ul class="auth-feature-list">
                <li>Add new places without leaving the map workflow.</li>
                <li>Write and manage reviews with your own account history.</li>
                <li>Upload location photos and save favorite spots.</li>
            </ul>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Back to map", width="stretch", key="auth_back"):
            st.session_state.current_page = "map"
            st.rerun()
    with form_col:
        sign_in_tab, register_tab = st.tabs(["Sign in", "Register"])

        with sign_in_tab:
            render_section_header(
                "Return to your account",
                kicker="Sign in",
                description="Use your email and password to continue editing locations and reviews.",
            )
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
                    st.success("Signed in successfully.")
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

        with register_tab:
            render_section_header(
                "Create a new account",
                kicker="Register",
                description="Set up an account to add places, upload photos, and participate in reviews.",
            )
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
def render_add_category_card() -> None:
    if not st.session_state.show_add_category:
        return

    render_section_header(
        "Add new category",
        kicker="Create",
        description="Create a natural location type such as cafe, hostel, academic block, sports facility, or service point.",
        state_key="show_add_category",
    )
    with st.form("add_category_form", clear_on_submit=True):
        category_name = st.text_input("Category name", placeholder="e.g. Cafe, Hostel, Academic Block")
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

    render_section_header(
        "Add new location",
        kicker="Create",
        description="Add a place with a clear name, category, address, and map coordinates. Clicking the map prefills latitude and longitude.",
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
            add_location(name, int(category_id), address, description, float(latitude), float(longitude))
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
                <p class="empty-copy">The right panel becomes a location inspector with overview details, gallery uploads, and review controls as soon as you choose a marker.</p>
                <span class="soft-chip">Tip: click the map first, then use Add New Location to prefill coordinates.</span>
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
    category_name = esc(loc["category_name"], "Uncategorized")
    address_text = esc(loc["address"], "Address not added yet.")
    description_text = esc(loc["description"], "No description has been provided for this location yet.")
    loc_name = esc(loc["name"], "Unknown location")
    latitude = float(loc["latitude"]) if pd.notna(loc["latitude"]) else 0.0
    longitude = float(loc["longitude"]) if pd.notna(loc["longitude"]) else 0.0

    st.markdown(
        f"""
        <div class="flat-section">
            <div class="surface-head">
                <div class="panel-kicker">Selected place</div>
                <h3 class="inspector-title">{loc_name}</h3>
                <p class="muted-copy">{description_text}</p>
            </div>
            <div class="hero-meta">
                <span class="soft-chip">{category_name}</span>
                <span class="soft-chip">Avg rating {esc(avg_text)}</span>
                <span class="soft-chip">{review_total} reviews</span>
                <span class="soft-chip">ID {loc_id}</span>
            </div>
            <div class="inspector-meta">
                <div class="meta-block">
                    <div class="meta-label">Address</div>
                    <div class="meta-value">{address_text}</div>
                </div>
                <div class="meta-block">
                    <div class="meta-label">Coordinates</div>
                    <div class="meta-value">{latitude:.5f}, {longitude:.5f}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    overview_tab, gallery_tab, reviews_tab = st.tabs(["Overview", "Gallery", "Reviews"])

    with overview_tab:
        st.markdown('<p class="section-label">Quick actions</p>', unsafe_allow_html=True)
        action_col1, action_col2 = st.columns(2)
        with action_col1:
            if st.button("Save favorite", key="save_fav_btn", width="stretch"):
                if require_login("add to favorites"):
                    try:
                        add_favorite(int(st.session_state.logged_in_user["user_id"]), loc_id)
                        st.success("Added to favorites.")
                    except Exception as ex:
                        st.error(f"Could not add favorite: {ex}")
        with action_col2:
            if st.session_state.logged_in_user:
                if st.button("Manage location", key="toggle_manage_loc", width="stretch"):
                    st.session_state.show_manage_loc = not st.session_state.get("show_manage_loc", False)

        st.markdown('<hr class="panel-divider">', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="meta-block">
                <div class="meta-label">About this location</div>
                <div class="meta-value">Use this inspector to update address details, add it to favorites, upload photos, or manage reviews without losing map context.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

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
                        sub_upd = st.form_submit_button("Save changes", type="primary")

                    if sub_upd:
                        update_location(loc_id, u_name, int(u_cat), u_addr, u_desc)
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
            if upl_file is not None and st.button("Save uploaded image", key="save_uploaded_image", width="stretch"):
                filepath = os.path.join(UPLOAD_DIR, upl_file.name)
                with open(filepath, "wb") as file_obj:
                    file_obj.write(upl_file.getbuffer())
                add_image(loc_id, filepath)
                st.success(f"Image {upl_file.name} uploaded successfully.")
                st.session_state.data_version += 1
                st.rerun()
        else:
            st.info("Sign in to upload photos for this location.")

        images_df = get_images_for_location(loc_id)
        if not images_df.empty:
            img_cols = st.columns(min(len(images_df), 2))
            for idx, row in images_df.iterrows():
                with img_cols[idx % max(len(img_cols), 1)]:
                    st.image(row["image_url"], width="stretch", caption=f"Image {row['image_id']}")
        else:
            st.info("No images uploaded yet.")

    with reviews_tab:
        st.markdown('<p class="section-label">Community reviews</p>', unsafe_allow_html=True)
        if st.button("Write review", key="open_review_btn", type="primary", width="stretch"):
            if require_login("add a review"):
                st.session_state.show_add_review_for_selected = True

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
        "Analytics",
        "Live insights into your Manipal Map data — leaderboards, query deep-dives, set operations, runtime demos, and trigger audit logs all in one place.",
        kicker="Analytics & SQL Explorer",
        chips=["Live data", "Interactive demos", "Trigger logs", "Cursor routines"],
    )

    # ── Refresh bar ────────────────────────────────────────────────────────
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

    # ── Live summary metrics (always fresh — no cache) ─────────────────────
    _ratings_df = average_rating_per_location()
    _all_locs   = get_locations()
    _total_reviews = int(_ratings_df["review_count"].fillna(0).sum()) if not _ratings_df.empty else 0
    _best_avg = (
        f"{float(_ratings_df['avg_rating'].dropna().max()):.2f}"
        if not _ratings_df.empty and _ratings_df["avg_rating"].dropna().shape[0] > 0
        else "N/A"
    )
    _review_logs_df    = get_review_logs()
    _deleted_audit_df  = get_deleted_location_audit()

    render_metric_row(
        [
            ("Locations", str(len(_all_locs)), "in the database"),
            ("Total reviews", str(_total_reviews), "across all locations"),
            ("Best avg rating", _best_avg, "highest-rated location"),
            ("Trigger log entries", str(len(_review_logs_df)), f"+ {len(_deleted_audit_df)} archived deletes"),
        ]
    )

    st.markdown('<hr class="panel-divider">', unsafe_allow_html=True)

    # ── Sub-tabs ───────────────────────────────────────────────────────────
    overview_tab, leaderboard_tab, setops_tab, runtime_tab, logs_tab = st.tabs(
        ["📊 Overview", "🏆 Leaderboards", "⚙️ Set Operations", "🔄 Runtime Demos", "📋 Trigger Logs"]
    )

    # ── Overview ──────────────────────────────────────────────────────────
    with overview_tab:
        st.markdown(
            """
            <div class="flat-section">
                <div class="surface-head">
                    <div class="panel-kicker">Live query results</div>
                    <div class="surface-title">Location ratings overview</div>
                    <p class="surface-copy">Average rating per location, ordered by score. Null-rated locations (no reviews yet) appear at the bottom.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        safe_df(average_rating_per_location(), "No locations found.")

        st.markdown('<hr class="panel-divider">', unsafe_allow_html=True)

        cat_col, band_col = st.columns(2, gap="large")
        with cat_col:
            st.markdown(
                """
                <div class="flat-section">
                    <div class="surface-head">
                        <div class="panel-kicker">View query</div>
                        <div class="surface-title">Category activity summary</div>
                        <p class="surface-copy">Powered by the <code>category_activity_summary</code> view — counts locations, reviewed locations, and computes an intensity band via the <code>rating_band()</code> UDF.</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            safe_df(get_category_activity_summary(), "No categories yet.")
        with band_col:
            st.markdown(
                """
                <div class="flat-section">
                    <div class="surface-head">
                        <div class="panel-kicker">UDF + view</div>
                        <div class="surface-title">Rating band classification</div>
                        <p class="surface-copy">Every location is assigned Excellent / Strong / Average / Needs Attention / Unrated using SQLite's registered <code>rating_band()</code> scalar function.</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            safe_df(location_rating_bands(), "No locations found.")

    # ── Leaderboards ──────────────────────────────────────────────────────
    with leaderboard_tab:
        top_col, reviewed_col = st.columns(2, gap="large")
        with top_col:
            min_rev = st.number_input("Minimum reviews threshold", min_value=1, max_value=20, value=1, step=1, key="leaderboard_min_reviews")
            st.markdown(
                """
                <div class="flat-section">
                    <div class="surface-head">
                        <div class="panel-kicker">HAVING filter</div>
                        <div class="surface-title">Top-rated locations</div>
                        <p class="surface-copy">Grouped by location with a HAVING clause filtering out locations below the review threshold. Ordered by average rating descending.</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            safe_df(top_rated_locations(min_reviews=int(min_rev)), "No locations meet this threshold.")
        with reviewed_col:
            st.markdown(
                """
                <div class="flat-section">
                    <div class="surface-head">
                        <div class="panel-kicker">CTE query</div>
                        <div class="surface-title">Most reviewed locations</div>
                        <p class="surface-copy">Uses a <code>WITH</code> clause (CTE) to pre-aggregate review counts before joining back to Locations. Shows places with the most community engagement.</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            safe_df(most_reviewed_locations(), "No reviews yet.")

        st.markdown('<hr class="panel-divider">', unsafe_allow_html=True)

        user_col, five_star_col = st.columns(2, gap="large")
        with user_col:
            st.markdown(
                """
                <div class="flat-section">
                    <div class="surface-head">
                        <div class="panel-kicker">GROUP BY aggregation</div>
                        <div class="surface-title">Most active reviewers</div>
                        <p class="surface-copy">Users ranked by total review count. Identifies the most engaged community contributors.</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            safe_df(users_with_most_reviews(), "No reviewers yet.")
        with five_star_col:
            st.markdown(
                """
                <div class="flat-section">
                    <div class="surface-head">
                        <div class="panel-kicker">EXISTS subquery</div>
                        <div class="surface-title">Users with a five-star review</div>
                        <p class="surface-copy">Uses an EXISTS correlated subquery — returns users who have submitted at least one perfect rating.</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            safe_df(users_with_five_star_review(), "No five-star reviews found.")

        st.markdown('<hr class="panel-divider">', unsafe_allow_html=True)
        best_col, corr_col = st.columns(2, gap="large")
        with best_col:
            st.markdown(
                """
                <div class="flat-section">
                    <div class="surface-head">
                        <div class="panel-kicker">NOT EXISTS / peer comparison</div>
                        <div class="surface-title">Category leaders</div>
                        <p class="surface-copy">The top-rated location in each category — no peer within the same category has a higher or equal average. Uses a NOT EXISTS peer comparison.</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            safe_df(locations_above_all_in_category(), "No exclusive category leaders found.")
        with corr_col:
            st.markdown(
                """
                <div class="flat-section">
                    <div class="surface-head">
                        <div class="panel-kicker">Correlated subquery</div>
                        <div class="surface-title">Location vs category average</div>
                        <p class="surface-copy">Each row shows a location's own average beside its category's overall average. Computed with a correlated scalar subquery inside the SELECT list.</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            safe_df(best_per_category_correlated(), "No reviewed locations found.")

    # ── Set Operations ────────────────────────────────────────────────────
    with setops_tab:
        st.markdown(
            """
            <div class="flat-section">
                <div class="surface-head">
                    <div class="panel-kicker">Set algebra on live data</div>
                    <div class="surface-title">UNION · EXCEPT · INTERSECT</div>
                    <p class="surface-copy">Each result below is computed fresh from the database. Expand a section to see the live output.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("UNION — top-rated OR most-reviewed", expanded=True):
            st.caption("Locations surfaced either by high rating (≥ 4.0 avg) OR by high review count (≥ 2). A location can appear for both reasons.")
            safe_df(locations_union_high_activity(), "No noteworthy locations found.")

        with st.expander("EXCEPT — active but not top-rated", expanded=False):
            st.caption("Reviewed places that have at least one review but do NOT qualify as top-rated. Useful for spotting locations that need improvement.")
            safe_df(active_but_not_top_rated(), "All reviewed locations are also top rated.")

        with st.expander("INTERSECT — favorited AND reviewed", expanded=False):
            st.caption("Locations that appear in both the Favorites table and the Reviews table — places the community both saved and rated.")
            safe_df(common_favorites_and_reviewed(), "No locations appear in both favorites and reviews.")

        with st.expander("NOT EXISTS (relational division) — users who reviewed all categories", expanded=False):
            st.caption("Uses a NOT EXISTS / EXCEPT combination to find users who reviewed at least one location in every category that has been reviewed.")
            safe_df(users_who_reviewed_all_categories(), "No user has reviewed all categories yet.")

    # ── Runtime Demos ─────────────────────────────────────────────────────
    with runtime_tab:
        render_db_runtime_sections()

    # ── Trigger Logs ──────────────────────────────────────────────────────
    with logs_tab:
        st.markdown(
            """
            <div class="flat-section">
                <div class="surface-head">
                    <div class="panel-kicker">Automatic DB-side logging</div>
                    <div class="surface-title">Review audit log</div>
                    <p class="surface-copy">Every INSERT or rating UPDATE on the Reviews table is automatically captured by SQLite triggers <code>trg_log_review_insert</code> and <code>trg_log_review_update</code>. No Python code writes these rows — they are purely trigger-driven.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("↻  Refresh logs", key="refresh_logs_btn", width="stretch"):
            st.rerun()
        safe_df(get_review_logs(), "No trigger log entries yet. Add or edit a review to generate log rows.")

        st.markdown('<hr class="panel-divider">', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="flat-section">
                <div class="surface-head">
                    <div class="panel-kicker">BEFORE DELETE trigger</div>
                    <div class="surface-title">Deleted location archive</div>
                    <p class="surface-copy">When a location is deleted, the <code>trg_archive_location_delete</code> trigger fires BEFORE the row is removed, capturing the location's name and related-row counts into <code>DeletedLocationAudit</code>.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
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
        "current_page": "map",
        "selected_category_id": None,
        # Incremented after every write so analytics always shows fresh data.
        "data_version": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_db()
init_state()

if st.session_state.current_page == "auth":
    brand_col, status_col = st.columns([5, 2])
    with brand_col:
        st.markdown(
            """
            <section class="hero-banner">
                <div class="app-kicker">Manipal map platform</div>
                <p class="main-title">Manipal Atlas</p>
                <p class="title-support">A dedicated sign-in and registration space for the map platform.</p>
            </section>
            """,
            unsafe_allow_html=True,
        )
    with status_col:
        if st.session_state.logged_in_user:
            st.markdown('<span class="status-pill">Signed in</span>', unsafe_allow_html=True)
            st.markdown(
                f"<p class='status-text'>Working as {esc(st.session_state.logged_in_user['name'])}</p>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown('<span class="status-pill">Account page</span>', unsafe_allow_html=True)
            st.markdown("<p class='status-text'>Sign in or register to unlock edit controls.</p>", unsafe_allow_html=True)
    render_auth_page()
else:
    title_col, auth_col = st.columns([5, 2])
    with title_col:
        st.markdown(
            """
            <section class="hero-banner">
                <div class="app-kicker">Manipal map platform</div>
                <p class="main-title">Manipal Atlas</p>
                <p class="title-support">A map-first workspace for discovering locations, managing place details, and tracking community reviews around Manipal.</p>
            </section>
            """,
            unsafe_allow_html=True,
        )
    with auth_col:
        if st.session_state.logged_in_user:
            st.markdown('<span class="status-pill">Signed in</span>', unsafe_allow_html=True)
            st.markdown(
                f"<p class='status-text'>Working as {esc(st.session_state.logged_in_user['name'])}</p>",
                unsafe_allow_html=True,
            )
            if st.button("Sign out", icon=":material/logout:", width="stretch"):
                st.session_state.logged_in_user = None
                st.success("Signed out.")
                st.rerun()
        else:
            st.markdown('<span class="status-pill">Guest mode</span>', unsafe_allow_html=True)
            st.markdown("<p class='status-text'>Sign in to add places, reviews, favorites, and photos.</p>", unsafe_allow_html=True)
            if st.button("Sign in", icon=":material/login:", type="primary", width="stretch"):
                st.session_state.current_page = "auth"
                st.rerun()

    nav_col, content_col = st.columns([1.08, 3.92], gap="large")

    with nav_col:
        st.markdown('<div class="panel-kicker">Workspace</div>', unsafe_allow_html=True)
        st.markdown('<p class="nav-title">Navigation</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="nav-copy">Move between map exploration and the Analytics workspace for live query results, leaderboards, set operations, runtime demos, and trigger logs.</p>',
            unsafe_allow_html=True,
        )

        pages = [
            ("Map View", "map", ":material/map:"),
            ("Analytics", "analytics", ":material/query_stats:"),
        ]
        for label, page_key, icon in pages:
            if st.button(
                label,
                icon=icon,
                type="primary" if st.session_state.current_page == page_key else "secondary",
                width="stretch",
                key=f"nav_{page_key}",
            ):
                st.session_state.current_page = page_key

        st.markdown('<hr class="panel-divider">', unsafe_allow_html=True)
        st.markdown('<p class="nav-title">Filters</p>', unsafe_allow_html=True)

        categories_df = get_categories()
        options = ["All"]
        category_map: dict[str, int] = {}
        for _, row in categories_df.iterrows():
            label = f"{row['category_name']} (ID {int(row['category_id'])})"
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

        st.markdown('<hr class="panel-divider">', unsafe_allow_html=True)
        st.markdown('<p class="nav-title">Quick actions</p>', unsafe_allow_html=True)

        if st.button("Add new category", icon=":material/category:", width="stretch"):
            st.session_state.show_add_category = not st.session_state.show_add_category

        if st.button("Add new location", icon=":material/add_location_alt:", width="stretch"):
            st.session_state.show_add_location = not st.session_state.show_add_location

        if st.button("Load sample data", width="stretch"):
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

        if st.session_state.current_page == "analytics":
            render_analytics_page()
        else:
            all_locations_df = get_locations()
            locations_df = search_locations_by_category(st.session_state.selected_category_id)
            render_map_page(locations_df, all_locations_df, categories_df)
