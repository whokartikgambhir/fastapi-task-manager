from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from sqlalchemy import text
import time
from datetime import datetime, timezone

from .db import get_db
from .routes import tasks

app = FastAPI(title="Task Management System", version="1.0.0")

# Track process start and stable uptime (monotonic not affected by clock changes)
STARTED_AT = datetime.now(timezone.utc)
BOOT_MONOTONIC = time.monotonic()


def _format_duration(seconds: float) -> str:
    """Return a compact human-readable duration like '1d 2h 3m 4s'."""
    total = int(seconds)
    days, rem = divmod(total, 86_400)
    hours, rem = divmod(rem, 3_600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    if minutes or hours or days:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


# Register routers
app.include_router(tasks.router)

# Health check (DB connectivity + uptime)
@app.get("/health")
def health(db: Session = Depends(get_db)):
    uptime_seconds = time.monotonic() - BOOT_MONOTONIC
    payload = {
        "status": "healthy",  # may be flipped below if DB check fails
        "uptime_seconds": _format_duration(uptime_seconds),
        "started_at": STARTED_AT.isoformat(),
        "version": app.version,
        "database": {"status": "up"},
    }
    try:
        db.execute(text("SELECT 1"))
        return payload
    except Exception as e:
        payload["status"] = "unhealthy"
        payload["database"] = {"status": "down", "error": str(e)}
        return JSONResponse(status_code=503, content=payload)

# Validation error handler -> 422
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "message": "Validation failed"},
    )

# Catch-all for unexpected errors -> 500
@app.middleware("http")
async def add_error_handling(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"message": "Internal server error"},
        )
