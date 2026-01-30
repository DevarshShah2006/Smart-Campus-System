import streamlit as st

from core.db import init_db, seed_defaults, get_db
from core.security import hash_password
from core.utils import ensure_dirs

from modules.auth import render_auth
from modules.attendance import (
    render_teacher_attendance,
    render_student_attendance,
    render_attendance_override,
    render_attendance_analytics,
)
from modules.notices import render_notice_board
from modules.resources import render_resources
from modules.schedule import render_schedule
from modules.feedback import render_feedback
from modules.issues import render_issues
from modules.lost_found import render_lost_found
from modules.events import render_events
from modules.analytics import render_analytics, render_exports
from modules.search import render_search
from modules.settings import render_settings
from modules.dashboard import render_student_dashboard


st.set_page_config(page_title="Smart Campus System", layout="wide")
ensure_dirs()
conn = init_db()
seed_defaults(conn, hash_password("admin123"))

if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None

roles = {row["id"]: row["name"] for row in conn.execute("SELECT * FROM roles")}

st.title("Smart Campus System")
st.caption("QR-Based Attendance + Academics + Campus Services + Analytics")

if not st.session_state.user:
    render_auth(conn)
else:
    user = st.session_state.user
    role_name = roles.get(user["role_id"], "student")

    with st.sidebar:
        st.write(f"Logged in as: {user.get('name', 'User')}")
        st.write(f"Role: {role_name.title()}")
        if st.button("Logout"):
            st.session_state.user = None
            st.session_state.role = None
            st.rerun()

        theme_choice = st.toggle("Light Mode")
        if theme_choice:
            st.info("Theme preference noted. Dark mode is default.")

        all_pages = [
            "Dashboard",
            "Attendance",
            "Notices",
            "Resources",
            "Schedule",
            "Feedback",
            "Issues",
            "Lost & Found",
            "Events",
            "Analytics",
            "CSV Export",
            "Manual Override",
            "System Settings",
            "Search",
        ]

        page = st.selectbox("Navigate", all_pages)

    if role_name == "student":
        if page == "Dashboard":
            render_student_dashboard(conn, user)
        elif page == "Attendance":
            render_student_attendance(conn, user)
        elif page == "Notices":
            render_notice_board(conn, user)
        elif page == "Resources":
            render_resources(conn, user)
        elif page == "Schedule":
            render_schedule(conn, user)
        elif page == "Feedback":
            render_feedback(conn, user)
        elif page == "Issues":
            render_issues(conn, user)
        elif page == "Lost & Found":
            render_lost_found(conn, user)
        elif page == "Events":
            render_events(conn, user)
        elif page == "Search":
            render_search(conn)
        elif page == "Analytics":
            render_analytics(conn)
        elif page == "CSV Export":
            st.warning("CSV Export is available for Admin/Teacher only.")
        elif page == "Manual Override":
            st.warning("Manual Override is available for Admin/Teacher only.")
        elif page == "System Settings":
            st.warning("System Settings is available for Admin/Teacher only.")
    else:
        if page == "Dashboard":
            st.info("Staff dashboard - showing attendance analytics")
            render_attendance_analytics(conn)
        elif page == "Attendance":
            render_teacher_attendance(conn, user)
            st.divider()
            render_attendance_analytics(conn)
        elif page == "Notices":
            render_notice_board(conn, user)
        elif page == "Resources":
            render_resources(conn, user)
        elif page == "Schedule":
            render_schedule(conn, user)
        elif page == "Feedback":
            render_feedback(conn, user)
        elif page == "Issues":
            render_issues(conn, user)
        elif page == "Lost & Found":
            render_lost_found(conn, user)
        elif page == "Events":
            render_events(conn, user)
        elif page == "Analytics":
            render_analytics(conn)
        elif page == "CSV Export":
            render_exports(conn)
        elif page == "Manual Override":
            render_attendance_override(conn, user)
        elif page == "System Settings":
            render_settings(conn)
        elif page == "Search":
            render_search(conn)
