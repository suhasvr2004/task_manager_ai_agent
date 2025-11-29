import streamlit as st
import sys
import os

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from frontend.utils.api_client import APIClient
from frontend.components.task_display import render_task_list
from frontend.components.task_form import render_task_form

st.set_page_config(
    page_title="Task List - Task Manager",
    page_icon="📋",
    layout="wide"
)

st.title("📋 Task List")

# Initialize API client
api_client = APIClient()

# Filters
col1, col2 = st.columns(2)
with col1:
    status_filter = st.selectbox(
        "Filter by Status",
        ["All", "pending", "in_progress", "completed", "archived"]
    )
with col2:
    priority_filter = st.selectbox(
        "Filter by Priority",
        ["All", "low", "medium", "high", "urgent"]
    )

# Check for edit/delete actions
task_to_edit = None
task_to_delete = None
status_to_update = None

for key in st.session_state.keys():
    if key.startswith("edit_task_"):
        task_id = key.replace("edit_task_", "")
        task_to_edit = st.session_state[key]
        del st.session_state[key]
        break
    elif key.startswith("delete_task_"):
        task_id = key.replace("delete_task_", "")
        task_to_delete = task_id
        del st.session_state[key]
        break
    elif key.startswith("update_status_"):
        task_id = key.replace("update_status_", "")
        status_to_update = (task_id, st.session_state[key])
        del st.session_state[key]
        break

# Handle delete (deletion is now handled in the component with confirmation)
# This section is kept for backward compatibility but the component handles it
if task_to_delete:
    confirm_key = f"delete_confirm_{task_to_delete}"
    if confirm_key not in st.session_state:
        st.session_state[confirm_key] = True
        st.rerun()

# Handle status update
if status_to_update:
    task_id, new_status = status_to_update
    try:
        with st.spinner("Updating task..."):
            result = api_client.update_task(task_id, {"status": new_status})
            if result:
                st.success(f"Task status updated to {new_status}!")
                st.rerun()
    except Exception as e:
        st.error(f"Error updating task: {str(e)}")

# Handle edit
if task_to_edit:
    st.markdown("---")
    st.subheader("Edit Task")
    form_data = render_task_form(task_to_edit)
    
    if form_data:
        try:
            with st.spinner("Updating task..."):
                result = api_client.update_task(task_to_edit["id"], form_data)
            if result:
                st.success("Task updated successfully!")
                st.rerun()
        except Exception as e:
            st.error(f"Error updating task: {str(e)}")

# Load and display tasks
try:
    with st.spinner("Loading tasks..."):
        tasks = api_client.list_tasks(
            status=None if status_filter == "All" else status_filter,
            priority=None if priority_filter == "All" else priority_filter
        )
    
    render_task_list(tasks, show_actions=True, api_client=api_client)

except Exception as e:
    st.error(f"Error loading tasks: {str(e)}")
    st.info("Make sure the backend API is running on http://localhost:8000")

