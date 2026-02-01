from __future__ import annotations

from datetime import datetime
            # JavaScript GPS capture button that sends value to Streamlit
            location_value = st.components.v1.html(
                """
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {
                            margin: 0;
                            padding: 10px;
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                        }
                        #captureBtn {
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            border: none;
                            padding: 15px 30px;
                            font-size: 16px;
                            font-weight: bold;
                            border-radius: 10px;
                            cursor: pointer;
                            width: 100%;
                            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
                            transition: all 0.3s ease;
                        }
                        #captureBtn:hover:not(:disabled) {
                            transform: translateY(-2px);
                            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
                        }
                        #captureBtn:disabled {
                            opacity: 0.6;
                            cursor: not-allowed;
                        }
                        #captureBtn.success {
                            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                        }
                        #status {
                            margin-top: 10px;
                            padding: 10px;
                            border-radius: 5px;
                            font-size: 14px;
                            display: none;
                        }
                        #status.error {
                            background: #fee;
                            color: #c00;
                            display: block;
                        }
                        #status.info {
                            background: #e3f2fd;
                            color: #1976d2;
                            display: block;
                        }
                    </style>
                </head>
                <body>
                    <button id=\"captureBtn\" onclick=\"getLocation()\">📍 Capture GPS Location</button>
                    <div id=\"status\"></div>
                    
                    <script>
                        function showStatus(message, type) {
                            const status = document.getElementById('status');
                            status.textContent = message;
                            status.className = type;
                        }
                        
                        function getLocation() {
                            const btn = document.getElementById('captureBtn');
                            
                            if (!navigator.geolocation) {
                                showStatus('❌ Geolocation is not supported by your browser', 'error');
                                return;
                            }
                            
                            btn.disabled = true;
                            btn.textContent = '⏳ Getting location...';
                            showStatus('📡 Requesting GPS location...', 'info');
                            
                            const options = {
                                enableHighAccuracy: true,
                                timeout: 10000,
                                maximumAge: 0
                            };
                            
                            navigator.geolocation.getCurrentPosition(
                                function(position) {
                                    const lat = position.coords.latitude;
                                    const lon = position.coords.longitude;
                                    const acc = position.coords.accuracy;
                                    
                                    btn.textContent = '✅ Location Captured!';
                                    btn.className = 'success';
                                    showStatus('✅ Success! Updating...', 'info');
                                    
                                    // Send value to Streamlit and request rerun
                                    const payload = { lat: String(lat), lon: String(lon), acc: String(acc) };
                                    try {
                                        window.parent.postMessage({ type: 'streamlit:setComponentValue', value: payload }, '*');
                                        window.parent.postMessage({ type: 'streamlit:requestRerun' }, '*');
                                    } catch (e) {
                                        // Fallback: put in query params
                                        const url = new URL(window.location.href);
                                        url.searchParams.set('t_lat', lat);
                                        url.searchParams.set('t_lon', lon);
                                        url.searchParams.set('t_acc', acc);
                                        window.location.href = url.toString();
                                    }
                                },
                                function(error) {
                                    btn.disabled = false;
                                    btn.textContent = '📍 Retry Capture Location';
                                    
                                    let errorMsg = '❌ ';
                                    switch(error.code) {
                                        case error.PERMISSION_DENIED:
                                            errorMsg += 'Permission denied. Please allow location access in browser settings.';
                                            break;
                                        case error.POSITION_UNAVAILABLE:
                                            errorMsg += 'Location unavailable. Please check your device settings.';
                                            break;
                                        case error.TIMEOUT:
                                            errorMsg += 'Location request timed out. Please try again.';
                                            break;
                                        default:
                                            errorMsg += 'An unknown error occurred: ' + error.message;
                                    }
                                    showStatus(errorMsg, 'error');
                                },
                                options
                            );
                        }
                    </script>
                </body>
                </html>
                """,
                height=170,
            )

            # If the component sent a value, persist it and rerun
            if location_value:
                try:
                    import json as _json
                    data = location_value
                    if isinstance(location_value, str):
                        data = _json.loads(location_value)
                    lat = float(data.get('lat', 0.0))
                    lon = float(data.get('lon', 0.0))
                    acc = float(data.get('acc', 0.0))
                    if lat and lon:
                        st.session_state.teacher_latitude = lat
                        st.session_state.teacher_longitude = lon
                        st.session_state.teacher_accuracy = acc
                        st.experimental_rerun() if hasattr(st, 'experimental_rerun') else st.rerun()
                except Exception:
                    pass
            st.stop()  # Stop rendering if location not captured
                    st.rerun()
        else:
            st.info("🌍 Click the button below to automatically capture your current GPS location")
            
            # JavaScript GPS capture button
            st.components.v1.html(
                """
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {
                            margin: 0;
                            padding: 10px;
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                        }
                        #captureBtn {
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            border: none;
                            padding: 15px 30px;
                            font-size: 16px;
                            font-weight: bold;
                            border-radius: 10px;
                            cursor: pointer;
                            width: 100%;
                            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
                            transition: all 0.3s ease;
                        }
                        #captureBtn:hover:not(:disabled) {
                            transform: translateY(-2px);
                            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
                        }
                        #captureBtn:disabled {
                            opacity: 0.6;
                            cursor: not-allowed;
                        }
                        #captureBtn.success {
                            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                        }
                        #status {
                            margin-top: 10px;
                            padding: 10px;
                            border-radius: 5px;
                            font-size: 14px;
                            display: none;
                        }
                        #status.error {
                            background: #fee;
                            color: #c00;
                            display: block;
                        }
                        #status.info {
                            background: #e3f2fd;
                            color: #1976d2;
                            display: block;
                        }
                    </style>
                </head>
                <body>
                    <button id="captureBtn" onclick="getLocation()">📍 Capture GPS Location</button>
                    <div id="status"></div>
                    
                    <script>
                        function showStatus(message, type) {
                            const status = document.getElementById('status');
                            status.textContent = message;
                            status.className = type;
                        }
                        
                        function getLocation() {
                            const btn = document.getElementById('captureBtn');
                            
                            if (!navigator.geolocation) {
                                showStatus('❌ Geolocation is not supported by your browser', 'error');
                                return;
                            }
                            
                            btn.disabled = true;
                            btn.textContent = '⏳ Getting location...';
                            showStatus('📡 Requesting GPS location...', 'info');
                            
                            const options = {
                                enableHighAccuracy: true,
                                timeout: 10000,
                                maximumAge: 0
                            };
                            
                            navigator.geolocation.getCurrentPosition(
                                function(position) {
                                    const lat = position.coords.latitude;
                                    const lon = position.coords.longitude;
                                    const acc = position.coords.accuracy;
                                    
                                    btn.textContent = '✅ Location Captured!';
                                    btn.className = 'success';
                                    showStatus('✅ Success! Redirecting...', 'info');
                                    
                                    // Send coords to Streamlit and request rerun
                                    try {
                                        window.parent.postMessage({
                                            type: 'streamlit:setQueryParams',
                                            queryParams: { t_lat: String(lat), t_lon: String(lon), t_acc: String(acc) }
                                        }, '*');
                                        window.parent.postMessage({ type: 'streamlit:requestRerun' }, '*');
                                    } catch (e) {
                                        // Fallback: update URL directly
                                        const url = new URL(window.location.href);
                                        url.searchParams.set('t_lat', lat);
                                        url.searchParams.set('t_lon', lon);
                                        url.searchParams.set('t_acc', acc);
                                        window.location.href = url.toString();
                                    }
                                },
                                function(error) {
                                    btn.disabled = false;
                                    btn.textContent = '📍 Retry Capture Location';
                                    
                                    let errorMsg = '❌ ';
                                    switch(error.code) {
                                        case error.PERMISSION_DENIED:
                                            errorMsg += 'Permission denied. Please allow location access in browser settings.';
                                            break;
                                        case error.POSITION_UNAVAILABLE:
                                            errorMsg += 'Location unavailable. Please check your device settings.';
                                            break;
                                        case error.TIMEOUT:
                                            errorMsg += 'Location request timed out. Please try again.';
                                            break;
                                        default:
                                            errorMsg += 'An unknown error occurred: ' + error.message;
                                    }
                                    showStatus(errorMsg, 'error');
                                },
                                options
                            );
                        }
                    </script>
                </body>
                </html>
                """,
                height=150,
            )
            st.stop()  # Stop rendering if location not captured

        with st.form("lecture_form"):
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
            
            # Hidden fields to store captured location
            if st.session_state.teacher_latitude != 0.0 and st.session_state.teacher_longitude != 0.0:
                st.caption(f"📍 Using GPS Location: {st.session_state.teacher_latitude:.6f}, {st.session_state.teacher_longitude:.6f}")
            
            submitted = st.form_submit_button("🚀 Create Session & Generate QR", use_container_width=True, type="primary")

        if submitted:
            if not (subject and room):
                st.error("❌ Subject and room are required.")
                return
            
            if st.session_state.teacher_latitude == 0.0 or st.session_state.teacher_longitude == 0.0:
                st.error("❌ Please capture your GPS location first using the button above!")
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
                    st.session_state.teacher_latitude,
                    st.session_state.teacher_longitude,
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
                base_url = st.text_input("📱 Attendance URL Base", value="http://localhost:8501", help="Change to your PC's IP for mobile access")
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

    if "attendance_lock" not in st.session_state:
        st.session_state.attendance_lock = set()

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
