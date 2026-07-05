"""
undergraduate.py
----------------
Concrete subclass of StudentModel for undergraduate students.

OOP Concepts Demonstrated:
  - INHERITANCE: UndergraduateStudent extends StudentModel, inheriting all
    properties, validation logic, and serialisation methods.
  - POLYMORPHISM: Overrides to_dict() to include undergraduate-specific fields.
"""

from typing import Any, Dict, List, Optional
from models.student_model import StudentModel, GRADE_OPTIONS, CAREER_INTERESTS


# Undergraduate-specific grade options
UNDERGRAD_GRADE_OPTIONS: List[str] = [
    "Freshman (Year 1)",
    "Sophomore (Year 2)",
    "Junior (Year 3)",
    "Senior (Year 4)",
]


class UndergraduateStudent(StudentModel):
    """
    Represents an undergraduate (college/university) student.

    Inherits from StudentModel (Inheritance).
    Adds an undergraduate-specific field: major.

    Polymorphism: overrides to_dict() to include 'major' and 'student_type'.
    """

    def __init__(
        self,
        cognito_sub: str,
        email: str,
        full_name: str,
        school: str,
        grade: str,
        gpa: float,
        career_interest: str,
        major: Optional[str] = None,
        student_id: Optional[str] = None,
        created_at=None,
        updated_at=None,
    ):
        # Call parent __init__ (Inheritance)
        super().__init__(
            cognito_sub=cognito_sub,
            email=email,
            full_name=full_name,
            school=school,
            grade=grade,
            gpa=gpa,
            career_interest=career_interest,
            student_id=student_id,
            created_at=created_at,
            updated_at=updated_at,
        )
        # Subclass-specific attribute
        self._major: Optional[str] = major

    @property
    def major(self) -> Optional[str]:
        """The student's declared major (undergraduate-specific field)."""
        return self._major

    @property
    def student_type(self) -> str:
        """Polymorphic type identifier."""
        return "undergraduate"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UndergraduateStudent":
        """
        Build an UndergraduateStudent from a raw dict.
        Inherits base validation; adds grade-range check for undergrads.
        """
        errors = cls._validate_fields(data)
        if data.get("grade") not in UNDERGRAD_GRADE_OPTIONS:
            errors.append(f"Undergraduate grade must be one of: {UNDERGRAD_GRADE_OPTIONS}")
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
            major=data.get("major", "").strip() or None,
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Polymorphic override: includes 'major' and 'student_type' fields
        in addition to the base student fields.
        """
        base = super().to_dict()
        base["major"] = self._major
        base["student_type"] = self.student_type
        return base

    def __repr__(self) -> str:
        return (
            f"<UndergraduateStudent email={self.email!r} "
            f"grade={self.grade!r} major={self._major!r}>"
        )
