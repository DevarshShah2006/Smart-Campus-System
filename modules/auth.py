import streamlit as st

from core.security import hash_password, verify_password
from core.utils import now_iso


def get_role_id(conn, role_name: str) -> int:
    cursor = conn.execute("SELECT id FROM roles WHERE name = ?", (role_name,))
    row = cursor.fetchone()
    return row["id"] if row else 0


def get_user_by_enrollment(conn, enrollment: str):
    cursor = conn.execute("SELECT * FROM users WHERE enrollment = ?", (enrollment,))
    return cursor.fetchone()


def get_user_by_username(conn, username: str):
    cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
    return cursor.fetchone()


def register_student(conn):
    st.subheader("Student Profile Setup")
    with st.form("student_register"):
        name = st.text_input("Full Name")
        enrollment = st.text_input("Enrollment Number")
        department = st.text_input("Department")
        year = st.selectbox("Year", [1, 2, 3, 4])
        password = st.text_input("Set Password", type="password")
        submitted = st.form_submit_button("Create Student Profile")

    if submitted:
        if not (name and enrollment and department and password):
            st.error("Please fill all required fields.")
            return

        if get_user_by_enrollment(conn, enrollment):
            st.warning("Enrollment already registered.")
            return

        role_id = get_role_id(conn, "student")
        conn.execute(
            """
            INSERT INTO users (role_id, name, enrollment, department, year, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (role_id, name, enrollment, department, year, hash_password(password), now_iso()),
        )
        conn.commit()
        st.success("Student profile created. Please log in.")


def login_user(conn):
    st.subheader("Login")
    role = st.selectbox("Role", ["student", "teacher", "admin"], key="login_role")

    if role == "student":
        enrollment = st.text_input("Enrollment Number", key="login_enrollment")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", key="login_student"):
            user = get_user_by_enrollment(conn, enrollment)
            if user and verify_password(password, user["password_hash"]):
                st.session_state.user = dict(user)
                st.session_state.role = role
                st.success("Logged in successfully.")
                st.rerun()
            else:
                st.error("Invalid enrollment or password.")
    else:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password_admin")
        if st.button("Login", key="login_admin"):
            user = get_user_by_username(conn, username)
            if user and verify_password(password, user["password_hash"]):
                st.session_state.user = dict(user)
                st.session_state.role = role
                st.success("Logged in successfully.")
                st.rerun()
            else:
                st.error("Invalid username or password.")


def render_auth(conn):
    st.markdown("### 🔐 Smart Campus System Login")
    st.markdown("---")
    login_user(conn)
