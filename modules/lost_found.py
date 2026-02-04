import streamlit as st
import pandas as pd

from core.utils import now_iso


def render_lost_found(conn, user):
    st.subheader("Lost & Found Portal")

    # Allow students to post Lost or Found
    if user["role_id"] == 1:
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

    if items and hasattr(items[0], "keys"):
        df = pd.DataFrame(items, columns=items[0].keys())
    else:
        df = pd.DataFrame(items)

    # Show description/contact and separate date/time
    if "created_at" in df.columns:
        dt = pd.to_datetime(df["created_at"], errors="coerce")
        df["date"] = dt.dt.date
        df["time"] = dt.dt.strftime("%H:%M")

    display_cols = [
        c for c in ["id", "item_type", "title", "description", "contact", "status", "date", "time"]
        if c in df.columns
    ]
    st.dataframe(df[display_cols] if display_cols else df, use_container_width=True)
