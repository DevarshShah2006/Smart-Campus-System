import streamlit as st

from core.security import verify_password


def get_user_by_enrollment(conn, enrollment: str):
    cursor = conn.execute("SELECT * FROM users WHERE enrollment = ?", (enrollment,))
    return cursor.fetchone()


def get_user_by_username(conn, username: str):
    cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
    return cursor.fetchone()


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
                actual_role = conn.execute(
                    "SELECT name FROM roles WHERE id = ?", (user["role_id"],)
                ).fetchone()
                if not actual_role or actual_role["name"] != role:
                    st.error(f"This account is not a {role}.")
                    return
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
