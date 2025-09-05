from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from .models import TaskStatus

# Base schema (common fields)
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None

# For creating a new task
class TaskCreate(TaskBase):
    status: Optional[TaskStatus] = TaskStatus.pending

# For updating an existing task
class TaskUpdate(BaseModel):
    title: Optional[str]
    status: Optional[TaskStatus]

# For returning task data in responses
class TaskOut(TaskBase):
    id: UUID
    status: TaskStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True   # allows returning SQLAlchemy objects directly
