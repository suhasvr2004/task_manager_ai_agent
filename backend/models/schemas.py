from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = Field(None, ge=0, le=24, description="Estimated time in hours (can be fractional, e.g., 0.5 for 30 minutes, 1.5 for 1h 30m)")
    tags: List[str] = Field(default_factory=list)
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        return v.strip()

class TaskCreate(TaskBase):
    assigned_to: Optional[str] = None
    created_by: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    tags: Optional[List[str]] = None

class TaskResponse(TaskBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    assigned_to: Optional[str] = None

class ReminderSchema(BaseModel):
    task_id: str
    reminder_time: datetime
    notification_type: str = "email"  # email, sms, in_app
    status: str = "pending"  # pending, sent, failed

class CalendarEventSchema(BaseModel):
    task_id: str
    calendar_id: str
    event_id: str
    title: str
    start_time: datetime
    end_time: datetime
    synced_at: datetime

