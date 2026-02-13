import streamlit as st
from datetime import datetime

from core.security import hash_password
from core.utils import now_iso


def render_admin_dashboard(conn, user):
    st.title("🎯 Admin Control Panel")
    st.markdown("---")
    
    # Statistics Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_students = conn.execute(
            """
            SELECT COUNT(*)
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE r.name = 'student'
            """
        ).fetchone()[0]
        st.metric("👨‍🎓 Total Students", total_students)
    
    with col2:
        total_teachers = conn.execute(
            """
            SELECT COUNT(*)
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE r.name = 'teacher'
            """
        ).fetchone()[0]
        st.metric("👨‍🏫 Total Teachers", total_teachers)
    
    with col3:
        total_lectures = conn.execute("SELECT COUNT(*) FROM lectures").fetchone()[0]
        st.metric("📚 Total Lectures", total_lectures)
    
    with col4:
        total_attendance = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
        st.metric("✅ Attendance Records", total_attendance)
    
    st.markdown("---")
    
    # Quick Actions
    st.subheader("⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("👥 Manage Users", use_container_width=True):
            st.session_state.admin_page = "users"
            st.rerun()
    
    with col2:
        if st.button("📊 View Analytics", use_container_width=True):
            st.session_state.admin_page = "analytics"
            st.rerun()
    
    with col3:
        if st.button("⚙️ System Settings", use_container_width=True):
            st.session_state.admin_page = "settings"
            st.rerun()
    
    st.markdown("---")
    
    # Recent Activity
    st.subheader("📋 Recent Activity")
    
    tab1, tab2, tab3 = st.tabs(["Recent Attendance", "Recent Issues", "Recent Events"])
    
    with tab1:
        recent_attendance = conn.execute(
            """
            SELECT a.enrollment, a.status, a.timestamp, l.subject
            FROM attendance a
            LEFT JOIN lectures l ON a.session_id = l.session_id
            ORDER BY a.timestamp DESC
            LIMIT 10
            """
        ).fetchall()
        
        if recent_attendance:
            for record in recent_attendance:
                st.text(f"📌 {record[0]} - {record[3]} - {record[1]} at {record[2][:16]}")
        else:
            st.info("No recent attendance records")
    
    with tab2:
        recent_issues = conn.execute(
            "SELECT title, category, status, created_at FROM issues ORDER BY created_at DESC LIMIT 10"
        ).fetchall()
        
        if recent_issues:
            for issue in recent_issues:
                st.text(f"🔧 {issue[0]} ({issue[1]}) - {issue[2]}")
        else:
            st.info("No recent issues")
    
    with tab3:
        recent_events = conn.execute(
            "SELECT title, event_date, location FROM events ORDER BY created_at DESC LIMIT 10"
        ).fetchall()
        
        if recent_events:
            for event in recent_events:
                st.text(f"🎉 {event[0]} - {event[1]} at {event[2]}")
        else:
            st.info("No recent events")


def render_user_management(conn, user):
    st.title("👥 User Management")
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Add Student", "Add Teacher", "View All Users", "Bulk Actions"])
    
    with tab1:
        st.subheader("➕ Register New Student")
        with st.form("student_register"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name *")
                enrollment = st.text_input("Enrollment Number *")
                department = st.text_input("Department *")
            with col2:
                year = st.selectbox("Year *", [1, 2, 3, 4, 5])
                batch = st.selectbox("Batch *", [1, 2, 3, 4])
                email = st.text_input("Email (Optional)")
                password = st.text_input("Set Password *", type="password")
            
            submitted = st.form_submit_button("✅ Create Student Profile", use_container_width=True)

        if submitted:
            if not (name and enrollment and department and password):
                st.error("❌ Please fill all required fields.")
                return

            existing = conn.execute("SELECT id FROM users WHERE enrollment = ?", (enrollment,)).fetchone()
            if existing:
                st.warning("⚠️ Enrollment already registered.")
                return

            role_id = conn.execute("SELECT id FROM roles WHERE name = ?", ("student",)).fetchone()[0]
            conn.execute(
                """
                INSERT INTO users (role_id, name, enrollment, department, year, batch, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (role_id, name, enrollment, department, year, batch, hash_password(password), now_iso()),
            )
            conn.commit()
            st.success(f"✅ Student {name} registered successfully!")
    
    with tab2:
        st.subheader("➕ Register New Teacher")
        with st.form("teacher_register"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name *", key="teacher_name")
                username = st.text_input("Username *", key="teacher_username")
            with col2:
                department = st.text_input("Department *", key="teacher_dept")
                password = st.text_input("Set Password *", type="password", key="teacher_pass")
            
            submitted = st.form_submit_button("✅ Create Teacher Profile", use_container_width=True)

        if submitted:
            if not (name and username and department and password):
                st.error("❌ Please fill all required fields.")
                return

            existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            if existing:
                st.warning("⚠️ Username already exists.")
                return

            role_id = conn.execute("SELECT id FROM roles WHERE name = ?", ("teacher",)).fetchone()[0]
            conn.execute(
                """
                INSERT INTO users (role_id, name, username, department, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (role_id, name, username, department, hash_password(password), now_iso()),
            )
            conn.commit()
            st.success(f"✅ Teacher {name} registered successfully!")
    
    with tab3:
        st.subheader("📋 All Users")
        
        filter_role = st.selectbox("Filter by Role", ["All", "Students", "Teachers", "Admins"])
        
        query = """
            SELECT u.id, u.name, u.enrollment, u.username, u.department, u.year, u.batch, r.name as role, u.created_at
            FROM users u
            LEFT JOIN roles r ON u.role_id = r.id
        """
        
        if filter_role == "Students":
            query += " WHERE r.name = 'student'"
        elif filter_role == "Teachers":
            query += " WHERE r.name = 'teacher'"
        elif filter_role == "Admins":
            query += " WHERE r.name = 'admin'"
        
        query += " ORDER BY u.created_at DESC"
        
        users = conn.execute(query).fetchall()
        
        if users:
            st.write(f"📊 Total Users: {len(users)}")
            for u in users:
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"**{u[1]}** ({u[7].title()})")
                with col2:
                    year_batch = f"Y{u[5]} B{u[6]}" if u[5] and u[6] else "Y/B N/A"
                    st.write(f"{u[2] or u[3] or 'N/A'} - {u[4] or 'N/A'} - {year_batch}")
                with col3:
                    if st.button("🗑️", key=f"del_{u[0]}"):
                        if u[7] != "admin":  # Don't allow deleting admin
                            conn.execute("DELETE FROM users WHERE id = ?", (u[0],))
                            conn.commit()
                            st.success("Deleted")
                            st.rerun()
                st.divider()
        else:
            st.info("No users found")

        st.markdown("---")
        st.subheader("✏️ Update Student Year/Batch")
        students = conn.execute(
            """
            SELECT u.enrollment, u.name, u.year, u.batch
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE r.name = 'student'
            ORDER BY u.name
            """
        ).fetchall()
        if students:
            student_options = {
                f"{s[1]} ({s[0]})": s for s in students if s[0]
            }
            selected_label = st.selectbox("Select Student", ["-- Select --"] + list(student_options.keys()))
            if selected_label != "-- Select --":
                selected = student_options[selected_label]
                new_year = st.selectbox("Year", [1, 2, 3, 4, 5], index=max((selected[2] or 1) - 1, 0))
                new_batch = st.selectbox("Batch", [1, 2, 3, 4], index=max((selected[3] or 1) - 1, 0))
                if st.button("Update Student"):
                    conn.execute(
                        "UPDATE users SET year = ?, batch = ? WHERE enrollment = ?",
                        (new_year, new_batch, selected[0]),
                    )
                    conn.commit()
                    st.success("Student updated.")
        else:
            st.info("No students found")
    
    with tab4:
        st.subheader("📦 Bulk Actions")
        st.info("🚧 Bulk user import/export coming soon!")
        
        if st.button("📥 Export All Students as CSV"):
            import pandas as pd
            students = conn.execute(
                """
                SELECT u.name, u.enrollment, u.department, u.year, u.batch, u.created_at
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE r.name = 'student'
                """
            ).fetchall()
            df = pd.DataFrame(students, columns=["Name", "Enrollment", "Department", "Year", "Batch", "Created"])
            csv = df.to_csv(index=False)
            st.download_button(
                "💾 Download CSV",
                csv,
                "students_export.csv",
                "text/csv"
            )
