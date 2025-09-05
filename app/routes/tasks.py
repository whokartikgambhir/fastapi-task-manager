from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import schemas, crud, db

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=schemas.TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(task: schemas.TaskCreate, db: Session = Depends(db.get_db)):
    return crud.create_task(db, task)


@router.get("/", response_model=schemas.PaginatedTasks)
def get_tasks(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(db.get_db),
):
    skip = (page - 1) * limit
    items = crud.list_tasks(db, skip=skip, limit=limit)
    total = crud.count_tasks(db)
    pages = (total + limit - 1) // limit if total else 0
    return {"items": items, "page": page, "limit": limit, "total": total, "pages": pages}


@router.get("/{task_id}", response_model=schemas.TaskOut)
def get_task(task_id: UUID, db: Session = Depends(db.get_db)):
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=schemas.TaskOut)
def update_task(task_id: UUID, payload: schemas.TaskUpdate, db: Session = Depends(db.get_db)):
    task = crud.update_task(db, task_id, payload)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}", status_code=status.HTTP_200_OK)
def delete_task(task_id: UUID, db: Session = Depends(db.get_db)):
    deleted = crud.delete_task(db, task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}
