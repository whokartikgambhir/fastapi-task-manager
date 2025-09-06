from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..db import get_db

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/live")
def liveness():
    # process is up; cheap check for k8s/docker healthchecks
    return {"status": "ok"}

@router.get("/ready")
def readiness(db: Session = Depends(get_db)):
    # verify DB connectivity
    db.execute(text("SELECT 1"))
    return {"status": "ready"}
