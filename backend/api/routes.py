from fastapi import APIRouter, HTTPException, Query, Body, Response
from typing import List, Optional
from datetime import datetime
from functools import lru_cache
from backend.models.schemas import (
    TaskCreate, TaskResponse, TaskUpdate, TaskStatus, TaskPriority
)
from backend.services.task_service import TaskService
from backend.agents.task_agent import TaskManagerAgent
from backend.config import get_settings
from loguru import logger

router = APIRouter(prefix="/api/v1", tags=["tasks"])
task_service = TaskService()

# Lazy initialization of agent to avoid import-time errors
_agent = None
_db_manager = None

def get_agent():
    global _agent
    if _agent is None:
        _agent = TaskManagerAgent()
    return _agent

def get_db_manager():
    """Get or create database manager instance (singleton)"""
    global _db_manager
    if _db_manager is None:
        from backend.database.client import DatabaseManager
        _db_manager = DatabaseManager()
    return _db_manager

# Cache for frequently accessed data with TTL
_response_cache = {}

# ============================================================================
# TASK CRUD ENDPOINTS
# ============================================================================

@router.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_task(task: TaskCreate, response: Response) -> TaskResponse:
    """Create a new task"""
    try:
        result = await task_service.create_task(task)
        if not result:
            logger.error("Task creation returned None")
            raise HTTPException(status_code=500, detail="Task creation failed: No data returned from database")
        
        # Clear cache when new task is created
        _response_cache.clear()
        
        # Add cache control headers
        response.headers["Cache-Control"] = "no-cache"
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error creating task: {error_msg}")
        # Only log full traceback in debug mode
        if get_settings().DEBUG:
            logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    response: Response,
    status: Optional[TaskStatus] = Query(None),
    priority: Optional[TaskPriority] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0)
) -> List[TaskResponse]:
    """List all tasks with optional filtering - optimized with caching"""
    try:
        # Create cache key
        cache_key = f"tasks_{status}_{priority}_{limit}_{offset}"
        
        # Check cache (simple in-memory cache for frequently accessed data)
        # In production, use Redis or similar
        if cache_key in _response_cache:
            cached_data, cached_time = _response_cache[cache_key]
            # Cache for 5 seconds
            if (datetime.now().timestamp() - cached_time) < 5:
                response.headers["X-Cache"] = "HIT"
                return cached_data
        
        results = await task_service.list_tasks(
            status=status.value if status else None,
            priority=priority.value if priority else None,
            limit=limit,
            offset=offset
        )
        
        # Cache the results
        _response_cache[cache_key] = (results, datetime.now().timestamp())
        response.headers["X-Cache"] = "MISS"
        
        # Add cache control headers
        response.headers["Cache-Control"] = "public, max-age=5"
        
        return results
    except Exception as e:
        logger.error(f"Error listing tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str) -> TaskResponse:
    """Get a specific task"""
    # Validate UUID format
    import re
    uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    if not uuid_pattern.match(task_id):
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    
    result = await task_service.get_task(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return result

@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, task_update: TaskUpdate, response: Response) -> TaskResponse:
    """Update a task"""
    # Validate UUID format
    import re
    uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    if not uuid_pattern.match(task_id):
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    
    try:
        result = await task_service.update_task(task_id, task_update)
        if not result:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Clear cache when task is updated
        _response_cache.clear()
        response.headers["Cache-Control"] = "no-cache"
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task_id: str, response: Response):
    """Delete a task"""
    # Validate UUID format
    import re
    uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    if not uuid_pattern.match(task_id):
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    
    try:
        success = await task_service.delete_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Clear cache when task is deleted
        _response_cache.clear()
        response.headers["Cache-Control"] = "no-cache"
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# AI AGENT ENDPOINTS
# ============================================================================

