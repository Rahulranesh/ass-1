"""
student_handler.py
------------------
Lambda handler for student profile CRUD operations.

OOP Concepts Demonstrated:
  - INHERITANCE: StudentHandler extends BaseHandler.
  - POLYMORPHISM: Different behaviour for POST (create) vs GET (view).
  - ENCAPSULATION: DB and repo dependencies are private attributes.
"""

import logging
import os
from typing import Any, Dict, Optional

from handlers.base_handler import BaseHandler
from models.student_model import StudentModel, GRADE_OPTIONS, CAREER_INTERESTS
from models.undergraduate import UndergraduateStudent, UNDERGRAD_GRADE_OPTIONS
from models.graduate import GraduateStudent, GRAD_GRADE_OPTIONS
from db.connection import DatabaseConnection
from db.procedures import StoredProcedureRepository

logger = logging.getLogger(__name__)

# Module-level singletons (reused across Lambda invocations for connection pooling)
_db = DatabaseConnection()
_repo = StoredProcedureRepository(_db)


class StudentHandler(BaseHandler):
    """
    Handles student profile creation (POST /students) and retrieval (GET /students/me).

    Inheritance: extends BaseHandler, reusing parse_body(), build_response(),
    success(), and error().

    Polymorphism: handle() dispatches to __create() or __get() based on HTTP method,
    each with different behaviour while keeping the same interface.

    Encapsulation: __db and __repo are private to this class.
    """

    def __init__(self, db: DatabaseConnection = _db, repo: StoredProcedureRepository = _repo):
        super().__init__()
        self.__db = db
        self.__repo = repo

    # ------------------------------------------------------------------ #
    #  ABSTRACT METHOD IMPLEMENTATIONS                                    #
    # ------------------------------------------------------------------ #

    def handle(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Route to __create or __get based on the HTTP method.

        Polymorphism: same method, different behaviour per HTTP verb.
        """
        http_method = event.get("httpMethod", "GET").upper()

        cognito_sub = self.get_cognito_sub(event)
        if not cognito_sub:
            return self.error("Unauthorized — missing authentication token.", 401)

        try:
            if http_method == "POST":
                body = self.parse_body(event)
                body["cognito_sub"] = cognito_sub
                return self.__create(body)
            elif http_method == "GET":
                return self.__get(cognito_sub)
            elif http_method == "PUT":
                body = self.parse_body(event)
                body["cognito_sub"] = cognito_sub
                return self.__update(body, cognito_sub)
            else:
                return self.error(f"Method {http_method} not allowed.", 405)
        except ValueError as exc:
            return self.error(str(exc), 400)
        except Exception as exc:  # pylint: disable=broad-except
            self._logger.exception("Unexpected error in StudentHandler.handle()")
            return self.error("Internal server error.", 500)

    def validate_input(self, body: Dict[str, Any]) -> Optional[str]:
        """
        Validate student profile input fields.
        Polymorphism: different validation from AuthHandler.validate_input().
        """
        required_fields = ["full_name", "email", "school", "grade", "gpa", "career_interest"]
        for field in required_fields:
            if not body.get(field):
                return f"Field '{field}' is required."

        try:
            gpa = float(body["gpa"])
            if not (0.0 <= gpa <= 4.0):
                return "GPA must be between 0.0 and 4.0."
        except (TypeError, ValueError):
            return "GPA must be a valid number."

        if body.get("grade") not in GRADE_OPTIONS:
            return f"Invalid grade. Choose from: {GRADE_OPTIONS}"

        if body.get("career_interest") not in CAREER_INTERESTS:
            return f"Invalid career interest. Choose from: {CAREER_INTERESTS}"

        return None

    # ------------------------------------------------------------------ #
    #  PRIVATE METHODS                                                    #
    # ------------------------------------------------------------------ #

    def __create(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a student profile.

        Polymorphism: uses the appropriate StudentModel subclass based on grade.
        - Graduate grades → GraduateStudent
        - Undergrad grades → UndergraduateStudent
        - Other → base StudentModel
        """
        # Choose correct model class based on grade (Polymorphism)
        grade = body.get("grade", "")
        try:
            if grade in GRAD_GRADE_OPTIONS:
                student = GraduateStudent.from_dict(body)
            elif grade in UNDERGRAD_GRADE_OPTIONS:
                student = UndergraduateStudent.from_dict(body)
            else:
                student = StudentModel.from_dict(body)
        except ValueError as exc:
            return self.error(str(exc), 400)

        # Validate using base class method
        validation_error = self.validate_input(body)
        if validation_error:
            return self.error(validation_error, 400)

        result = self.__repo.insert_student(
            cognito_sub=student.cognito_sub,
            email=student.email,
            full_name=student.full_name,
            school=student.school,
            grade=student.grade,
            gpa=student.gpa,
            career_interest=student.career_interest,
        )

        return self.success(
            {"message": "Profile created successfully.", **result},
            201,
        )

    def __get(self, cognito_sub: str) -> Dict[str, Any]:
        """Retrieve the logged-in student's profile via stored procedure."""
        row = self.__repo.get_student_by_sub(cognito_sub)
        if not row:
            return self.error("Student profile not found.", 404)

        # Reconstruct the appropriate model for serialisation
        grade = row.get("grade", "")
        if grade in GRAD_GRADE_OPTIONS:
            student = GraduateStudent.from_db_row(row)
        elif grade in UNDERGRAD_GRADE_OPTIONS:
            student = UndergraduateStudent.from_db_row(row)
        else:
            student = StudentModel.from_db_row(row)

        return self.success(student.to_dict())

    def __update(self, body: Dict[str, Any], cognito_sub: str) -> Dict[str, Any]:
        """Update an existing student's profile via stored procedure."""
        updated = self.__repo.update_student(
            cognito_sub=cognito_sub,
            school=body.get("school", ""),
            grade=body.get("grade", ""),
            gpa=float(body.get("gpa", 0)),
            career_interest=body.get("career_interest", ""),
        )
        if not updated:
            return self.error("Profile not found or no changes made.", 404)
        return self.success({"message": "Profile updated successfully."})


# ------------------------------------------------------------------ #
#  Lambda Entry Point                                                 #
# ------------------------------------------------------------------ #
_handler = StudentHandler()


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda entry point for the Student profile function."""
    return _handler.handle(event, context)
