from pathlib import Path
import streamlit as st
import pandas as pd

from core.utils import now_iso, UPLOADS_DIR, rows_to_dataframe, add_datetime_columns


def render_resources(conn, user):
    st.subheader("Lecture Resource Hub")
    upload_dir = UPLOADS_DIR / "resources"
    upload_dir.mkdir(parents=True, exist_ok=True)

    if user.get("role_name") != "student":
        # build sensible year/batch choices from existing students
        student_rows = conn.execute(
            "SELECT u.year, u.batch FROM users u LEFT JOIN roles r ON u.role_id = r.id WHERE r.name = 'student'"
        ).fetchall()
        available_years = sorted({row["year"] for row in student_rows if row["year"] is not None})
        for y in [1, 2, 3, 4, 5]:
            if y not in available_years:
                available_years.append(y)
        available_years = sorted(available_years)

        with st.form("resource_form"):
            title = st.text_input("Resource Title")
            subject = st.text_input("Subject")
            year = st.selectbox("Year", available_years, index=0)
            # batches available for selected year
            available_batches = sorted({row["batch"] for row in student_rows if row["year"] == year and row["batch"] is not None})
            if not available_batches:
                available_batches = [1, 2, 3, 4]
            batch = st.selectbox("Batch", available_batches, index=0)
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
                    INSERT INTO resources (title, subject, file_path, uploaded_by, created_at, year, batch)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (title, subject, str(file_path), user["id"], now_iso(), int(year), int(batch)),
                )
                conn.commit()
                st.success("Resource uploaded.")

    student_year = user.get("year")
    student_batch = user.get("batch")
    if user.get("role_name") == "student" and student_year and student_batch:
        records = conn.execute(
            "SELECT r.*, u.name as uploader FROM resources r LEFT JOIN users u ON r.uploaded_by = u.id WHERE r.year = ? AND r.batch = ? ORDER BY created_at DESC",
            (student_year, student_batch),
        ).fetchall()
    else:
        records = conn.execute(
            "SELECT r.*, u.name as uploader FROM resources r LEFT JOIN users u ON r.uploaded_by = u.id ORDER BY created_at DESC"
        ).fetchall()
    if not records:
        st.info("No resources yet.")
        return

    df = rows_to_dataframe(records)
    df = add_datetime_columns(df)

    display_cols = [c for c in ["title", "subject", "year", "batch", "date", "time"] if c in df.columns]
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
