"""SQLite data-access functions.

Each operation opens its own short-lived connection. That keeps the code easy
to understand and avoids sharing a SQLite connection across web requests.
"""

from datetime import datetime, timezone
import sqlite3

from config import DATABASE_PATH, EVENT_CAPACITY


class DuplicateRegistrationError(Exception):
    """Raised when an email address is already registered."""


class EventFullError(Exception):
    """Raised when no seats are left."""


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    """Create the registrations table on first run."""
    with _connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                college_department TEXT,
                registered_at TEXT NOT NULL
            )
            """
        )


def count_registrations() -> int:
    with _connection() as connection:
        row = connection.execute("SELECT COUNT(*) AS total FROM registrations").fetchone()
    return int(row["total"])


def create_registration(
    *, name: str, email: str, college_department: str | None
) -> dict:
    """Store one registration while safely enforcing duplicate and seat rules.

    ``BEGIN IMMEDIATE`` makes the availability check and insert one transaction.
    This prevents two simultaneous requests from both taking the last seat.
    """
    connection = _connection()
    try:
        connection.execute("BEGIN IMMEDIATE")

        duplicate = connection.execute(
            "SELECT 1 FROM registrations WHERE email = ?", (email,)
        ).fetchone()
        if duplicate:
            raise DuplicateRegistrationError

        total = connection.execute("SELECT COUNT(*) AS total FROM registrations").fetchone()[
            "total"
        ]
        if total >= EVENT_CAPACITY:
            raise EventFullError

        registered_at = datetime.now(timezone.utc).isoformat()
        cursor = connection.execute(
            """
            INSERT INTO registrations (name, email, college_department, registered_at)
            VALUES (?, ?, ?, ?)
            """,
            (name, email, college_department, registered_at),
        )
        row = connection.execute(
            "SELECT * FROM registrations WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        connection.commit()
        return dict(row)
    except (DuplicateRegistrationError, EventFullError):
        connection.rollback()
        raise
    except sqlite3.Error:
        connection.rollback()
        raise
    finally:
        connection.close()


def list_registrations() -> list[dict]:
    with _connection() as connection:
        rows = connection.execute(
            "SELECT * FROM registrations ORDER BY registered_at ASC, id ASC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_registration(registration_id: int) -> dict | None:
    with _connection() as connection:
        row = connection.execute(
            "SELECT * FROM registrations WHERE id = ?", (registration_id,)
        ).fetchone()
    return dict(row) if row else None
