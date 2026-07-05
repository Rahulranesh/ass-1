-- =============================================================================
-- schema.sql  (updated for Render/PostgreSQL deployment)
-- Adds: users table for JWT-based auth (replaces Cognito)
-- =============================================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- TABLE: users  (for JWT auth — replaces Cognito on Render)
-- =============================================================================

CREATE TABLE IF NOT EXISTS users (
    user_id         UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255)    NOT NULL UNIQUE,
    full_name       VARCHAR(255)    NOT NULL,
    password_hash   VARCHAR(255)    NOT NULL,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

COMMENT ON TABLE users IS 'Stores user credentials for JWT-based auth (used on Render instead of Cognito).';
COMMENT ON COLUMN users.password_hash IS 'bcrypt hash of the user password. Never store plaintext.';

-- =============================================================================
-- TABLE: students
-- =============================================================================

CREATE TABLE IF NOT EXISTS students (
    student_id      UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    cognito_sub     VARCHAR(255)    NOT NULL UNIQUE,
    email           VARCHAR(255)    NOT NULL UNIQUE,
    full_name       VARCHAR(255)    NOT NULL,
    school          VARCHAR(255)    NOT NULL,
    grade           VARCHAR(100)    NOT NULL,
    gpa             DECIMAL(3, 2)   NOT NULL CHECK (gpa >= 0.00 AND gpa <= 4.00),
    career_interest VARCHAR(150)    NOT NULL,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Index for quick lookup by user_id (used in every authenticated request)
CREATE INDEX IF NOT EXISTS idx_students_cognito_sub ON students (cognito_sub);
CREATE INDEX IF NOT EXISTS idx_students_email ON students (email);

COMMENT ON TABLE students IS 'Stores student profiles linked to user accounts.';
COMMENT ON COLUMN students.cognito_sub IS 'The user UUID from the users table (reused as cognito_sub for compatibility).';
COMMENT ON COLUMN students.gpa IS 'GPA on a 4.0 scale. Enforced between 0.00 and 4.00.';

-- =============================================================================
-- TABLE: student_audit_log
-- Populated by the audit TRIGGER below
-- =============================================================================

CREATE TABLE IF NOT EXISTS student_audit_log (
    log_id          UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID            NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    action          VARCHAR(10)     NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    changed_fields  JSONB,
    changed_by      VARCHAR(255),
    changed_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_student_id ON student_audit_log (student_id);
CREATE INDEX IF NOT EXISTS idx_audit_changed_at  ON student_audit_log (changed_at);

COMMENT ON TABLE student_audit_log IS 'Audit trail for all changes to the students table.';
