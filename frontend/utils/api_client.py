"""Optimized API client with connection pooling and caching"""
import httpx
import os
from typing import Optional, Dict, Any
from functools import lru_cache
import time

# API configuration
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")
TIMEOUT = 30

# Create a persistent HTTP client for connection reuse
_http_client: Optional[httpx.Client] = None

def get_client() -> httpx.Client:
    """Get or create persistent HTTP client"""
    global _http_client
    if _http_client is None:
        _http_client = httpx.Client(
            base_url=API_URL,
            timeout=TIMEOUT,
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            http2=True  # Use HTTP/2 for better performance
        )
    return _http_client

class APIClient:
    """Optimized HTTP client for backend API with connection pooling"""
    
    def __init__(self, base_url: str = API_URL):
        self.base_url = base_url
        self._client = get_client()
        self._cache: Dict[str, tuple] = {}  # Simple in-memory cache
    
    def _get_cached(self, key: str, ttl: int = 5) -> Optional[Any]:
        """Get cached response if still valid"""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < ttl:
                return data
            else:
                del self._cache[key]
        return None
    
    def _set_cache(self, key: str, data: Any):
        """Cache response"""
        self._cache[key] = (data, time.time())
    
    def _clear_cache(self):
        """Clear all cached responses"""
        self._cache.clear()
    
    def create_task(self, task_data: dict):
        """Create a new task"""
        try:
            response = self._client.post(f"{self.base_url}/tasks", json=task_data)
            response.raise_for_status()
            
            # Clear cache when creating new task
            self._clear_cache()
            
            if response.text:
                return response.json()
            else:
                return {"error": "Empty response from server"}
        except httpx.HTTPStatusError as e:
            error_text = e.response.text if e.response.text else str(e)
            raise Exception(f"HTTP {e.response.status_code}: {error_text}")
        except httpx.RequestError as e:
            raise Exception(f"Request failed: {str(e)}. Is the backend server running?")
        except ValueError as e:
            raise Exception(f"Invalid response from server: {str(e)}")
    
    def list_tasks(self, status=None, priority=None):
        """List tasks with caching"""
        try:
            # Create cache key
            cache_key = f"tasks_{status}_{priority}"
            
            # Check cache first
            cached = self._get_cached(cache_key, ttl=5)
            if cached is not None:
                return cached
            
            params = {}
            if status:
                params["status"] = status
            if priority:
                params["priority"] = priority
            
            response = self._client.get(f"{self.base_url}/tasks", params=params)
            response.raise_for_status()
            
            if response.text:
                data = response.json()
                # Cache the response
                self._set_cache(cache_key, data)
                return data
            else:
                return []
        except httpx.HTTPStatusError as e:
            error_text = e.response.text if e.response.text else str(e)
            raise Exception(f"HTTP {e.response.status_code}: {error_text}")
        except httpx.RequestError as e:
            raise Exception(f"Request failed: {str(e)}. Is the backend server running?")
        except ValueError as e:
            raise Exception(f"Invalid response from server: {str(e)}")
    
    def get_task(self, task_id: str):
        """Get a specific task with caching"""
        try:
            # Check cache
            cache_key = f"task_{task_id}"
            cached = self._get_cached(cache_key, ttl=10)
            if cached is not None:
                return cached
            
            response = self._client.get(f"{self.base_url}/tasks/{task_id}")
            response.raise_for_status()
            
            if response.text:
                data = response.json()
                # Cache the response
                self._set_cache(cache_key, data)
                return data
            else:
                return {"error": "Empty response from server"}
        except httpx.HTTPStatusError as e:
            error_text = e.response.text if e.response.text else str(e)
            raise Exception(f"HTTP {e.response.status_code}: {error_text}")
        except httpx.RequestError as e:
            raise Exception(f"Request failed: {str(e)}. Is the backend server running?")
        except ValueError as e:
            raise Exception(f"Invalid response from server: {str(e)}")
    
    def update_task(self, task_id: str, updates: dict):
        """Update a task"""
        try:
            response = self._client.patch(f"{self.base_url}/tasks/{task_id}", json=updates)
            response.raise_for_status()
            
            # Clear cache for this task and list
            self._clear_cache()
            
            if response.text:
                return response.json()
            else:
                return {"error": "Empty response from server"}
        except httpx.HTTPStatusError as e:
            error_text = e.response.text if e.response.text else str(e)
            raise Exception(f"HTTP {e.response.status_code}: {error_text}")
        except httpx.RequestError as e:
            raise Exception(f"Request failed: {str(e)}. Is the backend server running?")
        except ValueError as e:
            raise Exception(f"Invalid response from server: {str(e)}")
    
    def delete_task(self, task_id: str):
        """Delete a task"""
        try:
            response = self._client.delete(f"{self.base_url}/tasks/{task_id}")
            response.raise_for_status()
            
            # Clear cache
            self._clear_cache()
            
            return True
        except httpx.HTTPStatusError as e:
            error_text = e.response.text if e.response.text else str(e)
            raise Exception(f"HTTP {e.response.status_code}: {error_text}")
        except httpx.RequestError as e:
            raise Exception(f"Request failed: {str(e)}. Is the backend server running?")
        except ValueError as e:
            raise Exception(f"Invalid response from server: {str(e)}")
    
    def agent_chat(self, message: str, history: list = None):
        """Chat with AI agent
        
        Args:
            message: User's message
            history: Optional conversation history as list of dicts with 'user' and 'assistant' keys
        """
        try:
            payload = {"message": message}
            if history:
                payload["history"] = history
            
            response = self._client.post(
                f"{self.base_url}/agent/chat",
                json=payload
            )
            response.raise_for_status()
            if response.text:
                return response.json()
            else:
                return {"error": "Empty response from server"}
        except httpx.HTTPStatusError as e:
            error_text = e.response.text if e.response.text else str(e)
            raise Exception(f"HTTP {e.response.status_code}: {error_text}")
        except httpx.RequestError as e:
            raise Exception(f"Request failed: {str(e)}. Is the backend server running?")
        except ValueError as e:
            raise Exception(f"Invalid response from server: {str(e)}")
    
    def get_summary(self):
        """Get task summary"""
        try:
            response = self._client.get(f"{self.base_url}/agent/summary")
            response.raise_for_status()
            if response.text:
                return response.json()
            else:
                return {"error": "Empty response from server"}
        except httpx.HTTPStatusError as e:
            error_text = e.response.text if e.response.text else str(e)
            raise Exception(f"HTTP {e.response.status_code}: {error_text}")
        except httpx.RequestError as e:
            raise Exception(f"Request failed: {str(e)}. Is the backend server running?")
        except ValueError as e:
            raise Exception(f"Invalid response from server: {str(e)}")
    
    def search_tasks(self, query: str):
        """Search tasks"""
        try:
            response = self._client.get(
                f"{self.base_url}/search",
                params={"q": query}
            )
            response.raise_for_status()
            if response.text:
                return response.json()
            else:
                return {"error": "Empty response from server"}
        except httpx.HTTPStatusError as e:
            error_text = e.response.text if e.response.text else str(e)
            raise Exception(f"HTTP {e.response.status_code}: {error_text}")
        except httpx.RequestError as e:
            raise Exception(f"Request failed: {str(e)}. Is the backend server running?")
        except ValueError as e:
            raise Exception(f"Invalid response from server: {str(e)}")
    
    def get_notifications(self, is_read: bool = None, limit: int = 50) -> Dict:
        """Get notifications"""
        try:
            params = {"limit": limit}
            if is_read is not None:
                params["is_read"] = is_read
            response = self._client.get(
                f"{self.base_url}/notifications",
                params=params,
                timeout=10.0
            )
            response.raise_for_status()
            if response.text:
                return response.json()
            else:
                return {"notifications": [], "count": 0}
        except Exception as e:
            return {"notifications": [], "count": 0}
    
    def get_unread_count(self) -> int:
        """Get unread notifications count"""
        try:
            response = self._client.get(
                f"{self.base_url}/notifications/unread",
                timeout=5.0
            )
            response.raise_for_status()
            if response.text:
                data = response.json()
                return data.get("unread_count", 0)
            return 0
        except Exception:
            return 0
    
    def mark_notification_read(self, notification_id: str) -> bool:
        """Mark a notification as read"""
        try:
            response = self._client.patch(
                f"{self.base_url}/notifications/{notification_id}/read",
                timeout=5.0
            )
            response.raise_for_status()
            return True
        except Exception:
            return False
    
    def delete_notification(self, notification_id: str) -> bool:
        """Delete a notification"""
        try:
            response = self._client.delete(
                f"{self.base_url}/notifications/{notification_id}",
                timeout=5.0
            )
            response.raise_for_status()
            return True
        except Exception:
            return False
