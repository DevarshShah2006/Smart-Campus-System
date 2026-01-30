import streamlit as st
import pandas as pd


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

    st.markdown("**Notices**")
    st.dataframe(pd.DataFrame(notices), use_container_width=True)
    st.markdown("**Issues**")
    st.dataframe(pd.DataFrame(issues), use_container_width=True)
    st.markdown("**Events**")
    st.dataframe(pd.DataFrame(events), use_container_width=True)
    st.markdown("**Resources**")
    st.dataframe(pd.DataFrame(resources), use_container_width=True)
