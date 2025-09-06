from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from sqlalchemy import text
import time
from datetime import datetime, timezone
import logging
import uuid
from prometheus_fastapi_instrumentator import Instrumentator

from .logging_config import setup_logging, request_id_ctx
from .db import get_db
from .routes import tasks, health

# ---- initialize logging early ----
setup_logging()
log = logging.getLogger("app")

# ---- app & routers ----
app = FastAPI(title="Task Management System", version="1.0.0")
app.include_router(health.router)  # e.g., /health/live and /health/ready
app.include_router(tasks.router)

# ---- metrics (/metrics) ----
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# ---- uptime tracking ----
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


# ---- single middleware: request id + access log + 500 fallback ----
@app.middleware("http")
async def request_context_and_access_log(request: Request, call_next):
    # correlate with incoming header if present
    rid = request.headers.get("x-request-id") or str(uuid.uuid4())
    token = request_id_ctx.set(rid)
    start = time.perf_counter()
    response = None
    try:
        response = await call_next(request)
    except Exception:
        log.exception("unhandled_exception", extra={"path": str(request.url)})
        response = JSONResponse(status_code=500, content={"message": "Internal server error"})
    finally:
        duration_ms = (time.perf_counter() - start) * 1000.0
        log.info(
            "http_access",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": getattr(response, "status_code", 0),
                "duration_ms": round(duration_ms, 2),
                "client_ip": request.client.host if request.client else "-",
                "ua": request.headers.get("user-agent", "-"),
            },
        )
        # propagate request id back to client
        try:
            response.headers["x-request-id"] = rid
        except Exception:
            pass
        request_id_ctx.reset(token)
    return response


# ---- health summary at /health (readiness + uptime + DB check) ----
@app.get("/health")
def health_root(db: Session = Depends(get_db)):
    uptime_seconds = time.monotonic() - BOOT_MONOTONIC
    payload = {
        "status": "healthy",
        "uptime": _format_duration(uptime_seconds),
        "uptime_seconds": int(uptime_seconds),
        "started_at": STARTED_AT.isoformat(),
        "version": app.version,
        "database": {"status": "up"},
    }
    try:
        db.execute(text("SELECT 1"))
        return payload
    except Exception as e:
        log.error("health_db_down", extra={"error": repr(e)})
        payload["status"] = "unhealthy"
        payload["database"] = {"status": "down", "error": str(e)}
        return JSONResponse(status_code=503, content=payload)


# ---- validation error handler -> 422 ----
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    log.warning("validation_failed", extra={"path": request.url.path, "errors": exc.errors()})
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "message": "Validation failed"},
    )
