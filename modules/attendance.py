from __future__ import annotations

from datetime import datetime
from uuid import uuid4
import sqlite3

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from core.utils import haversine_distance, now_iso, parse_iso, add_minutes
from core.qr import generate_qr


# Initialize session state for GPS location
st.session_state.setdefault("geo_location", None)

# Check if location is in localStorage via JavaScript
st.components.v1.html(
    """
    <script>
    // Expose location data to Streamlit
    const stored = localStorage.getItem('streamlit_geo_location');
    if (stored) {
        window.streamlit_geo_location = JSON.parse(stored);
    }
    </script>
    """,
    height=1,
)


def _get_query_params():
    params = st.query_params
    return params


def _render_geolocation_block():
    st.info("📍 Allow GPS access to confirm presence. No device fingerprinting is used.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### 📍 Capture Your Location")
    with col2:
        if st.button("🔄 Clear", key="clear_geo"):
            st.session_state.geo_location = None
            # Clear query params
            st.query_params.clear()
            st.rerun()
    
    # HTML component with location capture using Streamlit's session communication
    st.components.v1.html(
        """
        <div style="padding: 16px; background: rgba(76, 175, 80, 0.1); border-radius: 8px; border: 2px solid #4CAF50;">
            <button id="geoBtn" onclick="captureLocation()" style="padding: 12px 24px; font-size: 16px; background: #4CAF50; color: white; border: none; border-radius: 6px; cursor: pointer; width: 100%; font-weight: bold;">
                📍 Get GPS Location
            </button>
            <div id="status" style="margin-top: 12px; font-size: 14px; color: #666; text-align: center;"></div>
        </div>
        
        <script>
        function captureLocation(){
            const btn = document.getElementById('geoBtn');
            const status = document.getElementById('status');
            
            if (!navigator.geolocation) {
                status.innerHTML = '❌ Geolocation not supported';
                status.style.color = 'red';
                return;
            }
            
            btn.disabled = true;
            btn.innerHTML = '📍 Getting Location...';
            status.innerHTML = '⏳ Acquiring GPS...';
            status.style.color = '#666';
            
            navigator.geolocation.getCurrentPosition(
                function(pos) {
                    const data = {
                        lat: pos.coords.latitude,
                        lon: pos.coords.longitude,
                        acc: pos.coords.accuracy
                    };
                    
                    // Store in localStorage
                    localStorage.setItem('streamlit_geo_location', JSON.stringify(data));
                    
                    status.innerHTML = `✅ Location captured!<br>Lat: ${data.lat.toFixed(6)}<br>Lon: ${data.lon.toFixed(6)}<br>Accuracy: ${data.acc.toFixed(1)}m`;
                    status.style.color = 'green';
                    btn.innerHTML = '✅ Location Captured';
                    btn.style.background = '#2196F3';
                    
                    // Add to URL params and reload
                    const params = new URLSearchParams(window.parent.location.search);
                    params.set('geo_lat', data.lat);
                    params.set('geo_lon', data.lon);
                    params.set('geo_acc', data.acc);
                    window.parent.location.search = params.toString();
                },
                function(err) {
                    status.innerHTML = '❌ ' + err.message;
                    status.style.color = 'red';
                    btn.disabled = false;
                    btn.innerHTML = '📍 Try Again';
                },
                { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
            );
        }
        
        // Check if location was stored
        window.addEventListener('load', function() {
            const params = new URLSearchParams(window.parent.location.search);
            if (params.has('geo_lat')) {
                const status = document.getElementById('status');
                status.innerHTML = `✅ Location: ${parseFloat(params.get('geo_lat')).toFixed(6)}, ${parseFloat(params.get('geo_lon')).toFixed(6)}`;
                status.style.color = 'green';
                document.getElementById('geoBtn').innerHTML = '✅ Location Captured';
                document.getElementById('geoBtn').disabled = true;
                document.getElementById('geoBtn').style.background = '#2196F3';
            }
        });
        </script>
        """,
        height=180,
    )


def _get_geo_from_query():
    if "geo_location" in st.session_state and st.session_state.geo_location:
        geo = st.session_state.geo_location
        lat = geo.get("lat")
        lon = geo.get("lon")
        acc = geo.get("acc")
        if lat and lon and acc is not None:
            return lat, lon, acc
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


