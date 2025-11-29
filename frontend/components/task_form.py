import streamlit as st
from datetime import datetime, date
from typing import Dict, Any, Optional

def render_task_form(task_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Render task creation/editing form
    
    Args:
        task_data: Optional existing task data for editing
    
    Returns:
        Dictionary with form data or None if not submitted
    """
    is_edit = task_data is not None
    
    with st.form(f"task_form_{'edit' if is_edit else 'create'}"):
        title = st.text_input(
            "Task Title*",
            value=task_data.get("title", "") if task_data else "",
            max_chars=255,
            help="Enter a clear, descriptive title for your task"
        )
        
        description = st.text_area(
            "Description",
            value=task_data.get("description", "") if task_data else "",
            help="Provide detailed information about the task"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            priority = st.selectbox(
                "Priority",
                ["low", "medium", "high", "urgent"],
                index=["low", "medium", "high", "urgent"].index(
                    task_data.get("priority", "medium") if task_data else "medium"
                )
            )
        
        with col2:
            due_date = st.date_input(
                "Due Date",
                value=datetime.fromisoformat(task_data["due_date"]).date() 
                if task_data and task_data.get("due_date") 
                else None
            )
        
        # Estimated time in hours and minutes
        st.write("**Estimated Time**")
        est_time_col1, est_time_col2 = st.columns(2)
        
        # Convert existing estimated_hours to hours and minutes for editing
        existing_hours = 0
        existing_minutes = 0
        if task_data and task_data.get("estimated_hours"):
            total_hours = float(task_data.get("estimated_hours", 0))
            existing_hours = int(total_hours)
            existing_minutes = int((total_hours - existing_hours) * 60)
        
        with est_time_col1:
            estimated_hours_input = st.number_input(
                "Hours",
                min_value=0,
                max_value=23,
                value=existing_hours if task_data else 0,
                step=1,
                help="Number of hours"
            )
        
        with est_time_col2:
            estimated_minutes_input = st.number_input(
                "Minutes",
                min_value=0,
                max_value=59,
                value=existing_minutes if task_data else 30,
                step=5,
                help="Number of minutes"
            )
        
        # Calculate total time in hours (for backend storage)
        estimated_hours = estimated_hours_input + (estimated_minutes_input / 60.0)
        
        # Display total time
        if estimated_hours > 0:
            if estimated_hours_input > 0 and estimated_minutes_input > 0:
                st.caption(f"Total: {estimated_hours_input}h {estimated_minutes_input}m ({estimated_hours:.2f} hours)")
            elif estimated_hours_input > 0:
                st.caption(f"Total: {estimated_hours_input} hour(s)")
            elif estimated_minutes_input > 0:
                st.caption(f"Total: {estimated_minutes_input} minute(s)")
        
        available_tags = ["work", "personal", "urgent", "important", "meeting", "coding", "review"]
        default_tags = task_data.get("tags", []) if task_data else []
        tags = st.multiselect(
            "Tags",
            available_tags,
            default=default_tags,
            help="Select relevant tags for categorization"
        )
        
        submitted = st.form_submit_button(
            "Update Task" if is_edit else "Create Task",
            type="primary"
        )
        
        if submitted:
            if not title:
                st.error("Task title is required!")
                return None
            
            form_data = {
                "title": title,
                "description": description,
                "priority": priority,
                "due_date": due_date.isoformat() if due_date else None,
                "estimated_hours": estimated_hours,
                "tags": tags
            }
            
            if is_edit:
                form_data["id"] = task_data["id"]
            
            return form_data
    
    return None

