"""
database.py
-----------
Database helper module for the Channel Broadcasting Management System.

Commands (run inside the project folder):
    python database.py init     -> creates the database and all tables
    python database.py schema  -> creates all tables in the configured database
    python database.py admin    -> creates the first administrator account

All application queries use parameterized SQL (no string concatenation).
"""

import getpass
import logging
import os
import sys
from contextlib import contextmanager

import psycopg2
from psycopg2 import extras, sql
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "broadcasting_management")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DATABASE_URL = os.getenv("DATABASE_URL")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Friendly database error that is safe to show to the user."""


def _connect(dbname=None):
    """Open a new PostgreSQL connection using the credentials from .env."""
    try:
        if DATABASE_URL and not dbname:
            return psycopg2.connect(DATABASE_URL, connect_timeout=5)
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=dbname or DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=5,
        )
        return conn
    except psycopg2.OperationalError as exc:
        logger.error("PostgreSQL connection failed: %s", exc)
        raise DatabaseError(
            "Could not connect to PostgreSQL. Please check that PostgreSQL is "
            "running and that the values in your .env file are correct."
        ) from exc


def get_connection():
    """Return a raw connection. The caller must close it."""
    return _connect()


@contextmanager
def transaction():
    """Context manager: commits on success, rolls back on failure, always closes."""
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_all(query, params=None):
    """Run a SELECT query and return a list of dictionaries."""
    conn = _connect()
    try:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]
    except psycopg2.OperationalError as exc:
        raise DatabaseError("Database connection lost while reading data.") from exc
    except psycopg2.Error as exc:
        logger.error("Query failed: %s", exc)
        raise DatabaseError("A database error occurred while reading data.") from exc
    finally:
        conn.close()


def fetch_one(query, params=None):
    """Run a SELECT query and return one dictionary or None."""
    rows = fetch_all(query, params)
    return rows[0] if rows else None


def execute(query, params=None):
    """Run an INSERT/UPDATE/DELETE query inside its own transaction.

    Returns the number of affected rows.
    """
    try:
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.rowcount
    except psycopg2.Error as exc:
        logger.error("Execute failed: %s", exc)
        raise DatabaseError("A database error occurred while saving data.") from exc


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
-- TABLE 1: users -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id       SERIAL PRIMARY KEY,
    full_name     VARCHAR(100) NOT NULL,
    agency_name   VARCHAR(120) NOT NULL,
    email         VARCHAR(120) NOT NULL UNIQUE,
    phone         VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(10)  NOT NULL DEFAULT 'user'
                  CHECK (role IN ('user', 'admin')),
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- TABLE 2: shows -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS shows (
    show_id           SERIAL PRIMARY KEY,
    user_id           INTEGER NOT NULL
                      REFERENCES users(user_id) ON DELETE RESTRICT,
    title             VARCHAR(200) NOT NULL,
    description       TEXT NOT NULL,
    category          VARCHAR(80)  NOT NULL,
    agency_name       VARCHAR(120) NOT NULL,
    host_name         VARCHAR(120) NOT NULL,
    channel_name      VARCHAR(120) NOT NULL,
    broadcast_date    DATE NOT NULL,
    start_time        TIME NOT NULL,
    end_time          TIME NOT NULL,
    language          VARCHAR(40)  NOT NULL,
    target_audience   VARCHAR(120),
    poster_url        VARCHAR(500),
    additional_notes  TEXT,
    status            VARCHAR(10)  NOT NULL DEFAULT 'Pending'
                      CHECK (status IN ('Pending', 'Approved', 'Rejected')),
    rejection_reason  TEXT,
    submitted_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_show_time_order CHECK (end_time > start_time)
);

-- TABLE 3: show_status_history --------------------------------------------
CREATE TABLE IF NOT EXISTS show_status_history (
    history_id      SERIAL PRIMARY KEY,
    show_id         INTEGER NOT NULL
                    REFERENCES shows(show_id) ON DELETE CASCADE,
    admin_id        INTEGER
                    REFERENCES users(user_id) ON DELETE SET NULL,
    previous_status VARCHAR(10),
    new_status      VARCHAR(10) NOT NULL
                    CHECK (new_status IN ('Pending', 'Approved', 'Rejected')),
    remarks         VARCHAR(500),
    changed_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for commonly searched / filtered columns -------------------------
CREATE INDEX IF NOT EXISTS idx_shows_title         ON shows (title);
CREATE INDEX IF NOT EXISTS idx_shows_broadcast_date ON shows (broadcast_date);
CREATE INDEX IF NOT EXISTS idx_shows_status        ON shows (status);
CREATE INDEX IF NOT EXISTS idx_shows_user_id       ON shows (user_id);
CREATE INDEX IF NOT EXISTS idx_shows_channel       ON shows (channel_name);
CREATE INDEX IF NOT EXISTS idx_users_email         ON users (LOWER(email));
CREATE INDEX IF NOT EXISTS idx_history_show_id     ON show_status_history (show_id);
"""


def create_database_if_missing():
    """Create the target database when it does not exist yet (idempotent)."""
    maintenance_conn = _connect("postgres")
    try:
        maintenance_conn.autocommit = True
        with maintenance_conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
            if cur.fetchone() is None:
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
                logger.info("Created database %s", DB_NAME)
            else:
                logger.info("Database %s already exists", DB_NAME)
    finally:
        maintenance_conn.close()


def init_db():
    """Create the database (if needed) and all tables."""
    create_database_if_missing()
    init_schema()


def init_schema():
    """Create all application tables in the configured database."""
    with transaction() as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
    print(" Database ready: tables users, shows, show_status_history created.")


# ---------------------------------------------------------------------------
# First administrator account
# ---------------------------------------------------------------------------

def create_admin():
    """Securely prompt for an administrator account (never stored in code)."""
    print("\n--- Create the first administrator account ---")
    full_name = input("Full name: ").strip()
    agency_name = input("Agency / organization name: ").strip()
    email = input("Email: ").strip().lower()
    phone = input("Phone (optional): ").strip()

    if not full_name or not agency_name or not email:
        print(" X Full name, agency name and email are required.")
        return 1

    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")
    if len(password) < 6:
        print(" X Password must be at least 6 characters.")
        return 1
    if password != confirm:
        print(" X Passwords do not match.")
        return 1

    existing = fetch_one("SELECT user_id FROM users WHERE LOWER(email) = LOWER(%s)", (email,))
    if existing:
        print(" X An account with this email already exists.")
        return 1

    execute(
        """
        INSERT INTO users (full_name, agency_name, email, phone, password_hash, role, is_active)
        VALUES (%s, %s, %s, %s, %s, 'admin', TRUE)
        """,
        (full_name, agency_name, email, phone or None, generate_password_hash(password)),
    )
    print(" Administrator account created. Sign in at  http://127.0.0.1:5000/admin/login")
    return 0


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        if command == "init":
            init_db()
        elif command == "schema":
            init_schema()
        elif command == "admin":
            fetch_one("SELECT 1")  # quick connection check
            sys.exit(create_admin())
        else:
            print("Usage: python database.py init | schema | admin")
            return 1
    except DatabaseError as exc:
        print(" X Database error: {}".format(exc))
        return 1
    except psycopg2.Error as exc:
        logger.error("PostgreSQL error: %s", exc)
        print(" X PostgreSQL error. Check the log above.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
