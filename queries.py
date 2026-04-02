"""All SQL operations for the Manipal Location & Review Management System."""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
from sqlalchemy import text

from db import engine, get_backend_name


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
# Core CRUD
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


def get_categories() -> pd.DataFrame:
    return _to_df("SELECT * FROM Categories ORDER BY category_name")


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
        GROUP BY l.location_id, l.name, c.category_name, l.address, l.description, l.latitude, l.longitude
        """,
        {"location_id": location_id},
    )


def get_reviews_for_location(location_id: int) -> pd.DataFrame:
    return _to_df(
        """
        SELECT
            r.review_id,
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
# Analytics Queries
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


# Compatibility function kept for earlier imports.
def locations_with_avg_above_four() -> pd.DataFrame:
    return _to_df(
        """
        SELECT
            l.location_id,
            l.name AS location_name,
            ROUND(AVG(r.rating), 2) AS avg_rating
        FROM Locations l
        JOIN Reviews r ON l.location_id = r.location_id
        GROUP BY l.location_id, l.name
        HAVING AVG(r.rating) > 4
        ORDER BY avg_rating DESC
        """
    )
