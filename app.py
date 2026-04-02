"""Map-first Streamlit app for the Manipal Location & Review Management System."""

from __future__ import annotations

from datetime import date
import hashlib
import secrets

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from db import init_db
from queries import (
    add_category,
    add_favorite,
    add_location,
    add_review_with_procedure,
    average_rating_per_location,
    get_categories,
    get_location_details,
    get_reviews_for_location,
    get_user_by_email,
    most_reviewed_locations,
    register_user,
    search_locations_by_category,
    top_rated_locations,
    users_with_most_reviews,
)
from sample_data import insert_sample_data


st.set_page_config(page_title="Manipal Locations", layout="wide")

st.markdown(
    """
    <style>
    :root {
        --bg-soft: #f8fbf7;
        --line-soft: #d9e6d7;
        --text-soft: #4a5b4d;
        --accent: #4f7b5a;
        --accent-dark: #2f5e3d;
    }
    .stApp {
        background: linear-gradient(180deg, #ffffff 0%, var(--bg-soft) 100%);
    }
    .main-title {
        font-size: 1.9rem;
        font-weight: 700;
        margin: 0;
    }
    .status-text {
        color: var(--text-soft);
        text-align: right;
        margin-top: 0.2rem;
    }
    .nav-shell {
        border: 1px solid var(--line-soft);
        border-radius: 14px;
        background: #ffffff;
        padding: 0.8rem;
        position: sticky;
        top: 1rem;
    }
    .card-shell {
        border: 1px solid var(--line-soft);
        border-radius: 12px;
        background: #ffffff;
        padding: 0.9rem;
        margin-bottom: 0.9rem;
    }
    .location-card {
        border: 1px solid var(--line-soft);
        border-radius: 14px;
        background: #ffffff;
        padding: 1rem;
        margin-top: 0.8rem;
    }
    .hint {
        padding: 0.55rem 0.7rem;
        border-radius: 9px;
        background: #edf6ed;
        color: var(--accent-dark);
        border: 1px solid #d0e6d4;
        margin-bottom: 0.6rem;
    }
    div[data-testid="stButton"] > button {
        border-radius: 10px;
        border: 1px solid #c8dac7;
        background: #f5faf4;
        color: var(--accent-dark);
        padding: 0.42rem 0.75rem;
        font-weight: 600;
    }
    div[data-testid="stButton"] > button:hover {
        border-color: var(--accent);
        background: #e9f4e6;
        color: var(--accent-dark);
    }
    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(180deg, #5f8d69 0%, #4f7b5a 100%);
        color: #ffffff;
        border-color: #4f7b5a;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        background: linear-gradient(180deg, #5a8964 0%, #456e50 100%);
        color: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


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
        st.session_state.show_auth = True
        return False
    return True


def safe_df(df: pd.DataFrame, message: str = "No records found.") -> None:
    if df.empty:
        st.info(message)
        return
    st.dataframe(df, use_container_width=True, hide_index=True)


def closeable_card_header(title: str, state_key: str) -> None:
    head_col, close_col = st.columns([12, 1])
    with head_col:
        st.markdown(f"#### {title}")
    with close_col:
        if st.button("X", key=f"close_{state_key}"):
            st.session_state[state_key] = False
            st.rerun()


def render_map(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No locations to show on map.")
        return

    valid = df.dropna(subset=["latitude", "longitude"])
    if valid.empty:
        st.info("Locations are missing coordinates.")
        return

    center = [valid["latitude"].mean(), valid["longitude"].mean()]
    fmap = folium.Map(location=center, zoom_start=15)

    # CircleMarker avoids occasional missing default Leaflet marker icon issues.
    for _, row in valid.iterrows():
        tooltip = f"ID:{int(row['location_id'])} | {row['name']}"
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=7,
            color="#2f5e3d",
            fill=True,
            fill_color="#4f7b5a",
            fill_opacity=0.95,
            weight=2,
            tooltip=tooltip,
            popup=row["name"],
        ).add_to(fmap)

    result = st_folium(fmap, width=None, height=520, key="map_view")

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


def render_auth_card() -> None:
    if not st.session_state.show_auth:
        return

    st.markdown('<div class="card-shell">', unsafe_allow_html=True)
    closeable_card_header("Sign In / Register", "show_auth")
    login_col, register_col = st.columns(2)

    with login_col:
        st.markdown("**Sign In**")
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            login_submit = st.form_submit_button("Sign In")

        if login_submit:
            user = get_user_by_email(email)
            if user and verify_password(password, user.get("password_hash")):
                st.session_state.logged_in_user = {
                    "user_id": int(user["user_id"]),
                    "name": user["name"],
                    "email": user["email"],
                }
                st.session_state.show_auth = False
                st.success("Signed in successfully.")
                st.rerun()
            else:
                st.error("Invalid email or password.")

    with register_col:
        st.markdown("**Register**")
        with st.form("register_form"):
            name = st.text_input("Name", key="reg_name")
            email = st.text_input("Email", key="reg_email")
            password = st.text_input("Password", type="password", key="reg_password")
            register_submit = st.form_submit_button("Create Account")

        if register_submit:
            try:
                register_user(name, email, hash_password(password))
                st.success("Registration successful. You can sign in now.")
            except Exception as ex:
                st.error(f"Registration failed: {ex}")
    st.markdown("</div>", unsafe_allow_html=True)


def render_add_category_card() -> None:
    if not st.session_state.show_add_category:
        return

    st.markdown('<div class="card-shell">', unsafe_allow_html=True)
    closeable_card_header("Add New Category", "show_add_category")
    with st.form("add_category_form"):
        category_name = st.text_input("Category Name")
        submitted = st.form_submit_button("Save Category")
    if submitted:
        try:
            add_category(category_name)
            st.success("Category added.")
        except Exception as ex:
            st.error(f"Could not add category: {ex}")
    st.markdown("</div>", unsafe_allow_html=True)


def render_add_location_card() -> None:
    if not st.session_state.show_add_location:
        return

    st.markdown('<div class="card-shell">', unsafe_allow_html=True)
    closeable_card_header("Add New Location", "show_add_location")
    if not require_login("add a location"):
        st.markdown("</div>", unsafe_allow_html=True)
        return

    categories = get_categories()
    if categories.empty:
        st.info("Create at least one category first.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    default_lat = 13.3520
    default_lng = 74.7920
    if st.session_state.last_clicked_coords:
        default_lat, default_lng = st.session_state.last_clicked_coords

    st.markdown(
        '<div class="hint">Click on the map to capture coordinates automatically, then submit this form.</div>',
        unsafe_allow_html=True,
    )
    if st.session_state.last_clicked_coords:
        st.caption(f"Using last clicked position: {default_lat:.6f}, {default_lng:.6f}")
    else:
        st.caption("No map point selected yet. You can still enter coordinates manually.")

    with st.form("add_location_form"):
        name = st.text_input("Name")
        category_id = st.selectbox(
            "Category",
            categories["category_id"].tolist(),
            format_func=lambda cid: f"{cid} - {categories.loc[categories['category_id'] == cid, 'category_name'].iloc[0]}",
        )
        address = st.text_input("Address")
        description = st.text_area("Description")
        latitude = st.number_input("Latitude", value=float(default_lat), format="%.6f")
        longitude = st.number_input("Longitude", value=float(default_lng), format="%.6f")
        submitted = st.form_submit_button("Save Location")

    if submitted:
        try:
            add_location(name, int(category_id), address, description, float(latitude), float(longitude))
            st.success("Location added.")
            st.rerun()
        except Exception as ex:
            st.error(f"Could not add location: {ex}")
    st.markdown("</div>", unsafe_allow_html=True)


def render_location_details() -> None:
    if not st.session_state.selected_location_id:
        st.info("Click a location marker to view details and reviews.")
        return

    details_df = get_location_details(int(st.session_state.selected_location_id))
    if details_df.empty:
        st.warning("Selected location could not be found.")
        return

    loc = details_df.iloc[0]
    st.markdown('<div class="location-card">', unsafe_allow_html=True)
    st.markdown(f"### {loc['name']}")

    a_col, b_col = st.columns(2)
    with a_col:
        st.markdown(f"**Category**: {loc['category_name']}")
        st.markdown(f"**Address**: {loc['address']}")
    with b_col:
        avg_text = loc['avg_rating'] if pd.notna(loc['avg_rating']) else "No ratings"
        st.markdown(f"**Average Rating**: {avg_text}")
        st.markdown(f"**Total Reviews**: {int(loc['review_count']) if pd.notna(loc['review_count']) else 0}")

    st.markdown(f"**Description**: {loc['description']}")

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("Write Review", key="open_review_btn"):
            if require_login("add a review"):
                st.session_state.show_add_review_for_selected = True
    with btn_col2:
        if st.button("Save Favorite", key="save_fav_btn"):
            if require_login("add to favorites"):
                try:
                    add_favorite(
                        int(st.session_state.logged_in_user["user_id"]),
                        int(st.session_state.selected_location_id),
                    )
                    st.success("Added to favorites.")
                except Exception as ex:
                    st.error(f"Could not add favorite: {ex}")

    st.markdown("#### Reviews")
    reviews_df = get_reviews_for_location(int(st.session_state.selected_location_id))
    safe_df(reviews_df, "No reviews yet for this location.")

    if st.session_state.show_add_review_for_selected and st.session_state.logged_in_user:
        st.markdown("##### Add Review")
        with st.form("add_review_for_selected"):
            rating = st.slider("Rating", 1, 5, 4)
            comment = st.text_area("Comment")
            review_date = st.date_input("Date", value=date.today())
            form_col1, form_col2 = st.columns(2)
            with form_col1:
                submitted = st.form_submit_button("Submit Review")
            with form_col2:
                cancel = st.form_submit_button("Cancel")

        if cancel:
            st.session_state.show_add_review_for_selected = False
            st.rerun()

        if submitted:
            try:
                avg_rating = add_review_with_procedure(
                    int(st.session_state.logged_in_user["user_id"]),
                    int(st.session_state.selected_location_id),
                    int(rating),
                    comment,
                    review_date,
                )
                st.success(f"Review added. New average rating: {avg_rating}")
                st.session_state.show_add_review_for_selected = False
                st.rerun()
            except Exception as ex:
                st.error(f"Could not add review: {ex}")
    st.markdown("</div>", unsafe_allow_html=True)


def render_analytics_page() -> None:
    st.subheader("Map Database")
    st.caption("JOIN, GROUP BY, HAVING and CTE based analytics.")

    st.markdown("#### Average Rating Per Location")
    safe_df(average_rating_per_location())

    st.markdown("#### Top Rated Locations")
    safe_df(top_rated_locations(min_reviews=1))

    st.markdown("#### Most Reviewed Locations")
    safe_df(most_reviewed_locations())

    st.markdown("#### Users With Most Reviews")
    safe_df(users_with_most_reviews())


def init_state() -> None:
    defaults = {
        "logged_in_user": None,
        "selected_location_id": None,
        "last_clicked_coords": None,
        "show_add_category": False,
        "show_add_location": False,
        "show_auth": False,
        "show_add_review_for_selected": False,
        "current_page": "map",
        "selected_category_id": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_db()
init_state()

title_col, auth_col = st.columns([5, 2])
with title_col:
    st.markdown('<p class="main-title">Manipal Location & Review Management</p>', unsafe_allow_html=True)
with auth_col:
    if st.session_state.logged_in_user:
        _, btn_col = st.columns([2.2, 1])
        with btn_col:
            if st.button("Sign Out", icon=":material/logout:"):
                st.session_state.logged_in_user = None
                st.session_state.show_auth = False
                st.success("Signed out.")
                st.rerun()
        st.markdown(
            f"<p class='status-text'>Signed in as {st.session_state.logged_in_user['name']}</p>",
            unsafe_allow_html=True,
        )
    else:
        _, btn_col = st.columns([2.2, 1])
        with btn_col:
            if st.button("Sign In", icon=":material/login:"):
                st.session_state.show_auth = not st.session_state.show_auth
        st.markdown("<p class='status-text'>Not signed in</p>", unsafe_allow_html=True)

nav_col, content_col = st.columns([1.15, 3.85], gap="large")

with nav_col:
    st.markdown('<div class="nav-shell">', unsafe_allow_html=True)
    st.markdown("**View Mode**")
    mode_col_1, mode_col_2 = st.columns(2)
    with mode_col_1:
        if st.button(
            "Map View",
            icon=":material/map:",
            type="primary" if st.session_state.current_page == "map" else "secondary",
            use_container_width=True,
        ):
            st.session_state.current_page = "map"
    with mode_col_2:
        if st.button(
            "Map Database",
            icon=":material/query_stats:",
            type="primary" if st.session_state.current_page == "analytics" else "secondary",
            use_container_width=True,
        ):
            st.session_state.current_page = "analytics"

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

    selected_label = st.selectbox("Filter by Category", options, index=options.index(current_label))
    st.session_state.selected_category_id = category_map.get(selected_label)

    if st.button("Add New Category", icon=":material/category:", use_container_width=True):
        st.session_state.show_add_category = not st.session_state.show_add_category

    if st.button("Add New Location", icon=":material/add_location_alt:", use_container_width=True):
        st.session_state.show_add_location = not st.session_state.show_add_location

    if st.button("Load Sample Data", use_container_width=True):
        try:
            insert_sample_data()
            st.success("Sample data loaded.")
            st.rerun()
        except Exception as ex:
            st.error(f"Could not load sample data: {ex}")

    st.markdown("</div>", unsafe_allow_html=True)

with content_col:
    render_auth_card()
    render_add_category_card()
    render_add_location_card()

    if st.session_state.current_page == "analytics":
        render_analytics_page()
    else:
        locations_df = search_locations_by_category(st.session_state.selected_category_id)
        render_map(locations_df)

        if st.session_state.last_clicked_coords:
            lat, lng = st.session_state.last_clicked_coords
            st.caption(f"Last clicked map position: {lat:.6f}, {lng:.6f}")

        render_location_details()
