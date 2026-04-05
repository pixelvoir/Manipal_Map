"""Database connection and schema setup for the Manipal Location & Review Management System."""

import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///manipal_map.db")
engine = create_engine(DATABASE_URL, future=True)


def init_db() -> None:
    """Create all required tables, constraints, triggers, and views for SQLite."""
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON"))

        # ------------------------------------------------------------------
        # Core tables
        # ------------------------------------------------------------------
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
                    email VARCHAR(150) UNIQUE NOT NULL,
                    password_hash TEXT
                )
                """
            )
        )

        # Backward-compatible migration
        cols = conn.execute(text("PRAGMA table_info(Users)")).fetchall()
        col_names = {row[1] for row in cols}
        if "password_hash" not in col_names:
            conn.execute(text("ALTER TABLE Users ADD COLUMN password_hash TEXT"))

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
                    FOREIGN KEY (category_id) REFERENCES Categories(category_id) ON DELETE SET NULL
                )
                """
            )
        )

        # We rely on application-level or explicit ON DELETE CASCADE.
        # Note: SQLite `ALTER TABLE` cannot add constraints. If the table already
        # exists, we will rely on our `delete_location()` function in queries.py 
        # to manually drop associated rows instead to cleanly demonstrate transaction blocks.
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
                    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (location_id) REFERENCES Locations(location_id) ON DELETE CASCADE
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
                    FOREIGN KEY (location_id) REFERENCES Locations(location_id) ON DELETE CASCADE
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
                    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (location_id) REFERENCES Locations(location_id) ON DELETE CASCADE
                )
                """
            )
        )

        # ------------------------------------------------------------------
        # ReviewLogs
        # ------------------------------------------------------------------
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS ReviewLogs (
                    log_id INTEGER PRIMARY KEY,
                    review_id INTEGER,
                    action VARCHAR(30) NOT NULL,
                    old_rating INTEGER,
                    new_rating INTEGER,
                    log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (review_id) REFERENCES Reviews(review_id) ON DELETE CASCADE
                )
                """
            )
        )

        # Migrate existing ReviewLogs
        log_cols = conn.execute(text("PRAGMA table_info(ReviewLogs)")).fetchall()
        log_col_names = {row[1] for row in log_cols}
        if "old_rating" not in log_col_names:
            conn.execute(text("ALTER TABLE ReviewLogs ADD COLUMN old_rating INTEGER"))
        if "new_rating" not in log_col_names:
            conn.execute(text("ALTER TABLE ReviewLogs ADD COLUMN new_rating INTEGER"))

        # ------------------------------------------------------------------
        # LocationStatus
        # ------------------------------------------------------------------
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS LocationStatus (
                    location_id INTEGER PRIMARY KEY,
                    status VARCHAR(20) NOT NULL DEFAULT 'good',
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (location_id) REFERENCES Locations(location_id) ON DELETE CASCADE
                )
                """
            )
        )

        # ------------------------------------------------------------------
        # TRIGGERS (SQLite only native implementation)
        # ------------------------------------------------------------------
        
        # TRIGGER 1: AFTER INSERT on Reviews — audit log
        conn.execute(text("DROP TRIGGER IF EXISTS trg_log_review_insert"))
        conn.execute(
            text(
                """
                CREATE TRIGGER trg_log_review_insert
                AFTER INSERT ON Reviews
                BEGIN
                    INSERT INTO ReviewLogs(review_id, action, new_rating)
                    VALUES (NEW.review_id, 'INSERT_REVIEW', NEW.rating);
                END
                """
            )
        )

        # TRIGGER 2: AFTER UPDATE on Reviews — log old vs new rating
        conn.execute(text("DROP TRIGGER IF EXISTS trg_log_review_update"))
        conn.execute(
            text(
                """
                CREATE TRIGGER trg_log_review_update
                AFTER UPDATE OF rating ON Reviews
                BEGIN
                    INSERT INTO ReviewLogs(review_id, action, old_rating, new_rating)
                    VALUES (NEW.review_id, 'UPDATE_RATING', OLD.rating, NEW.rating);
                END
                """
            )
        )

        # ------------------------------------------------------------------
        # VIEW
        # ------------------------------------------------------------------
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


if __name__ == "__main__":
    init_db()
    print("SQLite Database initialized successfully.")
