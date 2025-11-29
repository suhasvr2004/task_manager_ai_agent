from typing import List, Optional, Dict, Any
from datetime import datetime
from backend.models.schemas import TaskCreate, TaskUpdate, TaskResponse
from backend.database.client import DatabaseManager
from backend.config import get_settings
from loguru import logger

class TaskService:
    """Service layer for task management"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    async def create_task(self, task: TaskCreate) -> TaskResponse:
        """Create a new task - optimized"""
        try:
            # Only log in debug mode for performance
            if get_settings().DEBUG:
                logger.info(f"TaskService: Creating task '{task.title}'")
            task_data = task.model_dump()
            
            # Convert datetime objects to ISO format strings for JSON serialization
            if 'due_date' in task_data and task_data['due_date'] is not None:
                if isinstance(task_data['due_date'], datetime):
                    task_data['due_date'] = task_data['due_date'].isoformat()
            
            # Ensure estimated_hours is included even if 0
            if 'estimated_hours' not in task_data or task_data['estimated_hours'] is None:
                task_data['estimated_hours'] = 0.0
            
            result = await self.db_manager.supabase.create_task(task_data)
            
            if not result:
                logger.error("Database returned None for task creation")
                raise Exception("Task creation failed: No data returned from database")
            
            # Add to ChromaDB (non-blocking, don't fail task creation if this fails)
            try:
                content = f"{result['title']}. {result.get('description', '')}"
                # ChromaDB operations are synchronous but fast, so we run them directly
                # In production, consider using a background task queue for this
                self.db_manager.chroma.add_task_embedding(
                    result["id"],
                    content,
                    {"priority": result.get("priority", "medium"), "status": result.get("status", "pending")}
                )
            except Exception as chroma_error:
                # Log warning but don't fail the request - ChromaDB is optional for search
                logger.warning(f"Failed to add embedding to ChromaDB (non-critical): {chroma_error}")
            
            return result
        except Exception as e:
            logger.error(f"Error in TaskService.create_task: {str(e)}")
            raise
    
    async def get_task(self, task_id: str) -> Optional[TaskResponse]:
        """Get a specific task"""
        return await self.db_manager.supabase.get_task(task_id)
    
    async def list_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[TaskResponse]:
        """List tasks with optional filtering - normalizes priority/status to lowercase"""
        # Normalize status and priority to lowercase for case-insensitive matching
        if status:
            status = status.lower()
        if priority:
            priority = priority.lower()
        
        return await self.db_manager.supabase.list_tasks(
            status=status,
            priority=priority,
            limit=limit,
            offset=offset
        )
    
    async def update_task(self, task_id: str, task_update: TaskUpdate) -> Optional[TaskResponse]:
        """Update a task"""
        updates = task_update.model_dump(exclude_unset=True)
        
        # Convert datetime objects to ISO format strings for JSON serialization
        if 'due_date' in updates and updates['due_date'] is not None:
            if isinstance(updates['due_date'], datetime):
                updates['due_date'] = updates['due_date'].isoformat()
        
        result = await self.db_manager.supabase.update_task(task_id, updates)
        
        # Update ChromaDB (non-blocking)
        if result:
            try:
                content = f"{result['title']}. {result.get('description', '')}"
                self.db_manager.chroma.update_task_embedding(
                    task_id,
                    content,
                    {"priority": result.get("priority", "medium"), "status": result.get("status", "pending")}
                )
            except Exception as chroma_error:
                # Log warning but don't fail the update
                logger.warning(f"Failed to update ChromaDB embedding (non-critical): {chroma_error}")
        
        return result
    
    async def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        success = await self.db_manager.supabase.delete_task(task_id)
        if success:
            try:
                self.db_manager.chroma.delete_task_embedding(task_id)
            except Exception as chroma_error:
                # Log warning but don't fail the delete - ChromaDB cleanup is optional
                logger.warning(f"Failed to delete ChromaDB embedding (non-critical): {chroma_error}")
        return success
    
    def search_tasks(self, query: str) -> Dict[str, Any]:
        """Search tasks using semantic search"""
        return self.db_manager.chroma.search_tasks(query)

