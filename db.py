"""Database connection and schema setup for the Manipal Location & Review Management System.

Uses Python's built-in sqlite3 module directly — no ORM, no abstraction layer.
"""

import os
import sqlite3
from datetime import datetime
from threading import Lock

DATABASE_PATH: str = os.getenv("DATABASE_PATH", "manipal_map.db")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUERY_LOG_PATH = os.path.join(BASE_DIR, "query.log")
_QUERY_LOG_LOCK = Lock()


def reset_query_log() -> None:
    """Clear the SQL trace log for a fresh browser session."""
    with _QUERY_LOG_LOCK:
        with open(QUERY_LOG_PATH, "w", encoding="utf-8") as log_file:
            log_file.write("")


def _sqlite_trace(statement: str) -> None:
    """Persist every SQL statement so query behavior can be reviewed outside the UI."""
    if not statement:
        return
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {statement.strip()}\n"
    with _QUERY_LOG_LOCK:
        with open(QUERY_LOG_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(line)


# ── UDF registered on every connection ────────────────────────────────────────

def _sqlite_rating_band(value: float | None) -> str:
    if value is None:
        return "Unrated"
    if value >= 4.5:
        return "Excellent"
    if value >= 4.0:
        return "Strong"
    if value >= 3.0:
        return "Average"
    return "Needs Attention"


# ── Connection factory ─────────────────────────────────────────────────────────

def get_conn() -> sqlite3.Connection:
    """Open a fresh SQLite connection with pragmas and UDF registered.

    A new connection is created on every call (no pooling) so callers always
    see the latest committed data — equivalent to the NullPool behaviour we
    previously had with SQLAlchemy.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row          # rows act like dicts
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")   # concurrent reads + writes
    conn.create_function("rating_band", 1, _sqlite_rating_band)
    conn.set_trace_callback(_sqlite_trace)
    return conn


# ── Schema bootstrap ───────────────────────────────────────────────────────────

def init_db() -> None:
    """Create all required tables, views, and triggers if they do not exist."""
    conn = get_conn()
    try:
        # ---- Tables ----
        conn.execute("""
            CREATE TABLE IF NOT EXISTS Categories (
                category_id   INTEGER PRIMARY KEY,
                category_name VARCHAR(100) UNIQUE NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                user_id       INTEGER PRIMARY KEY,
                name          VARCHAR(100) NOT NULL,
                email         VARCHAR(150) UNIQUE NOT NULL,
                password_hash TEXT
            )
        """)

        # Backward-compatible migration
        existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(Users)").fetchall()}
        if "password_hash" not in existing_cols:
            conn.execute("ALTER TABLE Users ADD COLUMN password_hash TEXT")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS Locations (
                location_id INTEGER PRIMARY KEY,
                name        VARCHAR(150) NOT NULL,
                category_id INTEGER,
                address     TEXT,
                description TEXT,
                latitude    REAL,
                longitude   REAL,
                created_by  INTEGER,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES Categories(category_id) ON DELETE SET NULL
            )
        """)

        location_cols = {row[1] for row in conn.execute("PRAGMA table_info(Locations)").fetchall()}
        if "created_by" not in location_cols:
            conn.execute("ALTER TABLE Locations ADD COLUMN created_by INTEGER")
        if "created_at" not in location_cols:
            conn.execute("ALTER TABLE Locations ADD COLUMN created_at TIMESTAMP")

        # One-time category normalization: replace Cafe with Restaurant.
        conn.execute(
            """
            UPDATE Categories
            SET category_name = 'Restaurant'
            WHERE LOWER(TRIM(category_name)) = 'cafe'
              AND NOT EXISTS (
                  SELECT 1 FROM Categories WHERE LOWER(TRIM(category_name)) = 'restaurant'
              )
            """
        )
        conn.execute(
            """
            UPDATE Locations
            SET category_id = (
                SELECT category_id FROM Categories
                WHERE LOWER(TRIM(category_name)) = 'restaurant'
                LIMIT 1
            )
            WHERE category_id = (
                SELECT category_id FROM Categories
                WHERE LOWER(TRIM(category_name)) = 'cafe'
                LIMIT 1
            )
              AND EXISTS (SELECT 1 FROM Categories WHERE LOWER(TRIM(category_name)) = 'restaurant')
              AND EXISTS (SELECT 1 FROM Categories WHERE LOWER(TRIM(category_name)) = 'cafe')
            """
        )
        conn.execute(
            """
            DELETE FROM Categories
            WHERE LOWER(TRIM(category_name)) = 'cafe'
              AND EXISTS (SELECT 1 FROM Categories WHERE LOWER(TRIM(category_name)) = 'restaurant')
            """
        )

        conn.execute("""
            CREATE TABLE IF NOT EXISTS Reviews (
                review_id   INTEGER PRIMARY KEY,
                user_id     INTEGER NOT NULL,
                location_id INTEGER NOT NULL,
                rating      INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                comment     TEXT,
                date        DATE NOT NULL,
                FOREIGN KEY (user_id)     REFERENCES Users(user_id)     ON DELETE CASCADE,
                FOREIGN KEY (location_id) REFERENCES Locations(location_id) ON DELETE CASCADE
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS Images (
                image_id    INTEGER PRIMARY KEY,
                location_id INTEGER NOT NULL,
                image_url   TEXT,
                uploaded_by INTEGER,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (location_id) REFERENCES Locations(location_id) ON DELETE CASCADE
            )
        """)

        image_cols = {row[1] for row in conn.execute("PRAGMA table_info(Images)").fetchall()}
        if "uploaded_by" not in image_cols:
            conn.execute("ALTER TABLE Images ADD COLUMN uploaded_by INTEGER")
        if "uploaded_at" not in image_cols:
            conn.execute("ALTER TABLE Images ADD COLUMN uploaded_at TIMESTAMP")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS Favorites (
                user_id     INTEGER NOT NULL,
                location_id INTEGER NOT NULL,
                PRIMARY KEY (user_id, location_id),
                FOREIGN KEY (user_id)     REFERENCES Users(user_id)     ON DELETE CASCADE,
                FOREIGN KEY (location_id) REFERENCES Locations(location_id) ON DELETE CASCADE
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS ReviewLogs (
                log_id     INTEGER PRIMARY KEY,
                review_id  INTEGER,
                action     VARCHAR(30) NOT NULL,
                old_rating INTEGER,
                new_rating INTEGER,
                log_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (review_id) REFERENCES Reviews(review_id) ON DELETE CASCADE
            )
        """)

        # Backward-compatible migration for ReviewLogs columns
        log_cols = {row[1] for row in conn.execute("PRAGMA table_info(ReviewLogs)").fetchall()}
        if "old_rating" not in log_cols:
            conn.execute("ALTER TABLE ReviewLogs ADD COLUMN old_rating INTEGER")
        if "new_rating" not in log_cols:
            conn.execute("ALTER TABLE ReviewLogs ADD COLUMN new_rating INTEGER")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS LocationStatus (
                location_id  INTEGER PRIMARY KEY,
                status       VARCHAR(20) NOT NULL DEFAULT 'good',
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (location_id) REFERENCES Locations(location_id) ON DELETE CASCADE
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS DeletedLocationAudit (
                audit_id       INTEGER PRIMARY KEY,
                location_id    INTEGER NOT NULL,
                location_name  VARCHAR(150) NOT NULL,
                deleted_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                review_count   INTEGER NOT NULL DEFAULT 0,
                image_count    INTEGER NOT NULL DEFAULT 0,
                favorite_count INTEGER NOT NULL DEFAULT 0,
                deletion_mode  VARCHAR(40) NOT NULL DEFAULT 'trigger_archive'
            )
        """)

        # ---- Triggers ----
        conn.execute("DROP TRIGGER IF EXISTS trg_validate_review_insert")
        conn.execute("""
            CREATE TRIGGER trg_validate_review_insert
            BEFORE INSERT ON Reviews
            BEGIN
                SELECT CASE
                    WHEN TRIM(COALESCE(NEW.comment, '')) = '' THEN
                        RAISE(ABORT, 'Review comment cannot be empty.')
                END;
            END
        """)

        conn.execute("DROP TRIGGER IF EXISTS trg_validate_review_update")
        conn.execute("""
            CREATE TRIGGER trg_validate_review_update
            BEFORE UPDATE OF comment ON Reviews
            BEGIN
                SELECT CASE
                    WHEN TRIM(COALESCE(NEW.comment, '')) = '' THEN
                        RAISE(ABORT, 'Review comment cannot be empty.')
                END;
            END
        """)

        conn.execute("DROP TRIGGER IF EXISTS trg_log_review_insert")
        conn.execute("""
            CREATE TRIGGER trg_log_review_insert
            AFTER INSERT ON Reviews
            BEGIN
                INSERT INTO ReviewLogs(review_id, action, new_rating)
                VALUES (NEW.review_id, 'INSERT_REVIEW', NEW.rating);
            END
        """)

        conn.execute("DROP TRIGGER IF EXISTS trg_log_review_update")
        conn.execute("""
            CREATE TRIGGER trg_log_review_update
            AFTER UPDATE OF rating ON Reviews
            BEGIN
                INSERT INTO ReviewLogs(review_id, action, old_rating, new_rating)
                VALUES (NEW.review_id, 'UPDATE_RATING', OLD.rating, NEW.rating);
            END
        """)

        conn.execute("DROP TRIGGER IF EXISTS trg_archive_location_delete")
        conn.execute("""
            CREATE TRIGGER trg_archive_location_delete
            BEFORE DELETE ON Locations
            BEGIN
                INSERT INTO DeletedLocationAudit(
                    location_id, location_name,
                    review_count, image_count, favorite_count, deletion_mode
                )
                VALUES (
                    OLD.location_id,
                    OLD.name,
                    (SELECT COUNT(*) FROM Reviews  WHERE location_id = OLD.location_id),
                    (SELECT COUNT(*) FROM Images   WHERE location_id = OLD.location_id),
                    (SELECT COUNT(*) FROM Favorites WHERE location_id = OLD.location_id),
                    'trigger_archive'
                );
            END
        """)

        # ---- Views ----
        conn.execute("DROP VIEW IF EXISTS location_avg_rating")
        conn.execute("""
            CREATE VIEW location_avg_rating AS
            SELECT
                l.location_id,
                l.name                       AS location_name,
                ROUND(AVG(r.rating), 2)      AS avg_rating,
                COUNT(r.review_id)           AS review_count
            FROM Locations l
            LEFT JOIN Reviews r ON l.location_id = r.location_id
            GROUP BY l.location_id, l.name
        """)

        conn.execute("DROP VIEW IF EXISTS category_activity_summary")
        conn.execute("""
            CREATE VIEW category_activity_summary AS
            SELECT
                c.category_id,
                c.category_name,
                COUNT(DISTINCT l.location_id)                                          AS location_count,
                COUNT(DISTINCT CASE WHEN r.review_id IS NOT NULL THEN l.location_id END) AS reviewed_locations,
                ROUND(AVG(r.rating), 2)                                                AS category_avg_rating,
                COUNT(CASE WHEN r.rating = 5 THEN 1 END)                               AS five_star_reviews,
                rating_band(ROUND(AVG(r.rating), 2))                                   AS category_band
            FROM Categories c
            LEFT JOIN Locations l ON c.category_id = l.category_id
            LEFT JOIN Reviews r   ON l.location_id = r.location_id
            GROUP BY c.category_id, c.category_name
        """)

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print("SQLite database initialised successfully.")
