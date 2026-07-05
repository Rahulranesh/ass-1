"""
app.py — FastAPI server for Render deployment
----------------------------------------------
Wraps the OOP handlers into standard FastAPI HTTP routes.

Auth uses PyJWT + bcrypt (replaces AWS Cognito on Render).
All student operations call PostgreSQL stored procedures via
StoredProcedureRepository — same as the Lambda version.

Routes:
  POST   /auth              → register / login (no auth)
  POST   /students          → create profile (JWT required)
  GET    /students/me       → get own profile (JWT required)
  PUT    /students/me       → update profile (JWT required)
  GET    /health            → health check
  GET    /docs              → auto-generated Swagger UI (FastAPI)
"""

import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
import jwt as pyjwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field, field_validator

# ── Python path fix so backend/* imports work ─────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from db.connection import DatabaseConnection
from db.procedures import StoredProcedureRepository
from models.student_model import CAREER_INTERESTS, GRADE_OPTIONS, StudentModel
from models.graduate import GraduateStudent, GRAD_GRADE_OPTIONS
from models.undergraduate import UndergraduateStudent, UNDERGRAD_GRADE_OPTIONS

# ── Logging ───────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────
JWT_SECRET = os.environ.get("JWT_SECRET", "change-this-in-production-secret-key")
JWT_ALGO = "HS256"
JWT_EXPIRY_HOURS = int(os.environ.get("JWT_EXPIRY_HOURS", "24"))

# ── FastAPI app ────────────────────────────────────────────────────────────
app = FastAPI(
    title="Student Portal API",
    description="Full-stack student registration and profile API (OOP · Python · PostgreSQL)",
    version="1.0.0",
    docs_url="/docs",        # Swagger UI at /docs
    redoc_url="/redoc",      # ReDoc at /redoc
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Restrict to your frontend domain in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── DB singletons (connection pool reused across requests) ─────────────────
_db: Optional[DatabaseConnection] = None
_repo: Optional[StoredProcedureRepository] = None


def get_repo() -> StoredProcedureRepository:
    """Dependency injection: lazily initialise DB pool."""
    global _db, _repo
    if _db is None:
        _db = DatabaseConnection()
        _repo = StoredProcedureRepository(_db)
    return _repo


# ── JWT helpers ────────────────────────────────────────────────────────────

def create_token(user_id: str, email: str) -> str:
    """Issue a signed JWT access token."""
    payload = {
        "sub": user_id,
        "email": email,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT. Raises ValueError on failure."""
    return pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])


_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> dict:
    """
    FastAPI dependency — validates the Bearer JWT and returns the payload.
    Raises HTTP 401 if the token is missing or invalid.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )
    try:
        return decode_token(credentials.credentials)
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except pyjwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}")


# ── Pydantic request / response models ────────────────────────────────────

class AuthRequest(BaseModel):
    action: str = Field(..., examples=["register", "login"])
    email: str = Field(..., examples=["student@university.edu"])
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, examples=["Jane Smith"])
    confirmation_code: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")
        return v


class StudentCreateRequest(BaseModel):
    full_name: str = Field(..., min_length=1, examples=["Jane Smith"])
    school: str = Field(..., min_length=1, examples=["MIT"])
    grade: str = Field(..., examples=["Freshman (Year 1)"])
    gpa: float = Field(..., ge=0.0, le=4.0, examples=[3.8])
    career_interest: str = Field(..., examples=["Software Engineering"])
    major: Optional[str] = None
    thesis_topic: Optional[str] = None
    advisor_name: Optional[str] = None

    @field_validator("grade")
    @classmethod
    def validate_grade(cls, v: str) -> str:
        if v not in GRADE_OPTIONS:
            raise ValueError(f"grade must be one of: {GRADE_OPTIONS}")
        return v

    @field_validator("career_interest")
    @classmethod
    def validate_career(cls, v: str) -> str:
        if v not in CAREER_INTERESTS:
            raise ValueError(f"career_interest must be one of: {CAREER_INTERESTS}")
        return v


class StudentUpdateRequest(BaseModel):
    school: str = Field(..., min_length=1)
    grade: str
    gpa: float = Field(..., ge=0.0, le=4.0)
    career_interest: str


