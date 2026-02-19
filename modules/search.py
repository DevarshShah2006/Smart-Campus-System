import streamlit as st
import pandas as pd

from core.utils import rows_to_dataframe, add_datetime_columns


def render_search(conn):
    st.subheader("Search & Filter")
    query = st.text_input("Search keyword")
    if not query:
        st.info("Enter a keyword to search across modules.")
        return

    like = f"%{query}%"
    notices = conn.execute(
        "SELECT title, body, created_at FROM notices WHERE title LIKE ? OR body LIKE ?",
        (like, like),
    ).fetchall()
    issues = conn.execute(
        "SELECT title, description, status FROM issues WHERE title LIKE ? OR description LIKE ?",
        (like, like),
    ).fetchall()
    events = conn.execute(
        "SELECT title, description, event_date FROM events WHERE title LIKE ? OR description LIKE ?",
        (like, like),
    ).fetchall()
    resources = conn.execute(
        "SELECT title, subject, file_path FROM resources WHERE title LIKE ? OR subject LIKE ?",
        (like, like),
    ).fetchall()
    lectures = conn.execute(
        "SELECT session_id, subject, room, start_time, end_time, year, batch FROM lectures WHERE subject LIKE ? OR room LIKE ? OR session_id LIKE ?",
        (like, like, like),
    ).fetchall()

    st.markdown("**Notices**")
    df_notices = rows_to_dataframe(notices)
    df_notices = add_datetime_columns(df_notices)
    display = [c for c in ["title", "body", "date", "time"] if c in df_notices.columns]
    st.dataframe(df_notices[display] if display else df_notices, use_container_width=True)

    st.markdown("**Issues**")
    st.dataframe(pd.DataFrame(issues), use_container_width=True)

    st.markdown("**Events**")
    df_events = rows_to_dataframe(events)
    df_events = add_datetime_columns(df_events, col="event_date")
    display_ev = [c for c in ["title", "description", "date", "time"] if c in df_events.columns]
    st.dataframe(df_events[display_ev] if display_ev else df_events, use_container_width=True)

    st.markdown("**Resources**")
    st.dataframe(pd.DataFrame(resources), use_container_width=True)

    st.markdown("**Lectures**")
    df_lec = rows_to_dataframe(lectures)
    if not df_lec.empty and "start_time" in df_lec.columns:
        df_lec["date"] = pd.to_datetime(df_lec["start_time"], errors="coerce").dt.date
        df_lec["time"] = df_lec["start_time"].astype(str).str.slice(11, 16) + " - " + df_lec["end_time"].astype(str).str.slice(11, 16)
    display_lec = [c for c in ["session_id", "subject", "room", "date", "time", "year", "batch"] if c in df_lec.columns]
    st.dataframe(df_lec[display_lec] if display_lec else df_lec, use_container_width=True)
