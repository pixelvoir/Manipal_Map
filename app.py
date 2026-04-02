"""Streamlit UI for the Manipal Location & Review Management System."""

from __future__ import annotations

from datetime import date

import folium
import pandas as pd
import streamlit as st

from db import init_db
from queries import (
    add_category,
    add_favorite,
    add_location,
    add_review_with_procedure,
    add_user,
    average_rating_per_location,
    cte_average_rating,
    cursor_style_review_stats,
    delete_demo_category,
    delete_review,
    get_categories,
    get_favorites,
    get_locations,
    get_reviews,
    get_users,
    insert_demo_category,
    intersect_example,
    location_avg_rating_view,
    locations_sorted_by_rating,
    locations_with_avg_above_four,
    locations_with_highest_rating,
    reviews_with_user_and_location,
    search_locations_by_category,
    union_example,
    update_demo_category,
    update_location_description,
    users_reviewed_more_than_average,
)
from sample_data import insert_sample_data


st.set_page_config(page_title="Manipal Location & Review Management", layout="wide")

st.markdown(
    """
    <style>
    .main-title {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.4rem;
    }
    .sub-text {
        color: #4d4d4d;
        margin-bottom: 1rem;
    }
    .section-head {
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
        font-size: 1.2rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def _get_locations_for_map() -> pd.DataFrame:
    return get_locations()


def draw_map(df: pd.DataFrame, zoom: int = 15) -> None:
    if df.empty:
        st.info("No locations available to display on map.")
        return

    valid = df.dropna(subset=["latitude", "longitude"])
    if valid.empty:
        st.info("Locations do not have coordinates yet.")
        return

    center = [valid["latitude"].mean(), valid["longitude"].mean()]
    fmap = folium.Map(location=center, zoom_start=zoom)

    for _, row in valid.iterrows():
        popup_text = f"{row['name']} ({row['category_name']})"
        folium.Marker(
            [row["latitude"], row["longitude"]],
            popup=popup_text,
            tooltip=row["name"],
        ).add_to(fmap)

    st.components.v1.html(fmap._repr_html_(), height=500)


def show_df(df: pd.DataFrame, empty_msg: str = "No records found.") -> None:
    if df.empty:
        st.info(empty_msg)
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)


init_db()

st.markdown('<div class="main-title">Manipal Location & Review Management System</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-text">Simple DBMS mini-project for viva demonstration using Streamlit + SQLAlchemy.</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Navigation")
    menu = st.radio(
        "Go to",
        [
            "Add Category",
            "Add Location",
            "Add User",
            "Add Review",
            "View Locations",
            "View Reviews",
            "Add to Favorites",
            "Search/Filter Locations by Category",
        ],
    )

    st.markdown("---")
    if st.button("Load Sample Data"):
        try:
            insert_sample_data()
            _get_locations_for_map.clear()
            st.success("Sample data loaded.")
        except Exception as ex:
            st.error(f"Could not load sample data: {ex}")


if menu == "Add Category":
    st.markdown('<div class="section-head">Add Category</div>', unsafe_allow_html=True)
    with st.form("add_category_form"):
        category_name = st.text_input("Category Name")
        submitted = st.form_submit_button("Add Category")

    if submitted:
        try:
            add_category(category_name)
            st.success("Category added successfully.")
        except Exception as ex:
            st.error(f"Error: {ex}")

    show_df(get_categories())


elif menu == "Add Location":
    st.markdown('<div class="section-head">Add Location</div>', unsafe_allow_html=True)

    categories_df = get_categories()
    if categories_df.empty:
        st.warning("Please add categories first.")
    else:
        with st.form("add_location_form"):
            name = st.text_input("Location Name")
            category_id = st.selectbox(
                "Category",
                categories_df["category_id"].tolist(),
                format_func=lambda cid: f"{cid} - {categories_df.loc[categories_df['category_id'] == cid, 'category_name'].iloc[0]}",
            )
            address = st.text_input("Address")
            description = st.text_area("Description")

            st.write("Set pin coordinates")
            latitude = st.number_input("Latitude", value=13.3520, format="%.6f")
            longitude = st.number_input("Longitude", value=74.7920, format="%.6f")

            submitted = st.form_submit_button("Add Location")

        preview_map = folium.Map(location=[latitude, longitude], zoom_start=16)
        folium.Marker([latitude, longitude], tooltip="Selected Pin").add_to(preview_map)
        st.caption("Map preview for selected coordinates")
        st.components.v1.html(preview_map._repr_html_(), height=350)

        if submitted:
            try:
                add_location(name, int(category_id), address, description, float(latitude), float(longitude))
                _get_locations_for_map.clear()
                st.success("Location added successfully.")
            except Exception as ex:
                st.error(f"Error: {ex}")

    show_df(get_locations())


elif menu == "Add User":
    st.markdown('<div class="section-head">Add User</div>', unsafe_allow_html=True)
    with st.form("add_user_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        submitted = st.form_submit_button("Add User")

    if submitted:
        try:
            add_user(name, email)
            st.success("User added successfully.")
        except Exception as ex:
            st.error(f"Error: {ex}")

    show_df(get_users())


elif menu == "Add Review":
    st.markdown('<div class="section-head">Add Review</div>', unsafe_allow_html=True)

    users_df = get_users()
    locations_df = get_locations()

    if users_df.empty or locations_df.empty:
        st.warning("Please ensure users and locations are available first.")
    else:
        with st.form("add_review_form"):
            user_id = st.selectbox(
                "User",
                users_df["user_id"].tolist(),
                format_func=lambda uid: f"{uid} - {users_df.loc[users_df['user_id'] == uid, 'name'].iloc[0]}",
            )
            location_id = st.selectbox(
                "Location",
                locations_df["location_id"].tolist(),
                format_func=lambda lid: f"{lid} - {locations_df.loc[locations_df['location_id'] == lid, 'name'].iloc[0]}",
            )
            rating = st.slider("Rating", min_value=1, max_value=5, value=4)
            comment = st.text_area("Comment")
            review_date = st.date_input("Date", value=date.today())
            submitted = st.form_submit_button("Add Review")

        if submitted:
            try:
                avg_rating = add_review_with_procedure(
                    int(user_id),
                    int(location_id),
                    int(rating),
                    comment,
                    review_date,
                )
                st.success(f"Review added. New average for this location: {avg_rating}")
            except Exception as ex:
                st.error(f"Error: {ex}")

    show_df(get_reviews())


elif menu == "View Locations":
    st.markdown('<div class="section-head">View Locations (Map + Table)</div>', unsafe_allow_html=True)
    locations_df = _get_locations_for_map()
    draw_map(locations_df)
    show_df(locations_df)

    st.markdown("### Quick UPDATE Demo")
    if not locations_df.empty:
        with st.form("update_location_desc"):
            location_id = st.selectbox("Location ID", locations_df["location_id"].tolist())
            new_desc = st.text_input("New Description")
            update_submit = st.form_submit_button("Update Description")
        if update_submit:
            try:
                update_location_description(int(location_id), new_desc)
                _get_locations_for_map.clear()
                st.success("Location description updated.")
            except Exception as ex:
                st.error(f"Error: {ex}")


elif menu == "View Reviews":
    st.markdown('<div class="section-head">View Reviews + SQL Concepts Demo</div>', unsafe_allow_html=True)

    tabs = st.tabs(
        [
            "JOIN",
            "AGGREGATE",
            "HAVING",
            "SUBQUERY",
            "SET OPS",
            "VIEW",
            "ORDER BY + CTE",
            "BASIC CRUD",
            "ADVANCED",
        ]
    )

    with tabs[0]:
        st.caption("JOIN: reviews with username and location name")
        show_df(reviews_with_user_and_location())

    with tabs[1]:
        st.caption("GROUP BY + aggregate: avg rating and review count")
        show_df(average_rating_per_location())

    with tabs[2]:
        st.caption("HAVING: locations with average rating > 4")
        show_df(locations_with_avg_above_four())

    with tabs[3]:
        st.caption("Subquery: locations with highest average rating")
        show_df(locations_with_highest_rating())
        st.caption("Subquery: users who reviewed more than average")
        show_df(users_reviewed_more_than_average())

    with tabs[4]:
        st.caption("UNION example")
        show_df(union_example())
        st.caption("INTERSECT example")
        show_df(intersect_example())

    with tabs[5]:
        st.caption("View: location_avg_rating")
        show_df(location_avg_rating_view())

    with tabs[6]:
        st.caption("ORDER BY: locations sorted by rating")
        show_df(locations_sorted_by_rating())
        st.caption("WITH clause (CTE): average rating calculation")
        show_df(cte_average_rating())

    with tabs[7]:
        st.caption("Basic query operations: INSERT / UPDATE / DELETE demo row")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("INSERT demo category"):
                try:
                    insert_demo_category()
                    st.success("Inserted demo category.")
                except Exception as ex:
                    st.error(f"Insert error: {ex}")
        with c2:
            if st.button("UPDATE demo category"):
                try:
                    update_demo_category()
                    st.success("Updated demo category.")
                except Exception as ex:
                    st.error(f"Update error: {ex}")
        with c3:
            if st.button("DELETE demo category"):
                try:
                    delete_demo_category()
                    st.success("Deleted demo category.")
                except Exception as ex:
                    st.error(f"Delete error: {ex}")

        st.caption("SELECT categories")
        show_df(get_categories())

        st.caption("Optional DELETE on reviews")
        reviews_df = get_reviews()
        if not reviews_df.empty:
            del_id = st.selectbox("Choose Review ID to delete", reviews_df["review_id"].tolist())
            if st.button("Delete Selected Review"):
                try:
                    delete_review(int(del_id))
                    st.success("Review deleted.")
                except Exception as ex:
                    st.error(f"Delete review error: {ex}")

    with tabs[8]:
        st.caption("Advanced 1: Stored Procedure/Function style review insert")
        st.write(
            "Implemented in `add_review_with_procedure()`: PostgreSQL uses SQL function, SQLite uses equivalent transaction logic."
        )

        st.caption("Advanced 2: Trigger")
        st.write("`trg_log_review_insert` logs every review insert into `ReviewLogs`.")

        st.caption("Advanced 3: Cursor-style iteration")
        stats = cursor_style_review_stats()
        st.write(stats)


elif menu == "Add to Favorites":
    st.markdown('<div class="section-head">Add to Favorites</div>', unsafe_allow_html=True)

    users_df = get_users()
    locations_df = get_locations()

    if users_df.empty or locations_df.empty:
        st.warning("Please ensure users and locations are available first.")
    else:
        with st.form("add_favorite_form"):
            user_id = st.selectbox(
                "User",
                users_df["user_id"].tolist(),
                format_func=lambda uid: f"{uid} - {users_df.loc[users_df['user_id'] == uid, 'name'].iloc[0]}",
            )
            location_id = st.selectbox(
                "Location",
                locations_df["location_id"].tolist(),
                format_func=lambda lid: f"{lid} - {locations_df.loc[locations_df['location_id'] == lid, 'name'].iloc[0]}",
            )
            submitted = st.form_submit_button("Add to Favorites")

        if submitted:
            try:
                add_favorite(int(user_id), int(location_id))
                st.success("Added to favorites.")
            except Exception as ex:
                st.error(f"Error: {ex}")

    show_df(get_favorites())


elif menu == "Search/Filter Locations by Category":
    st.markdown('<div class="section-head">Search/Filter Locations by Category</div>', unsafe_allow_html=True)

    categories_df = get_categories()
    if categories_df.empty:
        st.info("No categories available.")
    else:
        category_id = st.selectbox(
            "Select Category",
            categories_df["category_id"].tolist(),
            format_func=lambda cid: f"{cid} - {categories_df.loc[categories_df['category_id'] == cid, 'category_name'].iloc[0]}",
        )

        filtered = search_locations_by_category(int(category_id))
        show_df(filtered)
        draw_map(filtered)
