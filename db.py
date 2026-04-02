"""Database connection and schema setup for the Manipal Location & Review Management System."""

from __future__ import annotations

import os
from sqlalchemy import create_engine, text


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///manipal_map.db")
engine = create_engine(DATABASE_URL, future=True)


def get_backend_name() -> str:
    """Return the SQL backend name (sqlite, postgresql, etc.)."""
    return engine.url.get_backend_name()


def init_db() -> None:
    """Create all required tables, constraints, trigger, and view."""
    backend = get_backend_name()

    with engine.begin() as conn:
        if backend == "sqlite":
            conn.execute(text("PRAGMA foreign_keys = ON"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS Categories (
                    category_id INTEGER PRIMARY KEY,
                    category_name VARCHAR(100) UNIQUE NOT NULL
                )
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS Users (
                    user_id INTEGER PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(150) UNIQUE NOT NULL
                )
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS Locations (
                    location_id INTEGER PRIMARY KEY,
                    name VARCHAR(150) NOT NULL,
                    category_id INTEGER,
                    address TEXT,
                    description TEXT,
                    latitude REAL,
                    longitude REAL,
                    FOREIGN KEY (category_id) REFERENCES Categories(category_id)
                )
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS Reviews (
                    review_id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    location_id INTEGER NOT NULL,
                    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                    comment TEXT,
                    date DATE NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES Users(user_id),
                    FOREIGN KEY (location_id) REFERENCES Locations(location_id)
                )
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS Images (
                    image_id INTEGER PRIMARY KEY,
                    location_id INTEGER NOT NULL,
                    image_url TEXT,
                    FOREIGN KEY (location_id) REFERENCES Locations(location_id)
                )
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS Favorites (
                    user_id INTEGER NOT NULL,
                    location_id INTEGER NOT NULL,
                    PRIMARY KEY (user_id, location_id),
                    FOREIGN KEY (user_id) REFERENCES Users(user_id),
                    FOREIGN KEY (location_id) REFERENCES Locations(location_id)
                )
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS ReviewLogs (
                    log_id INTEGER PRIMARY KEY,
                    review_id INTEGER,
                    action VARCHAR(30) NOT NULL,
                    log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (review_id) REFERENCES Reviews(review_id)
                )
                """
            )
        )

        if backend == "sqlite":
            conn.execute(text("DROP TRIGGER IF EXISTS trg_log_review_insert"))
            conn.execute(
                text(
                    """
                    CREATE TRIGGER trg_log_review_insert
                    AFTER INSERT ON Reviews
                    BEGIN
                        INSERT INTO ReviewLogs(review_id, action)
                        VALUES (NEW.review_id, 'INSERT_REVIEW');
                    END
                    """
                )
            )
        elif backend == "postgresql":
            conn.execute(
                text(
                    """
                    CREATE OR REPLACE FUNCTION log_review_insert()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        INSERT INTO ReviewLogs(review_id, action)
                        VALUES (NEW.review_id, 'INSERT_REVIEW');
                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                    """
                )
            )
            conn.execute(text("DROP TRIGGER IF EXISTS trg_log_review_insert ON Reviews"))
            conn.execute(
                text(
                    """
                    CREATE TRIGGER trg_log_review_insert
                    AFTER INSERT ON Reviews
                    FOR EACH ROW EXECUTE FUNCTION log_review_insert();
                    """
                )
            )

        conn.execute(text("DROP VIEW IF EXISTS location_avg_rating"))
        conn.execute(
            text(
                """
                CREATE VIEW location_avg_rating AS
                SELECT
                    l.location_id,
                    l.name AS location_name,
                    ROUND(AVG(r.rating), 2) AS avg_rating,
                    COUNT(r.review_id) AS review_count
                FROM Locations l
                LEFT JOIN Reviews r ON l.location_id = r.location_id
                GROUP BY l.location_id, l.name
                """
            )
        )

        if backend == "postgresql":
            conn.execute(
                text(
                    """
                    CREATE OR REPLACE FUNCTION add_review_and_get_avg(
                        p_user_id INT,
                        p_location_id INT,
                        p_rating INT,
                        p_comment TEXT,
                        p_date DATE
                    )
                    RETURNS NUMERIC AS $$
                    DECLARE
                        v_avg NUMERIC;
                    BEGIN
                        IF p_rating < 1 OR p_rating > 5 THEN
                            RAISE EXCEPTION 'Rating must be between 1 and 5';
                        END IF;

                        INSERT INTO Reviews(user_id, location_id, rating, comment, date)
                        VALUES (p_user_id, p_location_id, p_rating, p_comment, p_date);

                        SELECT ROUND(AVG(rating)::NUMERIC, 2)
                        INTO v_avg
                        FROM Reviews
                        WHERE location_id = p_location_id;

                        RETURN v_avg;
                    END;
                    $$ LANGUAGE plpgsql;
                    """
                )
            )


if __name__ == "__main__":
    init_db()
    print(f"Database initialized successfully using {get_backend_name()}.")
