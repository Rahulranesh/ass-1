"""
student_model.py
----------------
Domain model for a student record.

OOP Concepts Demonstrated:
  - ENCAPSULATION: All fields are validated through properties/methods;
    internal data stored in a private dict.
  - ABSTRACTION: Consumers use to_dict() and from_dict() without knowing
    internal representation details.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID


# Career interest choices — single source of truth
CAREER_INTERESTS: List[str] = [
    "Software Engineering",
    "Medicine / Healthcare",
    "Law",
    "Business / Finance",
    "Education",
    "Mechanical Engineering",
    "Civil Engineering",
    "Electrical Engineering",
    "Arts & Design",
    "Biology / Chemistry / Physics",
    "Data Science / AI",
    "Other",
]

GRADE_OPTIONS: List[str] = [
    # High School
    "Grade 9",
    "Grade 10",
    "Grade 11",
    "Grade 12",
    # College / University
    "Freshman (Year 1)",
    "Sophomore (Year 2)",
    "Junior (Year 3)",
    "Senior (Year 4)",
    # Graduate
    "Graduate / Masters",
    "Doctoral",
]


class StudentModel:
    """
    Encapsulates all data and validation logic for a Student record.

    Encapsulation is achieved through:
      - Private attribute __data that stores all field values.
      - Public methods (to_dict, from_dict) that control access.
      - Class-method validators that enforce business rules.

    Abstraction: callers use from_dict() / to_dict() without knowing
    how validation or storage is handled internally.
    """

    # Minimum/maximum GPA bounds
    _GPA_MIN: float = 0.0
    _GPA_MAX: float = 4.0

    def __init__(
        self,
        cognito_sub: str,
        email: str,
        full_name: str,
        school: str,
        grade: str,
        gpa: float,
        career_interest: str,
        student_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        # Encapsulation: store everything in a private dict
        self.__data: Dict[str, Any] = {
            "student_id": student_id,
            "cognito_sub": cognito_sub,
            "email": email,
            "full_name": full_name,
            "school": school,
            "grade": grade,
            "gpa": gpa,
            "career_interest": career_interest,
            "created_at": created_at,
            "updated_at": updated_at,
        }

    # ------------------------------------------------------------------ #
    #  READ-ONLY PROPERTIES (controlled access)                           #
    # ------------------------------------------------------------------ #

    @property
    def student_id(self) -> Optional[str]:
        return self.__data["student_id"]

    @property
    def cognito_sub(self) -> str:
        return self.__data["cognito_sub"]

    @property
    def email(self) -> str:
        return self.__data["email"]

    @property
    def full_name(self) -> str:
        return self.__data["full_name"]

    @property
    def school(self) -> str:
        return self.__data["school"]

    @property
    def grade(self) -> str:
        return self.__data["grade"]

    @property
    def gpa(self) -> float:
        return self.__data["gpa"]

    @property
    def career_interest(self) -> str:
        return self.__data["career_interest"]

    # ------------------------------------------------------------------ #
    #  CLASS-LEVEL FACTORY & VALIDATION                                   #
    # ------------------------------------------------------------------ #

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StudentModel":
        """
        Construct a StudentModel from a raw dict (e.g., API request body).
        Validates all fields before returning a valid object.
        Raises ValueError with a descriptive message on invalid input.

        Abstraction: callers do not need to know the field names or
        validation rules — they just pass in a dict.
        """
        errors = cls._validate_fields(data)
        if errors:
            raise ValueError("; ".join(errors))

        return cls(
            cognito_sub=data["cognito_sub"],
            email=data["email"].strip().lower(),
            full_name=data["full_name"].strip(),
            school=data["school"].strip(),
            grade=data["grade"],
            gpa=float(data["gpa"]),
            career_interest=data["career_interest"],
        )

    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> "StudentModel":
        """Reconstruct a StudentModel from a database row dict."""
        return cls(
            student_id=str(row["student_id"]),
            cognito_sub=row["cognito_sub"],
            email=row["email"],
            full_name=row["full_name"],
            school=row["school"],
            grade=row["grade"],
            gpa=float(row["gpa"]),
            career_interest=row["career_interest"],
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    @classmethod
    def _validate_fields(cls, data: Dict[str, Any]) -> List[str]:
        """
        Internal validation. Returns a list of error strings (empty = valid).
        Encapsulation: this logic is private to the model layer.
        """
        errors = []

        if not data.get("cognito_sub", "").strip():
            errors.append("cognito_sub is required")

        email = data.get("email", "").strip()
        if not email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            errors.append("Valid email is required")

        if not data.get("full_name", "").strip():
            errors.append("full_name is required")

        if not data.get("school", "").strip():
            errors.append("school is required")

        grade = data.get("grade", "")
        if grade not in GRADE_OPTIONS:
            errors.append(f"grade must be one of: {GRADE_OPTIONS}")

        try:
            gpa = float(data.get("gpa", -1))
            if not (cls._GPA_MIN <= gpa <= cls._GPA_MAX):
                errors.append(f"gpa must be between {cls._GPA_MIN} and {cls._GPA_MAX}")
        except (TypeError, ValueError):
            errors.append("gpa must be a valid number")

        if data.get("career_interest") not in CAREER_INTERESTS:
            errors.append(f"career_interest must be one of: {CAREER_INTERESTS}")

        return errors

    # ------------------------------------------------------------------ #
    #  SERIALISATION                                                       #
    # ------------------------------------------------------------------ #

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialise the model to a plain dict for API responses.
        Abstraction: consumers don't interact with __data directly.
        """
        result = dict(self.__data)
        # Convert datetime objects to ISO strings for JSON serialisation
        for key in ("created_at", "updated_at"):
            if isinstance(result[key], datetime):
                result[key] = result[key].isoformat()
        return result

    def __repr__(self) -> str:
        return f"<StudentModel email={self.email!r} grade={self.grade!r} gpa={self.gpa}>"
