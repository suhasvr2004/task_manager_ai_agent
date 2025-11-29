"""Utility functions for time calculations"""
from typing import Tuple

def hours_to_hours_minutes(total_hours: float) -> Tuple[int, int]:
    """
    Convert total hours to hours and minutes
    
    Args:
        total_hours: Total time in hours (can be fractional)
    
    Returns:
        Tuple of (hours, minutes)
    """
    hours = int(total_hours)
    minutes = int((total_hours - hours) * 60)
    return hours, minutes

def hours_minutes_to_hours(hours: int, minutes: int) -> float:
    """
    Convert hours and minutes to total hours
    
    Args:
        hours: Number of hours
        minutes: Number of minutes
    
    Returns:
        Total time in hours (fractional)
    """
    return hours + (minutes / 60.0)

def format_estimated_time(total_hours: float) -> str:
    """
    Format estimated time for display
    
    Args:
        total_hours: Total time in hours
    
    Returns:
        Formatted string like "2h 30m" or "45m" or "2 hours"
    """
    if not total_hours or total_hours == 0:
        return "Not set"
    
    hours, minutes = hours_to_hours_minutes(total_hours)
    
    if hours > 0 and minutes > 0:
        return f"{hours}h {minutes}m"
    elif hours > 0:
        return f"{hours} hour{'s' if hours > 1 else ''}"
    elif minutes > 0:
        return f"{minutes} minute{'s' if minutes > 1 else ''}"
    else:
        return f"{total_hours:.2f} hours"

