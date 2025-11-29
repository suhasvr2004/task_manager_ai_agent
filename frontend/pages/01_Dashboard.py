import streamlit as st
import sys
import os

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from frontend.utils.api_client import APIClient
from frontend.components.task_display import render_task_metrics, render_task_list
from frontend.components.calendar_view import render_calendar_view

st.set_page_config(
    page_title="Dashboard - Task Manager",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard")

# Initialize API client
api_client = APIClient()

try:
    # Load all tasks
    tasks = api_client.list_tasks()
    
    # Display metrics
    render_task_metrics(tasks)
    
    st.markdown("---")
    
    # View toggle
    view_mode = st.radio(
        "View Mode",
        ["List View", "Calendar View"],
        horizontal=True
    )
    
    if view_mode == "List View":
        st.subheader("Recent Tasks")
        # Show most recent 10 tasks
        recent_tasks = sorted(
            tasks,
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )[:10]
        render_task_list(recent_tasks, show_actions=True, api_client=api_client)
    else:
        render_calendar_view(tasks)
    
    # AI Summary Section
    st.markdown("---")
    st.subheader("🤖 AI Insights")
    
    if st.button("Get Task Summary"):
        with st.spinner("Analyzing tasks..."):
            try:
                summary = api_client.get_summary()
                st.write(summary.get("output", "No summary available"))
            except Exception as e:
                st.error(f"Error getting summary: {str(e)}")
    
    if st.button("Get Next Task Recommendation"):
        with st.spinner("Thinking..."):
            try:
                recommendation = api_client.agent_chat("What task should I work on next?")
                st.write(recommendation.get("output", "No recommendation available"))
            except Exception as e:
                st.error(f"Error getting recommendation: {str(e)}")

except Exception as e:
    st.error(f"Error loading dashboard: {str(e)}")
    st.info("Make sure the backend API is running on http://localhost:8000")

