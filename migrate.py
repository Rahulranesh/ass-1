#!/usr/bin/env python3
"""
migrate.py — Database migration script for Render deployment
--------------------------------------------------------------
Runs schema.sql, procedures.sql, and triggers.sql against the
Render PostgreSQL database.

Usage:
    DATABASE_URL=postgres://... python migrate.py

Or (after setting DATABASE_URL env var):
    python migrate.py
"""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    logger.error("psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

# SQL files to run in order
SQL_FILES = [
    "infrastructure/sql/schema.sql",
    "infrastructure/sql/procedures.sql",
    "infrastructure/sql/triggers.sql",
]


def get_dsn() -> str:
    """Get database connection string from env."""
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        return database_url.replace("postgres://", "postgresql://", 1)

    required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        logger.error("Set DATABASE_URL or these env vars: %s", ", ".join(missing))
        sys.exit(1)

    return (
        f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
        f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
    )


def run_sql_file(cursor, filepath: str) -> None:
    """Read and execute a SQL file."""
    # Try the path relative to this script's directory, then the repo root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(script_dir, filepath)

    if not os.path.exists(full_path):
        logger.warning("SQL file not found, skipping: %s", full_path)
        return

    with open(full_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    logger.info("Running: %s", filepath)
    cursor.execute(sql_content)
    logger.info("✓ Done: %s", filepath)


def main():
    dsn = get_dsn()
    logger.info("Connecting to database...")

    try:
        conn = psycopg2.connect(dsn)
        conn.autocommit = False
    except psycopg2.OperationalError as exc:
        logger.error("Failed to connect to database: %s", exc)
        sys.exit(1)

    try:
        with conn.cursor() as cur:
            for sql_file in SQL_FILES:
                run_sql_file(cur, sql_file)
        conn.commit()
        logger.info("")
        logger.info("✅ All migrations completed successfully!")
    except Exception as exc:
        conn.rollback()
        logger.error("Migration failed, rolling back: %s", exc)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
