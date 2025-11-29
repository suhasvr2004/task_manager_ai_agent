import streamlit as st
import sys
import os

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from frontend.utils.api_client import APIClient
from frontend.components.task_form import render_task_form

st.set_page_config(
    page_title="Create Task - Task Manager",
    page_icon="✏️",
    layout="wide"
)

st.title("✏️ Create New Task")

# Initialize API client
api_client = APIClient()

# Render task form
form_data = render_task_form()

if form_data:
    try:
        with st.spinner("Creating task..."):
            result = api_client.create_task(form_data)
        
        if result and "id" in result:
            st.success(f"✅ Task created successfully! ID: {result['id']}")
            st.balloons()
            
            # Show created task
            st.markdown("---")
            st.subheader("Created Task")
            st.json(result)
        else:
            st.error("Failed to create task. Please try again.")
    
    except Exception as e:
        st.error(f"Error creating task: {str(e)}")
        st.info("Make sure the backend API is running on http://localhost:8000")

# Help section
with st.expander("💡 Tips for Creating Tasks"):
    st.markdown("""
    - **Title**: Be specific and clear about what needs to be done
    - **Description**: Add context, requirements, or notes
    - **Priority**: 
      - Low: Can be done later
      - Medium: Normal priority
      - High: Important, should be done soon
      - Urgent: Needs immediate attention
    - **Due Date**: Set realistic deadlines
    - **Estimated Time**: Enter hours and minutes to estimate task duration
    - **Tags**: Use tags to categorize and filter tasks
    """)

