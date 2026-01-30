import streamlit as st
import pandas as pd

from core.utils import now_iso


def render_feedback(conn, user):
    st.subheader("Lecture Feedback")

    lectures = conn.execute("SELECT session_id, subject FROM lectures ORDER BY start_time DESC").fetchall()
    if not lectures:
        st.info("No lectures found.")
        return

    lecture_map = {row["session_id"]: row["subject"] for row in lectures}
    session_id = st.selectbox("Lecture Session", list(lecture_map.keys()))

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

    records = conn.execute("SELECT * FROM feedback ORDER BY created_at DESC").fetchall()
    if records:
        df = pd.DataFrame(records)
        st.dataframe(df[["session_id", "rating", "comments", "created_at"]], use_container_width=True)