@router.post("/agent/chat")
async def agent_chat(request: dict = Body(...)):
    """Chat with the AI Task Manager Agent"""
    try:
        message = request.get("message", "")
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Get conversation history if provided
        conversation_history = request.get("history", [])
        
        agent = get_agent()
        result = await agent.process_user_input(message, conversation_history=conversation_history)
        
        # Ensure we always return a proper response
        if result.get("status") == "error":
            logger.error(f"Agent error: {result.get('error')}")
            # Still return the result, but with proper status code
            return result
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in agent chat endpoint: {error_msg}")
        logger.exception("Full traceback:")
        return {
            "status": "error",
            "error": error_msg,
            "output": f"I encountered an error processing your request: {error_msg}",
            "timestamp": datetime.now().isoformat()
        }

@router.get("/agent/summary")
async def get_summary():
    """Get AI-generated task summary"""
    agent = get_agent()
    result = await agent.get_task_summary()
    return result

@router.get("/agent/next-task")
async def get_next_task():
    """Get AI recommendation for next task"""
    agent = get_agent()
    result = await agent.suggest_next_task()
    return result

# ============================================================================
# SEARCH ENDPOINT
# ============================================================================

@router.get("/search")
async def search_tasks(q: str = Query(..., min_length=1, max_length=200)):
    """Semantic search for tasks - optimized"""
    try:
        # Sanitize query
        query = q.strip()[:200]  # Limit length
        if not query:
            raise HTTPException(status_code=400, detail="Search query cannot be empty")
        
        results = task_service.search_tasks(query)
        return {"results": results, "query": query}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# ============================================================================
# NOTIFICATIONS ENDPOINTS
# ============================================================================

@router.get("/notifications")
async def get_notifications(
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    limit: int = Query(50, le=100, ge=1),
    offset: int = Query(0, ge=0)
):
    """Get all notifications - optimized query"""
    try:
        db_manager = get_db_manager()
        
        # Select only needed fields for better performance
        query = db_manager.supabase.client.table("notifications").select(
            "id,task_id,reminder_id,notification_type,title,message,notification_category,is_read,created_at"
        )
        
        if is_read is not None:
            query = query.eq("is_read", is_read)
        
        # Use index-friendly ordering
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        
        response = query.execute()
        notifications = response.data or []
        
        return {
            "notifications": notifications,
            "count": len(notifications),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error fetching notifications: {str(e)}")
        # If table doesn't exist, return empty list
        error_str = str(e).lower()
        if "does not exist" in error_str or "not found" in error_str or "schema cache" in error_str:
            return {
                "notifications": [],
                "count": 0,
                "message": "Notifications table not set up. Run setup_notifications_table.sql in Supabase."
            }
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notifications/unread")
async def get_unread_notifications():
    """Get unread notifications count - optimized query"""
    try:
        db_manager = get_db_manager()
        
        # Use count query for better performance
        response = db_manager.supabase.client.table("notifications").select(
            "id", count="exact"
        ).eq("is_read", False).execute()
        
        return {"unread_count": response.count or 0}
    except Exception as e:
        logger.warning(f"Error fetching unread count (table may not exist): {str(e)}")
        return {"unread_count": 0}

@router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    """Mark a notification as read"""
    try:
        # Validate UUID format
        import re
        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
        if not uuid_pattern.match(notification_id):
            raise HTTPException(status_code=400, detail="Invalid notification ID format")
        
        db_manager = get_db_manager()
        
        response = db_manager.supabase.client.table("notifications").update({
            "is_read": True
        }).eq("id", notification_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"success": True, "notification": response.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/notifications/{notification_id}")
async def delete_notification(notification_id: str):
    """Delete a notification"""
    try:
        # Validate UUID format
        import re
        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
        if not uuid_pattern.match(notification_id):
            raise HTTPException(status_code=400, detail="Invalid notification ID format")
        
        db_manager = get_db_manager()
        
        response = db_manager.supabase.client.table("notifications").delete().eq("id", notification_id).execute()
        
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))