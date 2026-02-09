from __future__ import annotations

from datetime import datetime
from uuid import uuid4
import sqlite3

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from streamlit_js_eval import streamlit_js_eval

from core.db import get_db
from core.utils import haversine_distance, now_iso, parse_iso, add_minutes, now_local
from core.qr import generate_qr

APP_BASE_URL = "https://smart-campus-system-4rvhza22xqtxanom66dczk.streamlit.app"


# Initialize session state for GPS location
st.session_state.setdefault("geo_location", None)

# Helpers to read query params robustly (supports list values)
def _qp_get(params, key: str):
    val = params.get(key)
    if val is None:
        return None
    # Streamlit query params may be lists
    if isinstance(val, (list, tuple)):
        return val[0] if val else None
    return val

def _sync_geo_from_url():
    params = _get_query_params()
    lat = _qp_get(params, "geo_lat")
    lon = _qp_get(params, "geo_lon")
    acc = _qp_get(params, "geo_acc")
    if lat and lon:
        try:
            st.session_state.geo_location = {
                "lat": float(lat),
                "lon": float(lon),
                "acc": float(acc) if acc is not None else 0.0,
            }
        except (ValueError, TypeError):
            pass

# GPS Message Handler - Receives GPS from JavaScript via postMessage
if "gps_message" not in st.session_state:
    st.session_state.gps_message = None


def _get_query_params():
    try:
        return dict(st.query_params)
    except Exception:
        return {}


