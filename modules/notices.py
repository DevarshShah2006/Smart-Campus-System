import streamlit as st
from core.utils import now_iso, build_timeline


def render_notice_board(conn, user):
    st.subheader("Digital Notice Board")
    if user["role_id"] != 1:
        with st.form("notice_form"):
            title = st.text_input("Notice Title")
            body = st.text_area("Notice Content")
            submitted = st.form_submit_button("Post Notice")

        if submitted:
            if not title or not body:
                st.error("Title and content are required.")
            else:
                conn.execute(
                    "INSERT INTO notices (title, body, posted_by, created_at) VALUES (?, ?, ?, ?)",
                    (title, body, user["id"], now_iso()),
                )
                conn.commit()
                st.success("Notice posted.")

    notices = conn.execute(
        "SELECT n.*, u.name as poster FROM notices n LEFT JOIN users u ON n.posted_by = u.id ORDER BY created_at DESC"
    ).fetchall()

    if not notices:
        st.info("No notices yet.")
        return

    timeline = build_timeline([dict(row) for row in notices])
    for item in timeline:
        st.markdown(f"**{item['title']}**")
        st.caption(f"By {item.get('poster', 'Unknown')} | {item['created_at']}")
        st.write(item["body"])
        st.divider()
