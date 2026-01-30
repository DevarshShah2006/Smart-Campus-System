import streamlit as st
import pandas as pd

from core.utils import now_iso


def render_events(conn, user):
    st.subheader("Campus Events & Workshops")

    if user["role_id"] != 1:
        with st.form("event_form"):
            title = st.text_input("Event Title")
            description = st.text_area("Description")
            event_date = st.date_input("Event Date")
            location = st.text_input("Location")
            submitted = st.form_submit_button("Create Event")

        if submitted:
            if not (title and description and location):
                st.error("All fields are required.")
            else:
                conn.execute(
                    """
                    INSERT INTO events (title, description, event_date, location, created_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (title, description, event_date.isoformat(), location, user["id"], now_iso()),
                )
                conn.commit()
                st.success("Event created.")

    events = conn.execute("SELECT * FROM events ORDER BY event_date DESC").fetchall()
    if not events:
        st.info("No events yet.")
        return

    df = pd.DataFrame(events)
    st.dataframe(df[["id", "title", "event_date", "location"]], use_container_width=True)

    if user["role_id"] == 1:
        event_id = st.selectbox("Register for Event", [row["id"] for row in events])
        if st.button("Register"):
            try:
                conn.execute(
                    "INSERT INTO event_registrations (event_id, enrollment, created_at) VALUES (?, ?, ?)",
                    (event_id, user["enrollment"], now_iso()),
                )
                conn.commit()
                st.success("Registered successfully.")
            except Exception:
                st.warning("Already registered or invalid event.")
