from langchain_core.tools import tool, StructuredTool
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
from backend.database.client import DatabaseManager
from backend.models.schemas import TaskCreate, TaskPriority
from backend.services.task_service import TaskService
from loguru import logger

db_manager = DatabaseManager()
task_service = TaskService()

class CreateTaskInput(BaseModel):
    """Input schema for create_task tool"""
    title: str = Field(..., description="Task title (required) - the name of the task")
    description: Optional[str] = Field(None, description="Detailed task description")
    priority: str = Field("medium", description="Priority level: low, medium, high, or urgent")
    due_date: Optional[str] = Field(None, description="Due date in ISO format (e.g., '2024-01-15T10:30:00') or relative like 'today', 'tomorrow', 'evening', 'morning'")
    estimated_hours: Optional[float] = Field(None, description="Estimated time to complete in hours (can be fractional like 0.5 for 30 minutes)")
    tags: Optional[List[str]] = Field(None, description="List of tag strings for categorization")

def run_async(coro):
    """Helper to run async code from sync context - works with uvloop"""
    try:
        # Try to get the current event loop
        try:
            loop = asyncio.get_running_loop()
            # If we're in a running loop (uvloop), we need to run in a thread
            import concurrent.futures
            import threading
            
            # Create a new event loop in a separate thread
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(coro)
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result(timeout=30)  # 30 second timeout
        except RuntimeError:
            # No running loop, create one
            return asyncio.run(coro)
    except Exception as e:
        logger.error(f"Error in run_async: {str(e)}")
        # Fallback: try with nest_asyncio as last resort
        try:
            import nest_asyncio
            nest_asyncio.apply()
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(coro)
        except Exception as e2:
            logger.error(f"Fallback async execution also failed: {str(e2)}")
            raise

