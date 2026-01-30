import streamlit as st
import pandas as pd

from core.utils import now_iso


def render_lost_found(conn, user):
    st.subheader("Lost & Found Portal")

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

    df = pd.DataFrame(items)
    st.dataframe(df[["id", "item_type", "title", "status", "created_at"]], use_container_width=True)
