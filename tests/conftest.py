"""Pytest configuration and fixtures"""
import pytest
import sys
import os
from typing import Generator

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.config import get_settings
from backend.models.schemas import TaskCreate, TaskPriority
from backend.database.client import DatabaseManager


@pytest.fixture
def settings():
    """Get application settings"""
    return get_settings()


@pytest.fixture
def db_manager():
    """Get database manager instance"""
    return DatabaseManager()


@pytest.fixture
def sample_task_data():
    """Sample task data for testing"""
    return {
        "title": "Test Task",
        "description": "This is a test task",
        "priority": TaskPriority.MEDIUM,
        "estimated_hours": 1.5,
        "tags": ["test", "pytest"]
    }


@pytest.fixture
def sample_task_create(sample_task_data):
    """Create a TaskCreate instance"""
    return TaskCreate(**sample_task_data)

