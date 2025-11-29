from typing import List, Optional, Dict, Any
from supabase import create_client
import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger
import uuid
from datetime import datetime
import warnings

class SupabaseClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'client'):
            from backend.config import get_settings
            
            # Suppress Supabase deprecation warnings (from library, not our code)
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=DeprecationWarning, module="supabase")
                settings = get_settings()
                self.client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_API_KEY
                )
            self.db_name = settings.SUPABASE_DB_NAME
            logger.info("Supabase client initialized")
    
    async def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create task in Supabase"""
        # Add ID and timestamps if not present
        if 'id' not in task_data:
            task_data['id'] = str(uuid.uuid4())
        if 'created_at' not in task_data:
            task_data['created_at'] = datetime.now().isoformat()
        if 'updated_at' not in task_data:
            task_data['updated_at'] = datetime.now().isoformat()
        
        # Ensure created_by is set (use a default UUID if not provided)
        if 'created_by' not in task_data or not task_data['created_by']:
            task_data['created_by'] = str(uuid.uuid4())  # Generate a default UUID
        
        # Convert any remaining datetime objects to ISO strings
        for key, value in task_data.items():
            if isinstance(value, datetime):
                task_data[key] = value.isoformat()
        
        # Filter None values but keep description (can be None) and estimated_hours (can be 0)
        filtered_data = {}
        for k, v in task_data.items():
            if v is not None:
                filtered_data[k] = v
            elif k == 'description':  # description can be None
                filtered_data[k] = v
            elif k == 'estimated_hours' and v == 0:  # estimated_hours can be 0 (for minutes-only tasks)
                filtered_data[k] = v
        
        task_data = filtered_data
        
        try:
            response = self.client.table("tasks").insert(task_data).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            else:
                error_msg = f"No data returned from Supabase insert. Response: {response}"
                logger.error(error_msg)
                # Check if it's an RLS policy issue
                if hasattr(response, 'error') and response.error:
                    if 'policy' in str(response.error).lower() or 'row level security' in str(response.error).lower():
                        raise Exception(f"Database permission error. Please check Row Level Security policies in Supabase. Original error: {response.error}")
                raise Exception("No data returned from database. Check if the 'tasks' table exists and RLS policies are configured.")
        except Exception as e:
            error_str = str(e)
            logger.error(f"Error inserting task into Supabase: {error_str}")
            logger.error(f"Task data: {task_data}")
            
            # Provide helpful error messages
            if 'relation' in error_str.lower() or 'does not exist' in error_str.lower():
                raise Exception("The 'tasks' table does not exist in Supabase. Please run the SQL schema from supabase_schema.sql in your Supabase SQL Editor.")
            elif 'policy' in error_str.lower() or 'row level security' in error_str.lower() or 'permission' in error_str.lower():
                raise Exception("Database permission error. Please check Row Level Security (RLS) policies in Supabase. Make sure public access policy is enabled.")
            elif 'violates' in error_str.lower() or 'constraint' in error_str.lower():
                raise Exception(f"Data validation error: {error_str}. Check that all required fields are provided and data types are correct.")
            else:
                raise Exception(f"Database error: {error_str}")
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve single task - optimized query"""
        # Select only needed fields
        response = self.client.table("tasks").select(
            "id,title,description,priority,status,due_date,estimated_hours,tags,created_at,updated_at,created_by"
        ).eq("id", task_id).execute()
        return response.data[0] if response.data else None
    
    async def list_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List tasks with optional filters - optimized query with proper indexing"""
        # Select only needed fields for better performance
        query = self.client.table("tasks").select(
            "id,title,description,priority,status,due_date,estimated_hours,tags,created_at,updated_at,created_by"
        )
        
        # Apply filters (use indexed columns)
        if status:
            # Normalize status to lowercase for case-insensitive matching
            # Status column is indexed
            query = query.eq("status", status.lower())
        if priority:
            # Normalize priority to lowercase for case-insensitive matching
            # Priority column is indexed
            query = query.eq("priority", priority.lower())
        
        # Use index-friendly ordering (created_at is indexed)
        # Use range for pagination (more efficient than limit/offset)
        try:
            response = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error listing tasks: {str(e)}")
            # Fallback to basic query if range fails
            response = query.order("created_at", desc=True).limit(limit).execute()
            return response.data or []
    
    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update task - optimized with validation"""
        if not updates:
            logger.warning("Update called with empty updates dict")
            return None
        
        # Always update the updated_at timestamp
        updates['updated_at'] = datetime.now().isoformat()
        
        # Convert any datetime objects to ISO strings
        for key, value in updates.items():
            if isinstance(value, datetime):
                updates[key] = value.isoformat()
        
        try:
            response = self.client.table("tasks").update(updates).eq(
                "id", task_id
            ).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating task {task_id}: {str(e)}")
            raise
    
    async def delete_task(self, task_id: str) -> bool:
        """Delete task"""
        response = self.client.table("tasks").delete().eq("id", task_id).execute()
        return True

class ChromaDBClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'client'):
            from backend.config import get_settings
            settings = get_settings()
            self.settings = settings
            self.client = chromadb.PersistentClient(
                path=settings.CHROMADB_PERSIST_DIR
            )
            self.collection = self.client.get_or_create_collection(
                name=settings.CHROMADB_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("ChromaDB client initialized")
    
    def add_task_embedding(
        self,
        task_id: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Add task embedding to ChromaDB"""
        self.collection.add(
            ids=[task_id],
            documents=[content],
            metadatas=[metadata]
        )
    
    def search_tasks(
        self,
        query: str,
        n_results: int = 10
    ) -> Dict[str, Any]:
        """Search tasks by semantic similarity"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results
    
    def update_task_embedding(
        self,
        task_id: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Update task embedding"""
        self.collection.update(
            ids=[task_id],
            documents=[content],
            metadatas=[metadata]
        )
    
    def delete_task_embedding(self, task_id: str) -> None:
        """Delete task embedding"""
        self.collection.delete(ids=[task_id])

class DatabaseManager:
    """Unified database manager combining Supabase and ChromaDB"""
    
    def __init__(self):
        self.supabase = SupabaseClient()
        self.chroma = ChromaDBClient()
    
    async def initialize_schema(self) -> None:
        """Initialize database schema - Ensure tables exist"""
        try:
            # Check if reminders table exists by trying to query it
            try:
                self.supabase.client.table("reminders").select("id").limit(1).execute()
                logger.info("Reminders table exists")
            except Exception as e:
                error_msg = str(e).lower()
                if "does not exist" in error_msg or "not found" in error_msg or "schema cache" in error_msg:
                    logger.warning("Reminders table not found. Please run the SQL schema from supabase_schema.sql in your Supabase SQL Editor.")
                    logger.warning("The reminders table needs to be created manually in Supabase.")
                else:
                    logger.error(f"Error checking reminders table: {e}")
            
            logger.info("Database schema check complete")
        except Exception as e:
            logger.error(f"Error initializing schema: {e}")