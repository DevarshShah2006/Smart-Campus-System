from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from math import radians, sin, cos, sqrt, atan2
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
QR_DIR = DATA_DIR / "qr"

APP_TZ = ZoneInfo("Asia/Kolkata")


def ensure_dirs():
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOADS_DIR / "events").mkdir(parents=True, exist_ok=True)
    (UPLOADS_DIR / "issues").mkdir(parents=True, exist_ok=True)
    (UPLOADS_DIR / "lost_found").mkdir(parents=True, exist_ok=True)
    (UPLOADS_DIR / "resources").mkdir(parents=True, exist_ok=True)
    QR_DIR.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return now_local().isoformat()


def now_local() -> datetime:
    return datetime.now(APP_TZ).replace(tzinfo=None)


def parse_iso(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is not None:
        dt = dt.astimezone(APP_TZ).replace(tzinfo=None)
    return dt


def add_minutes(value: datetime, minutes: int) -> datetime:
    return value + timedelta(minutes=minutes)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return r * c


def build_timeline(records: List[Dict]) -> List[Dict]:
    return sorted(records, key=lambda x: x.get("created_at", ""), reverse=True)


def summarize_counts(items: List[Dict], key: str) -> Dict[str, int]:
    summary: Dict[str, int] = {}
    for item in items:
        label = str(item.get(key, "Unknown"))
        summary[label] = summary.get(label, 0) + 1
    return summary


def to_chart_data(summary: Dict[str, int]) -> Tuple[List[str], np.ndarray]:
    labels = list(summary.keys())
    counts = np.array(list(summary.values()), dtype=int)
    return labels, counts


def rows_to_dataframe(rows):
    """Convert sqlite3.Row results to a pandas DataFrame."""
    import pandas as pd
    if not rows:
        return pd.DataFrame()
    if hasattr(rows[0], "keys"):
        return pd.DataFrame(rows, columns=rows[0].keys())
    return pd.DataFrame(rows)


def add_datetime_columns(df, col="created_at"):
    """Add separate date and time columns from a datetime column."""
    import pandas as pd
    if col in df.columns:
        dt = pd.to_datetime(df[col], errors="coerce")
        df["date"] = dt.dt.date
        df["time"] = dt.dt.strftime("%H:%M")
    return df
