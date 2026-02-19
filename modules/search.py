import streamlit as st

from core.utils import rows_to_dataframe, add_datetime_columns


def render_search(conn):
    st.subheader("Search & Filter")
    query = st.text_input("Search keyword")
    if not query:
        st.info("Enter a keyword to search across modules.")
        return

    like = f"%{query}%"
    notices = conn.execute(
        "SELECT title, body, created_at FROM notices WHERE title LIKE ? OR body LIKE ?",
        (like, like),
    ).fetchall()
    issues = conn.execute(
        "SELECT title, description, status FROM issues WHERE title LIKE ? OR description LIKE ?",
        (like, like),
    ).fetchall()
    events = conn.execute(
        "SELECT title, description, event_date FROM events WHERE title LIKE ? OR description LIKE ?",
        (like, like),
    ).fetchall()
    resources = conn.execute(
        "SELECT title, subject, file_path FROM resources WHERE title LIKE ? OR subject LIKE ?",
        (like, like),
    ).fetchall()
    lectures = conn.execute(
        "SELECT session_id, subject, room, start_time, end_time, year, batch FROM lectures WHERE subject LIKE ? OR room LIKE ? OR session_id LIKE ?",
        (like, like, like),
    ).fetchall()

    st.markdown("**Notices**")
    if notices:
        for n in notices:
            _n = dict(n) if hasattr(n, 'keys') else {"title": n[0], "body": n[1], "created_at": n[2]}
            _d = str(_n.get('created_at', ''))[:10]
            _t = str(_n.get('created_at', ''))[11:16]
            st.markdown(f"""
<div style='padding:0.6rem;margin:0.4rem 0;border-left:3px solid #666;background:rgba(255,255,255,0.05);border-radius:6px;'>
<b>{_n['title']}</b><br>
<span style='font-size:0.85rem'>{_n.get('body','')[:100]}</span><br>
<small style='color:#888'>📅 {_d} &nbsp; ⏰ {_t}</small>
</div>""", unsafe_allow_html=True)
    else:
        st.caption("No results")

    st.markdown("**Issues**")
    if issues:
        for i in issues:
            _i = dict(i) if hasattr(i, 'keys') else {"title": i[0], "description": i[1], "status": i[2]}
            _color = "green" if _i['status'] == "Resolved" else ("orange" if _i['status'] == "In Progress" else "red")
            st.markdown(f"""
<div style='padding:0.6rem;margin:0.4rem 0;border-left:3px solid {_color};background:rgba(255,255,255,0.05);border-radius:6px;'>
<b>{_i['title']}</b><br>
<span style='font-size:0.85rem'>{_i.get('description','')[:100]}</span><br>
<small style='color:{_color}'>{_i['status']}</small>
</div>""", unsafe_allow_html=True)
    else:
        st.caption("No results")

    st.markdown("**Events**")
    if events:
        for e in events:
            _e = dict(e) if hasattr(e, 'keys') else {"title": e[0], "description": e[1], "event_date": e[2]}
            st.markdown(f"""
<div style='padding:0.6rem;margin:0.4rem 0;border-left:3px solid #4a9eff;background:rgba(255,255,255,0.05);border-radius:6px;'>
<b>{_e['title']}</b><br>
<span style='font-size:0.85rem'>{_e.get('description','')[:100]}</span><br>
<small style='color:#888'>📅 {str(_e.get('event_date',''))[:10]}</small>
</div>""", unsafe_allow_html=True)
    else:
        st.caption("No results")

    st.markdown("**Resources**")
    if resources:
        for r in resources:
            _r = dict(r) if hasattr(r, 'keys') else {"title": r[0], "subject": r[1]}
            st.markdown(f"""
<div style='padding:0.6rem;margin:0.4rem 0;border-left:3px solid #a855f7;background:rgba(255,255,255,0.05);border-radius:6px;'>
<b>{_r['title']}</b><br>
<small style='color:#888'>📚 {_r.get('subject','')}</small>
</div>""", unsafe_allow_html=True)
    else:
        st.caption("No results")

    st.markdown("**Lectures**")
    if lectures:
        for lec in lectures:
            _l = dict(lec) if hasattr(lec, 'keys') else {"session_id": lec[0], "subject": lec[1], "room": lec[2], "start_time": lec[3], "end_time": lec[4], "year": lec[5], "batch": lec[6]}
            _ld = str(_l.get('start_time',''))[:10]
            _ls = str(_l.get('start_time',''))[11:16]
            _le = str(_l.get('end_time',''))[11:16]
            st.markdown(f"""
<div style='padding:0.6rem;margin:0.4rem 0;border-left:3px solid #22c55e;background:rgba(255,255,255,0.05);border-radius:6px;'>
<b>📚 {_l['subject']}</b> &mdash; {_l['room']}<br>
<small style='color:#888'>📅 {_ld} &nbsp; ⏰ {_ls} - {_le}</small><br>
<small style='color:#888'>🎓 Year {_l.get('year','-')} &nbsp; Batch {_l.get('batch','-')}</small>
</div>""", unsafe_allow_html=True)
    else:
        st.caption("No results")
