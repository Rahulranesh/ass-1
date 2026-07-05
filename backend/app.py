"""
app.py — Flask API Server for Render Deployment
-------------------------------------------------
Wraps the Lambda-style handlers into standard Flask HTTP routes.

Auth uses JWT tokens issued by our own auth system (no AWS Cognito needed).
Instead of Cognito, we use PyJWT + bcrypt for register/login.
The StudentHandler uses PostgreSQL directly — same stored procedures.

Routes:
  POST   /auth              → register / login / confirm (no-auth)
  POST   /students          → create profile (JWT required)
  GET    /students/me       → get own profile (JWT required)
  PUT    /students/me       → update profile (JWT required)
  GET    /health            → health check
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt
import jwt as pyjwt
from flask import Flask, jsonify, request
from flask_cors import CORS

# Add the backend directory itself to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from db.connection import DatabaseConnection
from db.procedures import StoredProcedureRepository
from models.student_model import StudentModel, GRADE_OPTIONS, CAREER_INTERESTS
from models.undergraduate import UndergraduateStudent, UNDERGRAD_GRADE_OPTIONS
from models.graduate import GraduateStudent, GRAD_GRADE_OPTIONS

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins="*", supports_credentials=True)

JWT_SECRET = os.environ.get("JWT_SECRET", "change-this-in-production-secret-key")
JWT_ALGO = "HS256"
JWT_EXPIRY_HOURS = int(os.environ.get("JWT_EXPIRY_HOURS", "24"))

# ---------------------------------------------------------------------------
# DB singletons (reused across requests — connection pooling)
# ---------------------------------------------------------------------------
_db = None
_repo = None

def get_db():
    global _db, _repo
    if _db is None:
        _db = DatabaseConnection()
        _repo = StoredProcedureRepository(_db)
    return _db, _repo

# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

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
    """Decode and validate a JWT. Raises if expired/invalid."""
    return pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])


def jwt_required(f):
    """Decorator: protects a route with JWT auth."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_token(token)
        except pyjwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except pyjwt.InvalidTokenError as exc:
            return jsonify({"error": f"Invalid token: {exc}"}), 401
        request.user = payload
        return f(*args, **kwargs)
    return decorated

# ---------------------------------------------------------------------------
# Auth routes — no JWT needed
# ---------------------------------------------------------------------------

@app.route("/auth", methods=["POST"])
def auth():
    """
    Unified auth endpoint.
    Body must have { "action": "register"|"login" }
    """
    body = request.get_json(force=True, silent=True) or {}
    action = body.get("action", "").lower()
    email = (body.get("email") or "").strip().lower()
    password = body.get("password", "")
    full_name = (body.get("full_name") or "").strip()

    # Basic validation
    if not email or "@" not in email:
        return jsonify({"error": "Valid email is required"}), 400
    if action in ("register", "login") and len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    _, repo = get_db()

    if action == "register":
        if not full_name:
            return jsonify({"error": "full_name is required for registration"}), 400
        # Hash password
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        try:
            result = repo.register_user(email=email, full_name=full_name, pw_hash=pw_hash)
        except Exception as exc:
            logger.error("Register error: %s", exc)
            err_msg = str(exc)
            if "unique" in err_msg.lower() or "duplicate" in err_msg.lower():
                return jsonify({"error": "An account with this email already exists"}), 409
            return jsonify({"error": "Registration failed. Please try again."}), 500
        return jsonify({
            "message": "Registration successful! You can now log in.",
            "user_id": result.get("user_id"),
        }), 201

    elif action == "login":
        try:
            user = repo.get_user_by_email(email)
        except Exception as exc:
            logger.error("Login DB error: %s", exc)
            return jsonify({"error": "Login failed. Please try again."}), 500

        if not user:
            return jsonify({"error": "Invalid email or password"}), 401

        # Verify password
        if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            return jsonify({"error": "Invalid email or password"}), 401

        token = create_token(user_id=str(user["user_id"]), email=email)
        return jsonify({
            "access_token": token,
            "id_token": token,         # same token — frontend stores both
            "refresh_token": token,    # simplified (no refresh flow needed for demo)
            "expires_in": JWT_EXPIRY_HOURS * 3600,
            "message": "Login successful.",
            "user": {"email": email, "full_name": user.get("full_name", "")},
        }), 200

    elif action == "confirm":
        # No email confirmation needed — accounts are auto-confirmed
        return jsonify({"message": "Account is already confirmed. Please log in."}), 200

    else:
        return jsonify({"error": f"Unknown action '{action}'. Use: register, login"}), 400


