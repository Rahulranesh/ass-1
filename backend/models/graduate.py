"""
graduate.py
-----------
Concrete subclass of StudentModel for graduate students.

OOP Concepts Demonstrated:
  - INHERITANCE: GraduateStudent extends StudentModel.
  - POLYMORPHISM: Overrides to_dict() and student_type property.
"""

from typing import Any, Dict, List, Optional
from models.student_model import StudentModel


GRAD_GRADE_OPTIONS: List[str] = [
    "Graduate / Masters",
    "Doctoral",
]


class GraduateStudent(StudentModel):
    """
    Represents a graduate (Masters/PhD) student.

    Inherits from StudentModel (Inheritance).
    Adds graduate-specific fields: thesis_topic and advisor_name.

    Polymorphism: overrides to_dict() and student_type.
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
        thesis_topic: Optional[str] = None,
        advisor_name: Optional[str] = None,
        student_id: Optional[str] = None,
        created_at=None,
        updated_at=None,
    ):
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
        self._thesis_topic: Optional[str] = thesis_topic
        self._advisor_name: Optional[str] = advisor_name

    @property
    def thesis_topic(self) -> Optional[str]:
        return self._thesis_topic

    @property
    def advisor_name(self) -> Optional[str]:
        return self._advisor_name

    @property
    def student_type(self) -> str:
        """Polymorphic type identifier for graduate students."""
        return "graduate"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GraduateStudent":
        """Build a GraduateStudent; validates grad-level grade options."""
        errors = cls._validate_fields(data)
        if data.get("grade") not in GRAD_GRADE_OPTIONS:
            errors.append(f"Graduate grade must be one of: {GRAD_GRADE_OPTIONS}")
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
            thesis_topic=data.get("thesis_topic", "").strip() or None,
            advisor_name=data.get("advisor_name", "").strip() or None,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Polymorphic override: adds thesis_topic, advisor_name, student_type."""
        base = super().to_dict()
        base["thesis_topic"] = self._thesis_topic
        base["advisor_name"] = self._advisor_name
        base["student_type"] = self.student_type
        return base

    def __repr__(self) -> str:
        return (
            f"<GraduateStudent email={self.email!r} "
            f"grade={self.grade!r} thesis={self._thesis_topic!r}>"
        )
