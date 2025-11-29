"""Timezone and datetime formatting utilities for Indian Standard Time (IST)"""
from datetime import datetime
from typing import Optional
import pytz

# Indian Standard Time timezone
IST = pytz.timezone('Asia/Kolkata')

def format_datetime_ist(dt: Optional[datetime], format_type: str = "full") -> str:
    """
    Format datetime to Indian Standard Time (IST) with DD/MM/YYYY and 12-hour format
    
    Args:
        dt: Datetime object (can be timezone-aware or naive)
        format_type: "full" for date + time, "date" for date only, "time" for time only
    
    Returns:
        Formatted string in IST: "DD/MM/YYYY HH:MM AM/PM" format
    """
    if not dt:
        return "Not set"
    
    try:
        # If datetime is naive, assume it's in IST and localize it
        if dt.tzinfo is None:
            # Localize naive datetime to IST
            dt = IST.localize(dt)
        
        # Convert to IST
        dt_ist = dt.astimezone(IST)
        
        if format_type == "date":
            return dt_ist.strftime("%d/%m/%Y")
        elif format_type == "time":
            return dt_ist.strftime("%I:%M %p")
        else:  # full
            return dt_ist.strftime("%d/%m/%Y %I:%M %p")
    except Exception as e:
        # Fallback to ISO format if conversion fails
        return dt.isoformat() if hasattr(dt, 'isoformat') else str(dt)

def format_datetime_string_ist(dt_string: Optional[str], format_type: str = "full") -> str:
    """
    Format datetime string to Indian Standard Time (IST) with DD/MM/YYYY and 12-hour format
    
    Args:
        dt_string: ISO format datetime string
        format_type: "full" for date + time, "date" for date only, "time" for time only
    
    Returns:
        Formatted string in IST: "DD/MM/YYYY HH:MM AM/PM" format
    """
    if not dt_string:
        return "Not set"
    
    try:
        # Parse ISO format string
        if isinstance(dt_string, str):
            # Handle ISO format with or without timezone
            if 'Z' in dt_string:
                dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            elif '+' in dt_string or dt_string.count('-') >= 3:
                dt = datetime.fromisoformat(dt_string)
            else:
                # Try parsing as simple ISO format
                dt = datetime.fromisoformat(dt_string)
                # Assume UTC if no timezone info
                dt = pytz.utc.localize(dt)
        else:
            dt = dt_string
        
        return format_datetime_ist(dt, format_type)
    except Exception as e:
        # Fallback to original string if parsing fails
        return str(dt_string)

def get_current_ist_time() -> datetime:
    """Get current time in IST"""
    return datetime.now(IST)

