from pathlib import Path

import streamlit as st

from core.utils import build_timeline
from core.qr import generate_qr


PUBLIC_APP_URL = "https://smart-campus-system-4rvhza22xqtxanom66dczk.streamlit.app/"


def _get_public_app_qr_path() -> Path:
    cached = st.session_state.get("public_app_qr_path")
    if cached:
        try:
            cached_path = Path(cached)
            if cached_path.exists():
                return cached_path
        except Exception:
            pass

    qr_path = generate_qr(PUBLIC_APP_URL)
    st.session_state.public_app_qr_path = str(qr_path)
    return qr_path


def render_student_dashboard(conn, user):
    st.subheader("Student Dashboard")

    st.markdown("---")
    st.markdown("### 📱 Scan to open the live app")
    st.caption("Share the HTTPS link easily by scanning this QR code.")
    try:
        public_qr = _get_public_app_qr_path()
        if public_qr.exists():
            st.image(str(public_qr), caption=PUBLIC_APP_URL, width=220)
        else:
            st.warning("QR code file not found. Please refresh the page.")
    except Exception as exc:
        st.warning(f"Could not generate QR code: {exc}")

    attendance = conn.execute(
        "SELECT session_id, status, timestamp FROM attendance WHERE enrollment = ? ORDER BY timestamp DESC LIMIT 5",
        (user["enrollment"],),
    ).fetchall()
    notices = conn.execute(
        "SELECT title, body, created_at FROM notices ORDER BY created_at DESC LIMIT 5"
    ).fetchall()
    events = conn.execute(
        "SELECT title, event_date, location FROM events ORDER BY event_date DESC LIMIT 5"
    ).fetchall()

    timeline = []
    for item in attendance:
        timeline.append({"type": "Attendance", "summary": f"{item['session_id']} - {item['status']}", "created_at": item["timestamp"]})
    for item in notices:
        timeline.append({"type": "Notice", "summary": item["title"], "created_at": item["created_at"]})
    for item in events:
        timeline.append({"type": "Event", "summary": f"{item['title']} at {item['location']}", "created_at": item["event_date"]})

    sorted_timeline = build_timeline(timeline)
    if not sorted_timeline:
        st.info("No recent activity.")
        return

    for entry in sorted_timeline:
        st.markdown(f"**{entry['type']}**: {entry['summary']}")
        st.caption(entry["created_at"])
        st.divider()
