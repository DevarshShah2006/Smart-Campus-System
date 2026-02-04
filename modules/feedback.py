import streamlit as st
import pandas as pd

from core.utils import now_iso


def render_feedback(conn, user):
    st.subheader("Lecture Feedback")

    lectures = conn.execute(
        "SELECT session_id, subject, room, start_time, end_time FROM lectures ORDER BY start_time DESC"
    ).fetchall()
    if not lectures:
        st.info("No lectures found.")
        return

    if lectures and hasattr(lectures[0], "keys"):
        lecture_map = {row["session_id"]: row for row in lectures}
    else:
        # columns order: session_id, subject, room, start_time, end_time
        lecture_map = {row[0]: row for row in lectures}

    def _lecture_label(session_id: str) -> str:
        row = lecture_map[session_id]
        if isinstance(row, dict) or hasattr(row, "keys"):
            subject = row["subject"]
            room = row["room"]
            start_time = row["start_time"]
            end_time = row["end_time"]
        else:
            subject, room, start_time, end_time = row[1], row[2], row[3], row[4]

        # Split into readable date + time with spacing
        date_part = str(start_time)[:10] if start_time else ""
        time_part = ""
        if start_time and end_time:
            time_part = f"{str(start_time)[11:16]} - {str(end_time)[11:16]}"
        return f"{subject}   |   {room}   |   {date_part}   |   {time_part}"

    session_id = st.selectbox(
        "Lecture Session",
        list(lecture_map.keys()),
        format_func=_lecture_label,
    )

    if user["role_id"] == 1:
        with st.form("feedback_form"):
            rating = st.slider("Rating", min_value=1, max_value=5, value=4)
            comments = st.text_area("Comments (optional)")
            submitted = st.form_submit_button("Submit Feedback")

        if submitted:
            conn.execute(
                """
                INSERT INTO feedback (session_id, enrollment, rating, comments, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, user["enrollment"], rating, comments, now_iso()),
            )
            conn.commit()
            st.success("Feedback submitted.")

    records = conn.execute(
        """
        SELECT f.session_id, f.rating, f.comments, f.created_at,
               l.subject, l.room, l.start_time, l.end_time
        FROM feedback f
        LEFT JOIN lectures l ON f.session_id = l.session_id
        ORDER BY f.created_at DESC
        """
    ).fetchall()
    if records:
        if records and hasattr(records[0], "keys"):
            df = pd.DataFrame(records, columns=records[0].keys())
        else:
            df = pd.DataFrame(
                records,
                columns=["session_id", "rating", "comments", "created_at", "subject", "room", "start_time", "end_time"],
            )

        # Add readable date/time columns
        if "start_time" in df.columns:
            df["date"] = pd.to_datetime(df["start_time"], errors="coerce").dt.date
            df["time"] = df["start_time"].astype(str).str.slice(11, 16) + " - " + df["end_time"].astype(str).str.slice(11, 16)

        display_cols = [
            c for c in ["session_id", "subject", "room", "date", "time", "rating", "comments"]
            if c in df.columns
        ]
        st.dataframe(df[display_cols] if display_cols else df, use_container_width=True)
