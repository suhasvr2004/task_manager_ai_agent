import streamlit as st
import sys
import os
from typing import List, Dict, Any
from datetime import datetime, date

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from frontend.utils.formatting import format_date, get_priority_color

def render_calendar_view(tasks: List[Dict[str, Any]]) -> None:
    """
    Render tasks in a calendar-like view
    
    Args:
        tasks: List of task dictionaries
    """
    # Group tasks by due date
    tasks_by_date = {}
    no_date_tasks = []
    
    for task in tasks:
        due_date = task.get("due_date")
        if due_date:
            try:
                if isinstance(due_date, str):
                    dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                    date_key = dt.date()
                else:
                    date_key = due_date.date() if hasattr(due_date, 'date') else due_date
                
                if date_key not in tasks_by_date:
                    tasks_by_date[date_key] = []
                tasks_by_date[date_key].append(task)
            except:
                no_date_tasks.append(task)
        else:
            no_date_tasks.append(task)
    
    # Display tasks grouped by date
    if tasks_by_date:
        st.subheader("Tasks by Due Date")
        
        # Sort dates
        sorted_dates = sorted(tasks_by_date.keys())
        
        for task_date in sorted_dates:
            date_str = task_date.strftime("%Y-%m-%d")
            tasks_for_date = tasks_by_date[task_date]
            
            with st.expander(f"📅 {date_str} ({len(tasks_for_date)} task(s))", expanded=False):
                for task in tasks_for_date:
                    priority_emoji = get_priority_color(task.get("priority", "medium"))
                    st.write(f"{priority_emoji} **{task.get('title', 'Untitled')}**")
                    if task.get("description"):
                        st.caption(task["description"])
    
    # Display tasks without due dates
    if no_date_tasks:
        st.subheader("Tasks Without Due Date")
        for task in no_date_tasks:
            priority_emoji = get_priority_color(task.get("priority", "medium"))
            st.write(f"{priority_emoji} **{task.get('title', 'Untitled')}**")
            if task.get("description"):
                st.caption(task["description"])

