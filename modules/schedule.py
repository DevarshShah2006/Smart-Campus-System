import streamlit as st
import pandas as pd

from core.utils import rows_to_dataframe


def render_schedule(conn, user):
    st.subheader("Lecture Schedule")

    if user.get("role_name") != "student":
        with st.form("schedule_form"):
            day = st.selectbox("Day", ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"])
            time = st.text_input("Time (e.g., 10:00-11:00)")
            subject = st.text_input("Subject")
            room = st.text_input("Room")
            year = st.number_input("Year", min_value=1, max_value=5, step=1)
            batch = st.number_input("Batch", min_value=1, max_value=10, step=1)
            submitted = st.form_submit_button("Add Schedule")

        if submitted:
            if not (day and time and subject):
                st.error("Day, time, and subject are required.")
            else:
                conn.execute(
                    "INSERT INTO schedules (day, time, subject, room, teacher_id, year, batch) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (day, time, subject, room, user["id"], int(year), int(batch)),
                )
                conn.commit()
                st.success("Schedule added.")

    student_year = user.get("year")
    student_batch = user.get("batch")
    if student_year and student_batch and user.get("role_name") == "student":
        schedules = conn.execute(
            """
            SELECT * FROM schedules
            WHERE year = ? AND batch = ?
            ORDER BY day, time
            """,
            (student_year, student_batch),
        ).fetchall()
        if not schedules:
            st.info("No schedule entries for your year/batch yet.")
            return

        df = rows_to_dataframe(schedules)
        display = [c for c in ["day", "time", "subject", "room"] if c in df.columns]
        st.dataframe(df[display], use_container_width=True)
        return

    schedules = conn.execute("SELECT * FROM schedules ORDER BY day, time").fetchall()
    if not schedules:
        st.info("No schedule entries yet.")
        return

    df = rows_to_dataframe(schedules)
    display_cols = [c for c in ["day", "time", "subject", "room", "year", "batch"] if c in df.columns]
    st.dataframe(df[display_cols] if display_cols else df, use_container_width=True)
