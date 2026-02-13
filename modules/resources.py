from pathlib import Path
import streamlit as st
import pandas as pd

from core.utils import now_iso, UPLOADS_DIR


def render_resources(conn, user):
    st.subheader("Lecture Resource Hub")
    upload_dir = UPLOADS_DIR / "resources"
    upload_dir.mkdir(parents=True, exist_ok=True)

    if user.get("role_name") != "student":
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

    # Build dataframe with safe columns whether rows are dict-like or tuples
    if records and hasattr(records[0], "keys"):
        df = pd.DataFrame(records, columns=records[0].keys())
    else:
        df = pd.DataFrame(records)

    # Add separate date/time columns
    if "created_at" in df.columns:
        dt = pd.to_datetime(df["created_at"], errors="coerce")
        df["date"] = dt.dt.date
        df["time"] = dt.dt.strftime("%H:%M")

    display_cols = [c for c in ["title", "subject", "date", "time"] if c in df.columns]
    if user.get("role_name") != "student" and "file_path" in df.columns:
        display_cols.append("file_path")
    st.dataframe(df[display_cols] if display_cols else df, use_container_width=True)

    # Helper to read values from dict-like rows or tuples
    def _row_get(row, key: str, idx: int):
        if isinstance(row, dict) or hasattr(row, "keys"):
            return row[key]
        return row[idx]

    for row in records:
        file_path = _row_get(row, "file_path", 3)
        title = _row_get(row, "title", 1)
        if Path(file_path).exists():
            with open(file_path, "rb") as f:
                st.download_button(
                    label=f"Download {title}",
                    data=f,
                    file_name=Path(file_path).name,
                    mime="application/octet-stream",
                )
