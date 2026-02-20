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
            submitted = st.form_submit_button("Add Schedule")

        if submitted:
            if not (day and time and subject):
                st.error("Day, time, and subject are required.")
            else:
                conn.execute(
                    "INSERT INTO schedules (day, time, subject, room, teacher_id) VALUES (?, ?, ?, ?, ?)",
                    (day, time, subject, room, user["id"]),
                )
                conn.commit()
                st.success("Schedule added.")

    student_year = user.get("year")
    student_batch = user.get("batch")
    if student_year and student_batch and user.get("role_name") == "student":
        lectures = conn.execute(
            """
            SELECT subject, room, start_time
            FROM lectures
            WHERE (year IS NULL OR year = ?) AND (batch IS NULL OR batch = ?)
            ORDER BY start_time
            """,
            (student_year, student_batch),
        ).fetchall()
        if not lectures:
            st.info("No lectures scheduled for your year/batch yet.")
            return

        df = rows_to_dataframe(lectures)
        df["start_time"] = pd.to_datetime(df["start_time"], errors="coerce")
        df["date"] = df["start_time"].dt.date
        df["time"] = df["start_time"].dt.strftime("%H:%M")

        display = [c for c in ["subject", "room", "date", "time"] if c in df.columns]
        st.dataframe(df[display], use_container_width=True)
        return

    schedules = conn.execute("SELECT * FROM schedules ORDER BY day, time").fetchall()
    if not schedules:
        st.info("No schedule entries yet.")
        return

    df = rows_to_dataframe(schedules)
    display_cols = [c for c in ["day", "time", "subject", "room"] if c in df.columns]
    st.dataframe(df[display_cols] if display_cols else df, use_container_width=True)
