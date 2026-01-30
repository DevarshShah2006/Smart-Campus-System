from __future__ import annotations

from datetime import datetime
from uuid import uuid4
import sqlite3

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from core.utils import haversine_distance, now_iso, parse_iso, add_minutes
from core.qr import generate_qr


def _get_setting(conn, key: str, default: float) -> float:
    row = conn.execute("SELECT value FROM system_settings WHERE key = ?", (key,)).fetchone()
    return float(row["value"]) if row else float(default)


def _get_query_params():
    params = st.query_params
    return params


def _render_geolocation_block():
    st.info("Allow GPS access to confirm presence. No device fingerprinting is used.")
    st.components.v1.html(
        """
        <script>
        function sendLocation(){
            if (!navigator.geolocation) {
                const params = new URLSearchParams(window.parent.location.search);
                params.set('geo_error', 'Geolocation not supported');
                window.parent.location.search = params.toString();
                return;
            }
            navigator.geolocation.getCurrentPosition(function(pos){
                const params = new URLSearchParams(window.parent.location.search);
                params.set('lat', pos.coords.latitude);
                params.set('lon', pos.coords.longitude);
                params.set('acc', pos.coords.accuracy);
                window.parent.location.search = params.toString();
            }, function(err){
                const params = new URLSearchParams(window.parent.location.search);
                params.set('geo_error', err.message);
                window.parent.location.search = params.toString();
            }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 });
        }
        </script>
        <button onclick="sendLocation()">Get GPS Location</button>
        """,
        height=120,
    )


def _get_geo_from_query():
    params = _get_query_params()
    if "geo_error" in params:
        st.warning(params.get("geo_error", "Unknown error"))
    try:
        lat = float(params.get("lat", ""))
        lon = float(params.get("lon", ""))
        acc = float(params.get("acc", ""))
        return lat, lon, acc
    except (ValueError, TypeError):
        return None


def _attendance_status(lecture, distance_m: float) -> str:
    now = datetime.utcnow()
    start = parse_iso(lecture["start_time"])
    end = parse_iso(lecture["end_time"])
    late_after = add_minutes(start, int(lecture["late_after_min"]))

    if now < start:
        return "Rejected (Too Early)"
    if now > end:
        return "Rejected (Closed)"

    if distance_m <= lecture["radius_m"]:
        return "Present" if now <= late_after else "Late"

    return "Rejected (Out of Radius)"


def _log_audit(conn, action: str, details: str, actor_id: int | None):
    conn.execute(
        "INSERT INTO audit_logs (action, details, actor_id, created_at) VALUES (?, ?, ?, ?)",
        (action, details, actor_id, now_iso()),
    )
    conn.commit()


