"""Map-first Streamlit app for the Manipal Location & Review Management System."""

from __future__ import annotations

from datetime import date
import hashlib
import os
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
    add_review,
    update_review,
    delete_review,
    update_location,
    delete_location,
    add_image,
    get_images_for_location,
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
    # Set operations
    locations_union_high_activity,
    active_but_not_top_rated,
    common_favorites_and_reviewed,
    # Advanced subqueries
    users_with_five_star_review,
    locations_above_all_in_category,
    best_per_category_correlated,
    users_who_reviewed_all_categories,
    # Transaction control
    demo_savepoint_transaction,
    # Cursor routine
    flag_low_rated_locations,
    # Audit / status helpers
    get_review_logs,
    get_location_status,
)
from sample_data import insert_sample_data

UPLOAD_DIR = "/home/arhan/Manipal_Map/uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
    .review-action {
        font-size: 0.8rem; 
        color: #777;
    }
    .hint {
        padding: 0.55rem 0.7rem;
        border-radius: 9px;
        background: #edf6ed;
        color: var(--accent-dark);
        border: 1px solid #d0e6d4;
        margin-bottom: 0.6rem;
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
            st.session_state.show_add_location = False
            st.rerun()
        except Exception as ex:
            st.error(f"Could not add location: {ex}")
    st.markdown("</div>", unsafe_allow_html=True)


def render_location_details() -> None:
    if not st.session_state.selected_location_id:
        st.info("Click a location marker to view details and reviews.")
        return

    loc_id = int(st.session_state.selected_location_id)
    details_df = get_location_details(loc_id)
    if details_df.empty:
        st.warning("Selected location could not be found. It may have been deleted.")
        st.session_state.selected_location_id = None
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
    
    # -----------------------------
    # Location Actions (Admin/Edit)
    # -----------------------------
    act_col1, act_col2, act_col3 = st.columns([1,1,2])
    with act_col1:
        if st.button("Save Favorite", key="save_fav_btn"):
            if require_login("add to favorites"):
                try:
                    add_favorite(int(st.session_state.logged_in_user["user_id"]), loc_id)
                    st.success("Added to favorites.")
                except Exception as ex:
                    st.error(f"Could not add favorite: {ex}")
    
    with act_col2:
        if st.session_state.logged_in_user:
            if st.button("Manage Location"):
                st.session_state.show_manage_loc = not st.session_state.get("show_manage_loc", False)

    if st.session_state.get("show_manage_loc", False) and st.session_state.logged_in_user:
        with st.expander("Update / Delete Location", expanded=True):
            st.warning("Updates push directly to DB. Deleting drops associated images and reviews.")
            categories = get_categories()
            # Update Form
            with st.form("update_loc_form"):
                u_name = st.text_input("Name", value=loc['name'])
                u_cat_col, u_add_col = st.columns(2)
                with u_cat_col:
                    u_cat = st.selectbox(
                        "Category",
                        categories["category_id"].tolist(),
                        index=categories["category_id"].tolist().index(loc['category_id']),
                        format_func=lambda cid: f"{cid} - {categories.loc[categories['category_id'] == cid, 'category_name'].iloc[0]}"
                    )
                with u_add_col:
                    u_addr = st.text_input("Address", value=loc['address'] if loc['address'] else "")
                
                u_desc = st.text_area("Description", value=loc['description'] if loc['description'] else "")
                sub_upd = st.form_submit_button("Submit Update")
            
            if sub_upd:
                update_location(loc_id, u_name, int(u_cat), u_addr, u_desc)
                st.success("Location updated successfully.")
                st.rerun()

            # Delete button
            if st.button("🗑️ Commit DELETE Location", type="primary"):
                delete_location(loc_id)
                st.session_state.selected_location_id = None
                st.success("Location completely deleted.")
                st.rerun()


    st.markdown("---")
    st.markdown("#### Images")
    # File Uploader
    if st.session_state.logged_in_user:
        upl_file = st.file_uploader("Upload Image to Gallery", type=["png", "jpg", "jpeg"], key="loc_img_upload")
        if upl_file is not None:
            # We must detect active submit because file_uploader re-runs immediately. We add a button.
            if st.button("Save Uploaded Image"):
                filepath = os.path.join(UPLOAD_DIR, upl_file.name)
                with open(filepath, "wb") as f:
                    f.write(upl_file.getbuffer())
                add_image(loc_id, filepath)
                st.success(f"Image {upl_file.name} uploaded successfully.")
                st.rerun()

    images_df = get_images_for_location(loc_id)
    if not images_df.empty:
        img_cols = st.columns(min(len(images_df), 4))
        for idx, row in images_df.iterrows():
            with img_cols[idx % 4]:
                st.image(row["image_url"], use_container_width=True, caption=f"Img {row['image_id']}")
    else:
        st.info("No images uploaded yet.")

    st.markdown("---")
    st.markdown("#### Reviews")
    review_btn_col, _ = st.columns([1, 4])
    with review_btn_col:
        if st.button("Write Review", key="open_review_btn"):
            if require_login("add a review"):
                st.session_state.show_add_review_for_selected = True

    if st.session_state.get("show_add_review_for_selected", False) and st.session_state.logged_in_user:
        with st.form("add_review_for_selected"):
            rating = st.slider("Rating", 1, 5, 4)
            comment = st.text_area("Comment")
            r_form_col1, r_form_col2 = st.columns(2)
            with r_form_col1:
                submitted = st.form_submit_button("Submit Review")
            with r_form_col2:
                cancel = st.form_submit_button("Cancel")

        if cancel:
            st.session_state.show_add_review_for_selected = False
            st.rerun()

        if submitted:
            try:
                avg_rating = add_review(
                    int(st.session_state.logged_in_user["user_id"]),
                    loc_id, int(rating), comment, date.today()
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
        for idx, r_row in reviews_df.iterrows():
            r_id = r_row['review_id']
            author = r_row['user_name']
            r_date = r_row['date']
            star_text = "⭐" * r_row['rating']
            st.markdown(f"**{author}** ({r_date}) - {star_text}\n\n{r_row['comment']}")
            
            # Show edit / delete controls only if the user owns the review
            if st.session_state.logged_in_user and st.session_state.logged_in_user['user_id'] == r_row['user_id']:
                ed_col1, ed_col2, _ = st.columns([1,1,4])
                with ed_col1:
                    if st.button("Edit", key=f"edit_rev_{r_id}", help="Edit your review"):
                        st.session_state[f"editing_review_{r_id}"] = True
                with ed_col2:
                    if st.button("Delete", key=f"del_rev_{r_id}", help="Delete your review"):
                        delete_review(int(r_id))
                        st.rerun()

                if st.session_state.get(f"editing_review_{r_id}", False):
                    with st.form(f"update_review_form_{r_id}"):
                        new_r = st.slider("New Rating", 1, 5, int(r_row['rating']), key=f"nr_{r_id}")
                        new_c = st.text_area("New Comment", value=r_row['comment'], key=f"nc_{r_id}")
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.form_submit_button("Confirm Update"):
                                update_review(int(r_id), new_r, new_c)
                                st.session_state[f"editing_review_{r_id}"] = False
                                st.rerun()
                        with c2:
                            if st.form_submit_button("Cancel Update"):
                                st.session_state[f"editing_review_{r_id}"] = False
                                st.rerun()
            st.write("---")

    st.markdown("</div>", unsafe_allow_html=True)


def render_analytics_page() -> None:
    st.subheader("Map Database")

    st.markdown("#### Average Rating Per Location")
    safe_df(average_rating_per_location())

    st.markdown("#### Top Rated Locations")
    safe_df(top_rated_locations(min_reviews=1))

    st.markdown("#### Most Reviewed Locations")
    safe_df(most_reviewed_locations())

    st.markdown("#### Users With Most Reviews")
    safe_df(users_with_most_reviews())


def render_advanced_sql_page() -> None:
    st.subheader("Advanced SQL (Pure SQLite Mode)")
    st.caption("Transactions, SET operations, Cursors and Explicit Logic blocks translated fully to SQLite functionality.")

    # ------------------------------------------------------------------
    # SET OPERATIONS
    # ------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 🔀 Set Operations")

    with st.expander("UNION — Noteworthy Locations (Top-Rated OR Most-Reviewed)", expanded=True):
        safe_df(locations_union_high_activity(), "No noteworthy locations found.")

    with st.expander("EXCEPT — Popular But Not Top-Rated", expanded=False):
        safe_df(active_but_not_top_rated(), "All reviewed locations are top-rated.")

    with st.expander("INTERSECT — Favorited AND Reviewed Locations", expanded=False):
        safe_df(common_favorites_and_reviewed(), "No locations appear in both Favorites and Reviews.")

    # ------------------------------------------------------------------
    # ADVANCED SUBQUERIES
    # ------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 🔍 Advanced Subqueries")

    with st.expander("EXISTS — Users With at Least One 5-Star Review", expanded=True):
        safe_df(users_with_five_star_review(), "No users have given a 5-star review.")

    with st.expander("ALL — Best Location in Each Category (beats ALL others)", expanded=False):
        safe_df(locations_above_all_in_category(), "No location exclusively leads its category.")

    with st.expander("Correlated Scalar Subquery — Location vs. Category Average", expanded=False):
        safe_df(best_per_category_correlated(), "No reviewed locations found.")

    with st.expander("NOT EXISTS (Double Negation) — Users Who Reviewed All Categories", expanded=False):
        safe_df(users_who_reviewed_all_categories(), "No user has reviewed all categories.")

    # ------------------------------------------------------------------
    # EXPLICIT TRANSACTION CONTROL
    # ------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 💾 Explicit Transaction Control (SAVEPOINT / ROLLBACK TO / RELEASE)")
    st.caption("Demonstrates explicit logic rollback in SQLite text paths natively.")

    with st.expander("Run SAVEPOINT Transaction Demo", expanded=True):
        all_reviews = _to_df_for_ui("SELECT review_id, user_id, location_id, rating, comment FROM Reviews ORDER BY review_id")
        if all_reviews.empty:
            st.info("No reviews yet. Load sample data first.")
        else:
            safe_df(all_reviews)
            txn_col1, txn_col2 = st.columns(2)
            with txn_col1:
                review_ids = all_reviews["review_id"].tolist()
                selected_rid = st.selectbox("Select Review ID to update", review_ids, key="txn_review_id")
            with txn_col2:
                new_rating_input = st.number_input("New Rating (0 or 6 to ROLLBACK)", min_value=0, max_value=6, value=4, key="txn_new_rating")
            if st.button("▶ Execute Transaction", key="run_txn"):
                res = demo_savepoint_transaction(int(selected_rid), int(new_rating_input))
                if res["status"] == "committed":
                    st.success(f"✅ COMMITTED — {res['message']}")
                elif res["status"] == "rolled_back":
                    st.warning(f"↩️ ROLLED BACK — {res['message']}")
                else:
                    st.error(f"❌ ERROR — {res['message']}")

    # ------------------------------------------------------------------
    # CURSOR-BASED ROUTINE
    # ------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 🔁 Python-level DB Cursor — Flag Low-Rated Locations")
    st.caption("Uses an active DB-API Python cursor iterating sequentially inside a transaction block to update `LocationStatus`.")

    with st.expander("Run Cursor Routine", expanded=True):
        threshold_val = st.slider("Flag threshold", min_value=1.0, max_value=5.0, value=3.5, step=0.5, key="cursor_threshold")
        if st.button("▶ Run Cursor Flagging Routine", key="run_cursor"):
            with st.spinner("Running cursor loop..."):
                status_df = flag_low_rated_locations(threshold=float(threshold_val))
            st.success("Cursor routine complete.")
            safe_df(status_df)
        else:
            existing = get_location_status()
            if not existing.empty:
                st.markdown("**Current LocationStatus table:**")
                safe_df(existing)
            else:
                st.info("Click to run cursor.")

    # ------------------------------------------------------------------
    # REVIEW AUDIT LOG
    # ------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 📋 Review Audit Log (SQLite AFTER UPDATE Trigger)")
    safe_df(get_review_logs(), "No audit log entries yet.")


def _to_df_for_ui(sql: str) -> pd.DataFrame:
    from db import engine
    from sqlalchemy import text
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
    st.markdown('<p class="main-title">Manipal Location Engine</p>', unsafe_allow_html=True)
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

    pg_cols = st.columns(3)
    pages = [
        ("Map View", "map", ":material/map:"),
        ("Analytics", "analytics", ":material/query_stats:"),
        ("Advanced SQL", "advanced", ":material/code:"),
    ]
    for col, (label, page_key, icon) in zip(pg_cols, pages):
        with col:
            if st.button(
                label,
                icon=icon,
                type="primary" if st.session_state.current_page == page_key else "secondary",
                use_container_width=True,
                key=f"nav_{page_key}",
            ):
                st.session_state.current_page = page_key

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
    elif st.session_state.current_page == "advanced":
        render_advanced_sql_page()
    else:
        locations_df = search_locations_by_category(st.session_state.selected_category_id)
        render_map(locations_df)

        if st.session_state.last_clicked_coords:
            lat, lng = st.session_state.last_clicked_coords
            st.caption(f"Last clicked map position: {lat:.6f}, {lng:.6f}")

        render_location_details()
