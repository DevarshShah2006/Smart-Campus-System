import streamlit as st
import pandas as pd


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

    schedules = conn.execute("SELECT * FROM schedules ORDER BY day, time").fetchall()
    if not schedules:
        st.info("No schedule entries yet.")
        return

    if schedules and hasattr(schedules[0], "keys"):
        df = pd.DataFrame(schedules, columns=schedules[0].keys())
    else:
        df = pd.DataFrame(schedules)

    display_cols = [c for c in ["day", "time", "subject", "room"] if c in df.columns]
    st.dataframe(df[display_cols] if display_cols else df, use_container_width=True)
