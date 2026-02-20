import streamlit as st
import pandas as pd

from core.utils import now_iso, rows_to_dataframe


def render_events(conn, user):
    st.subheader("Campus Events & Workshops")

    if user.get("role_name") != "student":
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

    df = rows_to_dataframe(events)

    display_cols = [c for c in ["id", "title", "event_date", "location"] if c in df.columns]
    # show a simple table for quick overview
    st.dataframe(df[display_cols] if display_cols else df, use_container_width=True)

    # Fetch facility email from settings or use a sensible default
    row = conn.execute("SELECT value FROM system_settings WHERE key = ?", ("facility_email",)).fetchone()
    facility_email = row[0] if row and len(row) > 0 else "facility@college.edu"

    # Render events as notice-like cards with registration instructions via email
    st.markdown("---")
    st.subheader("Event Details & Registration")
    for ev in events:
        if hasattr(ev, "keys"):
            eid = ev["id"]
            title = ev["title"]
            desc = ev.get("description", "")
            date = ev.get("event_date", "")
            location = ev.get("location", "")
        else:
            # column order: id, title, description, event_date, location, created_by, created_at
            eid, title, desc, date, location = ev[0], ev[1], ev[2], ev[3], ev[4]

        safe_subject = title.replace(' ', '%20')
        st.markdown(f"""
        <div style='padding:1rem; margin:0.5rem 0; border-left:4px solid #2b6cb0; background: rgba(255,255,255,0.02); border-radius:6px;'>
            <h3 style='margin:0 0 0.25rem 0;'>{title}</h3>
            <p style='margin:0.25rem 0;'>{desc}</p>
            <p style='color:#95a5a6; margin:0.25rem 0;'><strong>Date:</strong> {date} &nbsp;|&nbsp; <strong>Location:</strong> {location}</p>
            <p style='margin-top:0.5rem;'>To register for this event, please email <a href='mailto:{facility_email}?subject=Register%20for%20{safe_subject}' style='color:#9ad1ff'>{facility_email}</a> with your name and enrollment number.</p>
        </div>
        """, unsafe_allow_html=True)
