"""All SQL operations for the Manipal Location & Review Management System (SQLite strictly)."""

from datetime import date
from typing import Any

import pandas as pd
from sqlalchemy import text

from db import engine


def _to_df(sql: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)


def _execute(sql: str, params: dict[str, Any] | None = None) -> None:
    with engine.begin() as conn:
        conn.execute(text(sql), params or {})


# -----------------------------
# Authentication
# -----------------------------

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
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT user_id, name, email, password_hash
                FROM Users
                WHERE email = :email
                """
            ),
            {"email": email.strip().lower()},
        ).mappings().first()

    return dict(row) if row else None


# -----------------------------
# Category CRUD
# -----------------------------

def add_category(category_name: str) -> None:
    _execute(
        """
        INSERT INTO Categories(category_name)
        VALUES (:category_name)
        """,
        {"category_name": category_name.strip()},
    )


def get_categories() -> pd.DataFrame:
    return _to_df("SELECT * FROM Categories ORDER BY category_name")


# -----------------------------
# Location CRUD
# -----------------------------

def add_location(
    name: str,
    category_id: int,
    address: str,
    description: str,
    latitude: float,
    longitude: float,
) -> None:
    _execute(
        """
        INSERT INTO Locations(name, category_id, address, description, latitude, longitude)
        VALUES (:name, :category_id, :address, :description, :latitude, :longitude)
        """,
        {
            "name": name.strip(),
            "category_id": category_id,
            "address": address.strip(),
            "description": description.strip(),
            "latitude": latitude,
            "longitude": longitude,
        },
    )


def update_location(
    location_id: int,
    name: str,
    category_id: int,
    address: str,
    description: str,
) -> None:
    """Explicitly updates core fields of a location."""
    _execute(
        """
        UPDATE Locations
        SET name = :name,
            category_id = :category_id,
            address = :address,
            description = :description
        WHERE location_id = :location_id
        """,
        {
            "name": name.strip(),
            "category_id": category_id,
            "address": address.strip(),
            "description": description.strip(),
            "location_id": location_id,
        },
    )


def delete_location(location_id: int) -> None:
    """Manually cleans up location-referenced items then drops the location.
    Required explicitly if ON DELETE CASCADE is disabled or engine drops logic."""
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM ReviewLogs WHERE review_id IN (SELECT review_id FROM Reviews WHERE location_id = :lid)"), {"lid": location_id})
        conn.execute(text("DELETE FROM Reviews WHERE location_id = :lid"), {"lid": location_id})
        conn.execute(text("DELETE FROM Images WHERE location_id = :lid"), {"lid": location_id})
        conn.execute(text("DELETE FROM Favorites WHERE location_id = :lid"), {"lid": location_id})
        conn.execute(text("DELETE FROM LocationStatus WHERE location_id = :lid"), {"lid": location_id})
        conn.execute(text("DELETE FROM Locations WHERE location_id = :lid"), {"lid": location_id})


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
            l.longitude
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
            l.longitude
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
            ROUND(AVG(r.rating), 2) AS avg_rating,
            COUNT(r.review_id) AS review_count
        FROM Locations l
        LEFT JOIN Categories c ON l.category_id = c.category_id
        LEFT JOIN Reviews r ON l.location_id = r.location_id
        WHERE l.location_id = :location_id
        GROUP BY l.location_id, l.name, l.category_id, c.category_name, l.address, l.description, l.latitude, l.longitude
        """,
        {"location_id": location_id},
    )


# -----------------------------
# Reviews CRUD
# -----------------------------

def add_review(
    user_id: int,
    location_id: int,
    rating: int,
    comment: str,
    review_date: date,
) -> float:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO Reviews(user_id, location_id, rating, comment, date)
                VALUES (:user_id, :location_id, :rating, :comment, :review_date)
                """
            ),
            {
                "user_id": user_id,
                "location_id": location_id,
                "rating": rating,
                "comment": comment.strip(),
                "review_date": review_date,
            },
        )
        avg_rating = conn.execute(
            text("SELECT ROUND(AVG(rating), 2) FROM Reviews WHERE location_id = :location_id"),
            {"location_id": location_id},
        ).scalar_one()

    return float(avg_rating)


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
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM ReviewLogs WHERE review_id = :review_id"), {"review_id": review_id})
        conn.execute(text("DELETE FROM Reviews WHERE review_id = :review_id"), {"review_id": review_id})


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


# -----------------------------
# Favorites
# -----------------------------

def add_favorite(user_id: int, location_id: int) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("INSERT OR IGNORE INTO Favorites(user_id, location_id) VALUES (:user_id, :location_id)"),
            {"user_id": user_id, "location_id": location_id},
        )


# -----------------------------
# Images Feature
# -----------------------------

def add_image(location_id: int, local_file_url: str) -> None:
    _execute(
        "INSERT INTO Images(location_id, image_url) VALUES (:location_id, :image_url)",
        {"location_id": location_id, "image_url": local_file_url}
    )


def get_images_for_location(location_id: int) -> pd.DataFrame:
    return _to_df(
        "SELECT image_id, image_url FROM Images WHERE location_id = :location_id ORDER BY image_id DESC",
        {"location_id": location_id}
    )


# -----------------------------
# Standard Analytics Queries
# -----------------------------

def average_rating_per_location() -> pd.DataFrame:
    return _to_df(
        """
        SELECT
            l.location_id,
            l.name AS location_name,
            ROUND(AVG(r.rating), 2) AS avg_rating,
            COUNT(r.review_id) AS review_count
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
            l.name AS location_name,
            ROUND(AVG(r.rating), 2) AS avg_rating,
            COUNT(r.review_id) AS review_count
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

