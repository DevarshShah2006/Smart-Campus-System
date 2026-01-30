from pathlib import Path
import streamlit as st
import pandas as pd

from core.utils import now_iso, UPLOADS_DIR


def render_resources(conn, user):
    st.subheader("Lecture Resource Hub")
    upload_dir = UPLOADS_DIR / "resources"
    upload_dir.mkdir(parents=True, exist_ok=True)

    if user["role_id"] != 1:
        with st.form("resource_form"):
            title = st.text_input("Resource Title")
            subject = st.text_input("Subject")
            file = st.file_uploader("Upload PDF/PPT", type=["pdf", "ppt", "pptx"])
            submitted = st.form_submit_button("Upload Resource")

        if submitted:
            if not title or not subject or file is None:
                st.error("All fields are required.")
            else:
                file_path = upload_dir / file.name
                with open(file_path, "wb") as f:
                    f.write(file.getbuffer())

                conn.execute(
                    """
                    INSERT INTO resources (title, subject, file_path, uploaded_by, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (title, subject, str(file_path), user["id"], now_iso()),
                )
                conn.commit()
                st.success("Resource uploaded.")

    records = conn.execute(
        "SELECT r.*, u.name as uploader FROM resources r LEFT JOIN users u ON r.uploaded_by = u.id ORDER BY created_at DESC"
    ).fetchall()
    if not records:
        st.info("No resources yet.")
        return

    df = pd.DataFrame(records)
    st.dataframe(df[["title", "subject", "file_path", "created_at"]], use_container_width=True)
    for row in records:
        if Path(row["file_path"]).exists():
            with open(row["file_path"], "rb") as f:
                st.download_button(
                    label=f"Download {row['title']}",
                    data=f,
                    file_name=Path(row["file_path"]).name,
                    mime="application/octet-stream",
                )