def render_teacher_attendance(conn, user):
    st.subheader("Create Lecture Session")
    default_radius = _get_setting(conn, "radius_m", 40)
    default_late = int(_get_setting(conn, "late_after_min", 10))
    default_duration = int(_get_setting(conn, "time_window_min", 60))

    with st.form("lecture_form"):
        subject = st.text_input("Subject")
        room = st.text_input("Room / Classroom")
        date = st.date_input("Lecture Date")
        start_time = st.time_input("Start Time")
        duration_min = st.number_input("Duration (minutes)", min_value=30, max_value=240, value=default_duration)
        late_after_min = st.number_input("Late After (minutes)", min_value=0, max_value=30, value=default_late)
        latitude = st.number_input("Classroom Latitude", format="%.6f")
        longitude = st.number_input("Classroom Longitude", format="%.6f")
        radius_m = st.number_input("Allowed Radius (meters)", min_value=10, max_value=100, value=int(default_radius))
        submitted = st.form_submit_button("Create Session")

    if submitted:
        if not subject:
            st.error("Subject is required.")
            return

        start_dt = datetime.combine(date, start_time)
        end_dt = start_dt + pd.Timedelta(minutes=int(duration_min))
        session_id = f"{subject[:4].upper()}-{uuid4().hex[:8]}"

        conn.execute(
            """
            INSERT INTO lectures (session_id, teacher_id, subject, room, start_time, end_time, latitude, longitude, radius_m, late_after_min, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                user["id"],
                subject,
                room,
                start_dt.isoformat(),
                end_dt.isoformat(),
                latitude,
                longitude,
                radius_m,
                int(late_after_min),
                now_iso(),
            ),
        )
        conn.commit()
        st.success(f"Lecture session created: {session_id}")

        base_url = st.text_input("Attendance URL Base", value="http://localhost:8501")
        attendance_url = f"{base_url}/?session_id={session_id}"
        qr_path = generate_qr(attendance_url)
        st.image(str(qr_path), caption="Scan QR to open attendance")
        st.code(attendance_url)


def render_student_attendance(conn, user):
    st.subheader("Mark Attendance")

    params = _get_query_params()
    session_id = params.get("session_id", "")

    lectures = conn.execute(
        "SELECT * FROM lectures ORDER BY start_time DESC LIMIT 20"
    ).fetchall()
    lecture_map = {row["session_id"]: row for row in lectures}

    if not session_id:
        session_id = st.selectbox("Select Lecture Session", ["-- Select --"] + list(lecture_map.keys()))
        if session_id == "-- Select --":
            st.info("Scan the QR code or select a session.")
            return

    lecture = lecture_map.get(session_id)
    if not lecture:
        st.error("Invalid or expired session.")
        return

    st.write(f"Subject: {lecture['subject']}")
    st.write(f"Room: {lecture['room']}")

    if "attendance_lock" not in st.session_state:
        st.session_state.attendance_lock = set()

    if session_id in st.session_state.attendance_lock:
        st.warning("Attendance already marked in this browser session.")
        return

    _render_geolocation_block()
    geo = _get_geo_from_query()

    with st.form("attendance_confirm"):
        st.write("If GPS fails, you may enter coordinates manually.")
        manual_lat = st.number_input("Latitude", format="%.6f")
        manual_lon = st.number_input("Longitude", format="%.6f")
        manual_acc = st.number_input("Accuracy (meters)", min_value=0.0, value=0.0)
        submitted = st.form_submit_button("Confirm Presence")

    if submitted:
        if geo:
            lat, lon, acc = geo
        else:
            lat, lon, acc = manual_lat, manual_lon, manual_acc

        distance_m = haversine_distance(lat, lon, lecture["latitude"], lecture["longitude"])
        status = _attendance_status(lecture, distance_m)

        if acc > 100 or distance_m > lecture["radius_m"] * 1.5:
            _log_audit(conn, "ATTENDANCE_ANOMALY", f"{user['enrollment']} accuracy={acc} distance={distance_m:.1f}", user["id"])

        try:
            conn.execute(
                """
                INSERT INTO attendance (session_id, enrollment, timestamp, status, latitude, longitude, accuracy, distance_m)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (session_id, user["enrollment"], now_iso(), status, lat, lon, acc, distance_m),
            )
            conn.commit()
            st.session_state.attendance_lock.add(session_id)
            st.success(f"Attendance marked: {status}")
        except sqlite3.IntegrityError:
            st.error("Attendance already submitted for this session.")


def render_attendance_override(conn, user=None):
    st.subheader("Manual Override")
    records = conn.execute(
        "SELECT * FROM attendance ORDER BY timestamp DESC LIMIT 50"
    ).fetchall()
    if not records:
        st.info("No attendance records.")
        return

    df = pd.DataFrame(records)
    st.dataframe(df, use_container_width=True)
    record_id = st.number_input("Attendance ID", min_value=1, step=1)
    status = st.selectbox("New Status", ["Present", "Late", "Rejected (Manual)"])
    reason = st.text_area("Reason for Override")

    if st.button("Apply Override"):
        if not reason:
            st.warning("Reason is required.")
            return
        conn.execute(
            """
            UPDATE attendance
            SET status = ?, override_reason = ?, override_by = ?
            WHERE id = ?
            """,
            (status, reason, user["id"] if user else None, int(record_id)),
        )
        conn.commit()
        st.success("Override saved.")


def render_attendance_analytics(conn):
    st.subheader("Attendance Analytics")
    records = conn.execute("SELECT status, timestamp FROM attendance").fetchall()
    if not records:
        st.info("No attendance data yet.")
        return

    df = pd.DataFrame(records, columns=["status", "timestamp"])
    if df.empty or "timestamp" not in df.columns:
        st.info("No attendance data yet.")
        return
    
    df["date"] = pd.to_datetime(df["timestamp"]).dt.date
    summary = df.groupby(["date", "status"]).size().unstack(fill_value=0)

    fig, ax = plt.subplots()
    summary.plot(kind="bar", ax=ax)
    ax.set_xlabel("Date")
    ax.set_ylabel("Count")
    ax.set_title("Attendance Status by Date")
    st.pyplot(fig)
