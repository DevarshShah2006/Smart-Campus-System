import sqlite3
from pathlib import Path

from core.utils import now_iso

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "smart_campus.db"


def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            enrollment TEXT UNIQUE,
            department TEXT,
            year INTEGER,
            batch INTEGER,
            username TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (role_id) REFERENCES roles(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS lectures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            teacher_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            room TEXT,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            radius_m REAL NOT NULL,
            late_after_min INTEGER NOT NULL,
            year INTEGER,
            batch INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (teacher_id) REFERENCES users(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            enrollment TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            status TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            accuracy REAL,
            distance_m REAL,
            override_by INTEGER,
            override_reason TEXT,
            UNIQUE(session_id, enrollment)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            posted_by INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            file_path TEXT NOT NULL,
            uploaded_by INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            reported_by INTEGER NOT NULL,
            resolved_by INTEGER,
            created_at TEXT NOT NULL,
            resolved_at TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS lost_found (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            contact TEXT NOT NULL,
            posted_by INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            event_date TEXT NOT NULL,
            location TEXT NOT NULL,
            created_by INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS event_registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            enrollment TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(event_id, enrollment)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            enrollment TEXT NOT NULL,
            rating INTEGER NOT NULL,
            comments TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            details TEXT NOT NULL,
            actor_id INTEGER,
            created_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT NOT NULL,
            time TEXT NOT NULL,
            subject TEXT NOT NULL,
            room TEXT,
            teacher_id INTEGER NOT NULL
        )
        """
    )

    def _ensure_column(table: str, column: str, col_type: str):
        cols = [row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        if column not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")

    _ensure_column("users", "batch", "INTEGER")
    _ensure_column("lectures", "year", "INTEGER")
    _ensure_column("lectures", "batch", "INTEGER")

    conn.commit()
    return conn


def seed_defaults(conn, password_hash):
    cursor = conn.cursor()
    roles = ["student", "teacher", "admin"]
    for role in roles:
        cursor.execute("INSERT OR IGNORE INTO roles (name) VALUES (?)", (role,))

    cursor.execute("SELECT id FROM roles WHERE name = ?", ("admin",))
    admin_role_id = cursor.fetchone()["id"]

    cursor.execute(
        """
        INSERT OR IGNORE INTO users (role_id, name, username, password_hash, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (admin_role_id, "System Admin", "admin", password_hash, now_iso()),
    )

    cursor.execute("SELECT id FROM roles WHERE name = ?", ("teacher",))
    teacher_role_id = cursor.fetchone()["id"]

    cursor.execute(
        """
        INSERT OR IGNORE INTO users (role_id, name, username, password_hash, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (teacher_role_id, "Default Teacher", "teacher", password_hash, now_iso()),
    )

    conn.commit()