def _get_setting(conn, key: str, default: float) -> float:
    row = conn.execute("SELECT value FROM system_settings WHERE key = ?", (key,)).fetchone()
    return float(row["value"]) if row else float(default)


def render_teacher_attendance(conn, user):
    st.title("✅ Attendance Management")
    st.markdown("---")
    
    # Ensure session state is initialized
    if "geo_location" not in st.session_state:
        st.session_state.geo_location = None
    
    # Check for location in query params and populate session state
    params = _get_query_params()
    if params.get("geo_lat"):
        try:
            st.session_state.geo_location = {
                "lat": float(params.get("geo_lat")),
                "lon": float(params.get("geo_lon")),
                "acc": float(params.get("geo_acc"))
            }
        except (ValueError, TypeError):
            pass
    
    tab1, tab2 = st.tabs(["📝 Create New Session", "📋 View Sessions"])
    
    with tab1:
        st.subheader("Create Lecture Session")
        default_radius = _get_setting(conn, "radius_m", 40)
        default_late = int(_get_setting(conn, "late_after_min", 10))
        default_duration = int(_get_setting(conn, "time_window_min", 60))

        st.info("📍 You must be physically present at the classroom. GPS location will be verified.")
        
        # GPS Location capture
        _render_geolocation_block()
        
        # Display captured location
        geo = st.session_state.get("geo_location")
        if geo:
            lat = geo.get("lat")
            lon = geo.get("lon")
            acc = geo.get("acc")
            
            st.success("✅ Location verified! You can now create a session.")
            with st.expander("📍 Location Details", expanded=False):
                col1, col2, col3 = st.columns(3)
                col1.metric("📍 Latitude", f"{lat:.6f}")
                col2.metric("📍 Longitude", f"{lon:.6f}")
                col3.metric("📡 Accuracy", f"{acc:.1f}m")
        else:
            st.error("❌ GPS location not captured yet. Please click the button above to capture your location.")
            return

        with st.form("lecture_form"):
            st.markdown("### 📋 Lecture Details")
            col1, col2 = st.columns(2)
            
            with col1:
                subject = st.text_input("📚 Subject *", placeholder="e.g., Data Structures")
                room = st.text_input("🏫 Room / Classroom *", placeholder="e.g., Lab 301")
                date = st.date_input("📅 Lecture Date")
                start_time = st.time_input("⏰ Start Time")
            
            with col2:
                duration_min = st.number_input("⏱️ Duration (minutes)", min_value=30, max_value=240, value=default_duration)
                late_after_min = st.number_input("⏳ Late After (minutes)", min_value=0, max_value=30, value=default_late)
                radius_m = st.slider("📍 Allowed Radius (meters)", min_value=10, max_value=100, value=int(default_radius))
            
            st.info("💡 Session will be created at your current GPS location. Students must be within the radius to mark attendance.")
            
            submitted = st.form_submit_button("🚀 Create Session & Generate QR", use_container_width=True, type="primary")

        if submitted:
            if not (subject and room):
                st.error("❌ Subject and room are required.")
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
                    lat,
                    lon,
                    radius_m,
                    int(late_after_min),
                    now_iso(),
                ),
            )
            conn.commit()
            
            st.success(f"✅ Lecture session created: **{session_id}**")
            st.balloons()

            col1, col2 = st.columns(2)
            
            with col1:
                base_url = st.text_input("📱 Attendance URL Base", value="http://localhost:8502", help="Change to your PC's IP for mobile access")
                attendance_url = f"{base_url}/?session_id={session_id}"
                
                st.markdown("### 📱 QR Code")
                qr_path = generate_qr(attendance_url)
                st.image(str(qr_path), caption=f"Scan to mark attendance for {subject}", width=300)
            
            with col2:
                st.markdown("### 🔗 Direct Link")
                st.code(attendance_url, language="text")
                st.markdown(f"""
                **Session Details:**
                - 📚 Subject: {subject}
                - 🏫 Room: {room}
                - 📅 Date: {date}
                - ⏰ Time: {start_time} - {end_dt.time()}
                - 📍 Radius: {radius_m}m
                - ⏳ Late after: {late_after_min} min
                """)

            
            st.success(f"✅ Lecture session created: **{session_id}**")
            st.balloons()

            col1, col2 = st.columns(2)
            
            with col1:
                base_url = st.text_input("📱 Attendance URL Base", value="http://localhost:8502", help="Change to your PC's IP for mobile access")
                attendance_url = f"{base_url}/?session_id={session_id}"
                
                st.markdown("### 📱 QR Code")
                qr_path = generate_qr(attendance_url)
                st.image(str(qr_path), caption=f"Scan to mark attendance for {subject}", width=300)
            
            with col2:
                st.markdown("### 🔗 Direct Link")
                st.code(attendance_url, language="text")
                st.markdown(f"""
                **Session Details:**
                - 📚 Subject: {subject}
                - 🏫 Room: {room}
                - 📅 Date: {date}
                - ⏰ Time: {start_time} - {end_dt.time()}
                - 📍 Radius: {radius_m}m
                - ⏳ Late after: {late_after_min} min
                """)
    
    with tab2:
        st.subheader("📋 Recent Lecture Sessions")
        sessions = conn.execute(
            """
            SELECT session_id, subject, room, start_time, end_time,
                   (SELECT COUNT(*) FROM attendance WHERE session_id = lectures.session_id) as attendance_count
            FROM lectures
            WHERE teacher_id = ?
            ORDER BY start_time DESC
            LIMIT 20
            """,
            (user["id"],)
        ).fetchall()
        
        if not sessions:
            st.info("📭 No sessions created yet. Create your first session above!")
            return
        
        for session in sessions:
            with st.expander(f"📚 {session[1]} - {session[0]} ({session[5]} students)"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Room:** {session[2]}")
                    st.write(f"**Start:** {session[3][:16]}")
                with col2:
                    st.write(f"**End:** {session[4][:16]}")
                    st.write(f"**Attendance:** {session[5]} students")
                with col3:
                    if st.button("📊 View Details", key=f"view_{session[0]}"):
                        st.info("Detailed view coming soon!")
                
                # Show attendance for this session
                att_records = conn.execute(
                    """
                    SELECT a.enrollment, u.name, a.status, a.timestamp, a.distance_m
                    FROM attendance a
                    LEFT JOIN users u ON a.enrollment = u.enrollment
                    WHERE a.session_id = ?
                    ORDER BY a.timestamp
                    """,
                    (session[0],)
                ).fetchall()
                
                if att_records:
                    for record in att_records:
                        status_emoji = "✅" if record[2] == "Present" else ("⏰" if record[2] == "Late" else "❌")
                        st.text(f"{status_emoji} {record[0]} - {record[1]} - {record[2]} ({record[4]:.1f}m away)")
                else:
                    st.caption("No attendance marked yet")


def render_student_attendance(conn, user):
    st.title("✅ Mark Attendance")
    st.markdown("---")
    
    # Ensure session state is initialized
    st.session_state.setdefault("attendance_lock", set())

    params = _get_query_params()
    session_id = params.get("session_id", "")

    lectures = conn.execute(
        "SELECT * FROM lectures ORDER BY start_time DESC LIMIT 20"
    ).fetchall()
    lecture_map = {row["session_id"]: row for row in lectures}

    if not session_id:
        st.info("📱 Scan the QR code from your teacher to mark attendance, or select a session below.")
        session_id = st.selectbox(
            "📚 Select Lecture Session",
            ["-- Select --"] + list(lecture_map.keys()),
            format_func=lambda x: f"{lecture_map[x]['subject']} - {lecture_map[x]['room']} ({lecture_map[x]['start_time'][:16]})" if x != "-- Select --" else "-- Select --"
        )
        if session_id == "-- Select --":
            
            # Show attendance history
            st.markdown("---")
            st.subheader("📊 Your Attendance History")
            history = conn.execute(
                """
                SELECT a.session_id, l.subject, l.room, a.status, a.timestamp
                FROM attendance a
                LEFT JOIN lectures l ON a.session_id = l.session_id
                WHERE a.enrollment = ?
                ORDER BY a.timestamp DESC
                LIMIT 10
                """,
                (user["enrollment"],)
            ).fetchall()
            
            if history:
                for record in history:
                    status_color = "green" if record[3] == "Present" else ("orange" if record[3] == "Late" else "red")
                    st.markdown(f"""
                    <div style='padding: 0.75rem; margin: 0.5rem 0; border-left: 4px solid {status_color}; background: rgba(255,255,255,0.05); border-radius: 4px;'>
                        <strong>{record[1]}</strong> - {record[2]}<br>
                        Status: <span style='color: {status_color};'>{record[3]}</span><br>
                        <small>{record[4][:16]}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No attendance history yet")
            return

    lecture = lecture_map.get(session_id)
    if not lecture:
        st.error("❌ Invalid or expired session.")
        return

    st.markdown(f"""
    ### 📚 {lecture['subject']}
    **🏫 Room:** {lecture['room']}  
    **⏰ Time:** {lecture['start_time'][:16]} - {lecture['end_time'][:16]}  
    **📍 Radius:** {lecture['radius_m']}m
    """)
    
    st.markdown("---")

    # Ensure session state initialized
    st.session_state.setdefault("attendance_lock", set())

    # Check if already marked
    existing = conn.execute(
        "SELECT status, timestamp FROM attendance WHERE session_id = ? AND enrollment = ?",
        (session_id, user["enrollment"])
    ).fetchone()
    
    if existing:
        status_color = "green" if existing[0] == "Present" else ("orange" if existing[0] == "Late" else "red")
        st.markdown(f"""
        <div style='padding: 2rem; background: linear-gradient(135deg, rgba(46,213,115,0.2) 0%, rgba(0,184,148,0.2) 100%); 
                    border-radius: 12px; text-align: center; border: 2px solid {status_color};'>
            <h2 style='color: {status_color}; margin: 0;'>✅ Attendance Already Marked</h2>
            <p style='font-size: 1.2rem; margin: 1rem 0;'>Status: <strong>{existing[0]}</strong></p>
            <p style='color: #888;'>Marked at: {existing[1][:16]}</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    if session_id in st.session_state.attendance_lock:
        st.warning("⚠️ Attendance already marked in this browser session.")
        return

    st.info("📍 Click the button below to allow GPS access and mark your attendance.")
    _render_geolocation_block()
    geo = _get_geo_from_query()

    with st.form("attendance_confirm"):
        st.markdown("#### 🌐 GPS Coordinates")
        col1, col2, col3 = st.columns(3)
        with col1:
            manual_lat = st.number_input("Latitude", format="%.6f", value=geo[0] if geo else 0.0)
        with col2:
            manual_lon = st.number_input("Longitude", format="%.6f", value=geo[1] if geo else 0.0)
        with col3:
            manual_acc = st.number_input("Accuracy (m)", min_value=0.0, value=geo[2] if geo else 0.0)
        
        st.caption("💡 Coordinates will be auto-filled if GPS is enabled")
        
        submitted = st.form_submit_button("✅ Confirm My Presence", use_container_width=True, type="primary")

    if submitted:
        if geo:
            lat, lon, acc = geo
        else:
            lat, lon, acc = manual_lat, manual_lon, manual_acc
        
        if lat == 0.0 and lon == 0.0:
            st.error("❌ Please enable GPS or enter coordinates manually.")
            return

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
            
            status_color = "green" if "Present" in status else ("orange" if "Late" in status else "red")
            st.markdown(f"""
            <div style='padding: 2rem; background: linear-gradient(135deg, rgba(46,213,115,0.3) 0%, rgba(0,184,148,0.3) 100%); 
                        border-radius: 12px; text-align: center; margin: 2rem 0;'>
                <h1 style='color: {status_color}; margin: 0;'>🎉</h1>
                <h2 style='color: {status_color}; margin: 0.5rem 0;'>{status}</h2>
                <p style='font-size: 1.1rem;'>Distance: {distance_m:.1f}m from classroom</p>
            </div>
            """, unsafe_allow_html=True)
            st.balloons()
        except sqlite3.IntegrityError:
            st.error("❌ Attendance already submitted for this session.")


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
