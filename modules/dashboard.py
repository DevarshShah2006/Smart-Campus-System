import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from core.utils import build_timeline, rows_to_dataframe


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

    # ── 1. Attendance Pie Chart ──
    st.markdown("### 📊 Your Attendance")
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
    else:
        st.info("No lectures available yet.")

    st.markdown("---")

    # ── 2. Latest Notice ──
    st.markdown("### 📢 Latest Notice")
    latest_notice = conn.execute(
        "SELECT n.title, n.body, n.created_at, u.name as poster FROM notices n LEFT JOIN users u ON n.posted_by = u.id ORDER BY n.created_at DESC LIMIT 1"
    ).fetchone()

    if latest_notice:
        try:
            notice = dict(latest_notice)
        except Exception:
            notice = {
                "title": latest_notice[0] if len(latest_notice) > 0 else "",
                "body": latest_notice[1] if len(latest_notice) > 1 else "",
                "created_at": latest_notice[2] if len(latest_notice) > 2 else "",
                "poster": latest_notice[3] if len(latest_notice) > 3 else "Unknown",
            }
        n_title = str(notice.get("title", ""))
        n_body = str(notice.get("body", ""))
        n_date = str(notice.get("created_at", ""))[:10]
        n_time = str(notice.get("created_at", ""))[11:16]
        poster = str(notice.get("poster", "Unknown") or "Unknown")
        priority_color = "#666"
        if "[Urgent]" in n_title:
            priority_color = "red"
        elif "[Important]" in n_title:
            priority_color = "orange"

        st.markdown(
            f"<div style='padding:1rem;margin:0.5rem 0;background:rgba(255,255,255,0.05);"
            f"border-left:4px solid {priority_color};border-radius:8px;'>"
            f"<h4 style='margin:0 0 0.5rem 0;color:{priority_color};'>{n_title}</h4>"
            f"<p style='margin:0.5rem 0;line-height:1.6;'>{n_body}</p>"
            f"<p style='color:#888;font-size:0.85rem;margin:0;'>"
            f"\U0001f464 {poster} &nbsp; \U0001f4c5 {n_date} &nbsp; \u23f0 {n_time}"
            f"</p></div>",
            unsafe_allow_html=True,
        )
    else:
        st.info("📭 No notices yet.")

    st.markdown("---")

    # ── 3. Your Schedule ──
    st.markdown("### 🗓️ Your Schedule")
    schedules = conn.execute("SELECT * FROM schedules ORDER BY day, time").fetchall()

    if schedules:
        df = rows_to_dataframe(schedules)
        display_cols = [c for c in ["day", "time", "subject", "room"] if c in df.columns]
        st.dataframe(df[display_cols] if display_cols else df, use_container_width=True)
    else:
        st.info("No schedule entries yet.")
