import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from core.utils import summarize_counts, to_chart_data


def render_analytics(conn):
    st.subheader("Analytics & Insights")

    tab1, tab2, tab3 = st.tabs([
        "Attendance Trends",
        "Department Distribution",
        "Issue Resolution",
    ])

    with tab1:
        data = conn.execute("SELECT status FROM attendance").fetchall()
        if data:
            summary = summarize_counts([dict(row) for row in data], "status")
            labels, counts = to_chart_data(summary)
            fig, ax = plt.subplots()
            ax.bar(labels, counts)
            ax.set_ylabel("Count")
            ax.set_title("Attendance Status Distribution")
            st.pyplot(fig)
        else:
            st.info("No attendance data yet.")

    with tab2:
        data = conn.execute("SELECT department FROM users WHERE enrollment IS NOT NULL").fetchall()
        if data:
            summary = summarize_counts([dict(row) for row in data], "department")
            labels, counts = to_chart_data(summary)
            counts = np.array(counts)
            fig, ax = plt.subplots()
            ax.pie(counts, labels=labels, autopct="%1.1f%%")
            ax.set_title("Students by Department")
            st.pyplot(fig)
        else:
            st.info("No student data yet.")

    with tab3:
        data = conn.execute("SELECT category, status FROM issues").fetchall()
        if data:
            df = pd.DataFrame(data)
            pivot = df.pivot_table(index="category", columns="status", aggfunc="size", fill_value=0)
            fig, ax = plt.subplots()
            pivot.plot(kind="bar", ax=ax)
            ax.set_ylabel("Count")
            ax.set_title("Issue Resolution by Category")
            st.pyplot(fig)
        else:
            st.info("No issues data yet.")


def render_exports(conn):
    st.subheader("CSV Export")
    export_map = {
        "Attendance": "SELECT * FROM attendance",
        "Issues": "SELECT * FROM issues",
        "Notices": "SELECT * FROM notices",
        "Resources": "SELECT * FROM resources",
        "Events": "SELECT * FROM events",
    }
    dataset = st.selectbox("Select Dataset", list(export_map.keys()))
    if st.button("Generate CSV"):
        df = pd.read_sql_query(export_map[dataset], conn)
        st.download_button(
            label="Download CSV",
            data=df.to_csv(index=False),
            file_name=f"{dataset.lower()}_export.csv",
            mime="text/csv",
        )
