"""All SQL operations for the Manipal Location & Review Management System.

Uses Python's built-in sqlite3 directly — every query is a raw SQL string.
No ORM, no abstraction layer.
"""

from datetime import date
from typing import Any

import pandas as pd

from db import get_conn


# ── Internal helpers ───────────────────────────────────────────────────────────

def _to_df(sql: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
    """Execute a SELECT and return results as a DataFrame."""
    conn = get_conn()
    try:
        cursor = conn.execute(sql, params or {})
        cols = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return pd.DataFrame([dict(zip(cols, row)) for row in rows], columns=cols)
    finally:
        conn.close()


def _execute(sql: str, params: dict[str, Any] | None = None) -> None:
    """Execute a single write statement inside its own commit."""
    conn = get_conn()
    try:
        conn.execute(sql, params or {})
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Authentication ─────────────────────────────────────────────────────────────

def register_user(name: str, email: str, password_hash: str) -> None:
    _execute(
        """
        INSERT INTO Users(name, email, password_hash)
        VALUES (:name, :email, :password_hash)
        """,
        {
            "name": name.strip(),
            "email": email.strip().lower(),
            "password_hash": password_hash,
        },
    )


def get_user_by_email(email: str) -> dict[str, Any] | None:
    conn = get_conn()
    try:
        cursor = conn.execute(
            """
            SELECT user_id, name, email, password_hash
            FROM Users
            WHERE email = :email
            """,
            {"email": email.strip().lower()},
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ── Category CRUD ──────────────────────────────────────────────────────────────

def add_category(category_name: str) -> None:
    _execute(
        "INSERT INTO Categories(category_name) VALUES (:category_name)",
        {"category_name": category_name.strip()},
    )


def get_categories() -> pd.DataFrame:
    return _to_df("SELECT * FROM Categories ORDER BY category_name")


# ── Location CRUD ──────────────────────────────────────────────────────────────

def add_location(
    name: str,
    category_id: int,
    address: str,
    description: str,
    latitude: float,
    longitude: float,
    created_by: int | None = None,
) -> None:
    params = {
        "name": name.strip(),
        "category_id": category_id,
        "address": address.strip(),
        "description": description.strip(),
        "latitude": latitude,
        "longitude": longitude,
        "created_by": created_by,
    }
    if created_by is None:
        _execute(
            """
            INSERT INTO Locations(name, category_id, address, description, latitude, longitude)
            VALUES (:name, :category_id, :address, :description, :latitude, :longitude)
            """,
            params,
        )
        return

    _execute(
        """
        INSERT INTO Locations(name, category_id, address, description, latitude, longitude, created_by, created_at)
        VALUES (:name, :category_id, :address, :description, :latitude, :longitude, :created_by, CURRENT_TIMESTAMP)
        """,
        params,
    )


def update_location(
    location_id: int,
    name: str,
    category_id: int,
    address: str,
    description: str,
    latitude: float | None = None,
    longitude: float | None = None,
) -> None:
    """Explicitly updates core fields of a location."""
    _execute(
        """
        UPDATE Locations
        SET name        = :name,
            category_id = :category_id,
            address     = :address,
            description = :description,
            latitude    = COALESCE(:latitude, latitude),
            longitude   = COALESCE(:longitude, longitude)
        WHERE location_id = :location_id
        """,
        {
            "name": name.strip(),
            "category_id": category_id,
            "address": address.strip(),
            "description": description.strip(),
            "latitude": latitude,
            "longitude": longitude,
            "location_id": location_id,
        },
    )


def delete_location(location_id: int) -> None:
    """Delete a location — the trg_archive_location_delete trigger fires automatically."""
    _execute(
        "DELETE FROM Locations WHERE location_id = :lid",
        {"lid": location_id},
    )


def get_locations() -> pd.DataFrame:
    return _to_df(
        """
        SELECT
            l.location_id,
            l.name,
            l.category_id,
            c.category_name,
            l.address,
            l.description,
            l.latitude,
            l.longitude,
            l.created_by
        FROM Locations l
        LEFT JOIN Categories c ON l.category_id = c.category_id
        ORDER BY l.name
        """
    )


def search_locations_by_category(category_id: int | None) -> pd.DataFrame:
    if category_id is None:
        return get_locations()
    return _to_df(
        """
        SELECT
            l.location_id,
            l.name,
            l.category_id,
            c.category_name,
            l.address,
            l.description,
            l.latitude,
            l.longitude,
            l.created_by
        FROM Locations l
        JOIN Categories c ON l.category_id = c.category_id
        WHERE l.category_id = :category_id
        ORDER BY l.name
        """,
        {"category_id": category_id},
    )


def get_location_details(location_id: int) -> pd.DataFrame:
    return _to_df(
        """
        SELECT
            l.location_id,
            l.name,
            l.category_id,
            c.category_name,
            l.address,
            l.description,
            l.latitude,
            l.longitude,
            l.created_by,
            ROUND((SELECT AVG(r.rating) FROM Reviews r WHERE r.location_id = l.location_id), 2) AS avg_rating,
            (SELECT COUNT(*) FROM Reviews r WHERE r.location_id = l.location_id) AS review_count,
            (SELECT COUNT(*) FROM Favorites f WHERE f.location_id = l.location_id) AS favorite_count
        FROM Locations l
        LEFT JOIN Categories c ON l.category_id = c.category_id
        WHERE l.location_id = :location_id
        """,
        {"location_id": location_id},
    )


# ── Reviews CRUD ───────────────────────────────────────────────────────────────

def add_review(
    user_id: int,
    location_id: int,
    rating: int,
    comment: str,
    review_date: date,
) -> float:
    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO Reviews(user_id, location_id, rating, comment, date)
            VALUES (:user_id, :location_id, :rating, :comment, :review_date)
            """,
            {
                "user_id": user_id,
                "location_id": location_id,
                "rating": rating,
                "comment": comment.strip(),
                "review_date": str(review_date),
            },
        )
        cursor = conn.execute(
            "SELECT ROUND(AVG(rating), 2) FROM Reviews WHERE location_id = :location_id",
            {"location_id": location_id},
        )
        avg_rating = cursor.fetchone()[0]
        conn.commit()
        return float(avg_rating)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_review(review_id: int, new_rating: int, new_comment: str) -> None:
    _execute(
        """
        UPDATE Reviews
        SET rating = :rating, comment = :comment
        WHERE review_id = :review_id
        """,
        {"rating": new_rating, "comment": new_comment.strip(), "review_id": review_id},
    )


def delete_review(review_id: int) -> None:
    conn = get_conn()
    try:
        conn.execute(
            "DELETE FROM ReviewLogs WHERE review_id = :review_id",
            {"review_id": review_id},
        )
        conn.execute(
            "DELETE FROM Reviews WHERE review_id = :review_id",
            {"review_id": review_id},
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_reviews_for_location(location_id: int) -> pd.DataFrame:
    return _to_df(
        """
        SELECT
            r.review_id,
            r.user_id,
            u.name AS user_name,
            r.rating,
            r.comment,
            r.date
        FROM Reviews r
        JOIN Users u ON r.user_id = u.user_id
        WHERE r.location_id = :location_id
        ORDER BY r.date DESC, r.review_id DESC
        """,
        {"location_id": location_id},
    )


# ── Favorites ──────────────────────────────────────────────────────────────────

def add_favorite(user_id: int, location_id: int) -> None:
    _execute(
        "INSERT OR IGNORE INTO Favorites(user_id, location_id) VALUES (:user_id, :location_id)",
        {"user_id": user_id, "location_id": location_id},
    )


def remove_favorite(user_id: int, location_id: int) -> None:
    _execute(
        "DELETE FROM Favorites WHERE user_id = :user_id AND location_id = :location_id",
        {"user_id": user_id, "location_id": location_id},
    )


def get_favorite_location_ids(user_id: int) -> list[int]:
    df = _to_df(
        "SELECT location_id FROM Favorites WHERE user_id = :user_id ORDER BY location_id",
        {"user_id": user_id},
    )
    if df.empty:
        return []
    return [int(v) for v in df["location_id"].tolist()]


# ── Images ─────────────────────────────────────────────────────────────────────

def add_image(location_id: int, local_file_url: str, uploaded_by: int | None = None) -> None:
    columns = "location_id, image_url, uploaded_by"
    if uploaded_by is None:
        columns = "location_id, image_url"
    _execute(
        f"INSERT INTO Images({columns}{', uploaded_at' if uploaded_by is not None else ''}) VALUES (:location_id, :image_url{', :uploaded_by' if uploaded_by is not None else ''}{', CURRENT_TIMESTAMP' if uploaded_by is not None else ''})",
        {"location_id": location_id, "image_url": local_file_url, "uploaded_by": uploaded_by},
    )


def get_images_for_location(location_id: int) -> pd.DataFrame:
    return _to_df(
        "SELECT image_id, image_url, uploaded_by FROM Images WHERE location_id = :location_id ORDER BY image_id DESC",
        {"location_id": location_id},
    )


def get_locations_added_by_user(user_id: int) -> pd.DataFrame:
    return _to_df(
        """
        SELECT
            l.location_id,
            l.name AS location_name,
            c.category_name,
            l.address,
            l.created_at
        FROM Locations l
        LEFT JOIN Categories c ON l.category_id = c.category_id
        WHERE l.created_by = :user_id
        ORDER BY l.created_at DESC, l.location_id DESC
        """,
        {"user_id": user_id},
    )


def get_reviews_by_user(user_id: int) -> pd.DataFrame:
    return _to_df(
        """
        SELECT
            r.review_id,
            r.location_id,
            l.name AS location_name,
            r.rating,
            r.comment,
            r.date
        FROM Reviews r
        JOIN Locations l ON r.location_id = l.location_id
        WHERE r.user_id = :user_id
        ORDER BY r.date DESC, r.review_id DESC
        """,
        {"user_id": user_id},
    )


def get_images_uploaded_by_user(user_id: int) -> pd.DataFrame:
    return _to_df(
        """
        SELECT
            i.image_id,
            i.location_id,
            l.name AS location_name,
            i.image_url,
            i.uploaded_at
        FROM Images i
        JOIN Locations l ON i.location_id = l.location_id
        WHERE i.uploaded_by = :user_id
        ORDER BY i.uploaded_at DESC, i.image_id DESC
        """,
        {"user_id": user_id},
    )


def get_user_contribution_summary(user_id: int) -> pd.DataFrame:
    return _to_df(
        """
        SELECT
            (SELECT COUNT(*) FROM Locations WHERE created_by = :user_id) AS locations_added,
            (SELECT COUNT(*) FROM Reviews   WHERE user_id = :user_id) AS reviews_written,
            (SELECT COUNT(*) FROM Images    WHERE uploaded_by = :user_id) AS images_uploaded,
            (SELECT COUNT(*) FROM Favorites WHERE user_id = :user_id) AS favorites_saved
        """,
        {"user_id": user_id},
    )


def get_location_spotlight_insights(location_id: int) -> pd.DataFrame:
    return _to_df(
        """
        WITH base AS (
            SELECT
                l.location_id,
                l.category_id,
                l.name AS location_name,
                c.category_name,
                ROUND((SELECT AVG(r.rating) FROM Reviews r WHERE r.location_id = l.location_id), 2) AS avg_rating,
                (SELECT COUNT(*) FROM Reviews r WHERE r.location_id = l.location_id) AS review_count,
                (SELECT COUNT(*) FROM Favorites f WHERE f.location_id = l.location_id) AS favorite_count,
                (SELECT COUNT(*) FROM Images i WHERE i.location_id = l.location_id) AS image_count
            FROM Locations l
            LEFT JOIN Categories c ON l.category_id = c.category_id
            WHERE l.location_id = :location_id
        ),
        ranked AS (
            SELECT
                l.location_id,
                RANK() OVER (
                    PARTITION BY l.category_id
                    ORDER BY
                        COALESCE((SELECT AVG(r.rating) FROM Reviews r WHERE r.location_id = l.location_id), 0) DESC,
                        (SELECT COUNT(*) FROM Reviews r WHERE r.location_id = l.location_id) DESC,
                        (SELECT COUNT(*) FROM Favorites f WHERE f.location_id = l.location_id) DESC
                ) AS category_rank
            FROM Locations l
            WHERE l.category_id = (SELECT category_id FROM Locations WHERE location_id = :location_id)
        ),
        trend_source AS (
            SELECT
                rating,
                ROW_NUMBER() OVER (ORDER BY date DESC, review_id DESC) AS rn
            FROM Reviews
            WHERE location_id = :location_id
        ),
        trend AS (
            SELECT
                ROUND(AVG(CASE WHEN rn <= 3 THEN rating END), 2) AS recent_avg,
                ROUND(AVG(CASE WHEN rn BETWEEN 4 AND 6 THEN rating END), 2) AS previous_avg
            FROM trend_source
        )
        SELECT
            base.location_id,
            base.location_name,
            base.category_name,
            base.avg_rating,
            base.review_count,
            base.favorite_count,
            base.image_count,
            ranked.category_rank,
            trend.recent_avg,
            trend.previous_avg,
            CASE
                WHEN trend.recent_avg IS NULL OR trend.previous_avg IS NULL THEN 'No trend yet'
                WHEN trend.recent_avg > trend.previous_avg THEN 'Improving'
                WHEN trend.recent_avg < trend.previous_avg THEN 'Softening'
                ELSE 'Stable'
            END AS rating_trend
        FROM base
        LEFT JOIN ranked ON ranked.location_id = base.location_id
        CROSS JOIN trend
        """,
        {"location_id": location_id},
    )


def locations_popular_but_underrated(min_reviews: int = 2, max_avg: float = 4.0) -> pd.DataFrame:
    return _to_df(
        """
        SELECT
            l.location_id,
            l.name AS location_name,
            ROUND(AVG(r.rating), 2) AS avg_rating,
            COUNT(r.review_id) AS review_count,
            (SELECT COUNT(*) FROM Favorites f WHERE f.location_id = l.location_id) AS favorite_count
        FROM Locations l
        JOIN Reviews r ON l.location_id = r.location_id
        GROUP BY l.location_id, l.name
        HAVING COUNT(r.review_id) >= :min_reviews
           AND ROUND(AVG(r.rating), 2) < :max_avg
        ORDER BY review_count DESC, avg_rating ASC, l.name
        """,
        {"min_reviews": min_reviews, "max_avg": max_avg},
    )


# ── Standard Analytics Queries ─────────────────────────────────────────────────

def average_rating_per_location() -> pd.DataFrame:
    return _to_df(
        """
        SELECT
            l.location_id,
            l.name                    AS location_name,
            ROUND(AVG(r.rating), 2)   AS avg_rating,
            COUNT(r.review_id)        AS review_count
        FROM Locations l
        LEFT JOIN Reviews r ON l.location_id = r.location_id
        GROUP BY l.location_id, l.name
        ORDER BY CASE WHEN avg_rating IS NULL THEN 1 ELSE 0 END, avg_rating DESC, l.name
        """
    )


def top_rated_locations(min_reviews: int = 1) -> pd.DataFrame:
    return _to_df(
        """
        SELECT
            l.location_id,
            l.name                    AS location_name,
            ROUND(AVG(r.rating), 2)   AS avg_rating,
            COUNT(r.review_id)        AS review_count
        FROM Locations l
        JOIN Reviews r ON l.location_id = r.location_id
        GROUP BY l.location_id, l.name
        HAVING COUNT(r.review_id) >= :min_reviews
        ORDER BY avg_rating DESC, review_count DESC, l.name
        """,
        {"min_reviews": min_reviews},
    )


def most_reviewed_locations() -> pd.DataFrame:
    return _to_df(
        """
        WITH review_counts AS (
            SELECT location_id, COUNT(*) AS total_reviews
            FROM Reviews
            GROUP BY location_id
        )
        SELECT l.location_id, l.name AS location_name, rc.total_reviews
        FROM review_counts rc
        JOIN Locations l ON rc.location_id = l.location_id
        ORDER BY rc.total_reviews DESC, l.name
        """
    )


def most_favorited_locations(min_favorites: int = 1) -> pd.DataFrame:
    return _to_df(
        """
        SELECT
            l.location_id,
            l.name AS location_name,
            COUNT(f.user_id) AS favorite_count
        FROM Locations l
        JOIN Favorites f ON l.location_id = f.location_id
        GROUP BY l.location_id, l.name
        HAVING COUNT(f.user_id) >= :min_favorites
        ORDER BY favorite_count DESC, l.name
        """,
        {"min_favorites": min_favorites},
    )


def get_flagged_locations() -> pd.DataFrame:
    """Retrieve all locations marked as flagged by the cursor-based routine.
    
    Uses the LocationStatus table populated by flag_low_rated_locations cursor.
    Returns locations where status = 'flagged' (average rating below threshold).
    """
    return _to_df(
        """
        SELECT
            l.location_id,
            l.name AS location_name,
            ls.status,
            ROUND(AVG(r.rating), 2) AS avg_rating,
            COUNT(r.review_id) AS review_count
        FROM Locations l
        JOIN LocationStatus ls ON l.location_id = ls.location_id
        LEFT JOIN Reviews r ON l.location_id = r.location_id
        WHERE ls.status = 'flagged'
        GROUP BY l.location_id, l.name, ls.status
        ORDER BY avg_rating ASC, l.name
        """
    )


def recently_reviewed_locations(limit: int = 50) -> pd.DataFrame:
    return _to_df(
        """
        SELECT
            l.location_id,
            l.name AS location_name,
            MAX(r.date) AS last_review_date,
            COUNT(r.review_id) AS review_count
        FROM Locations l
        JOIN Reviews r ON l.location_id = r.location_id
        GROUP BY l.location_id, l.name
        ORDER BY last_review_date DESC, review_count DESC, l.name
        LIMIT :limit
        """,
        {"limit": limit},
    )


def users_with_most_reviews() -> pd.DataFrame:
    return _to_df(
        """
        WITH user_review_counts AS (
            SELECT user_id, COUNT(*) AS total_reviews
            FROM Reviews
            GROUP BY user_id
        )
        SELECT u.user_id, u.name AS user_name, u.email, urc.total_reviews
        FROM user_review_counts urc
        JOIN Users u ON urc.user_id = u.user_id
        ORDER BY urc.total_reviews DESC, u.name
        """
    )


def get_category_activity_summary() -> pd.DataFrame:
    return _to_df(
        """
        SELECT
            category_id,
            category_name,
            location_count,
            reviewed_locations,
            category_avg_rating,
            five_star_reviews,
            category_band
        FROM category_activity_summary
        ORDER BY
            CASE WHEN category_avg_rating IS NULL THEN 1 ELSE 0 END,
            category_avg_rating DESC,
            category_name
        """
    )


def location_rating_bands() -> pd.DataFrame:
    return _to_df(
        """
        SELECT
            location_id,
            location_name,
            avg_rating,
            review_count,
            rating_band(avg_rating) AS rating_band
        FROM location_avg_rating
        ORDER BY
            CASE WHEN avg_rating IS NULL THEN 1 ELSE 0 END,
            avg_rating DESC,
            location_name
        """
    )


# ── Set Operations ─────────────────────────────────────────────────────────────

def locations_union_high_activity() -> pd.DataFrame:
    return _to_df(
        """
        SELECT l.location_id, l.name AS location_name, 'Top Rated' AS reason
        FROM Locations l
        JOIN Reviews r ON l.location_id = r.location_id
        GROUP BY l.location_id, l.name
        HAVING ROUND(AVG(r.rating), 2) >= 4.0
        UNION
        SELECT l.location_id, l.name AS location_name, 'Most Reviewed' AS reason
        FROM Locations l
        JOIN Reviews r ON l.location_id = r.location_id
        GROUP BY l.location_id, l.name
        HAVING COUNT(r.review_id) >= 2
        ORDER BY location_name
        """
    )


def active_but_not_top_rated() -> pd.DataFrame:
    return _to_df(
        """
        SELECT l.location_id, l.name AS location_name
        FROM Locations l
        JOIN Reviews r ON l.location_id = r.location_id
        GROUP BY l.location_id, l.name
        HAVING COUNT(r.review_id) >= 1
        EXCEPT
        SELECT l.location_id, l.name AS location_name
        FROM Locations l
        JOIN Reviews r ON l.location_id = r.location_id
        GROUP BY l.location_id, l.name
        HAVING ROUND(AVG(r.rating), 2) >= 4.0
        ORDER BY location_name
        """
    )


def common_favorites_and_reviewed() -> pd.DataFrame:
    return _to_df(
        """
        SELECT DISTINCT l.location_id, l.name AS location_name
        FROM Favorites f
        JOIN Locations l ON f.location_id = l.location_id
        INTERSECT
        SELECT DISTINCT l.location_id, l.name AS location_name
        FROM Reviews r
        JOIN Locations l ON r.location_id = l.location_id
        ORDER BY location_name
        """
    )


# ── Advanced Subqueries ────────────────────────────────────────────────────────

def users_with_five_star_review() -> pd.DataFrame:
    return _to_df(
        """
        SELECT u.user_id, u.name AS user_name, u.email
        FROM Users u
        WHERE EXISTS (
            SELECT 1 FROM Reviews r WHERE r.user_id = u.user_id AND r.rating = 5
        )
        ORDER BY u.name
        """
    )


def locations_above_all_in_category() -> pd.DataFrame:
    return _to_df(
        """
        WITH loc_avgs AS (
            SELECT
                l.location_id, l.name, l.category_id, c.category_name,
                ROUND(AVG(r.rating), 2) AS avg_rating
            FROM Locations l
            JOIN Categories c ON l.category_id = c.category_id
            JOIN Reviews r    ON l.location_id = r.location_id
            GROUP BY l.location_id, l.name, l.category_id, c.category_name
        )
        SELECT la.location_id, la.name AS location_name, la.category_name, la.avg_rating
        FROM loc_avgs la
        WHERE NOT EXISTS (
            SELECT 1 FROM loc_avgs peer
            WHERE peer.category_id = la.category_id
              AND peer.location_id != la.location_id
              AND peer.avg_rating >= la.avg_rating
        )
        ORDER BY la.category_name, la.avg_rating DESC
        """
    )


def best_per_category_correlated() -> pd.DataFrame:
    return _to_df(
        """
        SELECT
            l.location_id,
            l.name AS location_name,
            c.category_name,
            ROUND(AVG(r.rating), 2) AS location_avg,
            (
                SELECT ROUND(AVG(r2.rating), 2)
                FROM Reviews r2
                JOIN Locations l2 ON r2.location_id = l2.location_id
                WHERE l2.category_id = l.category_id
            ) AS category_avg
        FROM Locations l
        JOIN Categories c ON l.category_id = c.category_id
        JOIN Reviews r    ON l.location_id = r.location_id
        GROUP BY l.location_id, l.name, c.category_name, l.category_id
        ORDER BY c.category_name, location_avg DESC
        """
    )


def users_who_reviewed_all_categories() -> pd.DataFrame:
    return _to_df(
        """
        SELECT u.user_id, u.name AS user_name
        FROM Users u
        WHERE NOT EXISTS (
            SELECT DISTINCT l.category_id
            FROM Locations l
            WHERE EXISTS (SELECT 1 FROM Reviews r2 WHERE r2.location_id = l.location_id)
            EXCEPT
            SELECT DISTINCT l2.category_id
            FROM Reviews r
            JOIN Locations l2 ON r.location_id = l2.location_id
            WHERE r.user_id = u.user_id
        )
        AND EXISTS (SELECT 1 FROM Reviews r3 WHERE r3.user_id = u.user_id)
        ORDER BY u.name
        """
    )


# ── Explicit Transaction Control (SAVEPOINT) ───────────────────────────────────

def demo_savepoint_transaction(review_id: int, new_rating: int) -> dict:
    """Demonstrates SAVEPOINT / ROLLBACK TO SAVEPOINT / RELEASE SAVEPOINT."""
    conn = get_conn()
    conn.isolation_level = None  # manual transaction control for SAVEPOINT
    try:
        conn.execute("BEGIN")

        row = conn.execute(
            "SELECT rating FROM Reviews WHERE review_id = :rid",
            {"rid": review_id},
        ).fetchone()

        if row is None:
            conn.execute("ROLLBACK")
            return {"status": "error", "message": f"Review {review_id} not found.", "old_rating": None}

        old_rating = row[0]
        conn.execute("SAVEPOINT sp_rating_update")

        if new_rating < 1 or new_rating > 5:
            conn.execute("ROLLBACK TO SAVEPOINT sp_rating_update")
            conn.execute("RELEASE SAVEPOINT sp_rating_update")
            conn.execute("COMMIT")
            return {
                "status": "rolled_back",
                "message": f"Invalid rating {new_rating}. Must be 1–5. ROLLBACK TO SAVEPOINT executed. No change made.",
                "old_rating": old_rating,
            }

        conn.execute(
            "UPDATE Reviews SET rating = :new_rating WHERE review_id = :rid",
            {"new_rating": new_rating, "rid": review_id},
        )
        conn.execute("RELEASE SAVEPOINT sp_rating_update")
        conn.execute("COMMIT")
        return {
            "status": "committed",
            "message": f"Rating updated from {old_rating} → {new_rating}. SAVEPOINT released, transaction COMMITTED.",
            "old_rating": old_rating,
        }
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass
        raise
    finally:
        conn.close()


def archive_delete_location_transaction(location_id: int) -> dict[str, Any]:
    """Archive and delete a location using an explicit SAVEPOINT workflow."""
    conn = get_conn()
    conn.isolation_level = None  # manual transaction control for SAVEPOINT
    try:
        conn.execute("BEGIN")

        row = conn.execute(
            """
            SELECT
                l.location_id,
                l.name,
                (SELECT COUNT(*) FROM Reviews   WHERE location_id = l.location_id) AS review_count,
                (SELECT COUNT(*) FROM Images    WHERE location_id = l.location_id) AS image_count,
                (SELECT COUNT(*) FROM Favorites WHERE location_id = l.location_id) AS favorite_count
            FROM Locations l
            WHERE l.location_id = :lid
            """,
            {"lid": location_id},
        ).fetchone()

        if row is None:
            conn.execute("ROLLBACK")
            return {"status": "error", "message": f"Location {location_id} not found."}

        conn.execute("SAVEPOINT sp_location_archive_delete")
        try:
            conn.execute(
                "DELETE FROM Locations WHERE location_id = :lid",
                {"lid": location_id},
            )
            conn.execute("RELEASE SAVEPOINT sp_location_archive_delete")
        except Exception as ex:
            conn.execute("ROLLBACK TO SAVEPOINT sp_location_archive_delete")
            conn.execute("RELEASE SAVEPOINT sp_location_archive_delete")
            conn.execute("ROLLBACK")
            return {"status": "rolled_back", "message": f"Delete failed and was rolled back: {ex}"}

        audit_row = conn.execute(
            """
            SELECT audit_id, location_name, deleted_at, review_count, image_count, favorite_count, deletion_mode
            FROM DeletedLocationAudit
            WHERE location_id = :lid
            ORDER BY audit_id DESC
            LIMIT 1
            """,
            {"lid": location_id},
        ).fetchone()

        conn.execute("COMMIT")

        if audit_row is None:
            return {"status": "error", "message": "Delete completed but no archive record was captured."}

        return {
            "status": "committed",
            "message": (
                f"Deleted '{audit_row[1]}' and archived counts: "
                f"{audit_row[3]} reviews, {audit_row[4]} images, "
                f"{audit_row[5]} favorites."
            ),
        }
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass
        raise
    finally:
        conn.close()


# ── Cursor-Based Routine (Python-level cursor over raw SQL) ────────────────────

def flag_low_rated_locations(threshold: float = 3.5) -> pd.DataFrame:
    """Python-level cursor loop — analogous to an explicit PL/SQL cursor loop.

    Fetches all location averages, iterates row-by-row, and upserts into
    LocationStatus based on a threshold condition.
    """
    conn = get_conn()
    try:
        # Open the "cursor" — fetch the full result set
        cursor = conn.execute(
            """
            SELECT l.location_id, ROUND(AVG(r.rating), 2) AS avg_r
            FROM Locations l
            LEFT JOIN Reviews r ON l.location_id = r.location_id
            GROUP BY l.location_id
            """
        )
        rows = cursor.fetchall()

        # Iterate row-by-row and decide status (cursor loop body)
        for row in rows:
            loc_id = row[0]
            avg_r  = row[1]
            status = "flagged" if (avg_r is None or avg_r < threshold) else "good"
            conn.execute(
                """
                INSERT INTO LocationStatus(location_id, status, last_updated)
                VALUES (:lid, :status, CURRENT_TIMESTAMP)
                ON CONFLICT(location_id) DO UPDATE
                    SET status = excluded.status, last_updated = excluded.last_updated
                """,
                {"lid": loc_id, "status": status},
            )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    # Return the updated status table as a DataFrame
    return _to_df(
        """
        SELECT
            ls.location_id,
            l.name AS location_name,
            ROUND(AVG(r.rating), 2) AS avg_rating,
            ls.status,
            ls.last_updated
        FROM LocationStatus ls
        JOIN Locations l ON ls.location_id = l.location_id
        LEFT JOIN Reviews r ON l.location_id = r.location_id
        GROUP BY ls.location_id, l.name, ls.status, ls.last_updated
        ORDER BY ls.status DESC, avg_rating ASC
        """
    )


def parameterized_category_cursor(category_id: int, threshold: float = 4.0) -> pd.DataFrame:
    """Parameterized cursor analogue — scoped to a single category with a threshold.

    Simulates a parameterized explicit cursor by binding :category_id and
    then iterating the result set row-by-row to apply a classification decision.
    """
    conn = get_conn()
    try:
        cursor = conn.execute(
            """
            SELECT
                l.location_id,
                l.name AS location_name,
                c.category_name,
                ROUND(AVG(r.rating), 2) AS avg_rating,
                COUNT(r.review_id)      AS review_count
            FROM Locations l
            JOIN Categories c ON l.category_id = c.category_id
            LEFT JOIN Reviews r ON l.location_id = r.location_id
            WHERE l.category_id = :category_id
            GROUP BY l.location_id, l.name, c.category_name
            ORDER BY l.name
            """,
            {"category_id": category_id},
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    # Row-by-row classification (cursor loop body)
    results: list[dict[str, Any]] = []
    for row in rows:
        avg_rating     = float(row[3]) if row[3] is not None else None
        classification = "highlight" if avg_rating is not None and avg_rating >= threshold else "watch"
        results.append(
            {
                "location_id":     row[0],
                "location_name":   row[1],
                "category_name":   row[2],
                "avg_rating":      avg_rating,
                "review_count":    int(row[4]),
                "cursor_decision": classification,
            }
        )

    return pd.DataFrame(results)


# ── Audit Log Queries ──────────────────────────────────────────────────────────

def get_review_logs() -> pd.DataFrame:
    return _to_df(
        """
        SELECT rl.log_id, rl.review_id, rl.action, rl.old_rating, rl.new_rating, rl.log_time
        FROM ReviewLogs rl
        ORDER BY rl.log_time DESC, rl.log_id DESC
        """
    )


def get_location_status() -> pd.DataFrame:
    return _to_df(
        """
        SELECT ls.location_id, l.name AS location_name, ls.status, ls.last_updated
        FROM LocationStatus ls
        JOIN Locations l ON ls.location_id = l.location_id
        ORDER BY ls.status DESC, l.name
        """
    )


def get_deleted_location_audit() -> pd.DataFrame:
    return _to_df(
        """
        SELECT
            audit_id,
            location_id,
            location_name,
            deleted_at,
            review_count,
            image_count,
            favorite_count,
            deletion_mode
        FROM DeletedLocationAudit
        ORDER BY deleted_at DESC, audit_id DESC
        """
    )