def _create_task_impl(
    title: str,
    description: Optional[str] = None,
    priority: str = "medium",
    due_date: Optional[str] = None,
    estimated_hours: Optional[float] = None,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Internal implementation of create_task.
    
    Creates a new task in the database with the provided parameters.
    """
    try:
        # Parse relative dates like "today", "tomorrow"
        parsed_due_date = due_date
        if due_date:
            due_date_lower = due_date.lower().strip()
            now = datetime.now()
            if due_date_lower == "today":
                parsed_due_date = now.replace(hour=18, minute=0, second=0, microsecond=0).isoformat()
            elif due_date_lower == "tomorrow":
                tomorrow = now + timedelta(days=1)
                parsed_due_date = tomorrow.replace(hour=18, minute=0, second=0, microsecond=0).isoformat()
            elif "evening" in due_date_lower or "tonight" in due_date_lower:
                parsed_due_date = now.replace(hour=20, minute=0, second=0, microsecond=0).isoformat()
            elif "morning" in due_date_lower:
                tomorrow = now + timedelta(days=1) if now.hour >= 12 else now
                parsed_due_date = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0).isoformat()
        
        # Create TaskCreate object for validation
        task_priority = TaskPriority.MEDIUM
        if priority.lower() == "high":
            task_priority = TaskPriority.HIGH
        elif priority.lower() == "urgent":
            task_priority = TaskPriority.URGENT
        elif priority.lower() == "low":
            task_priority = TaskPriority.LOW
        
        # Parse due_date to datetime if provided
        due_date_obj = None
        if parsed_due_date:
            try:
                # Handle ISO format with or without timezone
                if 'Z' in parsed_due_date:
                    due_date_obj = datetime.fromisoformat(parsed_due_date.replace('Z', '+00:00'))
                elif '+' in parsed_due_date or parsed_due_date.count('-') >= 3:
                    due_date_obj = datetime.fromisoformat(parsed_due_date)
                else:
                    # Try parsing as simple ISO format
                    due_date_obj = datetime.fromisoformat(parsed_due_date)
            except Exception as e:
                logger.warning(f"Could not parse due_date '{parsed_due_date}': {e}")
                due_date_obj = None
        
        task_create = TaskCreate(
            title=title,
            description=description,
            priority=task_priority,
            due_date=due_date_obj,
            estimated_hours=estimated_hours,
            tags=tags or [],
            created_by=None  # Let database client generate UUID
        )
        
        # Use task service to create task
        result = run_async(task_service.create_task(task_create))
        
        if result and result.get("id"):
            logger.info(f"Task created successfully: ID={result['id']}, Title={result.get('title')}, Status={result.get('status')}, Priority={result.get('priority')}")
            return {
                "success": True,
                "task_id": result["id"],
                "title": result.get("title"),
                "status": result.get("status", "pending"),
                "priority": result.get("priority", "medium"),
                "message": f"✅ Task '{title}' created successfully! ID: {result['id']}. Status: {result.get('status', 'pending')}, Priority: {result.get('priority', 'medium')}"
            }
        else:
            logger.error(f"Task creation returned no data. Result: {result}")
            return {
                "success": False,
                "error": "Task creation failed: No data returned from database"
            }
    except Exception as e:
        logger.error(f"Error in create_task tool: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": f"Failed to create task: {str(e)}"
        }

# Create the tool with explicit schema for better Gemini compatibility
create_task = StructuredTool.from_function(
    func=_create_task_impl,
    name="create_task",
    description="Create a new task in the database. Provide title (required), description, priority (low/medium/high/urgent), due_date (ISO format or 'today'/'tomorrow'), estimated_hours, and tags.",
    args_schema=CreateTaskInput,
    return_direct=False
)

@tool
def get_task(task_id: str) -> Dict[str, Any]:
    """Get a specific task by ID"""
    try:
        result = run_async(db_manager.supabase.get_task(task_id))
        return result or {"error": "Task not found"}
    except Exception as e:
        logger.error(f"Error in get_task tool: {str(e)}")
        return {"error": f"Failed to get task: {str(e)}"}

@tool
def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    List all tasks with optional filtering. Use this tool when user asks to "list", "show", "display", "get all", or "find" tasks.
    
    CRITICAL: This tool is ONLY for LISTING/VIEWING existing tasks. NEVER use this to create tasks.
    
    Args:
        status: Filter by status (pending, in_progress, completed, archived). Case-insensitive. Examples: "pending", "PENDING", "Pending" all work.
        priority: Filter by priority (low, medium, high, urgent). Case-insensitive. Examples: "high", "HIGH", "High", "urgent" all work.
        limit: Maximum number of results (default: 50, max: 100)
    
    Returns:
        List of task dictionaries with full details including: id, title, description, priority, status, due_date, estimated_hours, tags, created_at, updated_at
        
    Examples:
        - "List all high priority tasks" → list_tasks(priority="high")
        - "Show me pending tasks" → list_tasks(status="pending")
        - "Display all urgent tasks" → list_tasks(priority="urgent")
        - "List all tasks" → list_tasks()
        - "Show me tasks due today" → list_tasks() then filter by due_date in response
    """
    try:
        # Normalize priority to lowercase for case-insensitive matching
        normalized_priority = priority.lower() if priority else None
        normalized_status = status.lower() if status else None
        
        results = run_async(db_manager.supabase.list_tasks(
            status=normalized_status,
            priority=normalized_priority,
            limit=limit
        ))
        return results or []
    except Exception as e:
        logger.error(f"Error in list_tasks tool: {str(e)}")
        return []

@tool
def update_task(
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    due_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update task fields. Use this when user wants to change task properties.
    
    Args:
        task_id: UUID of the task to update (REQUIRED). Can extract from user input like "[task_id: xxx]" or just UUID.
        title: New title (optional)
        description: New description (optional)
        status: New status - must be one of: "pending", "in_progress", "completed", "archived" (optional)
        priority: New priority - must be one of: "low", "medium", "high", "urgent" (optional, lowercase)
        due_date: New due date in ISO format or relative like "today", "tomorrow" (optional)
    
    Returns:
        Updated task dictionary with all fields
        
    Examples:
        - "Update task [task_id] status to in_progress" → update_task(task_id="[id]", status="in_progress")
        - "Update task [task_id] priority to urgent" → update_task(task_id="[id]", priority="urgent")
        - "Change task [task_id] to completed" → update_task(task_id="[id]", status="completed")
    """
    try:
        from backend.models.schemas import TaskUpdate
        
        updates = {}
        if title: updates["title"] = title
        if description is not None: updates["description"] = description
        if status: updates["status"] = status
        if priority: updates["priority"] = priority
        if due_date: updates["due_date"] = due_date
        
        task_update = TaskUpdate(**updates)
        result = run_async(task_service.update_task(task_id, task_update))
        
        if result:
            return {
                "success": True,
                "message": f"Task updated successfully",
                "task": result
            }
        else:
            return {"error": "Failed to update task: Task not found"}
    except Exception as e:
        logger.error(f"Error in update_task tool: {str(e)}")
        return {"error": f"Failed to update task: {str(e)}"}

@tool
def delete_task(task_id: str) -> Dict[str, str]:
    """Delete a task by ID"""
    try:
        result = run_async(task_service.delete_task(task_id))
        return {
            "success": result,
            "message": "Task deleted successfully" if result else "Failed to delete task",
            "task_id": task_id
        }
    except Exception as e:
        logger.error(f"Error in delete_task tool: {str(e)}")
        return {"success": False, "error": f"Failed to delete task: {str(e)}"}

@tool
def search_tasks(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search tasks by semantic meaning using AI embeddings. Use this when user wants to find tasks by keywords, topics, or tags.
    Returns full task details including Task IDs.
    
    Args:
        query: Natural language search query (e.g., "personal tasks", "work related", "code review", "meetings", "work tag")
        max_results: Maximum results to return (default: 10, max: 50)
    
    Returns:
        List of task dictionaries with FULL details: id, title, description, priority, status, due_date, tags, etc.
        ALWAYS display all returned tasks with their Task IDs prominently.
    
    Examples:
        - "Search for tasks about code review" → search_tasks(query="code review")
        - "Find tasks with tag 'work'" → search_tasks(query="work tag")
        - "Show me all tasks related to meetings" → search_tasks(query="meetings")
        - "Find personal tasks" → search_tasks(query="personal tasks")
    """
    try:
        # Expand short queries to improve semantic search
        expanded_query = query
        if len(query.split()) <= 2:
            # For short queries like "personal", expand with context
            expanded_query = f"tasks related to {query} or about {query}"
        
        # Perform semantic search
        chroma_results = db_manager.chroma.search_tasks(expanded_query, max_results)
        
        task_ids = chroma_results["ids"][0] if chroma_results["ids"] else []
        
        if not task_ids:
            # Fallback: try direct text search in Supabase if semantic search returns nothing
            logger.info(f"Semantic search returned no results, trying text search for: {query}")
            all_tasks = run_async(db_manager.supabase.list_tasks(limit=100))
            
            # Simple text matching as fallback
            query_lower = query.lower()
            matching_tasks = []
            for task in all_tasks:
                title = (task.get("title") or "").lower()
                description = (task.get("description") or "").lower()
                tags = [tag.lower() for tag in (task.get("tags") or [])]
                
                if (query_lower in title or 
                    query_lower in description or 
                    any(query_lower in tag for tag in tags)):
                    matching_tasks.append(task)
                    if len(matching_tasks) >= max_results:
                        break
            
            return matching_tasks if matching_tasks else []
        
        # Fetch full task details for each ID
        tasks = []
        for task_id in task_ids:
            try:
                task = run_async(db_manager.supabase.get_task(task_id))
                if task:
                    tasks.append(task)
            except Exception as e:
                logger.warning(f"Could not fetch task {task_id}: {e}")
                continue
        
        logger.info(f"Search for '{query}' returned {len(tasks)} tasks")
        return tasks
        
    except Exception as e:
        logger.error(f"Error in search_tasks tool: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return []