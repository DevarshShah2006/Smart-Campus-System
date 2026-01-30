import streamlit as st
import pandas as pd

from core.utils import now_iso


def render_issues(conn, user):
    st.subheader("Campus Issue Reporting")

    if user["role_id"] == 1:
        with st.form("issue_form"):
            title = st.text_input("Issue Title")
            category = st.selectbox("Category", ["Wi-Fi", "Electricity", "Cleanliness", "Security", "Other"])
            description = st.text_area("Description")
            submitted = st.form_submit_button("Report Issue")

        if submitted:
            if not (title and description):
                st.error("Title and description are required.")
            else:
                conn.execute(
                    """
                    INSERT INTO issues (title, category, description, status, reported_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (title, category, description, "Open", user["id"], now_iso()),
                )
                conn.commit()
                st.success("Issue reported.")

    issues = conn.execute("SELECT * FROM issues ORDER BY created_at DESC").fetchall()
    if not issues:
        st.info("No issues reported.")
        return

    df = pd.DataFrame(issues)
    st.dataframe(df[["id", "title", "category", "status", "created_at"]], use_container_width=True)

    if user["role_id"] != 1:
        issue_id = st.number_input("Issue ID", min_value=1, step=1)
        status = st.selectbox("Update Status", ["Open", "In Progress", "Resolved"])
        if st.button("Update Issue Status"):
            conn.execute(
                """
                UPDATE issues
                SET status = ?, resolved_by = ?, resolved_at = ?
                WHERE id = ?
                """,
                (status, user["id"], now_iso(), int(issue_id)),
            )
            conn.commit()
            st.success("Issue status updated.")