# -----------------------------
# SET OPERATIONS
# -----------------------------

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

# -----------------------------
# ADVANCED SUBQUERIES
# -----------------------------

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
            JOIN Reviews r ON l.location_id = r.location_id
            GROUP BY l.location_id, l.name, l.category_id, c.category_name
        )
        SELECT la.location_id, la.name AS location_name, la.category_name, la.avg_rating
        FROM loc_avgs la
        WHERE NOT EXISTS (
            SELECT 1 FROM loc_avgs peer
            WHERE peer.category_id = la.category_id AND peer.location_id != la.location_id AND peer.avg_rating >= la.avg_rating
        )
        ORDER BY la.category_name, la.avg_rating DESC
        """
    )

def best_per_category_correlated() -> pd.DataFrame:
    return _to_df(
        """
        SELECT
            l.location_id, l.name AS location_name, c.category_name,
            ROUND(AVG(r.rating), 2) AS location_avg,
            (SELECT ROUND(AVG(r2.rating), 2) FROM Reviews r2 JOIN Locations l2 ON r2.location_id = l2.location_id WHERE l2.category_id = l.category_id) AS category_avg
        FROM Locations l
        JOIN Categories c ON l.category_id = c.category_id
        JOIN Reviews r ON l.location_id = r.location_id
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
        ) AND EXISTS (SELECT 1 FROM Reviews r3 WHERE r3.user_id = u.user_id)
        ORDER BY u.name
        """
    )


# -----------------------------
# EXPLICIT TRANSACTION CONTROL
# -----------------------------

def demo_savepoint_transaction(review_id: int, new_rating: int) -> dict:
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT rating FROM Reviews WHERE review_id = :rid"),
            {"rid": review_id},
        ).fetchone()

        if row is None:
            return {"status": "error", "message": f"Review {review_id} not found.", "old_rating": None}

        old_rating = row[0]
        conn.execute(text("SAVEPOINT sp_rating_update"))

        if new_rating < 1 or new_rating > 5:
            conn.execute(text("ROLLBACK TO SAVEPOINT sp_rating_update"))
            conn.execute(text("RELEASE SAVEPOINT sp_rating_update"))
            return {
                "status": "rolled_back",
                "message": f"Invalid rating {new_rating}. Must be 1–5. ROLLBACK TO SAVEPOINT executed. No change made.",
                "old_rating": old_rating,
            }

        conn.execute(
            text("UPDATE Reviews SET rating = :new_rating WHERE review_id = :rid"),
            {"new_rating": new_rating, "rid": review_id},
        )
        conn.execute(text("RELEASE SAVEPOINT sp_rating_update"))
        return {
            "status": "committed",
            "message": f"Rating updated from {old_rating} → {new_rating}. SAVEPOINT released, transaction COMMITTED.",
            "old_rating": old_rating,
        }

# -----------------------------
# CURSOR-BASED ROUTINE (Python-level cursor over raw SQL)
# -----------------------------

def flag_low_rated_locations(threshold: float = 3.5) -> pd.DataFrame:
    """ Python-level cursor loop (DB-API cursor, analogous to PL/SQL explicit cursor loop) """
    with engine.begin() as conn:
        cursor_result = conn.execute(
            text(
                """
                SELECT l.location_id, ROUND(AVG(r.rating), 2) AS avg_r
                FROM Locations l
                LEFT JOIN Reviews r ON l.location_id = r.location_id
                GROUP BY l.location_id
                """
            )
        )
        rows = cursor_result.fetchall()
        for row in rows:
            loc_id = row[0]
            avg_r = row[1]
            status = "flagged" if (avg_r is None or avg_r < threshold) else "good"
            conn.execute(
                text(
                    """
                    INSERT INTO LocationStatus(location_id, status, last_updated)
                    VALUES (:lid, :status, CURRENT_TIMESTAMP)
                    ON CONFLICT(location_id) DO UPDATE SET status = excluded.status, last_updated = excluded.last_updated
                    """
                ),
                {"lid": loc_id, "status": status},
            )

    return _to_df(
        """
        SELECT ls.location_id, l.name AS location_name, ROUND(AVG(r.rating), 2) AS avg_rating, ls.status, ls.last_updated
        FROM LocationStatus ls
        JOIN Locations l ON ls.location_id = l.location_id
        LEFT JOIN Reviews r ON l.location_id = r.location_id
        GROUP BY ls.location_id, l.name, ls.status, ls.last_updated
        ORDER BY ls.status DESC, avg_rating ASC
        """
    )


def get_review_logs() -> pd.DataFrame:
    return _to_df("SELECT rl.log_id, rl.review_id, rl.action, rl.old_rating, rl.new_rating, rl.log_time FROM ReviewLogs rl ORDER BY rl.log_time DESC, rl.log_id DESC")

def get_location_status() -> pd.DataFrame:
    return _to_df("SELECT ls.location_id, l.name AS location_name, ls.status, ls.last_updated FROM LocationStatus ls JOIN Locations l ON ls.location_id = l.location_id ORDER BY ls.status DESC, l.name")
