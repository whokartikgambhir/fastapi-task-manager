from app.db import engine
from sqlalchemy import text

def test_connection():
    try:
        # simple test query
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("Database connection successful:", result.scalar())
    except Exception as e:
        print("Database connection failed:", e)

if __name__ == "__main__":
    test_connection()
