import streamlit as st
import matplotlib.pyplot as plt

from core.utils import build_timeline


def render_student_dashboard(conn, user):
    st.subheader("Student Dashboard")

    student_year = user.get("year")
    student_batch = user.get("batch")
    if student_year and student_batch:
        total_lectures = conn.execute(
            """
            SELECT COUNT(*) FROM lectures
            WHERE (year IS NULL OR year = ?) AND (batch IS NULL OR batch = ?)
            """,
            (student_year, student_batch),
        ).fetchone()[0]
    else:
        total_lectures = conn.execute("SELECT COUNT(*) FROM lectures").fetchone()[0]

    attended_lectures = conn.execute(
        """
        SELECT COUNT(*) FROM attendance a
        WHERE a.enrollment = ? AND a.status IN ('Present', 'Late')
        """,
        (user["enrollment"],),
    ).fetchone()[0]

    attendance_pct = (attended_lectures / total_lectures * 100) if total_lectures else 0
    st.metric("✅ Attendance %", f"{attendance_pct:.1f}%", help="Based on lectures available for your year/batch")

    if total_lectures:
        missed_lectures = max(total_lectures - attended_lectures, 0)
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie(
            [attended_lectures, missed_lectures],
            labels=["Attended", "Missed"],
            autopct="%1.1f%%",
            startangle=90,
            colors=["#2ecc71", "#e74c3c"],
        )
        ax.axis("equal")
        st.pyplot(fig, use_container_width=False)

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
