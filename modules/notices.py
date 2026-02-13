import streamlit as st
from core.utils import now_iso, build_timeline


def render_notice_board(conn, user):
    st.title("📢 Digital Notice Board")
    st.markdown("---")
    
    if user.get("role_name") != "student":  # Teacher or Admin
        with st.expander("✏️ Post New Notice", expanded=False):
            with st.form("notice_form"):
                title = st.text_input("📌 Notice Title *", placeholder="e.g., Holiday Announcement")
                body = st.text_area("📝 Notice Content *", placeholder="Write your notice here...", height=150)
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    priority = st.selectbox("🚨 Priority", ["Normal", "Important", "Urgent"])
                with col2:
                    submitted = st.form_submit_button("📤 Post Notice", use_container_width=True, type="primary")

            if submitted:
                if not title or not body:
                    st.error("❌ Title and content are required.")
                else:
                    conn.execute(
                        "INSERT INTO notices (title, body, posted_by, created_at) VALUES (?, ?, ?, ?)",
                        (f"[{priority}] {title}", body, user["id"], now_iso()),
                    )
                    conn.commit()
                    st.success("✅ Notice posted successfully!")
                    st.rerun()
        
        st.markdown("---")

    # Display notices
    notices = conn.execute(
        "SELECT n.*, u.name as poster FROM notices n LEFT JOIN users u ON n.posted_by = u.id ORDER BY created_at DESC LIMIT 50"
    ).fetchall()

    if not notices:
        st.info("📭 No notices yet.")
        return

    # Search filter
    search = st.text_input("🔍 Search Notices", placeholder="Type to search...")
    
    timeline = build_timeline([dict(row) for row in notices])
    
    for item in timeline:
        if search and search.lower() not in item['title'].lower() and search.lower() not in item['body'].lower():
            continue
        
        # Determine priority color
        priority_color = "#666"
        if "[Urgent]" in item['title']:
            priority_color = "red"
        elif "[Important]" in item['title']:
            priority_color = "orange"
        
        st.markdown(f"""
        <div style='padding: 1.5rem; margin: 1rem 0; background: rgba(255,255,255,0.05); 
                    border-left: 4px solid {priority_color}; border-radius: 8px;'>
            <h3 style='margin: 0 0 0.5rem 0; color: {priority_color};'>{item['title']}</h3>
            <p style='margin: 0.5rem 0 1rem 0; line-height: 1.6;'>{item['body']}</p>
            <p style='color: #888; font-size: 0.9rem; margin: 0;'>
                👤 Posted by {item.get('poster', 'Unknown')} | 📅 {item['created_at'][:16]}
            </p>
        </div>
        """, unsafe_allow_html=True)