def _render_geolocation_block(use_mock=False):
    """Render GPS capture UI (streamlit-js-eval)"""

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("### Capture Your Location")
    with col2:
        if st.button("Use Mock GPS", key="mock_gps", help="For testing without real GPS"):
            # Mock GPS coordinates (somewhere reasonable)
            st.session_state.geo_location = {
                "lat": 23.0225,  # Example: Ahmedabad
                "lon": 72.5714,
                "acc": 10.0,
                "source": "mock",
            }
            st.success("Mock GPS enabled for demo!")
            st.rerun()
    with col3:
        if st.button("Clear", key="clear_geo"):
            st.session_state.geo_location = None
            try:
                st.query_params.clear()
            except Exception:
                pass
            st.rerun()

    st.session_state.setdefault("gps_request", False)
    if st.button("Get Real GPS Location", key="real_gps"):
        st.session_state.gps_request = True

    loc = None
    if st.session_state.gps_request:
        loc = streamlit_js_eval(
            js_expressions="""
            new Promise((resolve) => {
                if (!navigator.geolocation) {
                    resolve({ error: "Geolocation not supported by this browser." });
                    return;
                }
                navigator.geolocation.getCurrentPosition(
                    (pos) => resolve({
                        lat: pos.coords.latitude,
                        lon: pos.coords.longitude,
                        acc: pos.coords.accuracy,
                        source: "real"
                    }),
                    (err) => resolve({ error: err && err.message ? err.message : "GPS permission denied or unavailable." })
                );
            })
            """,
            key="get_location"
        )

    if loc and isinstance(loc, dict) and "lat" in loc and "lon" in loc:
        st.session_state.geo_location = loc
        st.session_state.gps_request = False
        st.success("GPS captured and synced to Python.")
    elif st.session_state.gps_request and loc is not None:
        if isinstance(loc, dict) and loc.get("error"):
            st.warning(f"Could not read GPS: {loc['error']}")
        else:
            st.warning("Could not read GPS. Check browser permissions or use Mock/Manual GPS.")


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
    # Use local time because lecture times are stored as naive local times
    now = now_local()
    start = parse_iso(lecture["start_time"])
    end = parse_iso(lecture["end_time"])
    late_after = add_minutes(start, int(lecture["late_after_min"]))

    # Add a small buffer (2 minutes) to start time to account for clock drift
    start_buffer = start - pd.Timedelta(minutes=2)

    if now < start_buffer:
        return f"Rejected (Too Early - Starts {start.strftime('%H:%M')})"
    if now > end:
        return f"Rejected (Closed - Ended {end.strftime('%H:%M')})"

    if distance_m <= lecture["radius_m"]:
        return "Present" if now <= late_after else "Late"

    return f"Rejected (Out of Radius: {distance_m:.1f}m > {lecture['radius_m']}m)"


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
    
    # Initialize session state
    if "geo_location" not in st.session_state:
        st.session_state.geo_location = None
    
    tab1, tab2 = st.tabs(["📝 Create New Session", "📋 View Sessions"])
    
    with tab1:
        st.subheader("Create Lecture Session")
        
        # STEP 1: Get GPS Location
        st.info("📍 You must be physically present at the classroom. GPS location will be verified.")
        st.markdown("### Step 1: Capture Your GPS Location")
        
        # Sync GPS from URL (robust for both list/str values)
        _sync_geo_from_url()

        # Render GPS capture component
        _render_geolocation_block()

        # Sync again after component updates URL (ensures values get picked up)
        if not st.session_state.geo_location:
            _sync_geo_from_url()
        
        # Fallback control to force sync if rerun timing misses
        params = _get_query_params()
        col_sync, col_dbg = st.columns([1, 3])
        with col_sync:
            if st.button("🔄 Sync GPS Now", help="Force sync GPS from URL params"):
                _sync_geo_from_url()
                if st.session_state.geo_location:
                    st.success("✅ GPS synced successfully!")
                else:
                    st.warning("⚠️ No GPS found. Try 'Mock GPS' or enter manually.")
                st.rerun()

        with col_dbg:
            lat_dbg = _qp_get(params, "geo_lat")
            lon_dbg = _qp_get(params, "geo_lon")
            if lat_dbg and lon_dbg and not st.session_state.geo_location:
                st.caption(f"GPS in URL → lat={lat_dbg}, lon={lon_dbg} (sync needed)")
        
        # Manual entry fallback (always available)
        with st.expander("Manual GPS Entry", expanded=not bool(st.session_state.geo_location)):
            m_lat = st.number_input("Manual Latitude", value=0.0, format="%.6f", key="teacher_manual_lat")
            m_lon = st.number_input("Manual Longitude", value=0.0, format="%.6f", key="teacher_manual_lon")
            m_acc = st.number_input("Manual Accuracy (m)", min_value=0.0, value=10.0, key="teacher_manual_acc")
            if st.button("Use Manual Coordinates", help="Use these coordinates if GPS fails"):
                if m_lat == 0.0 and m_lon == 0.0:
                    st.warning("Please enter valid coordinates.")
                else:
                    st.session_state.geo_location = {"lat": m_lat, "lon": m_lon, "acc": m_acc, "source": "manual"}
                    st.success("Manual coordinates saved.")
                    st.rerun()

        # Show location if captured
        if st.session_state.geo_location:
            geo = st.session_state.geo_location
            source_emoji = "🎭" if geo.get("source") == "mock" else "🌍"
            source_text = "Mock GPS (Demo Mode)" if geo.get("source") == "mock" else "Real GPS"
            st.success(
                f"✅ Location Captured! {source_emoji} {source_text}\n📍 Lat: {geo['lat']:.6f} | Lon: {geo['lon']:.6f} | Accuracy: {geo['acc']:.1f}m"
            )

            # Debug panel (can be collapsed)
            with st.expander("🔎 Debug: GPS + Params", expanded=False):
                st.caption("Query params:")
                try:
                    st.code(str(dict(st.query_params)))
                except Exception:
                    st.code("<unavailable>")
                st.caption("Session geo:")
                st.code(str(st.session_state.geo_location))

        # STEP 2: Lecture form (always visible)
        st.markdown("---")
        st.markdown("### Step 2: Enter Lecture Details")

        default_radius = _get_setting(conn, "radius_m", 40)
        default_late = int(_get_setting(conn, "late_after_min", 10))
        default_duration = int(_get_setting(conn, "time_window_min", 60))

        with st.form("lecture_form", clear_on_submit=False):
            col1, col2 = st.columns(2)

            with col1:
                subject = st.text_input("📚 Subject *", placeholder="e.g., Data Structures")
                room = st.text_input("🏫 Room / Classroom *", placeholder="e.g., Lab 301")
                now_local_dt = now_local()
                date = st.date_input("📅 Lecture Date", value=now_local_dt.date())
                start_time = st.time_input("⏰ Start Time", value=now_local_dt.time().replace(second=0, microsecond=0))

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

            if not st.session_state.geo_location:
                st.error("❌ Please capture GPS or enter manual coordinates before creating the session.")
                return

            try:
                geo = st.session_state.geo_location
                lat = geo["lat"]
                lon = geo["lon"]

                start_dt = datetime.combine(date, start_time)
                end_dt = start_dt + pd.Timedelta(minutes=int(duration_min))
                session_id = f"{subject[:4].upper()}-{uuid4().hex[:8]}"

                # Insert into database
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

                # Display QR Code and details
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### 📱 QR Code")
                    attendance_url = f"{APP_BASE_URL}/?session_id={session_id}"

                    st.markdown("#### Generating QR Code...")
                    try:
                        qr_path = generate_qr(attendance_url)
                        if qr_path and qr_path.exists():
                            # Verify file is real and get file size
                            file_size = qr_path.stat().st_size
                            st.image(str(qr_path), caption=f"Scan to mark attendance for {subject}", width=300)
                            st.success(f"✅ QR Code generated successfully!")

                            # Show verification details
                            with st.expander("🔍 QR Code Details", expanded=False):
                                st.caption(f"📁 File Path: {qr_path}")
                                st.caption(f"📊 File Size: {file_size} bytes")
                                st.caption(f"✅ File Exists: True")
                                st.caption(f"📍 URL Encoded: {attendance_url}")
                        else:
                            st.error("❌ QR file not found after generation")
                    except Exception as e:
                        st.error(f"❌ Error generating QR: {str(e)}")
                        st.info(f"📱 Share this URL instead: {attendance_url}")

                with col2:
                    st.markdown("### 🔗 Direct Link")
                    st.code(attendance_url, language="text")

                    # Regenerate QR if needed
                    if st.button("🔄 Regenerate QR", help="Generate a new QR code"):
                        try:
                            qr_path = generate_qr(attendance_url)
                            if qr_path.exists():
                                file_size = qr_path.stat().st_size
                                st.success(f"✅ QR regenerated! ({file_size} bytes)")
                                st.rerun()
                            else:
                                st.error("❌ QR generation failed")
                        except Exception as e:
                            st.error(f"Failed to regenerate: {e}")

                    st.markdown(f"""
                    **Session Details:**
                    - 📚 Subject: {subject}
                    - 🏫 Room: {room}
                    - 📅 Date: {date}
                    - ⏰ Time: {start_time} - {end_dt.time()}
                    - 📍 Radius: {radius_m}m
                    - ⏳ Late after: {late_after_min} min
                    - 🌍 Location: ({lat:.6f}, {lon:.6f})
                    """)

                # Reset helpers
                st.session_state["force_show_form"] = False
                # Keep geo for convenience; do not clear immediately
                # Clear URL params to avoid duplicate sync
                try:
                    st.query_params.clear()
                except Exception:
                    pass

            except Exception as e:
                st.error(f"❌ Error creating session: {str(e)}")
    
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
    session_id = (_qp_get(params, "session_id") or "").strip()

    if st.button("🔄 Refresh sessions", help="Reload the latest lecture list"):
        st.rerun()

    fresh_conn = get_db()
    try:
        lectures = fresh_conn.execute(
            "SELECT * FROM lectures ORDER BY start_time DESC LIMIT 20"
        ).fetchall()
    finally:
        fresh_conn.close()
    lecture_map = {row["session_id"]: row for row in lectures}

    if not lectures:
        st.info("No lecture sessions found yet. Ask your teacher to create one, then refresh.")

    def _select_session() -> str | None:
        st.info("📱 Scan the QR code from your teacher to mark attendance, or select a session below.")
        selected = st.selectbox(
            "📚 Select Lecture Session",
            ["-- Select --"] + list(lecture_map.keys()),
            format_func=lambda x: f"{lecture_map[x]['subject']} - {lecture_map[x]['room']} ({lecture_map[x]['start_time'][:16]})" if x != "-- Select --" else "-- Select --"
        )
        if selected == "-- Select --":
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
                    ts = pd.to_datetime(record[4], errors="coerce")
                    date_str = ts.strftime("%Y-%m-%d") if pd.notna(ts) else str(record[4])[:10]
                    time_str = ts.strftime("%H:%M") if pd.notna(ts) else str(record[4])[11:16]
                    st.markdown(f"""
                    <div style='padding: 0.75rem; margin: 0.5rem 0; border-left: 4px solid {status_color}; background: rgba(255,255,255,0.05); border-radius: 4px;'>
                        <strong>{record[1]}</strong> - {record[2]}<br>
                        Status: <span style='color: {status_color};'>{record[3]}</span><br>
                        <small>{date_str} {time_str}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No attendance history yet")
            return None

        return selected

    if not session_id:
        session_id = _select_session()
        if not session_id:
            return

    lecture = lecture_map.get(session_id)
    if session_id and not lecture:
        lecture = conn.execute(
            "SELECT * FROM lectures WHERE session_id = ?",
            (session_id,),
        ).fetchone()
    if not lecture:
        st.warning("⚠️ Invalid or expired session. Please select a valid lecture below.")
        session_id = _select_session()
        if not session_id:
            return
        lecture = lecture_map.get(session_id)
        if not lecture:
            lecture = conn.execute(
                "SELECT * FROM lectures WHERE session_id = ?",
                (session_id,),
            ).fetchone()
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

    # Better GPS capture flow for students
    st.info("📍 **Step 1:** Click 'Get Real GPS Location' below (or use 'Mock GPS' for testing)")
    st.info("📍 **Step 2:** If GPS fails, scroll down and enter coordinates manually")
    
    _render_geolocation_block()
    
    # Sync GPS from URL if present
    _sync_geo_from_url()
    
    # Manual Sync Button
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Sync GPS Now", help="Force sync GPS from URL"):
            _sync_geo_from_url()
            if st.session_state.geo_location:
                st.success("✅ GPS synced!")
            st.rerun()
    with col2:
        if st.button("🎭 Use Mock GPS", key="student_mock", help="For demo/testing"):
            st.session_state.geo_location = {
                "lat": 23.0225,
                "lon": 72.5714,
                "acc": 10.0,
                "source": "mock"
            }
            st.success("🎭 Mock GPS enabled!")
            st.rerun()

    geo = _get_geo_from_query()

    default_lat = float(geo[0]) if geo else 0.0
    default_lon = float(geo[1]) if geo else 0.0
    default_acc = float(geo[2]) if geo else 10.0

    with st.form("attendance_confirm"):
        st.markdown("#### 🌐 GPS Coordinates (Auto or Manual)")
        st.caption("If 'Get GPS Location' failed, enter coordinates manually below (ask Teacher for Lat/Lon if needed).")
        col1, col2, col3 = st.columns(3)
        with col1:
            manual_lat = st.number_input(
                "Latitude",
                min_value=-90.0,
                max_value=90.0,
                value=default_lat,
                step=0.000001,
                format="%.6f",
            )
        with col2:
            manual_lon = st.number_input(
                "Longitude",
                min_value=-180.0,
                max_value=180.0,
                value=default_lon,
                step=0.000001,
                format="%.6f",
            )
        with col3:
            manual_acc = st.number_input(
                "Accuracy (m)",
                min_value=0.0,
                value=default_acc,
                step=0.1,
            )
        
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
            
            # Generate and show receipt QR
            st.markdown("---")
            st.markdown("#### 📋 Attendance Receipt QR")
            try:
                receipt_url = f"{APP_BASE_URL}/?session_id={session_id}&receipt=true&enrollment={user['enrollment']}"
                receipt_qr = generate_qr(receipt_url)
                if receipt_qr and receipt_qr.exists():
                    file_size = receipt_qr.stat().st_size
                    col_receipt, col_info = st.columns(2)
                    with col_receipt:
                        st.image(str(receipt_qr), caption="Receipt QR Code", width=200)
                        with st.expander("📁 Receipt QR Details", expanded=False):
                            st.caption(f"📁 File: {receipt_qr.name}")
                            st.caption(f"📊 Size: {file_size} bytes")
                            st.caption(f"✅ Generated: Yes")
                    with col_info:
                        st.markdown(f"""
                        **✅ Attendance Confirmed**
                        - Student: {user['name']}
                        - Enrollment: {user['enrollment']}
                        - Session: {session_id}
                        - Status: **{status}**
                        - Time: {now_local().strftime('%H:%M:%S')}
                        - Distance: {distance_m:.1f}m
                        """)
                else:
                    st.warning("⚠️ Receipt QR file not generated properly")
            except Exception as e:
                st.warning(f"Could not generate receipt QR: {e}")
            
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
