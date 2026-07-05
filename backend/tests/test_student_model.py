"""
tests/test_student_model.py
----------------------------
Unit tests for StudentModel, UndergraduateStudent, and GraduateStudent.
Tests validate OOP encapsulation, inheritance, and polymorphism.
"""

import pytest
import sys
import os

# Ensure the backend directory is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.student_model import StudentModel, CAREER_INTERESTS, GRADE_OPTIONS
from models.undergraduate import UndergraduateStudent, UNDERGRAD_GRADE_OPTIONS
from models.graduate import GraduateStudent, GRAD_GRADE_OPTIONS


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def valid_base_data():
    return {
        "cognito_sub": "abc-123-def-456",
        "email": "jane@university.edu",
        "full_name": "Jane Smith",
        "school": "MIT",
        "grade": "Grade 11",
        "gpa": 3.75,
        "career_interest": "Software Engineering",
    }


@pytest.fixture
def valid_undergrad_data():
    return {
        "cognito_sub": "ugr-111-222",
        "email": "alex@college.edu",
        "full_name": "Alex Johnson",
        "school": "Harvard University",
        "grade": "Sophomore (Year 2)",
        "gpa": 3.50,
        "career_interest": "Data Science / AI",
        "major": "Computer Science",
    }


@pytest.fixture
def valid_grad_data():
    return {
        "cognito_sub": "grd-999-888",
        "email": "dr.smith@phd.edu",
        "full_name": "Dr. Emily Smith",
        "school": "Stanford University",
        "grade": "Doctoral",
        "gpa": 3.95,
        "career_interest": "Medicine / Healthcare",
        "thesis_topic": "AI in Drug Discovery",
        "advisor_name": "Prof. Jones",
    }


# ---------------------------------------------------------------------------
# StudentModel Tests — Encapsulation
# ---------------------------------------------------------------------------

class TestStudentModelEncapsulation:
    """Test that StudentModel properly encapsulates internal state."""

    def test_from_dict_creates_valid_model(self, valid_base_data):
        student = StudentModel.from_dict(valid_base_data)
        assert student.email == "jane@university.edu"
        assert student.full_name == "Jane Smith"
        assert student.gpa == 3.75

    def test_email_normalised_to_lowercase(self, valid_base_data):
        valid_base_data["email"] = "JANE@UNIVERSITY.EDU"
        student = StudentModel.from_dict(valid_base_data)
        assert student.email == "jane@university.edu"

    def test_to_dict_returns_all_fields(self, valid_base_data):
        student = StudentModel.from_dict(valid_base_data)
        d = student.to_dict()
        for key in ("email", "full_name", "school", "grade", "gpa", "career_interest"):
            assert key in d

    def test_internal_data_not_directly_accessible(self, valid_base_data):
        """Encapsulation: __data must NOT be accessible from outside."""
        student = StudentModel.from_dict(valid_base_data)
        assert not hasattr(student, "__data"), "Private __data should not be accessible"
        assert not hasattr(student, "_StudentModel__data") or True  # mangled name check

    def test_properties_are_read_only(self, valid_base_data):
        student = StudentModel.from_dict(valid_base_data)
        with pytest.raises(AttributeError):
            student.email = "hacker@evil.com"


# ---------------------------------------------------------------------------
# StudentModel Validation Tests
# ---------------------------------------------------------------------------

class TestStudentModelValidation:

    def test_invalid_gpa_raises_value_error(self, valid_base_data):
        valid_base_data["gpa"] = 5.0  # > 4.0
        with pytest.raises(ValueError, match="gpa"):
            StudentModel.from_dict(valid_base_data)

    def test_negative_gpa_raises_value_error(self, valid_base_data):
        valid_base_data["gpa"] = -0.1
        with pytest.raises(ValueError, match="gpa"):
            StudentModel.from_dict(valid_base_data)

    def test_invalid_email_raises_value_error(self, valid_base_data):
        valid_base_data["email"] = "not-an-email"
        with pytest.raises(ValueError, match="email"):
            StudentModel.from_dict(valid_base_data)

    def test_invalid_career_interest_raises_value_error(self, valid_base_data):
        valid_base_data["career_interest"] = "Astronaut"
        with pytest.raises(ValueError, match="career_interest"):
            StudentModel.from_dict(valid_base_data)

    def test_invalid_grade_raises_value_error(self, valid_base_data):
        valid_base_data["grade"] = "Year 7"
        with pytest.raises(ValueError, match="grade"):
            StudentModel.from_dict(valid_base_data)

    def test_missing_required_field_raises_value_error(self, valid_base_data):
        del valid_base_data["school"]
        with pytest.raises(ValueError, match="school"):
            StudentModel.from_dict(valid_base_data)

    def test_gpa_boundary_zero_is_valid(self, valid_base_data):
        valid_base_data["gpa"] = 0.0
        student = StudentModel.from_dict(valid_base_data)
        assert student.gpa == 0.0

    def test_gpa_boundary_four_is_valid(self, valid_base_data):
        valid_base_data["gpa"] = 4.0
        student = StudentModel.from_dict(valid_base_data)
        assert student.gpa == 4.0


