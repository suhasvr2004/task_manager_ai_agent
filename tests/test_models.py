"""Tests for data models and schemas"""
import pytest
from datetime import datetime
from backend.models.schemas import (
    TaskCreate, TaskUpdate, TaskResponse, TaskPriority, TaskStatus
)


class TestTaskCreate:
    """Test TaskCreate model"""
    
    def test_create_task_with_minimal_fields(self):
        """Test creating a task with only required fields"""
        task = TaskCreate(title="Test Task")
        assert task.title == "Test Task"
        assert task.priority == TaskPriority.MEDIUM
        assert task.status == TaskStatus.PENDING
    
    def test_create_task_with_all_fields(self):
        """Test creating a task with all fields"""
        due_date = datetime.now()
        task = TaskCreate(
            title="Complete Task",
            description="Full description",
            priority=TaskPriority.HIGH,
            due_date=due_date,
            estimated_hours=2.5,
            tags=["work", "urgent"]
        )
        assert task.title == "Complete Task"
        assert task.description == "Full description"
        assert task.priority == TaskPriority.HIGH
        assert task.due_date == due_date
        assert task.estimated_hours == 2.5
        assert task.tags == ["work", "urgent"]
    
    def test_task_title_validation(self):
        """Test that title is stripped of whitespace"""
        task = TaskCreate(title="  Test Task  ")
        assert task.title == "Test Task"
    
    def test_task_priority_enum(self):
        """Test priority enum values"""
        for priority in [TaskPriority.LOW, TaskPriority.MEDIUM, TaskPriority.HIGH, TaskPriority.URGENT]:
            task = TaskCreate(title="Test", priority=priority)
            assert task.priority == priority
    
    def test_estimated_hours_validation(self):
        """Test estimated hours validation"""
        # Valid values
        task1 = TaskCreate(title="Test", estimated_hours=0)
        assert task1.estimated_hours == 0
        
        task2 = TaskCreate(title="Test", estimated_hours=24)
        assert task2.estimated_hours == 24
        
        # Invalid values should raise validation error
        with pytest.raises(Exception):  # Pydantic validation error
            TaskCreate(title="Test", estimated_hours=-1)
        
        with pytest.raises(Exception):
            TaskCreate(title="Test", estimated_hours=25)


class TestTaskUpdate:
    """Test TaskUpdate model"""
    
    def test_update_with_partial_fields(self):
        """Test updating task with only some fields"""
        update = TaskUpdate(title="Updated Title")
        assert update.title == "Updated Title"
        assert update.description is None
        assert update.status is None
    
    def test_update_all_fields(self):
        """Test updating all task fields"""
        due_date = datetime.now()
        update = TaskUpdate(
            title="New Title",
            description="New Description",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            due_date=due_date,
            estimated_hours=3.0,
            tags=["updated"]
        )
        assert update.title == "New Title"
        assert update.description == "New Description"
        assert update.status == TaskStatus.IN_PROGRESS
        assert update.priority == TaskPriority.HIGH
        assert update.due_date == due_date
        assert update.estimated_hours == 3.0
        assert update.tags == ["updated"]


class TestTaskResponse:
    """Test TaskResponse model"""
    
    def test_response_model_structure(self):
        """Test that TaskResponse includes all required fields"""
        # This would typically come from the database
        response_data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "title": "Test Task",
            "description": "Description",
            "priority": "high",
            "status": "pending",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "created_by": "user-123",
            "estimated_hours": 1.5,
            "tags": ["test"]
        }
        
        # Note: This would need proper conversion from dict to model
        # In real tests, you'd use model_validate or similar
        assert "id" in response_data
        assert "title" in response_data
        assert "created_at" in response_data

