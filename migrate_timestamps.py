import argparse
import sqlite3
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from core.db import DB_PATH
APP_TZ = ZoneInfo("Asia/Kolkata")

TABLES = [
    ("users", "id", ["created_at"]),
    ("lectures", "id", ["start_time", "end_time", "created_at"]),
    ("attendance", "id", ["timestamp"]),
    ("notices", "id", ["created_at"]),
    ("resources", "id", ["created_at"]),
    ("issues", "id", ["created_at", "resolved_at"]),
    ("lost_found", "id", ["created_at"]),
    ("events", "id", ["event_date", "created_at"]),
    ("event_registrations", "id", ["created_at"]),
    ("feedback", "id", ["created_at"]),
    ("audit_logs", "id", ["created_at"]),
    ("system_settings", "key", ["updated_at"]),
]


def _convert_to_ist(value: str) -> str | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(APP_TZ).replace(tzinfo=None)
    return dt.isoformat()


def main(apply: bool):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    total_updates = 0

    for table, pk, cols in TABLES:
        columns = ", ".join([pk] + cols)
        rows = conn.execute(f"SELECT {columns} FROM {table}").fetchall()
        for row in rows:
            updates = {}
            for col in cols:
                new_value = _convert_to_ist(row[col])
                if new_value and new_value != row[col]:
                    updates[col] = new_value
            if updates:
                total_updates += 1
                if apply:
                    set_clause = ", ".join([f"{c} = ?" for c in updates.keys()])
                    values = list(updates.values()) + [row[pk]]
                    conn.execute(f"UPDATE {table} SET {set_clause} WHERE {pk} = ?", values)
                else:
                    print(f"{table}.{row[pk]} -> {updates}")

    if apply:
        conn.commit()
        print(f"Updated rows: {total_updates}")
    else:
        print(f"Dry run complete. Rows that would update: {total_updates}")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Apply updates to the database")
    args = parser.parse_args()
    main(args.apply)
