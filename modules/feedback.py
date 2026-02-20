import streamlit as st
import pandas as pd

from core.utils import now_iso, rows_to_dataframe


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

    session_id = None
    if user.get("role_name") == "student":
        session_id = st.selectbox(
            "Lecture Session",
            list(lecture_map.keys()),
            format_func=_lecture_label,
        )

    if user.get("role_name") == "student":
        with st.form("feedback_form"):
            rating = st.slider("Rating", min_value=1, max_value=5, value=4)
            comments = st.text_area("Comments (optional)")
            submitted = st.form_submit_button("Submit Feedback")

        if submitted:
            existing = conn.execute(
                "SELECT id FROM feedback WHERE session_id = ? AND enrollment = ?",
                (session_id, user["enrollment"]),
            ).fetchone()
            if existing:
                st.warning("You have already submitted feedback for this lecture.")
            else:
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
        df = rows_to_dataframe(records)

        df["subject"] = df.get("subject", pd.Series(dtype="object")).fillna("Unknown")
        df["room"] = df.get("room", pd.Series(dtype="object")).fillna("TBD")
        df["start_time"] = pd.to_datetime(df.get("start_time"), errors="coerce")
        df["end_time"] = pd.to_datetime(df.get("end_time"), errors="coerce")
        fallback = pd.to_datetime(df.get("created_at"), errors="coerce")
        df["date"] = df["start_time"].dt.date.fillna(fallback.dt.date)
        start_fmt = df["start_time"].dt.strftime("%H:%M")
        end_fmt = df["end_time"].dt.strftime("%H:%M")
        df["time"] = start_fmt.fillna("--:--") + " - " + end_fmt.fillna("--:--")

        display_cols = [
            c for c in ["session_id", "subject", "room", "date", "time", "rating", "comments"]
            if c in df.columns
        ]
        st.dataframe(df[display_cols] if display_cols else df, use_container_width=True)
