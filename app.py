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
    @import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap');

    :root {
        --bg-main: #eef2ee;
        --bg-panel: rgba(255, 255, 255, 0.86);
        --line-soft: rgba(27, 56, 45, 0.12);
        --text-main: #10281f;
        --text-soft: #5d6f67;
        --accent: #1f6a52;
        --accent-strong: #103b2f;
        --shadow-soft: 0 20px 50px rgba(17, 31, 25, 0.08);
    }
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(64, 125, 99, 0.18), transparent 24%),
            radial-gradient(circle at top right, rgba(22, 73, 57, 0.14), transparent 22%),
            linear-gradient(180deg, #f8fbf9 0%, var(--bg-main) 100%);
        color: var(--text-main);
        font-family: "Instrument Sans", sans-serif;
    }
    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        background-image:
            linear-gradient(rgba(16, 40, 31, 0.035) 1px, transparent 1px),
            linear-gradient(90deg, rgba(16, 40, 31, 0.035) 1px, transparent 1px);
        background-size: 32px 32px;
        opacity: 0.32;
        pointer-events: none;
        z-index: 0;
    }
    section.main > div.block-container {
        padding-top: 1.6rem;
        padding-bottom: 2rem;
        max-width: 1500px;
        position: relative;
        z-index: 1;
    }
    #MainMenu,
    footer,
    header[data-testid="stHeader"] {
        visibility: hidden;
    }
    .hero-banner,
    .review-shell {
        border: 1px solid var(--line-soft);
        background: var(--bg-panel);
        box-shadow: var(--shadow-soft);
        backdrop-filter: blur(20px);
    }
    .app-kicker,
    .panel-kicker {
        text-transform: uppercase;
        letter-spacing: 0.18em;
        font-size: 0.72rem;
        font-weight: 700;
        color: var(--accent);
        margin-bottom: 0.5rem;
    }
    .main-title {
        font-family: "Space Grotesk", sans-serif;
        font-size: 2.35rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.04em;
        color: var(--text-main);
    }
    .title-support {
        max-width: 40rem;
        color: var(--text-soft);
        margin-top: 0.45rem;
        margin-bottom: 0;
        line-height: 1.55;
    }
    .status-text {
        color: var(--text-soft);
        text-align: right;
        margin: 0.45rem 0 0;
        font-size: 0.95rem;
    }
    .status-pill {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 999px;
        padding: 0.5rem 0.9rem;
        border: 1px solid rgba(31, 106, 82, 0.18);
        background: rgba(255, 255, 255, 0.84);
        color: var(--accent-strong);
        font-size: 0.82rem;
        font-weight: 700;
    }
    .nav-title {
        font-family: "Space Grotesk", sans-serif;
        font-size: 1.15rem;
        margin: 0 0 0.35rem;
        color: var(--text-main);
    }
    .nav-copy {
        color: var(--text-soft);
        font-size: 0.95rem;
        line-height: 1.5;
        margin-bottom: 1.1rem;
    }
    .hero-banner {
        border-radius: 24px;
        padding: 1.05rem 1.15rem;
        margin-bottom: 1rem;
    }
    .hero-banner {
        background:
            linear-gradient(135deg, rgba(255, 255, 255, 0.94) 0%, rgba(236, 244, 239, 0.9) 100%);
    }
    .hero-title,
    .panel-title {
        font-family: "Space Grotesk", sans-serif;
        font-size: 1.55rem;
        margin: 0;
        color: var(--text-main);
        letter-spacing: -0.03em;
    }
    .hero-copy,
    .panel-copy,
    .muted-copy {
        color: var(--text-soft);
        line-height: 1.55;
        margin-top: 0.45rem;
    }
    .hero-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
        margin-top: 0.9rem;
    }
    .soft-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        border-radius: 999px;
        border: 1px solid rgba(31, 106, 82, 0.14);
        background: rgba(255, 255, 255, 0.84);
        padding: 0.38rem 0.72rem;
        color: var(--accent-strong);
        font-size: 0.82rem;
        font-weight: 600;
    }
    .metric-shell {
        border-radius: 22px;
        border: 1px solid var(--line-soft);
        background: rgba(255, 255, 255, 0.76);
        padding: 1rem;
        box-shadow: 0 12px 28px rgba(17, 31, 25, 0.05);
        margin-bottom: 1rem;
    }
    .metric-label {
        color: var(--text-soft);
        text-transform: uppercase;
        letter-spacing: 0.16em;
        font-size: 0.72rem;
        font-weight: 700;
        margin-bottom: 0.45rem;
    }
    .metric-value {
        font-family: "Space Grotesk", sans-serif;
        font-size: 2rem;
        line-height: 1;
        color: var(--text-main);
        margin: 0;
    }
    .metric-detail {
        color: var(--text-soft);
        margin-top: 0.4rem;
        margin-bottom: 0;
        font-size: 0.92rem;
    }
    .map-caption,
    .section-label {
        color: var(--text-soft);
        font-size: 0.9rem;
        margin-bottom: 0.7rem;
    }
    .inspector-title {
        font-family: "Space Grotesk", sans-serif;
        font-size: 1.65rem;
        margin: 0.15rem 0 0;
        color: var(--text-main);
    }
    .inspector-meta {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.75rem;
        margin-top: 1rem;
    }
    .meta-block {
        border-radius: 18px;
        padding: 0.85rem 0.95rem;
        background: rgba(245, 249, 246, 0.92);
        border: 1px solid rgba(27, 56, 45, 0.08);
    }
    .meta-label {
        color: var(--text-soft);
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        margin-bottom: 0.35rem;
    }
    .meta-value {
        color: var(--text-main);
        font-weight: 700;
        line-height: 1.45;
    }
    .empty-shell {
        border-radius: 24px;
        padding: 1.4rem 1.2rem;
        border: 1px dashed rgba(27, 56, 45, 0.16);
        background: rgba(255, 255, 255, 0.52);
    }
    .empty-title {
        font-family: "Space Grotesk", sans-serif;
        color: var(--text-main);
        font-size: 1.3rem;
        margin-bottom: 0.45rem;
    }
    .empty-copy {
        color: var(--text-soft);
        line-height: 1.6;
        margin-bottom: 0.9rem;
    }
    .review-shell {
        border-radius: 20px;
        padding: 0.9rem 1rem;
        margin-bottom: 0.85rem;
    }
    .review-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.7rem;
        margin-bottom: 0.35rem;
    }
    .review-author {
        color: var(--text-main);
        font-weight: 700;
    }
    .review-date {
        color: var(--text-soft);
        font-size: 0.9rem;
    }
    .review-comment {
        color: var(--text-main);
        margin: 0.35rem 0 0;
        line-height: 1.55;
    }
    .panel-divider {
        height: 1px;
        border: 0;
        background: rgba(27, 56, 45, 0.08);
        margin: 1rem 0;
    }
    .flat-section {
        margin-bottom: 1.1rem;
    }
    .surface-head {
        margin-bottom: 0.9rem;
    }
    .surface-title {
        font-family: "Space Grotesk", sans-serif;
        font-size: 1.2rem;
        margin: 0;
        color: var(--text-main);
    }
    .surface-copy {
        color: var(--text-soft);
        line-height: 1.55;
        margin: 0.35rem 0 0;
    }
    .auth-hero {
        max-width: 44rem;
        margin: 0 auto 1.5rem;
        text-align: center;
    }
    .auth-title {
        font-family: "Space Grotesk", sans-serif;
        font-size: 2.2rem;
        line-height: 1.05;
        margin: 0;
        color: var(--text-main);
    }
    .auth-copy {
        color: var(--text-soft);
        max-width: 34rem;
        margin: 0.8rem auto 0;
        line-height: 1.6;
    }
    .auth-feature-list {
        margin: 1rem 0 0;
        padding-left: 1rem;
        color: var(--text-soft);
        line-height: 1.7;
    }
    .auth-feature-list li {
        margin-bottom: 0.45rem;
    }
    .auth-panel {
        padding: 1.2rem 1.1rem;
        border: 1px solid rgba(27, 56, 45, 0.1);
        border-radius: 22px;
        background: rgba(255, 255, 255, 0.66);
        box-shadow: 0 18px 40px rgba(17, 31, 25, 0.06);
        min-height: 100%;
    }
    .auth-panel-title {
        font-family: "Space Grotesk", sans-serif;
        font-size: 1.35rem;
        margin: 0;
        color: var(--text-main);
    }
    .auth-panel-copy {
        color: var(--text-soft);
        margin: 0.45rem 0 1rem;
        line-height: 1.55;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.78);
        border: 1px solid rgba(27, 56, 45, 0.1);
        border-radius: 999px;
        padding: 0.5rem 0.9rem;
        color: var(--text-soft);
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--accent-strong) 0%, var(--accent) 100%);
        color: #ffffff !important;
        border-color: transparent;
    }
    .stExpander {
        border: 1px solid rgba(27, 56, 45, 0.1) !important;
        border-radius: 18px !important;
        background: rgba(255, 255, 255, 0.74) !important;
    }
    .stAlert {
        border-radius: 18px;
    }
    .stDataFrame,
    div[data-testid="stTable"] {
        border-radius: 18px;
        overflow: hidden;
        border: 1px solid rgba(27, 56, 45, 0.1);
    }
    .element-container iframe {
        border-radius: 22px !important;
        border: 1px solid rgba(27, 56, 45, 0.12) !important;
        box-shadow: 0 24px 50px rgba(17, 31, 25, 0.14);
    }
    div[data-testid="stButton"] > button,
    div[data-testid="stFormSubmitButton"] > button {
        min-height: 2.9rem;
        border-radius: 16px;
        border: 1px solid rgba(16, 59, 47, 0.12);
        background: rgba(255, 255, 255, 0.82);
        color: var(--text-main);
        font-weight: 700;
        letter-spacing: 0.01em;
        box-shadow: 0 12px 24px rgba(17, 31, 25, 0.08);
        transition: transform 0.16s ease, box-shadow 0.16s ease, border-color 0.16s ease;
    }
    div[data-testid="stButton"] > button:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {
        transform: translateY(-1px);
        border-color: rgba(16, 59, 47, 0.24);
        box-shadow: 0 16px 28px rgba(17, 31, 25, 0.12);
    }
    div[data-testid="stButton"] > button[kind="primary"],
    div[data-testid="stFormSubmitButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent-strong) 0%, var(--accent) 100%);
        color: #ffffff;
        border-color: rgba(16, 59, 47, 0.1);
    }
    div[data-testid="stButton"] > button p,
    div[data-testid="stFormSubmitButton"] > button p {
        font-size: 0.95rem;
    }
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    div[data-baseweb="base-input"] > div,
    .stTextArea textarea,
    .stNumberInput input {
        border-radius: 16px !important;
        border: 1px solid rgba(27, 56, 45, 0.12) !important;
        background: rgba(255, 255, 255, 0.92) !important;
        box-shadow: none !important;
        color: var(--text-main) !important;
    }
    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea {
        background: rgba(255, 255, 255, 0.92) !important;
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
        color: var(--text-main) !important;
        -webkit-text-fill-color: var(--text-main) !important;
        caret-color: var(--text-main) !important;
        opacity: 1 !important;
    }
    .stTextInput input::placeholder,
    .stNumberInput input::placeholder,
    .stTextArea textarea::placeholder,
    div[data-baseweb="input"] input::placeholder,
    div[data-baseweb="base-input"] input::placeholder,
    div[data-baseweb="select"] input::placeholder {
        color: #8ea099 !important;
        opacity: 1 !important;
    }
    label[data-testid="stWidgetLabel"] p,
    .stSelectbox label p,
    .stNumberInput label p,
    .stTextInput label p,
    .stTextArea label p,
    .stSlider label p {
        color: var(--text-main) !important;
        font-weight: 600 !important;
    }
    div[data-baseweb="select"] svg,
    .stNumberInput button svg {
        fill: var(--text-main) !important;
    }
    .stNumberInput button {
        background: transparent !important;
        border: 0 !important;
        box-shadow: none !important;
    }
    .stSelectbox div[data-baseweb="select"] > div,
    .stNumberInput div[data-baseweb="base-input"] > div,
    .stTextInput div[data-baseweb="input"] > div {
        min-height: 3.2rem;
    }
    .stFileUploader {
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.7);
        border: 1px dashed rgba(27, 56, 45, 0.18);
        padding: 0.2rem;
    }
    @media (max-width: 900px) {
        .main-title {
            font-size: 1.9rem;
        }
        .inspector-meta {
            grid-template-columns: 1fr;
        }
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
                        st.rerun()

                if st.button("Delete location", key="delete_location_btn", type="primary", width="stretch"):
                    delete_location(loc_id)
                    st.session_state.selected_location_id = None
                    st.session_state.show_manage_loc = False
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
                                    st.rerun()
                            with upd_col2:
                                if st.form_submit_button("Cancel"):
                                    st.session_state[f"editing_review_{r_id}"] = False
                                    st.rerun()


def build_coverage_audit_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Topic": "Complex queries (GROUP BY / HAVING / nested / WITH)",
                "Status": "Implemented properly",
                "Grade": "OK",
                "Evidence": "Grouped ratings, HAVING filters, CTEs, correlated subqueries, EXISTS / NOT EXISTS are all present.",
                "Audit note": "The query layer goes beyond basic SELECT usage and demonstrates meaningful multi-table logic.",
            },
            {
                "Topic": "Set operations (UNION / INTERSECT / EXCEPT)",
                "Status": "Implemented properly",
                "Grade": "OK",
                "Evidence": "UNION, INTERSECT, and EXCEPT are implemented as raw SQL queries.",
                "Audit note": "SQLite uses EXCEPT instead of MINUS, which is a valid dialect substitution.",
            },
            {
                "Topic": "Views",
                "Status": "Implemented properly",
                "Grade": "OK",
                "Evidence": "The schema defines location_avg_rating and category_activity_summary as reusable derived relations.",
                "Audit note": "View coverage is now stronger because the project exposes more than one non-trivial derived relation.",
            },
            {
                "Topic": "Transactions (COMMIT / ROLLBACK / SAVEPOINT)",
                "Status": "Implemented properly",
                "Grade": "OK",
                "Evidence": "The app now includes a rating SAVEPOINT demo plus a richer archive-and-delete transaction workflow.",
                "Audit note": "Transaction control is demonstrated in both update and destructive multi-step scenarios.",
            },
            {
                "Topic": "Triggers",
                "Status": "Implemented properly",
                "Grade": "OK",
                "Evidence": "Audit, validation, and delete-archive triggers are all implemented at the schema level.",
                "Audit note": "This is meaningful trigger coverage with both business-rule enforcement and audit behavior.",
            },
            {
                "Topic": "Stored procedures / functions / packages",
                "Status": "Partially implemented",
                "Grade": "Partial",
                "Evidence": "SQLite user-defined scalar function rating_band is registered and used in views/queries.",
                "Audit note": "Function coverage improves, but SQLite still lacks true stored procedures and packages.",
            },
            {
                "Topic": "Cursors (explicit / implicit / parameterized)",
                "Status": "Partially implemented",
                "Grade": "Partial",
                "Evidence": "The app has both a general cursor routine and a parameterized category-scoped cursor analogue.",
                "Audit note": "Cursor depth is better now, though it remains a Python analogue rather than true PL/SQL cursor syntax.",
            },
            {
                "Topic": "Exception handling",
                "Status": "Implemented properly",
                "Grade": "OK",
                "Evidence": "SQLite trigger validation now raises DB-level errors via RAISE(ABORT, ...), alongside application handling.",
                "Audit note": "This is a reasonable SQLite equivalent for database-side business-rule exception behavior.",
            },
        ]
    )


