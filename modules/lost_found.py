import streamlit as st
import pandas as pd

from core.utils import now_iso, rows_to_dataframe, add_datetime_columns


def render_lost_found(conn, user):
    st.subheader("Lost & Found Portal")

    with st.form("lost_found_form"):
        item_type = st.selectbox("Type", ["Lost", "Found"])
        title = st.text_input("Item Title")
        description = st.text_area("Description")
        contact = st.text_input("Contact Info")
        submitted = st.form_submit_button("Post")

    if submitted:
        if not (title and description and contact):
            st.error("All fields are required.")
        else:
            conn.execute(
                """
                INSERT INTO lost_found (item_type, title, description, contact, posted_by, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (item_type, title, description, contact, user["id"], now_iso(), "Open"),
            )
            conn.commit()
            st.success("Post created.")

    items = conn.execute("SELECT * FROM lost_found ORDER BY created_at DESC").fetchall()
    if not items:
        st.info("No posts yet.")
        return

    df = rows_to_dataframe(items)
    df = add_datetime_columns(df)

    display_cols = [
        c for c in ["id", "item_type", "title", "description", "contact", "status", "date", "time"]
        if c in df.columns
    ]
    st.dataframe(df[display_cols] if display_cols else df, use_container_width=True)
