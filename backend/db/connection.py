"""
connection.py
-------------
Encapsulates all PostgreSQL RDS connection management.

OOP Concepts Demonstrated:
  - ENCAPSULATION: Connection credentials and pool are completely hidden.
    External code only calls get_connection() and release_connection().
  - ABSTRACTION: Callers never deal with psycopg2 details directly.
"""

import logging
import os
from contextlib import contextmanager
from typing import Generator

import psycopg2
import psycopg2.extras
from psycopg2 import pool

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Manages a thread-safe PostgreSQL connection pool.

    Encapsulation:
      - The connection string and pool object are private attributes.
      - External code only accesses the database through the context manager.

    Abstraction:
      - Users call `with DatabaseConnection.get_cursor() as cur:` without
        knowing how connections are obtained or returned to the pool.

    Usage:
        db = DatabaseConnection()
        with db.get_cursor() as cursor:
            cursor.callproc("insert_student", [sub, email, ...])
    """

    # Private class constants (Encapsulation)
    __MIN_CONNECTIONS: int = 1
    __MAX_CONNECTIONS: int = 10

    def __init__(self):
        self.__pool: pool.ThreadedConnectionPool = self.__create_pool()

    # ------------------------------------------------------------------ #
    #  PRIVATE METHODS (Encapsulation)                                    #
    # ------------------------------------------------------------------ #

    def __create_pool(self) -> pool.ThreadedConnectionPool:
        """
        Build a psycopg2 threaded connection pool from environment variables.
        Raises EnvironmentError if required config is missing.
        """
        required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
        missing = [var for var in required if not os.environ.get(var)]
        if missing:
            raise EnvironmentError(
                f"Missing required DB environment variables: {', '.join(missing)}"
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
            "Creating DB connection pool to %s:%s/%s",
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
        """Acquire a connection from the pool (internal use only)."""
        return self.__pool.getconn()

    def __release_connection(self, conn: psycopg2.extensions.connection) -> None:
        """Return a connection to the pool (internal use only)."""
        self.__pool.putconn(conn)

    # ------------------------------------------------------------------ #
    #  PUBLIC INTERFACE (Abstraction)                                     #
    # ------------------------------------------------------------------ #

    @contextmanager
    def get_cursor(self) -> Generator:
        """
        Context manager that provides a database cursor.

        Handles connection acquisition, commit-on-success, rollback-on-error,
        and connection release — all hidden from the caller.

        Yields:
            psycopg2 cursor (RealDictCursor for dict-style row access).

        Example:
            with db.get_cursor() as cur:
                cur.callproc("insert_student", [arg1, arg2, ...])
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
        """
        Quick connectivity check. Returns True if the database is reachable.
        Abstraction: callers just check True/False.
        """
        try:
            with self.get_cursor() as cur:
                cur.execute("SELECT 1")
            return True
        except Exception as exc:
            logger.error("DB health check failed: %s", exc)
            return False

    def close_all(self) -> None:
        """Close all connections in the pool (call on Lambda cold-start cleanup)."""
        if self.__pool:
            self.__pool.closeall()
            logger.info("All DB connections closed.")
