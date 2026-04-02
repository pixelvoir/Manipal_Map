"""All SQL operations for the Manipal Location & Review Management System.

Every function here is intentionally simple and beginner-friendly so the SQL
concepts are easy to explain in viva.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
from sqlalchemy import text

from db import engine, get_backend_name


# -----------------------------
# Utility helpers
# -----------------------------

def _to_df(sql: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)


def _execute(sql: str, params: dict[str, Any] | None = None) -> None:
    with engine.begin() as conn:
        conn.execute(text(sql), params or {})


# -----------------------------
# INSERT operations
# -----------------------------

def add_category(category_name: str) -> None:
    _execute(
        """
        INSERT INTO Categories(category_name)
        VALUES (:category_name)
        """,
        {"category_name": category_name.strip()},
    )


def add_user(name: str, email: str) -> None:
    _execute(
        """
        INSERT INTO Users(name, email)
        VALUES (:name, :email)
        """,
        {"name": name.strip(), "email": email.strip().lower()},
    )


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


def add_review_with_procedure(
    user_id: int,
    location_id: int,
    rating: int,
    comment: str,
    review_date: date,
) -> float:
    """Advanced concept: procedure/function style insertion.

    - PostgreSQL: calls SQL function `add_review_and_get_avg`.
    - SQLite: performs equivalent logic in one transaction.
    """
    backend = get_backend_name()

    if backend == "postgresql":
        with engine.connect() as conn:
            avg_rating = conn.execute(
                text(
                    """
                    SELECT add_review_and_get_avg(
                        :user_id, :location_id, :rating, :comment, :review_date
                    ) AS avg_rating
                    """
                ),
                {
                    "user_id": user_id,
                    "location_id": location_id,
                    "rating": rating,
                    "comment": comment.strip(),
                    "review_date": review_date,
                },
            ).scalar_one()
            return float(avg_rating)

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
            text(
                """
                SELECT ROUND(AVG(rating), 2)
                FROM Reviews
                WHERE location_id = :location_id
                """
            ),
            {"location_id": location_id},
        ).scalar_one()

    return float(avg_rating)


def add_favorite(user_id: int, location_id: int) -> None:
    _execute(
        """
        INSERT INTO Favorites(user_id, location_id)
        VALUES (:user_id, :location_id)
        """,
        {"user_id": user_id, "location_id": location_id},
    )


# -----------------------------
# SELECT operations
# -----------------------------

def get_categories() -> pd.DataFrame:
    return _to_df("SELECT * FROM Categories ORDER BY category_name")


def get_users() -> pd.DataFrame:
    return _to_df("SELECT * FROM Users ORDER BY name")


def get_locations() -> pd.DataFrame:
    return _to_df(
        """
        SELECT l.location_id, l.name, c.category_name, l.address, l.description, l.latitude, l.longitude
        FROM Locations l
        LEFT JOIN Categories c ON l.category_id = c.category_id
        ORDER BY l.name
        """
    )


def get_reviews() -> pd.DataFrame:
    return _to_df("SELECT * FROM Reviews ORDER BY date DESC")


def get_favorites() -> pd.DataFrame:
    return _to_df(
        """
        SELECT f.user_id, u.name AS user_name, f.location_id, l.name AS location_name
        FROM Favorites f
        JOIN Users u ON f.user_id = u.user_id
        JOIN Locations l ON f.location_id = l.location_id
        ORDER BY u.name, l.name
        """
    )


def search_locations_by_category(category_id: int) -> pd.DataFrame:
    return _to_df(
        """
        SELECT l.location_id, l.name, c.category_name, l.address, l.description, l.latitude, l.longitude
        FROM Locations l
        JOIN Categories c ON l.category_id = c.category_id
        WHERE c.category_id = :category_id
        ORDER BY l.name
        """,
        {"category_id": category_id},
    )


# -----------------------------
# UPDATE / DELETE operations
# -----------------------------

def update_location_description(location_id: int, new_description: str) -> None:
    _execute(
        """
        UPDATE Locations
        SET description = :new_description
        WHERE location_id = :location_id
        """,
        {"new_description": new_description.strip(), "location_id": location_id},
    )


def delete_review(review_id: int) -> None:
    _execute("DELETE FROM Reviews WHERE review_id = :review_id", {"review_id": review_id})


def insert_demo_category() -> None:
    _execute(
        """
        INSERT INTO Categories(category_name)
        VALUES ('Demo Temp Category')
        """
    )


def update_demo_category() -> None:
    _execute(
        """
        UPDATE Categories
        SET category_name = 'Demo Temp Category Updated'
        WHERE category_name = 'Demo Temp Category'
        """
    )


def delete_demo_category() -> None:
    _execute(
        """
        DELETE FROM Categories
        WHERE category_name IN ('Demo Temp Category', 'Demo Temp Category Updated')
        """
    )


# -----------------------------
# JOIN / Aggregation / HAVING
# -----------------------------

def reviews_with_user_and_location() -> pd.DataFrame:
    """JOIN example: show review with user name and location name."""
    return _to_df(
        """
        SELECT r.review_id, u.name AS user_name, l.name AS location_name, r.rating, r.comment, r.date
        FROM Reviews r
        JOIN Users u ON r.user_id = u.user_id
        JOIN Locations l ON r.location_id = l.location_id
        ORDER BY r.date DESC
        """
    )


def average_rating_per_location() -> pd.DataFrame:
    """GROUP BY aggregate: average rating and count per location."""
    return _to_df(
        """
        SELECT l.location_id, l.name AS location_name,
               ROUND(AVG(r.rating), 2) AS avg_rating,
               COUNT(r.review_id) AS review_count
        FROM Locations l
        LEFT JOIN Reviews r ON l.location_id = r.location_id
        GROUP BY l.location_id, l.name
         ORDER BY CASE WHEN avg_rating IS NULL THEN 1 ELSE 0 END, avg_rating DESC, l.name
        """
    )


def locations_with_avg_above_four() -> pd.DataFrame:
    """HAVING example: locations where average rating > 4."""
    return _to_df(
        """
        SELECT l.location_id, l.name AS location_name,
               ROUND(AVG(r.rating), 2) AS avg_rating
        FROM Locations l
        JOIN Reviews r ON l.location_id = r.location_id
        GROUP BY l.location_id, l.name
        HAVING AVG(r.rating) > 4
        ORDER BY avg_rating DESC
        """
    )


# -----------------------------
# Subqueries / Set Ops / View / CTE
# -----------------------------

def locations_with_highest_rating() -> pd.DataFrame:
    """Subquery example: locations whose avg rating equals maximum avg rating."""
    return _to_df(
        """
        SELECT x.location_id, x.location_name, x.avg_rating
        FROM (
            SELECT l.location_id, l.name AS location_name, ROUND(AVG(r.rating), 2) AS avg_rating
            FROM Locations l
            JOIN Reviews r ON l.location_id = r.location_id
            GROUP BY l.location_id, l.name
        ) x
        WHERE x.avg_rating = (
            SELECT MAX(y.avg_rating)
            FROM (
                SELECT ROUND(AVG(r2.rating), 2) AS avg_rating
                FROM Reviews r2
                GROUP BY r2.location_id
            ) y
        )
        """
    )


def users_reviewed_more_than_average() -> pd.DataFrame:
    """Subquery example: users with review count above average user review count."""
    return _to_df(
        """
        SELECT u.user_id, u.name, u.email, stats.review_count
        FROM Users u
        JOIN (
            SELECT r.user_id, COUNT(*) AS review_count
            FROM Reviews r
            GROUP BY r.user_id
        ) stats ON u.user_id = stats.user_id
        WHERE stats.review_count > (
            SELECT AVG(sub.review_count)
            FROM (
                SELECT COUNT(*) AS review_count
                FROM Reviews
                GROUP BY user_id
            ) sub
        )
        ORDER BY stats.review_count DESC, u.name
        """
    )


def union_example() -> pd.DataFrame:
    """Set operation UNION: merge user names and location names into one list."""
    return _to_df(
        """
        SELECT name AS label, 'USER' AS source
        FROM Users
        UNION
        SELECT name AS label, 'LOCATION' AS source
        FROM Locations
        ORDER BY label
        """
    )


def intersect_example() -> pd.DataFrame:
    """Set operation INTERSECT: users who both reviewed and favorited the same location."""
    return _to_df(
        """
        SELECT DISTINCT user_id
        FROM Reviews
        INTERSECT
        SELECT DISTINCT user_id
        FROM Favorites
        """
    )


def location_avg_rating_view() -> pd.DataFrame:
    """View example: read pre-created view `location_avg_rating`."""
    return _to_df(
        """
        SELECT *
        FROM location_avg_rating
        ORDER BY CASE WHEN avg_rating IS NULL THEN 1 ELSE 0 END, avg_rating DESC, location_name
        """
    )


def cte_average_rating() -> pd.DataFrame:
    """WITH clause (CTE) example: calculate average rating and sort."""
    return _to_df(
        """
        WITH rating_cte AS (
            SELECT location_id, ROUND(AVG(rating), 2) AS avg_rating
            FROM Reviews
            GROUP BY location_id
        )
        SELECT l.location_id, l.name AS location_name, rc.avg_rating
        FROM Locations l
        LEFT JOIN rating_cte rc ON l.location_id = rc.location_id
        ORDER BY CASE WHEN rc.avg_rating IS NULL THEN 1 ELSE 0 END, rc.avg_rating DESC, l.name
        """
    )


def locations_sorted_by_rating() -> pd.DataFrame:
    """ORDER BY example: sort locations by average rating (high to low)."""
    return _to_df(
        """
        SELECT l.location_id, l.name AS location_name, ROUND(AVG(r.rating), 2) AS avg_rating
        FROM Locations l
        LEFT JOIN Reviews r ON l.location_id = r.location_id
        GROUP BY l.location_id, l.name
        ORDER BY CASE WHEN avg_rating IS NULL THEN 1 ELSE 0 END, avg_rating DESC, l.name
        """
    )


def cursor_style_review_stats() -> dict[str, float]:
    """Cursor-style iteration in Python to compute review statistics.

    SQLite does not support stored cursors like PostgreSQL PL/pgSQL, so this
    function demonstrates cursor-like row iteration with DB-API cursor.
    """
    raw_conn = engine.raw_connection()
    try:
        cur = raw_conn.cursor()
        cur.execute("SELECT rating FROM Reviews")

        total = 0
        count = 0
        for (rating,) in cur.fetchall():
            total += int(rating)
            count += 1

        avg = round(total / count, 2) if count else 0.0
        cur.close()
    finally:
        raw_conn.close()

    return {"total_reviews": count, "average_rating": avg}
