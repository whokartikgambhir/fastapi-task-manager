import time, logging, uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from .logging_config import request_id_ctx

log = logging.getLogger("app")

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("x-request-id") or str(uuid.uuid4())
        token = request_id_ctx.set(rid)
        start = time.perf_counter()
        try:
            response = await call_next(request)
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
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
            request_id_ctx.reset(token)
