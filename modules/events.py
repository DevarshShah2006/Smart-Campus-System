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

    if events and hasattr(events[0], "keys"):
        df = pd.DataFrame(events, columns=events[0].keys())
    else:
        df = pd.DataFrame(events)

    display_cols = [c for c in ["id", "title", "event_date", "location"] if c in df.columns]
    st.dataframe(df[display_cols] if display_cols else df, use_container_width=True)

    if user["role_id"] == 1:
        if events and hasattr(events[0], "keys"):
            event_ids = [row["id"] for row in events]
        else:
            # columns order: id, title, description, event_date, location, created_by, created_at
            event_ids = [row[0] for row in events]

        event_id = st.selectbox("Register for Event", event_ids)
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
