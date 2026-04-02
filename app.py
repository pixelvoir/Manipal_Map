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
    get_locations,
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
    .title-row {
        margin-bottom: 0.75rem;
    }
    .main-title {
        font-size: 1.85rem;
        font-weight: 700;
        margin: 0;
    }
    .muted {
        color: #4f4f4f;
    }
    .panel {
        border: 1px solid #e7e7e7;
        border-radius: 10px;
        padding: 0.8rem 0.9rem;
        margin-top: 0.75rem;
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
        st.warning(f"Please login to {action_text}.")
        st.session_state.show_auth = True
        return False
    return True


def safe_df(df: pd.DataFrame, message: str = "No records found.") -> None:
    if df.empty:
        st.info(message)
        return
    st.dataframe(df, use_container_width=True, hide_index=True)


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

    for _, row in valid.iterrows():
        tooltip = f"ID:{int(row['location_id'])} | {row['name']}"
        folium.Marker(
            [row["latitude"], row["longitude"]],
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


def render_auth_panel() -> None:
    if not st.session_state.show_auth:
        return

    with st.expander("Login / Register", expanded=True):
        col_login, col_register = st.columns(2)

        with col_login:
            st.subheader("Login")
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                login_submit = st.form_submit_button("Login")

            if login_submit:
                user = get_user_by_email(email)
                if user and verify_password(password, user.get("password_hash")):
                    st.session_state.logged_in_user = {
                        "user_id": int(user["user_id"]),
                        "name": user["name"],
                        "email": user["email"],
                    }
                    st.session_state.show_auth = False
                    st.success("Logged in successfully.")
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

        with col_register:
            st.subheader("Register")
            with st.form("register_form"):
                name = st.text_input("Name", key="reg_name")
                email = st.text_input("Email", key="reg_email")
                password = st.text_input("Password", type="password", key="reg_password")
                register_submit = st.form_submit_button("Register")

            if register_submit:
                try:
                    register_user(name, email, hash_password(password))
                    st.success("Registration successful. Please login.")
                except Exception as ex:
                    st.error(f"Registration failed: {ex}")


def render_add_category() -> None:
    if not st.session_state.show_add_category:
        return
    with st.expander("Add Category", expanded=True):
        with st.form("add_category_form"):
            category_name = st.text_input("Category Name")
            submitted = st.form_submit_button("Save Category")
        if submitted:
            try:
                add_category(category_name)
                st.success("Category added.")
            except Exception as ex:
                st.error(f"Could not add category: {ex}")


def render_add_location() -> None:
    if not st.session_state.show_add_location:
        return

    with st.expander("Add Location", expanded=True):
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

        st.caption("Coordinates can be entered manually or auto-filled from last map click.")
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


def render_location_details() -> None:
    if not st.session_state.selected_location_id:
        st.info("Click a map marker to view location details.")
        return

    details_df = get_location_details(int(st.session_state.selected_location_id))
    if details_df.empty:
        st.warning("Selected location could not be found.")
        return

    loc = details_df.iloc[0]

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader(f"{loc['name']}")
    st.write(f"Category: {loc['category_name']}")
    st.write(f"Address: {loc['address']}")
    st.write(f"Description: {loc['description']}")
    st.write(f"Average Rating: {loc['avg_rating'] if pd.notna(loc['avg_rating']) else 'No ratings'}")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Add Review"):
            if require_login("add a review"):
                st.session_state.show_add_review_for_selected = True
    with col_b:
        if st.button("Add to Favorites"):
            if require_login("add to favorites"):
                try:
                    add_favorite(
                        int(st.session_state.logged_in_user["user_id"]),
                        int(st.session_state.selected_location_id),
                    )
                    st.success("Added to favorites.")
                except Exception as ex:
                    st.error(f"Could not add favorite: {ex}")

    st.markdown("### Reviews")
    reviews_df = get_reviews_for_location(int(st.session_state.selected_location_id))
    safe_df(reviews_df, "No reviews yet for this location.")

    if st.session_state.show_add_review_for_selected and st.session_state.logged_in_user:
        with st.form("add_review_for_selected"):
            rating = st.slider("Rating", 1, 5, 4)
            comment = st.text_area("Comment")
            review_date = st.date_input("Date", value=date.today())
            submitted = st.form_submit_button("Submit Review")

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
    st.caption("Meaningful SQL query outputs using JOIN, GROUP BY, HAVING, and CTE.")

    st.markdown("#### Average Rating Per Location")
    safe_df(average_rating_per_location())

    st.markdown("#### Top Rated Locations (HAVING count >= 1)")
    safe_df(top_rated_locations(min_reviews=1))

    st.markdown("#### Most Reviewed Locations (CTE)")
    safe_df(most_reviewed_locations())

    st.markdown("#### Users With Most Reviews (JOIN + CTE)")
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
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_db()
init_state()

title_col, auth_col = st.columns([4, 2])
with title_col:
    st.markdown('<div class="title-row"><p class="main-title">Manipal Location & Review Management</p></div>', unsafe_allow_html=True)
with auth_col:
    if st.session_state.logged_in_user:
        st.markdown(
            f"<p class='muted' style='text-align:right;'>Logged in as {st.session_state.logged_in_user['name']}</p>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown("<p class='muted' style='text-align:right;'>Not logged in</p>", unsafe_allow_html=True)

controls = st.columns(6)
if controls[0].button("Add Category"):
    st.session_state.show_add_category = not st.session_state.show_add_category
if controls[1].button("Add Location"):
    st.session_state.show_add_location = not st.session_state.show_add_location
if controls[2].button("Map Database"):
    st.session_state.current_page = "analytics"
if controls[3].button("Map View"):
    st.session_state.current_page = "map"
if controls[4].button("Load Sample Data"):
    try:
        insert_sample_data()
        st.success("Sample data loaded.")
        st.rerun()
    except Exception as ex:
        st.error(f"Could not load sample data: {ex}")

if st.session_state.logged_in_user:
    if controls[5].button("Logout"):
        st.session_state.logged_in_user = None
        st.session_state.show_auth = False
        st.success("Logged out.")
        st.rerun()
else:
    if controls[5].button("Login"):
        st.session_state.show_auth = not st.session_state.show_auth

render_auth_panel()
render_add_category()
render_add_location()

if st.session_state.current_page == "analytics":
    render_analytics_page()
else:
    categories_df = get_categories()
    options = ["All"]
    category_map: dict[str, int] = {}
    for _, row in categories_df.iterrows():
        label = f"{row['category_name']} (ID {int(row['category_id'])})"
        options.append(label)
        category_map[label] = int(row["category_id"])

    selected_label = st.selectbox("Filter by Category", options, index=0)
    selected_category_id = category_map.get(selected_label)

    locations_df = search_locations_by_category(selected_category_id)
    render_map(locations_df)

    if st.session_state.last_clicked_coords:
        lat, lng = st.session_state.last_clicked_coords
        st.caption(f"Last clicked map position: {lat:.6f}, {lng:.6f}")

    render_location_details()
