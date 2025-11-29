from langchain_core.tools import tool
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from backend.database.client import DatabaseManager
from backend.utils.timezone_utils import format_datetime_ist, get_current_ist_time, IST
from loguru import logger
import asyncio
import pytz

db_manager = DatabaseManager()

def run_async(coro):
    """Helper to run async code from sync context"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(coro)
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)

@tool
def create_reminder(
    task_id: str,
    reminder_time: Optional[str] = None,
    reminder_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a reminder for a task. Use this when user wants to be reminded about a task.
    
    Args:
        task_id: ID of the task to remind about (REQUIRED - UUID format, e.g., "46d6dfae-b367-40ec-b3b8-77246979a72b")
                 Extract from user input. Can be in formats: "[task_id: xxx]", "task_id: xxx", or just the UUID.
                 If user says "yes" after task creation, use the task_id from the created task.
        reminder_time: When to send reminder (optional). Can be:
            - Relative: "in 1 hour", "in 2 hours", "in 30 minutes", "in 1 day"
            - Specific: "tomorrow at 9am", "today at 5pm"
            - ISO format: "2024-01-15T10:30:00"
            - If not provided, defaults to 1 hour from now
        reminder_text: Optional reminder message
    
    Returns:
        Confirmation with reminder ID and time in IST format (DD/MM/YYYY HH:MM AM/PM)
    
    Examples:
        - "Create a reminder for task [task_id] in 1 hour" → create_reminder(task_id="[id]", reminder_time="in 1 hour")
        - "Create a reminder for task [task_id] tomorrow at 9am" → create_reminder(task_id="[id]", reminder_time="tomorrow at 9am")
        - User says "yes" after task creation → create_reminder(task_id="[created_task_id]", reminder_time="in 1 hour")
    """
    try:
        # Clean task_id - remove brackets and labels if present
        # Handle formats like "[task_id: 46d6dfae-b367-40ec-b3b8-77246979a72b]" or just the UUID
        task_id = task_id.strip()
        if "task_id" in task_id.lower() or ":" in task_id:
            # Extract UUID from formats like "[task_id: xxx]" or "task_id: xxx"
            import re
            uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
            match = re.search(uuid_pattern, task_id, re.IGNORECASE)
            if match:
                task_id = match.group(0)
        
        # Parse reminder time (all times in IST)
        reminder_datetime = None
        
        if not reminder_time:
            # Default: 1 hour from now (in IST)
            reminder_datetime = get_current_ist_time() + timedelta(hours=1)
        else:
            # Parse relative times (use IST as reference)
            reminder_time_lower = reminder_time.lower()
            now_ist = get_current_ist_time()
            
            if "in" in reminder_time_lower:
                # Parse "in X hour(s)", "in X minute(s)", "in X day(s)"
                time_value = 1
                
                # Extract number
                try:
                    words = reminder_time_lower.split()
                    for i, word in enumerate(words):
                        if word == "in" and i + 1 < len(words):
                            try:
                                time_value = int(words[i + 1])
                            except:
                                pass
                except:
                    pass
                
                # Determine unit (use IST time)
                if "minute" in reminder_time_lower:
                    reminder_datetime = now_ist + timedelta(minutes=time_value)
                elif "hour" in reminder_time_lower:
                    reminder_datetime = now_ist + timedelta(hours=time_value)
                elif "day" in reminder_time_lower:
                    reminder_datetime = now_ist + timedelta(days=time_value)
                else:
                    # Default to hours if no unit specified
                    reminder_datetime = now_ist + timedelta(hours=time_value)
            elif "tomorrow" in reminder_time_lower:
                tomorrow = now_ist + timedelta(days=1)
                if "9am" in reminder_time_lower or "morning" in reminder_time_lower:
                    reminder_datetime = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
                else:
                    reminder_datetime = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
            else:
                # Try to parse as ISO format string
                try:
                    parsed_dt = datetime.fromisoformat(reminder_time.replace('Z', '+00:00'))
                    # Convert to IST if timezone-aware, or localize if naive
                    if parsed_dt.tzinfo is None:
                        reminder_datetime = IST.localize(parsed_dt)
                    else:
                        reminder_datetime = parsed_dt.astimezone(IST)
                except:
                    # If parsing fails, use current IST time + 1 hour as fallback
                    reminder_datetime = now_ist + timedelta(hours=1)
        
        # Ensure reminder_datetime is timezone-aware in IST
        if reminder_datetime.tzinfo is None:
            reminder_datetime = IST.localize(reminder_datetime)
        else:
            # Convert to IST if it's in a different timezone
            reminder_datetime = reminder_datetime.astimezone(IST)
        
        # Create reminder in database
        # Note: reminder_text is not in schema, so we'll store it in a comment or skip it
        reminder_data = {
            "task_id": task_id,
            "reminder_time": reminder_datetime.isoformat(),  # Convert to ISO string for Supabase
            "notification_type": "in_app",
            "status": "pending"
        }
        
        # Insert into reminders table
        try:
            response = db_manager.supabase.client.table("reminders").insert(reminder_data).execute()
        except Exception as db_error:
            error_msg = str(db_error).lower()
            logger.error(f"Database error creating reminder: {str(db_error)}")
            
            # Check if reminders table exists
            if "does not exist" in error_msg or "not found" in error_msg or "schema cache" in error_msg:
                return {
                    "success": False,
                    "error": (
                        "⚠️ Reminders table not found in Supabase.\n\n"
                        "**Quick Fix (3 steps):**\n"
                        "1. Go to Supabase Dashboard → SQL Editor\n"
                        "2. Copy and run the SQL from `setup_reminders_table.sql` file\n"
                        "3. Restart your backend server\n\n"
                        "**Or use this SQL directly:**\n"
                        "```sql\n"
                        "CREATE TABLE IF NOT EXISTS reminders (\n"
                        "    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,\n"
                        "    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,\n"
                        "    reminder_time TIMESTAMP NOT NULL,\n"
                        "    notification_type VARCHAR(20) DEFAULT 'in_app',\n"
                        "    status VARCHAR(20) DEFAULT 'pending',\n"
                        "    created_at TIMESTAMP DEFAULT NOW()\n"
                        ");\n"
                        "CREATE INDEX IF NOT EXISTS idx_reminders_task_id ON reminders(task_id);\n"
                        "ALTER TABLE reminders ENABLE ROW LEVEL SECURITY;\n"
                        "CREATE POLICY \"Allow public access\" ON reminders\n"
                        "    FOR ALL USING (true) WITH CHECK (true);\n"
                        "```\n\n"
                        "See `QUICK_SETUP_REMINDERS.md` for detailed instructions."
                    )
                }
            
            # Check if task exists first
            try:
                task_check = db_manager.supabase.client.table("tasks").select("id").eq("id", task_id).execute()
                if not task_check.data:
                    return {
                        "success": False,
                        "error": f"Task with ID {task_id} not found. Please verify the task ID is correct. Use 'List all tasks' to see available task IDs."
                    }
            except:
                pass
            
            return {
                "success": False,
                "error": f"Database error: {str(db_error)}. Please check your Supabase configuration and ensure the reminders table exists."
            }
        
        if response.data:
            # Format reminder time in IST with DD/MM/YYYY and 12-hour format
            formatted_time = format_datetime_ist(reminder_datetime, format_type="full")
            
            return {
                "success": True,
                "message": f"✅ Reminder created! You'll be reminded at {formatted_time} (IST)",
                "reminder_id": response.data[0].get("id"),
                "reminder_time": reminder_datetime.isoformat(),  # Keep ISO format for database
                "reminder_time_formatted": formatted_time  # Human-readable IST format
            }
        else:
            return {
                "success": False,
                "error": "Failed to create reminder"
            }
    except Exception as e:
        logger.error(f"Error creating reminder: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to create reminder: {str(e)}"
        }

@tool
def list_reminders(task_id: Optional[str] = None) -> Dict[str, Any]:
    """
    List reminders for tasks. Use this when user wants to see reminders.
    
    Args:
        task_id: Optional task ID to filter reminders (UUID format). If provided, shows reminders only for that task.
                 If not provided, shows all reminders.
                 Can extract from user input like "[task_id: xxx]" or just UUID.
    
    Returns:
        Dictionary with "reminders" list and "count" of reminders found
        
    Examples:
        - "List reminders for task [task_id]" → list_reminders(task_id="[id]")
        - "List all reminders" → list_reminders()
        - "Show reminders" → list_reminders()
    """
    try:
        query = db_manager.supabase.client.table("reminders").select("*")
        if task_id:
            query = query.eq("task_id", task_id)
        
        response = query.execute()
        return {
            "reminders": response.data or [],
            "count": len(response.data) if response.data else 0
        }
    except Exception as e:
        logger.error(f"Error listing reminders: {str(e)}")
        return {"reminders": [], "count": 0, "error": str(e)}

