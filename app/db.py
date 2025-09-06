import os
import time
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Setup Logging
logger = logging.getLogger("app.db")
logger.setLevel(logging.INFO)

# Load environment variables from .env
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in .env file")

# SQLAlchemy Engine Setup
# echo=True enables SQLAlchemy's built-in SQL logging (only enable in dev)
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# Monitor & Log Slow Queries
SLOW_QUERY_THRESHOLD_MS = 200  # log queries slower than 200ms

@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """
    Attach start time before executing each query.
    """
    conn.info.setdefault("query_start_time", []).append(time.perf_counter())

@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """
    Log queries that exceed the SLOW_QUERY_THRESHOLD_MS.
    """
    start_time = conn.info["query_start_time"].pop(-1)
    total_ms = (time.perf_counter() - start_time) * 1000

    if total_ms >= SLOW_QUERY_THRESHOLD_MS:
        logger.warning(
            "Slow query detected",
            extra={
                "duration_ms": round(total_ms, 2),
                "statement": statement.strip().replace("\n", " ")[:500],
                "parameters": str(parameters)[:200],
            },
        )

# Dependency for FastAPI routes
def get_db():
    """
    Dependency for getting a database session.
    Ensures session is closed after request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
