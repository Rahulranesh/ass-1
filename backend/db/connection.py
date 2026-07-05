"""
connection.py (updated for Render)
-----------------------------------
Supports both individual DB_* env vars AND Render's DATABASE_URL.
"""

import logging
import os
from contextlib import contextmanager
from typing import Generator
from urllib.parse import urlparse

import psycopg2
import psycopg2.extras
from psycopg2 import pool

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Manages a thread-safe PostgreSQL connection pool.

    Supports two configuration modes:
      1. DATABASE_URL env var (Render provides this automatically)
      2. Individual DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD env vars

    Encapsulation:
      - The connection string and pool object are private attributes.
      - External code only accesses the database through the context manager.

    Usage:
        db = DatabaseConnection()
        with db.get_cursor() as cursor:
            cursor.callproc("insert_student", [sub, email, ...])
    """

    __MIN_CONNECTIONS: int = 1
    __MAX_CONNECTIONS: int = 5  # Reduced for free tier

    def __init__(self):
        self.__pool: pool.ThreadedConnectionPool = self.__create_pool()

    def __create_pool(self) -> pool.ThreadedConnectionPool:
        """
        Build a psycopg2 threaded connection pool.
        Prefers DATABASE_URL (Render) over individual env vars.
        """
        database_url = os.environ.get("DATABASE_URL")

        if database_url:
            # Render provides DATABASE_URL — use it directly
            # Render uses postgres:// prefix but psycopg2 needs postgresql://
            dsn = database_url.replace("postgres://", "postgresql://", 1)
            # Add sslmode if not already specified
            if "sslmode" not in dsn:
                dsn += "?sslmode=require"
            logger.info("Creating DB pool from DATABASE_URL")
        else:
            # Fall back to individual env vars (local dev / AWS)
            required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
            missing = [v for v in required if not os.environ.get(v)]
            if missing:
                raise EnvironmentError(
                    f"Missing DB config. Set DATABASE_URL or: {', '.join(missing)}"
                )
            dsn = (
                f"host={os.environ['DB_HOST']} "
                f"port={os.environ['DB_PORT']} "
                f"dbname={os.environ['DB_NAME']} "
                f"user={os.environ['DB_USER']} "
                f"password={os.environ['DB_PASSWORD']} "
                f"sslmode=require"
            )
            logger.info(
                "Creating DB pool to %s:%s/%s",
                os.environ["DB_HOST"],
                os.environ["DB_PORT"],
                os.environ["DB_NAME"],
            )

        return pool.ThreadedConnectionPool(
            self.__MIN_CONNECTIONS,
            self.__MAX_CONNECTIONS,
            dsn=dsn,
            cursor_factory=psycopg2.extras.RealDictCursor,
        )

    def __get_connection(self) -> psycopg2.extensions.connection:
        return self.__pool.getconn()

    def __release_connection(self, conn: psycopg2.extensions.connection) -> None:
        self.__pool.putconn(conn)

    @contextmanager
    def get_cursor(self) -> Generator:
        """
        Context manager providing a database cursor.
        Handles connection acquisition, commit, rollback, and release.
        """
        conn = self.__get_connection()
        try:
            with conn.cursor() as cursor:
                yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self.__release_connection(conn)

    def health_check(self) -> bool:
        """Quick connectivity check."""
        try:
            with self.get_cursor() as cur:
                cur.execute("SELECT 1")
            return True
        except Exception as exc:
            logger.error("DB health check failed: %s", exc)
            return False

    def close_all(self) -> None:
        """Close all connections in the pool."""
        if self.__pool:
            self.__pool.closeall()
            logger.info("All DB connections closed.")