# ── Auth routes ────────────────────────────────────────────────────────────

@app.post(
    "/auth",
    summary="Register or Login",
    tags=["Auth"],
    responses={
        200: {"description": "Login successful"},
        201: {"description": "Registration successful"},
        400: {"description": "Validation error"},
        401: {"description": "Invalid credentials"},
        409: {"description": "Email already exists"},
    },
)
async def auth(body: AuthRequest, repo: StoredProcedureRepository = Depends(get_repo)):
    """
    Unified auth endpoint.

    - **action = "register"** → creates a new account
    - **action = "login"** → returns a JWT access token
    - **action = "confirm"** → no-op (no email confirmation on Render)
    """
    action = body.action.lower()

    if action == "register":
        if not body.full_name or not body.full_name.strip():
            raise HTTPException(400, "full_name is required for registration")
        pw_hash = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()
        try:
            result = repo.register_user(
                email=body.email,
                full_name=body.full_name.strip(),
                pw_hash=pw_hash,
            )
        except Exception as exc:
            err = str(exc).lower()
            if "unique" in err or "duplicate" in err:
                raise HTTPException(409, "An account with this email already exists")
            logger.error("Register error: %s", exc)
            raise HTTPException(500, "Registration failed. Please try again.")

        return {
            "message": "Registration successful! You can now log in.",
            "user_id": result.get("user_id"),
        }

    elif action == "login":
        try:
            user = repo.get_user_by_email(body.email)
        except Exception as exc:
            logger.error("Login DB error: %s", exc)
            raise HTTPException(500, "Login failed. Please try again.")

        if not user or not bcrypt.checkpw(
            body.password.encode(), user["password_hash"].encode()
        ):
            raise HTTPException(401, "Invalid email or password")

        token = create_token(user_id=str(user["user_id"]), email=body.email)
        return {
            "access_token": token,
            "id_token": token,
            "refresh_token": token,
            "expires_in": JWT_EXPIRY_HOURS * 3600,
            "message": "Login successful.",
            "user": {"email": body.email, "full_name": user.get("full_name", "")},
        }

    elif action == "confirm":
        return {"message": "Account is already confirmed. Please log in."}

    else:
        raise HTTPException(400, f"Unknown action '{action}'. Use: register, login")


# ── Student profile routes ─────────────────────────────────────────────────

@app.post(
    "/students",
    status_code=201,
    summary="Create student profile",
    tags=["Students"],
)
async def create_student(
    body: StudentCreateRequest,
    current_user: dict = Depends(get_current_user),
    repo: StoredProcedureRepository = Depends(get_repo),
):
    """
    Create a student profile for the logged-in user.

    Requires **Bearer JWT** in the Authorization header.
    Automatically selects the correct model subclass
    (GraduateStudent / UndergraduateStudent / StudentModel) based on grade.
    """
    cognito_sub = current_user["sub"]
    email = current_user.get("email", "")

    data = {
        **body.model_dump(),
        "cognito_sub": cognito_sub,
        "email": email,
    }

    grade = body.grade
    try:
        if grade in GRAD_GRADE_OPTIONS:
            student = GraduateStudent.from_dict(data)
        elif grade in UNDERGRAD_GRADE_OPTIONS:
            student = UndergraduateStudent.from_dict(data)
        else:
            student = StudentModel.from_dict(data)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    try:
        result = repo.insert_student(
            cognito_sub=student.cognito_sub,
            email=student.email,
            full_name=student.full_name,
            school=student.school,
            grade=student.grade,
            gpa=student.gpa,
            career_interest=student.career_interest,
        )
    except Exception as exc:
        err = str(exc).lower()
        if "unique" in err or "duplicate" in err:
            raise HTTPException(409, "Profile already exists. Use PUT /students/me to update.")
        logger.error("Insert student error: %s", exc)
        raise HTTPException(500, "Failed to create profile. Please try again.")

    return {"message": "Profile created successfully.", **result}


