import streamlit as st
import pandas as pd

from core.utils import now_iso, rows_to_dataframe, add_datetime_columns
from core.db import DB_PATH


def render_issues(conn, user):
    st.subheader("Campus Issue Reporting")

    if user.get("role_name") == "student":
        with st.form("issue_form"):
            title = st.text_input("Issue Title")
            category = st.selectbox("Category", ["Wi-Fi", "Electricity", "Cleanliness", "Security", "Other"])
            description = st.text_area("Description")
            submitted = st.form_submit_button("Report Issue")

        if submitted:
            if not (title and description):
                st.error("Title and description are required.")
            else:
                cur = conn.execute(
                    """
                    INSERT INTO issues (title, category, description, status, reported_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (title, category, description, "Open", user["id"], now_iso()),
                )
                conn.commit()
                last_id = cur.lastrowid if hasattr(cur, "lastrowid") else None
                st.success(f"Issue reported.")

    issues = conn.execute("SELECT * FROM issues ORDER BY created_at DESC").fetchall()
    if not issues:
        st.info("No issues reported.")
        return

    df = rows_to_dataframe(issues)
    df = add_datetime_columns(df)

    display_cols = [c for c in ["id", "title", "category", "status", "date", "time"] if c in df.columns]
    st.dataframe(df[display_cols] if display_cols else df, use_container_width=True)

    if user.get("role_name") != "student":
        issue_id = st.number_input("Issue ID", min_value=1, step=1)
        status = st.selectbox("Update Status", ["Open", "In Progress", "Resolved"])
        if st.button("Update Issue Status"):
            if status == "Resolved":
                conn.execute(
                    """
                    UPDATE issues
                    SET status = ?, resolved_by = ?, resolved_at = ?
                    WHERE id = ?
                    """,
                    (status, user["id"], now_iso(), int(issue_id)),
                )
            else:
                conn.execute(
                    """
                    UPDATE issues
                    SET status = ?, resolved_by = NULL, resolved_at = NULL
                    WHERE id = ?
                    """,
                    (status, int(issue_id)),
                )
            conn.commit()
            st.success("Issue status updated.")
            st.rerun()