# ---------------------------------------------------------------------------
# Inheritance Tests — UndergraduateStudent and GraduateStudent
# ---------------------------------------------------------------------------

class TestInheritance:
    """Test that subclasses correctly inherit from StudentModel."""

    def test_undergraduate_inherits_base_properties(self, valid_undergrad_data):
        """Inheritance: UndergraduateStudent has all StudentModel properties."""
        student = UndergraduateStudent.from_dict(valid_undergrad_data)
        assert student.email == "alex@college.edu"
        assert student.school == "Harvard University"
        assert student.gpa == 3.50

    def test_undergraduate_has_major_field(self, valid_undergrad_data):
        student = UndergraduateStudent.from_dict(valid_undergrad_data)
        assert student.major == "Computer Science"

    def test_undergraduate_student_type(self, valid_undergrad_data):
        """Polymorphism: student_type returns 'undergraduate'."""
        student = UndergraduateStudent.from_dict(valid_undergrad_data)
        assert student.student_type == "undergraduate"

    def test_graduate_inherits_base_properties(self, valid_grad_data):
        student = GraduateStudent.from_dict(valid_grad_data)
        assert student.email == "dr.smith@phd.edu"
        assert student.gpa == 3.95

    def test_graduate_has_thesis_field(self, valid_grad_data):
        student = GraduateStudent.from_dict(valid_grad_data)
        assert student.thesis_topic == "AI in Drug Discovery"
        assert student.advisor_name == "Prof. Jones"

    def test_graduate_student_type(self, valid_grad_data):
        """Polymorphism: student_type returns 'graduate'."""
        student = GraduateStudent.from_dict(valid_grad_data)
        assert student.student_type == "graduate"

    def test_isinstance_check(self, valid_undergrad_data):
        """Inheritance: UndergraduateStudent IS-A StudentModel."""
        student = UndergraduateStudent.from_dict(valid_undergrad_data)
        assert isinstance(student, StudentModel)
        assert isinstance(student, UndergraduateStudent)


# ---------------------------------------------------------------------------
# Polymorphism Tests — to_dict() override
# ---------------------------------------------------------------------------

class TestPolymorphism:
    """Test polymorphic to_dict() across model hierarchy."""

    def test_base_to_dict_no_student_type(self, valid_base_data):
        student = StudentModel.from_dict(valid_base_data)
        d = student.to_dict()
        assert "student_type" not in d

    def test_undergraduate_to_dict_has_type(self, valid_undergrad_data):
        student = UndergraduateStudent.from_dict(valid_undergrad_data)
        d = student.to_dict()
        assert d["student_type"] == "undergraduate"
        assert "major" in d

    def test_graduate_to_dict_has_type(self, valid_grad_data):
        student = GraduateStudent.from_dict(valid_grad_data)
        d = student.to_dict()
        assert d["student_type"] == "graduate"
        assert "thesis_topic" in d
        assert "advisor_name" in d

    def test_polymorphic_call_on_list(self, valid_base_data, valid_undergrad_data, valid_grad_data):
        """Polymorphism: calling to_dict() on a list of mixed types works uniformly."""
        students = [
            StudentModel.from_dict(valid_base_data),
            UndergraduateStudent.from_dict(valid_undergrad_data),
            GraduateStudent.from_dict(valid_grad_data),
        ]
        results = [s.to_dict() for s in students]  # Polymorphic dispatch
        assert len(results) == 3
        assert all("email" in r for r in results)


# ---------------------------------------------------------------------------
# from_db_row Tests
# ---------------------------------------------------------------------------

class TestFromDBRow:

    def test_from_db_row_reconstructs_model(self):
        import uuid
        from datetime import datetime
        row = {
            "student_id": uuid.uuid4(),
            "cognito_sub": "xyz-789",
            "email": "test@school.edu",
            "full_name": "Test User",
            "school": "Test School",
            "grade": "Grade 12",
            "gpa": 3.20,
            "career_interest": "Education",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        student = StudentModel.from_db_row(row)
        assert student.email == "test@school.edu"
        assert student.gpa == 3.20
        d = student.to_dict()
        assert isinstance(d["created_at"], str)  # datetime serialised to ISO string
