import streamlit as st
import pandas as pd

from core.utils import rows_to_dataframe


def render_schedule(conn, user):
    st.subheader("Lecture Schedule")

    if user.get("role_name") != "student":
        # Prepare year/batch choices from existing student data
        student_rows = conn.execute(
            "SELECT u.year, u.batch FROM users u LEFT JOIN roles r ON u.role_id = r.id WHERE r.name = 'student'"
        ).fetchall()
        available_years = sorted({row["year"] for row in student_rows if row["year"] is not None})
        for y in [1, 2, 3, 4, 5]:
            if y not in available_years:
                available_years.append(y)
        available_years = sorted(available_years)

        with st.form("schedule_form"):
            day = st.selectbox("Day", ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"])
            time = st.text_input("Time (e.g., 10:00-11:00)")
            subject = st.text_input("Subject")
            room = st.text_input("Room")
            year = st.selectbox("Year", available_years, index=0)
            available_batches = sorted({row["batch"] for row in student_rows if row["year"] == year and row["batch"] is not None})
            if not available_batches:
                available_batches = [1, 2, 3, 4]
            batch = st.selectbox("Batch", available_batches, index=0)
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