def build_substitution_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Substitution": "Python functions instead of stored procedures",
                "Academic verdict": "Weak substitution",
                "Evaluation": "Acceptable for a practical SQLite app, but it still falls short if the lab explicitly expects DB-resident procedures.",
            },
            {
                "Substitution": "SQLite user-defined function instead of stored PL/SQL function",
                "Academic verdict": "Reasonable SQLite substitution",
                "Evaluation": "It improves function coverage, but it is still weaker than a full stored-function ecosystem in PostgreSQL or Oracle.",
            },
            {
                "Substitution": "Python cursor loop instead of explicit PL/SQL cursor",
                "Academic verdict": "Partial substitution",
                "Evaluation": "It now includes a parameterized cursor-style routine, but many graders will still mark it as weaker than native procedural cursors.",
            },
            {
                "Substitution": "SQLite triggers and RAISE() instead of procedural exception blocks",
                "Academic verdict": "Acceptable substitution",
                "Evaluation": "This is genuine DB-side enforcement and should count well for trigger and business-rule validation coverage.",
            },
        ]
    )


def build_improvement_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Action": "If PostgreSQL is allowed, move archival delete into a stored procedure",
                "Why": "That would close the biggest remaining procedural SQL gap.",
            },
            {
                "Action": "Add more trigger-backed business rules",
                "Why": "Examples like duplicate-review prevention would deepen practical trigger usage further.",
            },
            {
                "Action": "Expose the SQLite user-defined function in more reports",
                "Why": "That would make the function coverage feel less one-off.",
            },
            {
                "Action": "Add a second parameterized cursor scenario",
                "Why": "A second cursor use case would make the analogue feel more deliberate and academically stronger.",
            },
            {
                "Action": "Document SQLite limitations explicitly in the report",
                "Why": "It helps justify why procedures/packages are only partially covered in this engine.",
            },
        ]
    )


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
                    st.success(result["message"])
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
    audit_df = build_coverage_audit_df()
    substitution_df = build_substitution_df()
    improvement_df = build_improvement_df()

    ratings_df = average_rating_per_location()
    top_df = top_rated_locations(min_reviews=1)
    reviewed_df = most_reviewed_locations()
    users_df = users_with_most_reviews()
    category_view_df = get_category_activity_summary()
    rating_band_df = location_rating_bands()
    view_df = _to_df_for_ui(
        "SELECT * FROM location_avg_rating ORDER BY review_count DESC, avg_rating DESC, location_name"
    )
    union_df = locations_union_high_activity()
    except_df = active_but_not_top_rated()
    intersect_df = common_favorites_and_reviewed()
    exists_df = users_with_five_star_review()
    all_df = locations_above_all_in_category()
    correlated_df = best_per_category_correlated()
    universal_df = users_who_reviewed_all_categories()
    review_logs_df = get_review_logs()
    deleted_audit_df = get_deleted_location_audit()

    implemented_count = int((audit_df["Status"] == "Implemented properly").sum())
    partial_count = int((audit_df["Status"] == "Partially implemented").sum())
    missing_count = int((audit_df["Status"] == "Missing").sum())

    render_page_banner(
        "DBMS Lab Audit",
        "A strict evaluator-style review of this project against common Database Systems Lab requirements: complex SQL, set operations, views, transactions, cursors, triggers, and procedural depth.",
        kicker="Checklist-based assessment",
    )
    st.markdown(
        f"""
        <div class="flat-section">
            <div class="surface-head">
                <div class="surface-title">Audit summary</div>
                <p class="surface-copy">{implemented_count} implemented, {partial_count} partial, {missing_count} missing. Final verdict: much stronger for SQLite now, but still only partially equivalent to a full PL/SQL lab because SQLite does not offer true stored procedures or packages.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    coverage_tab, queries_tab, advanced_tab, runtime_tab, improvements_tab = st.tabs(
        ["Coverage Check", "Complex Queries", "Set Ops + Subqueries", "Transactions + Triggers", "Improvements"]
    )

    with coverage_tab:
        render_data_panel(
            "Coverage check",
            "Strict topic-by-topic grading against a DBMS lab manual style checklist.",
            audit_df,
        )
        render_data_panel(
            "Audit interpretation",
            "The strongest remaining limitation is procedural SQL depth: SQLite can support triggers, views, SAVEPOINT workflows, validation with RAISE(), and user-defined functions, but not true stored procedures or packages.",
            audit_df[["Topic", "Status", "Audit note"]],
        )

    with queries_tab:
        render_data_panel(
            "Complex aggregate query",
            "Average rating per location demonstrates joins, GROUP BY, aggregate functions, and ORDER BY.",
            ratings_df,
        )
        render_data_panel(
            "HAVING-based ranking query",
            "Top-rated locations filters grouped rows with HAVING and orders by multiple derived measures.",
            top_df,
        )
        render_data_panel(
            "WITH clause / CTE query",
            "Most-reviewed locations uses a review-count CTE before joining back to the location relation.",
            reviewed_df,
        )
        render_data_panel(
            "Category activity view",
            "A second derived relation summarizing category-level activity, average rating, and review intensity band.",
            category_view_df,
        )
        render_data_panel(
            "Derived relation / view",
            "The location_avg_rating view proves that summary logic is modeled as a reusable derived relation.",
            view_df,
        )
        render_data_panel(
            "SQLite function-backed query",
            "Location rows classified through the SQLite user-defined function rating_band().",
            rating_band_df,
        )

    with advanced_tab:
        left_col, right_col = st.columns(2, gap="large")
        with left_col:
            render_data_panel(
                "UNION",
                "Locations surfaced either by high rating or by high review activity.",
                union_df,
                "No noteworthy locations found.",
            )
            render_data_panel(
                "EXCEPT",
                "Reviewed places that are active but do not qualify as top rated.",
                except_df,
                "All reviewed locations are top rated.",
            )
            render_data_panel(
                "INTERSECT",
                "Locations that appear in both Favorites and Reviews.",
                intersect_df,
                "No overlap between favorites and reviewed locations.",
            )
        with right_col:
            render_data_panel(
                "EXISTS",
                "Users with at least one five-star review.",
                exists_df,
                "No users have given a five-star review.",
            )
            render_data_panel(
                "ALL / universal comparison",
                "Best location in each category using a peer-comparison query.",
                all_df,
                "No exclusive category leaders found.",
            )
            render_data_panel(
                "Correlated subquery",
                "Location average compared against its category average inside the same query.",
                correlated_df,
                "No reviewed locations found.",
            )
            render_data_panel(
                "NOT EXISTS / relational division style",
                "Users who reviewed all reviewed categories.",
                universal_df,
                "No user has reviewed all categories.",
            )
            render_data_panel(
                "Grouped reviewer analytics",
                "Users with most reviews is another meaningful grouped analytics query over the review table.",
                users_df,
            )

    with runtime_tab:
        render_db_runtime_sections()
        render_data_panel(
            "Trigger evidence: ReviewLogs",
            "The trigger-backed audit table records insert and rating-update activity automatically.",
            review_logs_df,
            "No trigger log entries yet.",
        )
        render_data_panel(
            "Delete archive evidence",
            "Archived delete records captured by the BEFORE DELETE trigger on Locations.",
            deleted_audit_df,
            "No archived location deletions yet.",
        )

    with improvements_tab:
        render_data_panel(
            "Practical substitutions",
            "Where SQLite uses an equivalent rather than a full PL/SQL feature, this table shows how strong the substitution is academically.",
            substitution_df,
        )
        render_data_panel(
            "Suggestions to improve score",
            "Concrete changes that would raise the project closer to a strong lab submission.",
            improvement_df,
        )


def render_advanced_sql_page() -> None:
    render_page_banner(
        "SQL Concept Demos",
        "This page is the interactive runtime sandbox for the database concepts surfaced in the audit view, including set operations, subqueries, transactions, cursor-style processing, and trigger logs.",
        kicker="Interactive demos",
    )

    set_col, subquery_col = st.columns(2, gap="large")
    with set_col:
        st.markdown(
            """
            <div class="flat-section">
                <div class="surface-head">
                    <div class="panel-kicker">SQL tools</div>
                    <div class="surface-title">Set operations</div>
                    <p class="surface-copy">Compare location groups using UNION, EXCEPT, and INTERSECT queries.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("UNION: noteworthy locations", expanded=True):
            safe_df(locations_union_high_activity(), "No noteworthy locations found.")
        with st.expander("EXCEPT: popular but not top rated", expanded=False):
            safe_df(active_but_not_top_rated(), "All reviewed locations are top rated.")
        with st.expander("INTERSECT: favorited and reviewed", expanded=False):
            safe_df(common_favorites_and_reviewed(), "No locations appear in both favorites and reviews.")

    with subquery_col:
        st.markdown(
            """
            <div class="flat-section">
                <div class="surface-head">
                    <div class="panel-kicker">SQL tools</div>
                    <div class="surface-title">Advanced subqueries</div>
                    <p class="surface-copy">Inspect EXISTS, ALL, correlated subqueries, and universal-review coverage logic.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("EXISTS: users with a five-star review", expanded=True):
            safe_df(users_with_five_star_review(), "No users have given a five-star review.")
        with st.expander("ALL: best location in each category", expanded=False):
            safe_df(locations_above_all_in_category(), "No location exclusively leads its category.")
        with st.expander("Correlated: location vs category average", expanded=False):
            safe_df(best_per_category_correlated(), "No reviewed locations found.")
        with st.expander("NOT EXISTS: users who reviewed all categories", expanded=False):
            safe_df(users_who_reviewed_all_categories(), "No user has reviewed all categories.")

    render_data_panel(
        "Function-backed classification",
        "Rows classified by the SQLite user-defined function rating_band().",
        location_rating_bands(),
    )
    render_data_panel(
        "Category activity view",
        "A second derived relation summarizing activity and rating band at the category level.",
        get_category_activity_summary(),
    )

    render_db_runtime_sections()

    render_data_panel(
        "Review audit log",
        "Changes to review ratings are tracked through the SQLite trigger-backed audit table.",
        get_review_logs(),
        "No audit log entries yet.",
    )
    render_data_panel(
        "Deleted location archive log",
        "Each deleted location is archived by a BEFORE DELETE trigger before cascading cleanup occurs.",
        get_deleted_location_audit(),
        "No archived location deletions yet.",
    )


def _to_df_for_ui(sql: str) -> pd.DataFrame:
    from sqlalchemy import text

    from db import engine

    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)


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
            '<p class="nav-copy">Move between map exploration, the DBMS lab audit view, and the interactive SQL concept demos from one control rail.</p>',
            unsafe_allow_html=True,
        )

        pages = [
            ("Map View", "map", ":material/map:"),
            ("DBMS Audit", "analytics", ":material/query_stats:"),
            ("SQL Demos", "advanced", ":material/code:"),
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
                st.rerun()
            except Exception as ex:
                st.error(f"Could not load sample data: {ex}")

    with content_col:
        render_add_category_card()
        render_add_location_card()

        if st.session_state.current_page == "analytics":
            render_analytics_page()
        elif st.session_state.current_page == "advanced":
            render_advanced_sql_page()
        else:
            all_locations_df = get_locations()
            locations_df = search_locations_by_category(st.session_state.selected_category_id)
            render_map_page(locations_df, all_locations_df, categories_df)