@app.get(
    "/students/me",
    summary="Get my profile",
    tags=["Students"],
)
async def get_student(
    current_user: dict = Depends(get_current_user),
    repo: StoredProcedureRepository = Depends(get_repo),
):
    """
    Retrieve the logged-in user's student profile.

    Returns the full profile dict. Returns **404** if no profile exists yet
    (frontend should redirect to /profile/create).
    """
    cognito_sub = current_user["sub"]
    try:
        row = repo.get_student_by_sub(cognito_sub)
    except Exception as exc:
        logger.error("Get student error: %s", exc)
        raise HTTPException(500, "Failed to retrieve profile.")

    if not row:
        raise HTTPException(404, "Student profile not found.")

    grade = row.get("grade", "")
    if grade in GRAD_GRADE_OPTIONS:
        student = GraduateStudent.from_db_row(row)
    elif grade in UNDERGRAD_GRADE_OPTIONS:
        student = UndergraduateStudent.from_db_row(row)
    else:
        student = StudentModel.from_db_row(row)

    return student.to_dict()


@app.put(
    "/students/me",
    summary="Update my profile",
    tags=["Students"],
)
async def update_student(
    body: StudentUpdateRequest,
    current_user: dict = Depends(get_current_user),
    repo: StoredProcedureRepository = Depends(get_repo),
):
    """
    Update the logged-in user's mutable profile fields.
    Email cannot be changed (enforced by a database trigger).
    """
    cognito_sub = current_user["sub"]
    try:
        updated = repo.update_student(
            cognito_sub=cognito_sub,
            school=body.school,
            grade=body.grade,
            gpa=body.gpa,
            career_interest=body.career_interest,
        )
    except Exception as exc:
        logger.error("Update student error: %s", exc)
        raise HTTPException(500, "Failed to update profile.")

    if not updated:
        raise HTTPException(404, "Profile not found.")

    return {"message": "Profile updated successfully."}


@app.get("/debug-db", summary="Debug DB connection", tags=["System"])
def debug_db():
    import os
    import traceback
    import psycopg2
    
    db_keys = {
        "DATABASE_URL": "SET (masked)" if os.environ.get("DATABASE_URL") else "MISSING",
        "DB_HOST": os.environ.get("DB_HOST", "MISSING"),
        "DB_PORT": os.environ.get("DB_PORT", "MISSING"),
        "DB_NAME": os.environ.get("DB_NAME", "MISSING"),
        "DB_USER": os.environ.get("DB_USER", "MISSING"),
        "DB_PASSWORD": "SET (masked)" if os.environ.get("DB_PASSWORD") else "MISSING"
    }
    
    database_url = os.environ.get("DATABASE_URL")
    error_msg = None
    tb = None
    connection_status = "Not attempted"
    
    try:
        if database_url:
            dsn = database_url.replace("postgres://", "postgresql://", 1)
            if "sslmode" not in dsn:
                if "?" in dsn:
                    dsn += "&sslmode=require"
                else:
                    dsn += "?sslmode=require"
            conn = psycopg2.connect(dsn)
            conn.close()
            connection_status = "Success connecting with DATABASE_URL"
        else:
            # Try individual env vars
            required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
            missing = [v for v in required if not os.environ.get(v)]
            if missing:
                connection_status = f"DATABASE_URL not set, and missing individual vars: {missing}"
            else:
                dsn = (
                    f"host={os.environ['DB_HOST']} "
                    f"port={os.environ['DB_PORT']} "
                    f"dbname={os.environ['DB_NAME']} "
                    f"user={os.environ['DB_USER']} "
                    f"password={os.environ['DB_PASSWORD']} "
                    f"sslmode=require"
                )
                conn = psycopg2.connect(dsn)
                conn.close()
                connection_status = "Success connecting with individual environment variables"
    except Exception as e:
        connection_status = "Failed connecting"
        error_msg = str(e)
        tb = traceback.format_exc()
        
    return {
        "env_vars_present": db_keys,
        "connection_status": connection_status,
        "error": error_msg,
        "traceback": tb
    }


# ── Health check ────────────────────────────────────────────────────────────

@app.get("/health", summary="Health check", tags=["System"])
async def health(repo: StoredProcedureRepository = Depends(get_repo)):
    """
    Returns DB connectivity status.
    Render uses this to decide if the service is healthy.
    """
    try:
        db_ok = repo._StoredProcedureRepository__db.health_check()
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "db": db_ok}


# ── Entry point (for local dev) ─────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
