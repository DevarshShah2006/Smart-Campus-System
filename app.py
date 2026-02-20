import sqlite3

import streamlit as st

from core.db import (
    init_db,
    seed_defaults,
)
from core.security import hash_password
from core.utils import ensure_dirs

from modules.auth import render_auth
from modules.admin import (
    render_admin_dashboard,
    render_user_management,
)
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
from modules.analytics import (
    render_analytics,
    render_exports,
)
from modules.search import render_search
from modules.settings import render_settings
from modules.dashboard import render_student_dashboard


st.set_page_config(
    page_title="Smart Campus System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)


try:
    ensure_dirs()
    conn = init_db()
    seed_defaults(conn, hash_password("admin123"))
except sqlite3.Error as e:
    st.error(f"Database error: {e}")
    st.stop()

if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

try:
    roles = {row["id"]: row["name"] for row in conn.execute("SELECT * FROM roles")}
except sqlite3.Error as e:
    st.error(f"Database error: {e}")
    st.stop()

# Custom CSS for better UI
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        padding: 0.5rem;
        font-weight: 500;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .sidebar .stButton>button {
        text-align: left;
        padding-left: 1rem;
    }
    h1 {
        color: #2B6CB0;
        font-weight: 700;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            """
            <div style='text-align: center; padding: 2rem 0;'>
                <h1 style='font-size: 3rem; margin-bottom: 0.5rem;'>🎓</h1>
                <h1>Smart Campus System</h1>
                <p style='font-size: 1.2rem; color: #666; margin-top: 0.5rem;'>
                    QR-Based Attendance • Academics • Campus Services • Analytics
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("---")
        render_auth(conn)

else:
    user = st.session_state.user
    role_name = roles.get(user["role_id"], "student")
    if user.get("role_name") != role_name:
        st.session_state.user = {**user, "role_name": role_name}
        user = st.session_state.user

    if st.session_state.get("active_user_id") != user.get("id"):
        keys_to_clear = [
            "attendance_lock",
            "geo_location",
            "gps_request",
            "gps_message",
            "show_full_qr",
            "full_qr_path",
            "full_qr_caption",
            "teacher_view_session",
        ]
        for key in keys_to_clear:
            st.session_state.pop(key, None)
        st.session_state.active_user_id = user.get("id")
        st.session_state.current_page = "Dashboard"

    with st.sidebar:
        st.markdown(f"""
        <div style='text-align: center; padding: 1rem 0; border-bottom: 2px solid #333; margin-bottom: 1rem;'>
            <h2 style='margin: 0;'>🎓 Smart Campus</h2>
            <p style='color: #888; margin: 0.5rem 0 0 0;'>{user.get('name', 'User')}</p>
            <p style='color: #666; font-size: 0.9rem; margin: 0;'>{role_name.title()}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            st.session_state.user = None
            st.session_state.role = None
            st.session_state.current_page = "Dashboard"
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📑 Navigation")
        
        # Define menu items based on role
        if role_name == "student":
            menu_items = [
                ("🏠", "Dashboard"),
                ("✅", "Attendance"),
                ("📢", "Notices"),
                ("📚", "Resources"),
                ("📅", "Schedule"),
                ("⭐", "Feedback"),
                ("🔧", "Issues"),
                ("🔍", "Lost & Found"),
                ("🎉", "Events"),
                ("🔎", "Search"),
                ("📊", "Analytics"),
            ]
        elif role_name == "teacher":
            menu_items = [
                ("🏠", "Dashboard"),
                ("✅", "Attendance"),
                ("📢", "Notices"),
                ("📚", "Resources"),
                ("📅", "Schedule"),
                ("⭐", "Feedback"),
                ("🔧", "Issues"),
                ("🔍", "Lost & Found"),
                ("🎉", "Events"),
                ("📊", "Analytics"),
                ("📥", "CSV Export"),
                ("✏️", "Manual Override"),
                ("🔎", "Search"),
            ]
        else:  # admin
            menu_items = [
                ("🎯", "Dashboard"),
                ("👥", "User Management"),
                ("📢", "Notices"),
                ("📅", "Schedule"),
                ("🔧", "Issues"),
                ("🔍", "Lost & Found"),
                ("🎉", "Events"),
                ("📊", "Analytics"),
                ("📥", "CSV Export"),
                ("✏️", "Manual Override"),
                ("⚙️", "System Settings"),
                ("🔎", "Search"),
            ]
        
        for icon, page_name in menu_items:
            if st.button(
                f"{icon}  {page_name}",
                use_container_width=True,
                key=f"nav_{page_name}",
                type="primary" if st.session_state.current_page == page_name else "secondary"
            ):
                st.session_state.current_page = page_name
                st.rerun()
    
    # Main content area
    page = st.session_state.current_page
    
    # Route to appropriate page
    if role_name == "admin":
        if page == "Dashboard":
            render_admin_dashboard(conn, user)
        elif page == "User Management":
            render_user_management(conn, user)
        elif page == "Notices":
            render_notice_board(conn, user)
        elif page == "Schedule":
            render_schedule(conn, user)
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
    
    elif role_name == "teacher":
        if page == "Dashboard":
            st.title("Teacher Dashboard")
            render_attendance_analytics(conn)
        elif page == "Attendance":
            render_teacher_attendance(conn, user)
            st.markdown("---")
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
        elif page == "Search":
            render_search(conn)
    
    else:  # student
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
