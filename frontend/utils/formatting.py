from datetime import datetime
from typing import Optional, Dict, Any

def format_datetime(dt: Optional[str]) -> str:
    """Format datetime string for display"""
    if not dt:
        return "No date"
    try:
        if isinstance(dt, str):
            dt_obj = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        else:
            dt_obj = dt
        return dt_obj.strftime("%Y-%m-%d %H:%M")
    except:
        return str(dt)

def format_date(dt: Optional[str]) -> str:
    """Format date string for display"""
    if not dt:
        return "No due date"
    try:
        if isinstance(dt, str):
            dt_obj = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        else:
            dt_obj = dt
        return dt_obj.strftime("%Y-%m-%d")
    except:
        return str(dt)

def get_priority_color(priority: str) -> str:
    """Get color for priority badge"""
    colors = {
        "low": "🟢",
        "medium": "🟡",
        "high": "🟠",
        "urgent": "🔴"
    }
    return colors.get(priority.lower(), "⚪")

def get_status_emoji(status: str) -> str:
    """Get emoji for status"""
    emojis = {
        "pending": "⏳",
        "in_progress": "🔄",
        "completed": "✅",
        "archived": "📦"
    }
    return emojis.get(status.lower(), "❓")

def format_task_display(task: Dict[str, Any]) -> str:
    """Format task for display"""
    priority_emoji = get_priority_color(task.get("priority", "medium"))
    status_emoji = get_status_emoji(task.get("status", "pending"))
    
    return f"{priority_emoji} {status_emoji} {task.get('title', 'Untitled')}"

