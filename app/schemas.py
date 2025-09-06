from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from .models import TaskStatus


# Base schema (common fields)
class TaskBase(BaseModel):
    model_config = ConfigDict(extra="forbid")  # ⛔ Forbid unexpected fields

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


# For creating a new task
class TaskCreate(TaskBase):
    status: Optional[TaskStatus] = TaskStatus.pending


# For updating an existing task
class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")  # ⛔ Forbid unexpected fields

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None


# For returning task data in responses
class TaskOut(TaskBase):
    id: UUID
    status: TaskStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True  # ✅ Allows returning SQLAlchemy objects directly


# For paginated tasks response
class PaginatedTasks(BaseModel):
    model_config = ConfigDict(extra="forbid")  # ⛔ Forbid unexpected fields

    items: List[TaskOut]
    page: int
    limit: int
    total: int
    pages: int
