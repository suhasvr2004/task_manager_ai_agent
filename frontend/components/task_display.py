import streamlit as st
import sys
import os
from typing import Dict, Any, List, Optional

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from frontend.utils.formatting import (
    format_datetime,
    format_date,
    get_priority_color,
    get_status_emoji
)
from frontend.utils.time_utils import format_estimated_time

def render_task_card(task: Dict[str, Any], show_actions: bool = True, api_client=None) -> None:
    """
    Render a single task as a card
    
    Args:
        task: Task dictionary
        show_actions: Whether to show action buttons
        api_client: API client instance for delete operations
    """
    task_id = task.get('id', '')
    priority_emoji = get_priority_color(task.get("priority", "medium"))
    status_emoji = get_status_emoji(task.get("status", "pending"))
    
    title = f"{priority_emoji} {status_emoji} **{task.get('title', 'Untitled')}**"
    
    # Check if delete confirmation is needed
    delete_confirm_key = f"delete_confirm_{task_id}"
    if delete_confirm_key in st.session_state and st.session_state[delete_confirm_key]:
        with st.expander(title, expanded=True):
            st.warning(f"⚠️ Are you sure you want to delete: **{task.get('title', 'Untitled')}**?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, Delete", key=f"confirm_delete_{task_id}", type="primary"):
                    if api_client:
                        try:
                            success = api_client.delete_task(task_id)
                            if success:
                                st.success("Task deleted successfully!")
                                # Clear session state
                                if delete_confirm_key in st.session_state:
                                    del st.session_state[delete_confirm_key]
                                if f"delete_task_{task_id}" in st.session_state:
                                    del st.session_state[f"delete_task_{task_id}"]
                                st.rerun()
                            else:
                                st.error("Failed to delete task")
                        except Exception as e:
                            st.error(f"Error deleting task: {str(e)}")
                    else:
                        st.session_state[f"delete_task_{task_id}"] = True
                        if delete_confirm_key in st.session_state:
                            del st.session_state[delete_confirm_key]
                        st.rerun()
            with col2:
                if st.button("❌ Cancel", key=f"cancel_delete_{task_id}"):
                    if delete_confirm_key in st.session_state:
                        del st.session_state[delete_confirm_key]
                    if f"delete_task_{task_id}" in st.session_state:
                        del st.session_state[f"delete_task_{task_id}"]
                    st.rerun()
        return
    
    with st.expander(title, expanded=False):
        # Task ID - prominently displayed
        st.code(f"Task ID: {task_id}", language=None)
        st.caption("💡 Copy this ID to use in commands like 'Create a reminder for task [ID]'")
        
        # Description
        description = task.get("description", "No description")
        if description:
            st.write(f"**Description:** {description}")
        
        # Metadata
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Status:** {task.get('status', 'pending').replace('_', ' ').title()}")
            st.write(f"**Priority:** {task.get('priority', 'medium').title()}")
        
        with col2:
            st.write(f"**Due Date:** {format_date(task.get('due_date'))}")
            estimated = task.get("estimated_hours")
            if estimated:
                st.write(f"**Estimated:** {format_estimated_time(estimated)}")
        
        # Tags
        tags = task.get("tags", [])
        if tags:
            st.write(f"**Tags:** {', '.join(tags)}")
        
        # Timestamps
        st.caption(f"Created: {format_datetime(task.get('created_at'))}")
        if task.get("updated_at") != task.get("created_at"):
            st.caption(f"Updated: {format_datetime(task.get('updated_at'))}")
        
        # Actions
        if show_actions:
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Edit", key=f"edit_{task['id']}"):
                    st.session_state[f"edit_task_{task['id']}"] = task
            
            with col2:
                if st.button("🗑️ Delete", key=f"delete_{task['id']}", type="secondary"):
                    st.session_state[f"delete_task_{task['id']}"] = True
                    st.session_state[f"delete_confirm_{task['id']}"] = True
            
            with col3:
                status = task.get("status", "pending")
                if status == "pending":
                    if st.button("Start", key=f"start_{task['id']}"):
                        st.session_state[f"update_status_{task['id']}"] = "in_progress"
                elif status == "in_progress":
                    if st.button("Complete", key=f"complete_{task['id']}"):
                        st.session_state[f"update_status_{task['id']}"] = "completed"

def render_task_list(tasks: List[Dict[str, Any]], show_actions: bool = True, api_client=None) -> None:
    """
    Render a list of tasks
    
    Args:
        tasks: List of task dictionaries
        show_actions: Whether to show action buttons
        api_client: API client instance for delete operations
    """
    if not tasks:
        st.info("No tasks found.")
        return
    
    st.write(f"Found {len(tasks)} task(s)")
    
    for task in tasks:
        render_task_card(task, show_actions=show_actions, api_client=api_client)

def render_task_metrics(tasks: List[Dict[str, Any]]) -> None:
    """
    Render task metrics
    
    Args:
        tasks: List of task dictionaries
    """
    total = len(tasks)
    pending = len([t for t in tasks if t.get('status') == 'pending'])
    in_progress = len([t for t in tasks if t.get('status') == 'in_progress'])
    completed = len([t for t in tasks if t.get('status') == 'completed'])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Tasks", total)
    with col2:
        st.metric("Pending", pending)
    with col3:
        st.metric("In Progress", in_progress)
    with col4:
        st.metric("Completed", completed)

