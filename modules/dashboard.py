import streamlit as st

from core.utils import build_timeline


def render_student_dashboard(conn, user):
    st.subheader("Student Dashboard")

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
