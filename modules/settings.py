import streamlit as st
from core.utils import now_iso


def _get_setting(conn, key: str, default: str):
    row = conn.execute("SELECT value FROM system_settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def _set_setting(conn, key: str, value: str):
    conn.execute(
        """
        INSERT INTO system_settings (key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
        """,
        (key, value, now_iso()),
    )
    conn.commit()


def render_settings(conn):
    st.subheader("System Settings")

    default_radius = float(_get_setting(conn, "radius_m", "40"))
    default_late = int(_get_setting(conn, "late_after_min", "10"))
    time_window = int(_get_setting(conn, "time_window_min", "60"))

    radius_m = st.number_input("Default Radius (meters)", min_value=10, max_value=100, value=int(default_radius))
    late_after_min = st.number_input("Default Late Window (minutes)", min_value=0, max_value=30, value=int(default_late))
    time_window_min = st.number_input("Default Lecture Duration (minutes)", min_value=30, max_value=240, value=int(time_window))

    if st.button("Save Settings"):
        _set_setting(conn, "radius_m", str(radius_m))
        _set_setting(conn, "late_after_min", str(late_after_min))
        _set_setting(conn, "time_window_min", str(time_window_min))
        st.success("Settings saved.")
