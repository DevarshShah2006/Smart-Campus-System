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
            contact_email = st.text_input("Contact Email (for registrations)")
            submitted = st.form_submit_button("Create Event")

        if submitted:
            if not (title and description and location):
                st.error("All fields are required.")
            else:
                # ensure contact_email column exists
                cols = [r["name"] for r in conn.execute("PRAGMA table_info(events)").fetchall()]
                if "contact_email" not in cols:
                    conn.execute("ALTER TABLE events ADD COLUMN contact_email TEXT")

                conn.execute(
                    """
                    INSERT INTO events (title, description, event_date, location, created_by, created_at, contact_email)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (title, description, event_date.isoformat(), location, user["id"], now_iso(), contact_email),
                )
                conn.commit()
                st.success("Event created.")

    events = conn.execute("SELECT e.*, u.name as poster FROM events e LEFT JOIN users u ON e.created_by = u.id ORDER BY event_date DESC").fetchall()
    if not events:
        st.info("No events yet.")
        return
    # Render events as notice-like containers (no table)

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
            keys = list(ev.keys())
            desc = ev["description"] if "description" in keys else ""
            date = ev["event_date"] if "event_date" in keys else ""
            location = ev["location"] if "location" in keys else ""
            contact = ev["contact_email"] if "contact_email" in keys else None
            poster = ev["poster"] if "poster" in keys else None
            created_at = ev["created_at"] if "created_at" in keys else None
        else:
            # column order fallback
            eid, title, desc, date, location = ev[0], ev[1], ev[2], ev[3], ev[4]
            contact = ev[5] if len(ev) > 5 else None
            poster = None
            created_at = None

        safe_subject = title.replace(' ', '%20')
        contact_info = f"Contact: {contact}" if contact else f"Email: {facility_email}"
        st.markdown(f"""
        <div style='padding:1rem; margin:0.5rem 0; border-left:4px solid #2b6cb0; background: rgba(255,255,255,0.02); border-radius:6px;'>
            <h3 style='margin:0 0 0.25rem 0;'>{title}</h3>
            <p style='margin:0.25rem 0;'>{desc}</p>
            <p style='color:#95a5a6; margin:0.25rem 0;'><strong>Date:</strong> {date} &nbsp;|&nbsp; <strong>Location:</strong> {location}</p>
            <p style='margin-top:0.5rem;'>{contact_info}. To register, email with your name and enrollment number.</p>
            <p style='color:#888; font-size:0.9rem; margin:0.5rem 0 0 0;'>👤 Posted by {poster or 'Unknown'}{(' | 📅 ' + str(created_at)[:10]) if created_at else ''}</p>
        </div>
        """, unsafe_allow_html=True)
