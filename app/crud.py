from typing import List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models, schemas

def create_task(db: Session, payload: schemas.TaskCreate) -> models.Task:
    task = models.Task(**payload.dict())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def get_task(db: Session, task_id: UUID) -> Optional[models.Task]:
    return db.query(models.Task).filter(models.Task.id == task_id).first()

def list_tasks(db: Session, skip: int = 0, limit: int = 10) -> List[models.Task]:
    return (
        db.query(models.Task)
        .order_by(models.Task.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

def count_tasks(db: Session) -> int:
    return db.query(func.count(models.Task.id)).scalar() or 0

def update_task(db: Session, task_id: UUID, payload: schemas.TaskUpdate) -> Optional[models.Task]:
    task = get_task(db, task_id)
    if not task:
        return None
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(task, k, v)
    db.commit()
    db.refresh(task)
    return task

def delete_task(db: Session, task_id: UUID) -> Optional[models.Task]:
    task = get_task(db, task_id)
    if not task:
        return None
    db.delete(task)
    db.commit()
    return task
