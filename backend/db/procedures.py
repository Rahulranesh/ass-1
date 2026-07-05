"""
procedures.py
-------------
Thin wrappers around PostgreSQL stored procedures.

All database writes and reads go through stored procedures (not raw SQL)
to satisfy the assignment requirement (#6).

OOP Concepts Demonstrated:
  - ENCAPSULATION: SQL details hidden inside StoredProcedureRepository.
  - ABSTRACTION: Callers use insert_student() and get_student() without
    knowing the SQL or stored procedure names.
"""

import logging
from typing import Any, Dict, List, Optional

from db.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class StoredProcedureRepository:
    """
    Repository that invokes PostgreSQL stored procedures for all
    student-related database operations.

    Encapsulation:
      - The DatabaseConnection instance is a private dependency.
      - Stored procedure names are private constants.

    Abstraction:
      - Public methods have semantic names (insert_student, get_student_by_sub).
    """

    # Private stored procedure names (Encapsulation)
    __SP_INSERT_STUDENT = "insert_student"
    __SP_GET_BY_SUB = "get_student_by_cognito_sub"
    __SP_LIST_ALL = "list_all_students"
    __SP_UPDATE_STUDENT = "update_student_profile"

    def __init__(self, db: DatabaseConnection):
        # Dependency injection — allows easy mocking in tests
        self.__db = db

    # ------------------------------------------------------------------ #
    #  PUBLIC METHODS (Abstraction)                                       #
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

        The procedure returns the newly created student_id (UUID).

        Args:
            cognito_sub: Cognito user UUID.
            email: Student email address.
            full_name: Full display name.
            school: School name.
            grade: Grade level.
            gpa: GPA (0.00–4.00).
            career_interest: Selected career interest.

        Returns:
            Dict with the new student_id.

        Raises:
            RuntimeError: If the procedure raises a DB error.
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
        Retrieve a student profile by Cognito sub by calling
        `get_student_by_cognito_sub` stored procedure.

        Args:
            cognito_sub: The Cognito user UUID.

        Returns:
            A dict of student fields, or None if not found.
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
        """
        List all students (admin use only) via `list_all_students` stored proc.

        Returns:
            List of student dicts.
        """
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
        Update an existing student's profile via `update_student_profile` proc.

        Returns:
            True if the record was found and updated, False otherwise.
        """
        args = [cognito_sub, school, grade, gpa, career_interest]
        logger.info("Calling stored procedure: %s", self.__SP_UPDATE_STUDENT)

        with self.__db.get_cursor() as cur:
            cur.callproc(self.__SP_UPDATE_STUDENT, args)
            result = cur.fetchone()

        updated = bool(result and result.get("rows_affected", 0) > 0)
        logger.info("Update result for %s: %s", cognito_sub, updated)
        return updated