# ---------------------------------------------------------------------------
# Student profile routes — JWT required
# ---------------------------------------------------------------------------

@app.route("/students", methods=["POST"])
@jwt_required
def create_student():
    """Create a student profile for the logged-in user."""
    body = request.get_json(force=True, silent=True) or {}
    cognito_sub = request.user["sub"]
    email = request.user.get("email", body.get("email", ""))
    body["cognito_sub"] = cognito_sub
    body["email"] = email

    # Required fields check
    required = ["full_name", "school", "grade", "gpa", "career_interest"]
    for field in required:
        if not body.get(field):
            return jsonify({"error": f"Field '{field}' is required"}), 400

    try:
        gpa = float(body["gpa"])
        if not (0.0 <= gpa <= 4.0):
            return jsonify({"error": "GPA must be between 0.0 and 4.0"}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "GPA must be a valid number"}), 400

    if body.get("grade") not in GRADE_OPTIONS:
        return jsonify({"error": f"Invalid grade. Choose from: {GRADE_OPTIONS}"}), 400

    if body.get("career_interest") not in CAREER_INTERESTS:
        return jsonify({"error": f"Invalid career interest"}), 400

    grade = body.get("grade", "")
    try:
        if grade in GRAD_GRADE_OPTIONS:
            student = GraduateStudent.from_dict(body)
        elif grade in UNDERGRAD_GRADE_OPTIONS:
            student = UndergraduateStudent.from_dict(body)
        else:
            student = StudentModel.from_dict(body)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    _, repo = get_db()
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
        logger.error("Insert student error: %s", exc)
        err_msg = str(exc)
        if "unique" in err_msg.lower() or "duplicate" in err_msg.lower():
            return jsonify({"error": "Profile already exists. Use PUT to update."}), 409
        return jsonify({"error": "Failed to create profile. Please try again."}), 500

    return jsonify({"message": "Profile created successfully.", **result}), 201


@app.route("/students/me", methods=["GET"])
@jwt_required
def get_student():
    """Get the logged-in user's student profile."""
    cognito_sub = request.user["sub"]
    _, repo = get_db()

    try:
        row = repo.get_student_by_sub(cognito_sub)
    except Exception as exc:
        logger.error("Get student error: %s", exc)
        return jsonify({"error": "Failed to retrieve profile."}), 500

    if not row:
        return jsonify({"error": "Student profile not found."}), 404

    grade = row.get("grade", "")
    if grade in GRAD_GRADE_OPTIONS:
        student = GraduateStudent.from_db_row(row)
    elif grade in UNDERGRAD_GRADE_OPTIONS:
        student = UndergraduateStudent.from_db_row(row)
    else:
        student = StudentModel.from_db_row(row)

    return jsonify(student.to_dict()), 200


@app.route("/students/me", methods=["PUT"])
@jwt_required
def update_student():
    """Update the logged-in user's student profile."""
    cognito_sub = request.user["sub"]
    body = request.get_json(force=True, silent=True) or {}

    _, repo = get_db()
    try:
        updated = repo.update_student(
            cognito_sub=cognito_sub,
            school=body.get("school", ""),
            grade=body.get("grade", ""),
            gpa=float(body.get("gpa", 0)),
            career_interest=body.get("career_interest", ""),
        )
    except Exception as exc:
        logger.error("Update student error: %s", exc)
        return jsonify({"error": "Failed to update profile."}), 500

    if not updated:
        return jsonify({"error": "Profile not found."}), 404

    return jsonify({"message": "Profile updated successfully."}), 200


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    """Render uses this to check if the service is up."""
    try:
        db, _ = get_db()
        db_ok = db.health_check()
    except Exception:
        db_ok = False
    status = "ok" if db_ok else "degraded"
    return jsonify({"status": status, "db": db_ok}), 200 if db_ok else 503


# ---------------------------------------------------------------------------
# CORS preflight handler (needed for browser fetch from frontend)
# ---------------------------------------------------------------------------

@app.route("/auth", methods=["OPTIONS"])
@app.route("/students", methods=["OPTIONS"])
@app.route("/students/me", methods=["OPTIONS"])
def handle_options():
    return "", 204


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "production") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
