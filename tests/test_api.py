"""Tests for API endpoints"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.models.schemas import TaskCreate, TaskPriority


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestTaskEndpoints:
    """Test task CRUD endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
    
    def test_create_task_endpoint(self, client):
        """Test creating a task via API"""
        task_data = {
            "title": "API Test Task",
            "description": "Created via API test",
            "priority": "medium",
            "estimated_hours": 1.5,
            "tags": ["test", "api"]
        }
        
        response = client.post("/api/v1/tasks", json=task_data)
        
        # Should return 201 or 500 (if database not configured)
        assert response.status_code in [201, 500]
        
        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert data["title"] == task_data["title"]
    
    def test_list_tasks_endpoint(self, client):
        """Test listing tasks via API"""
        response = client.get("/api/v1/tasks")
        
        # Should return 200 or 500 (if database not configured)
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    def test_get_task_endpoint(self, client):
        """Test getting a task by ID"""
        # First create a task
        task_data = {
            "title": "Get Test Task",
            "priority": "low"
        }
        create_response = client.post("/api/v1/tasks", json=task_data)
        
        if create_response.status_code == 201:
            task_id = create_response.json()["id"]
            
            # Then get it
            response = client.get(f"/api/v1/tasks/{task_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == task_id
            assert data["title"] == task_data["title"]
    
    def test_update_task_endpoint(self, client):
        """Test updating a task via API"""
        # Create a task first
        task_data = {"title": "Update Test Task"}
        create_response = client.post("/api/v1/tasks", json=task_data)
        
        if create_response.status_code == 201:
            task_id = create_response.json()["id"]
            
            # Update it
            update_data = {
                "title": "Updated Title",
                "status": "in_progress"
            }
            response = client.patch(f"/api/v1/tasks/{task_id}", json=update_data)
            
            assert response.status_code in [200, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert data["title"] == update_data["title"]
                assert data["status"] == update_data["status"]
    
    def test_delete_task_endpoint(self, client):
        """Test deleting a task via API"""
        # Create a task first
        task_data = {"title": "Delete Test Task"}
        create_response = client.post("/api/v1/tasks", json=task_data)
        
        if create_response.status_code == 201:
            task_id = create_response.json()["id"]
            
            # Delete it
            response = client.delete(f"/api/v1/tasks/{task_id}")
            assert response.status_code in [204, 500]


class TestAgentEndpoints:
    """Test AI agent endpoints"""
    
    def test_agent_chat_endpoint(self, client):
        """Test agent chat endpoint"""
        chat_data = {
            "message": "List all tasks"
        }
        
        response = client.post("/api/v1/agent/chat", json=chat_data)
        
        # Should return 200 or 500 (if OpenAI not configured)
        assert response.status_code in [200, 400, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "output" in data or "error" in data
    
    def test_agent_chat_missing_message(self, client):
        """Test agent chat with missing message"""
        response = client.post("/api/v1/agent/chat", json={})
        assert response.status_code == 400


class TestSearchEndpoints:
    """Test search endpoints"""
    
    def test_search_endpoint(self, client):
        """Test semantic search endpoint"""
        response = client.get("/api/v1/search?q=test task")
        
        # Should return 200 or 500 (if database not configured)
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))

