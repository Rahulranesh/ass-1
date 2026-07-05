-- =============================================================================
-- procedures.sql (updated for Render deployment)
-- Adds: register_user(), get_user_by_email() for JWT auth
-- =============================================================================


-- =============================================================================
-- PROC: register_user
-- Registers a new user (replaces Cognito sign_up on Render)
-- =============================================================================

CREATE OR REPLACE FUNCTION register_user(
    p_email         VARCHAR(255),
    p_full_name     VARCHAR(255),
    p_password_hash VARCHAR(255)
)
RETURNS TABLE(user_id UUID)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    INSERT INTO users (email, full_name, password_hash)
    VALUES (p_email, p_full_name, p_password_hash)
    RETURNING users.user_id;
END;
$$;

COMMENT ON FUNCTION register_user IS 'Insert a new user record with a bcrypt-hashed password.';


-- =============================================================================
-- PROC: get_user_by_email
-- Look up user for login
-- =============================================================================

CREATE OR REPLACE FUNCTION get_user_by_email(
    p_email VARCHAR(255)
)
RETURNS TABLE(
    user_id       UUID,
    email         VARCHAR(255),
    full_name     VARCHAR(255),
    password_hash VARCHAR(255)
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT u.user_id, u.email, u.full_name, u.password_hash
    FROM users u
    WHERE u.email = LOWER(p_email);
END;
$$;

COMMENT ON FUNCTION get_user_by_email IS 'Retrieve user credentials for login verification.';


-- =============================================================================
-- PROC: insert_student
-- Insert a new student profile with validation
-- =============================================================================

CREATE OR REPLACE FUNCTION insert_student(
    p_cognito_sub    VARCHAR(255),
    p_email          VARCHAR(255),
    p_full_name      VARCHAR(255),
    p_school         VARCHAR(255),
    p_grade          VARCHAR(100),
    p_gpa            DECIMAL(3,2),
    p_career_interest VARCHAR(150)
)
RETURNS TABLE(student_id UUID)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Business rule: GPA must be valid
    IF p_gpa < 0.00 OR p_gpa > 4.00 THEN
        RAISE EXCEPTION 'GPA must be between 0.00 and 4.00. Got: %', p_gpa;
    END IF;

    RETURN QUERY
    INSERT INTO students (
        cognito_sub, email, full_name, school, grade, gpa, career_interest
    )
    VALUES (
        p_cognito_sub, LOWER(p_email), p_full_name, p_school,
        p_grade, p_gpa, p_career_interest
    )
    RETURNING students.student_id;
END;
$$;

COMMENT ON FUNCTION insert_student IS 'Insert a validated student profile record.';


-- =============================================================================
-- PROC: get_student_by_cognito_sub
-- Fetch one student profile by user UUID
-- =============================================================================

CREATE OR REPLACE FUNCTION get_student_by_cognito_sub(
    p_cognito_sub VARCHAR(255)
)
RETURNS TABLE(
    student_id      UUID,
    cognito_sub     VARCHAR(255),
    email           VARCHAR(255),
    full_name       VARCHAR(255),
    school          VARCHAR(255),
    grade           VARCHAR(100),
    gpa             DECIMAL(3,2),
    career_interest VARCHAR(150),
    created_at      TIMESTAMP WITH TIME ZONE,
    updated_at      TIMESTAMP WITH TIME ZONE
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.student_id, s.cognito_sub, s.email, s.full_name,
        s.school, s.grade, s.gpa, s.career_interest,
        s.created_at, s.updated_at
    FROM students s
    WHERE s.cognito_sub = p_cognito_sub;
END;
$$;

COMMENT ON FUNCTION get_student_by_cognito_sub IS 'Retrieve a single student profile by user UUID.';


-- =============================================================================
-- PROC: list_all_students
-- Admin: list all student profiles
-- =============================================================================

CREATE OR REPLACE FUNCTION list_all_students()
RETURNS TABLE(
    student_id      UUID,
    email           VARCHAR(255),
    full_name       VARCHAR(255),
    school          VARCHAR(255),
    grade           VARCHAR(100),
    gpa             DECIMAL(3,2),
    career_interest VARCHAR(150),
    created_at      TIMESTAMP WITH TIME ZONE
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.student_id, s.email, s.full_name, s.school,
        s.grade, s.gpa, s.career_interest, s.created_at
    FROM students s
    ORDER BY s.created_at DESC;
END;
$$;

COMMENT ON FUNCTION list_all_students IS 'Admin: return all student profiles ordered by creation date.';


-- =============================================================================
-- PROC: update_student_profile
-- Update mutable student fields
-- =============================================================================

CREATE OR REPLACE FUNCTION update_student_profile(
    p_cognito_sub    VARCHAR(255),
    p_school         VARCHAR(255),
    p_grade          VARCHAR(100),
    p_gpa            DECIMAL(3,2),
    p_career_interest VARCHAR(150)
)
RETURNS TABLE(rows_affected INTEGER)
LANGUAGE plpgsql
AS $$
DECLARE
    v_rows INTEGER;
BEGIN
    UPDATE students
    SET
        school          = p_school,
        grade           = p_grade,
        gpa             = p_gpa,
        career_interest = p_career_interest
        -- updated_at is handled by the trigger
    WHERE cognito_sub = p_cognito_sub;

    GET DIAGNOSTICS v_rows = ROW_COUNT;
    RETURN QUERY SELECT v_rows;
END;
$$;

COMMENT ON FUNCTION update_student_profile IS 'Update mutable student fields. Email cannot be changed (enforced by trigger).';
