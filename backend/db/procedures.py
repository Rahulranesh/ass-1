"""
procedures.py (updated for Render deployment)
----------------------------------------------
Adds register_user() and get_user_by_email() for JWT-based auth
(replaces Cognito when running on Render).

All student methods remain unchanged.
"""

import logging
from typing import Any, Dict, List, Optional

from db.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class StoredProcedureRepository:
    """
    Repository that invokes PostgreSQL stored procedures for all
    student-related and auth database operations.

    Encapsulation:
      - The DatabaseConnection instance is a private dependency.
      - Stored procedure names are private constants.

    Abstraction:
      - Public methods have semantic names.
    """

    # Private stored procedure names (Encapsulation)
    __SP_INSERT_STUDENT = "insert_student"
    __SP_GET_BY_SUB = "get_student_by_cognito_sub"
    __SP_LIST_ALL = "list_all_students"
    __SP_UPDATE_STUDENT = "update_student_profile"
    __SP_REGISTER_USER = "register_user"
    __SP_GET_USER_BY_EMAIL = "get_user_by_email"

    def __init__(self, db: DatabaseConnection):
        # Dependency injection — allows easy mocking in tests
        self.__db = db

    # ------------------------------------------------------------------ #
    #  AUTH METHODS                                                        #
    # ------------------------------------------------------------------ #

    def register_user(self, email: str, full_name: str, pw_hash: str) -> Dict[str, Any]:
        """
        Register a new user via the `register_user` stored procedure.
        Returns the new user_id.
        """
        logger.info("Calling stored procedure: %s", self.__SP_REGISTER_USER)
        with self.__db.get_cursor() as cur:
            cur.callproc(self.__SP_REGISTER_USER, [email, full_name, pw_hash])
            result = cur.fetchone()
        user_id = result["user_id"] if result else None
        return {"user_id": str(user_id) if user_id else None}

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a user record by email for login verification.
        Returns dict with user_id, email, full_name, password_hash or None.
        """
        logger.info("Calling stored procedure: %s", self.__SP_GET_USER_BY_EMAIL)
        with self.__db.get_cursor() as cur:
            cur.callproc(self.__SP_GET_USER_BY_EMAIL, [email])
            result = cur.fetchone()
        if result is None:
            return None
        return dict(result)

    # ------------------------------------------------------------------ #
    #  STUDENT PROFILE METHODS                                            #
    # ------------------------------------------------------------------ #

    def insert_student(
        self,
        cognito_sub: str,
        email: str,
        full_name: str,
        school: str,
        grade: str,
        gpa: float,
        career_interest: str,
    ) -> Dict[str, Any]:
        """
        Insert a new student by calling the `insert_student` stored procedure.
        Returns dict with the new student_id.
        """
        args = [cognito_sub, email, full_name, school, grade, gpa, career_interest]
        logger.info("Calling stored procedure: %s", self.__SP_INSERT_STUDENT)

        with self.__db.get_cursor() as cur:
            cur.callproc(self.__SP_INSERT_STUDENT, args)
            result = cur.fetchone()

        student_id = result["student_id"] if result else None
        logger.info("Inserted student with ID: %s", student_id)
        return {"student_id": str(student_id) if student_id else None}

    def get_student_by_sub(self, cognito_sub: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a student profile by user ID (cognito_sub).
        Returns a dict of student fields, or None if not found.
        """
        logger.info("Calling stored procedure: %s", self.__SP_GET_BY_SUB)

        with self.__db.get_cursor() as cur:
            cur.callproc(self.__SP_GET_BY_SUB, [cognito_sub])
            result = cur.fetchone()

        if result is None:
            logger.warning("No student found for cognito_sub=%s", cognito_sub)
            return None

        return dict(result)

    def list_all_students(self) -> List[Dict[str, Any]]:
        """List all students (admin use only)."""
        logger.info("Calling stored procedure: %s", self.__SP_LIST_ALL)

        with self.__db.get_cursor() as cur:
            cur.callproc(self.__SP_LIST_ALL, [])
            rows = cur.fetchall()

        return [dict(row) for row in rows]

    def update_student(
        self,
        cognito_sub: str,
        school: str,
        grade: str,
        gpa: float,
        career_interest: str,
    ) -> bool:
        """
        Update an existing student's profile.
        Returns True if the record was updated.
        """
        args = [cognito_sub, school, grade, gpa, career_interest]
        logger.info("Calling stored procedure: %s", self.__SP_UPDATE_STUDENT)

        with self.__db.get_cursor() as cur:
            cur.callproc(self.__SP_UPDATE_STUDENT, args)
            result = cur.fetchone()

        updated = bool(result and result.get("rows_affected", 0) > 0)
        logger.info("Update result for %s: %s", cognito_sub, updated)
        return updated
