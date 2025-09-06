import logging, sys, uuid, contextvars
from logging.config import dictConfig
from pythonjsonlogger import jsonlogger

# Per-request correlation id
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")

class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True

def setup_logging():
    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_id": {"()": RequestIdFilter},
        },
        "formatters": {
            "console": {
                "format": "%(asctime)s %(levelname)s %(name)s [req=%(request_id)s] %(message)s"
            },
            "json": {
                "()": jsonlogger.JsonFormatter,
                "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(pathname)s %(lineno)d",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "console",
                "filters": ["request_id"],
            },
            "json": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "json",
                "filters": ["request_id"],
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["console"], "level": "INFO", "propagate": False},
            "uvicorn.access": {"handlers": ["console"], "level": "INFO", "propagate": False},
            "sqlalchemy.engine": {"handlers": ["console"], "level": "WARNING", "propagate": False},
            "app": {"handlers": ["console"], "level": "INFO", "propagate": False},
        },
        "root": {"handlers": ["console"], "level": "INFO"},
    })
