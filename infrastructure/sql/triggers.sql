-- =============================================================================
-- triggers.sql
-- PostgreSQL Triggers for Student Portal
-- Assignment #6: Triggers for automated timestamp updates and audit logging
-- =============================================================================


-- =============================================================================
-- FUNCTION: set_updated_at()
-- Purpose: Automatically update the updated_at column on every UPDATE.
-- Used by: TRIGGER update_student_timestamp
-- =============================================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- Set updated_at to current UTC time
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION set_updated_at IS
'Trigger function that sets updated_at = NOW() before any UPDATE on students.';


-- =============================================================================
-- TRIGGER: update_student_timestamp
-- Fires: BEFORE UPDATE on the students table
-- Purpose: Ensure updated_at is never stale — enforced at DB level, not app level.
-- =============================================================================

DROP TRIGGER IF EXISTS update_student_timestamp ON students;

CREATE TRIGGER update_student_timestamp
    BEFORE UPDATE ON students
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

COMMENT ON TRIGGER update_student_timestamp ON students IS
'Automatically refreshes updated_at to NOW() before every UPDATE.';


-- =============================================================================
-- FUNCTION: log_student_action()
-- Purpose: Helper function called by stored procedures to write to audit log.
-- =============================================================================

CREATE OR REPLACE FUNCTION log_student_action(
    p_student_id    UUID,
    p_action        VARCHAR(10),
    p_changed_fields JSONB,
    p_changed_by    VARCHAR(255)
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO student_audit_log (student_id, action, changed_fields, changed_by)
    VALUES (p_student_id, p_action, p_changed_fields, p_changed_by);
END;
$$;

COMMENT ON FUNCTION log_student_action IS
'Inserts a row into student_audit_log. Called by stored procedures, not directly.';


-- =============================================================================
-- FUNCTION: audit_student_changes()
-- Purpose: Capture old vs new field values on UPDATE for detailed audit trail.
-- Used by: TRIGGER student_audit_trigger
-- =============================================================================

CREATE OR REPLACE FUNCTION audit_student_changes()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_changed_fields JSONB := '{}';
BEGIN
    -- Build a JSON object of only the fields that actually changed
    IF OLD.school           IS DISTINCT FROM NEW.school THEN
        v_changed_fields := v_changed_fields || jsonb_build_object(
            'school', jsonb_build_object('old', OLD.school, 'new', NEW.school)
        );
    END IF;

    IF OLD.grade            IS DISTINCT FROM NEW.grade THEN
        v_changed_fields := v_changed_fields || jsonb_build_object(
            'grade', jsonb_build_object('old', OLD.grade, 'new', NEW.grade)
        );
    END IF;

    IF OLD.gpa              IS DISTINCT FROM NEW.gpa THEN
        v_changed_fields := v_changed_fields || jsonb_build_object(
            'gpa', jsonb_build_object('old', OLD.gpa, 'new', NEW.gpa)
        );
    END IF;

    IF OLD.career_interest  IS DISTINCT FROM NEW.career_interest THEN
        v_changed_fields := v_changed_fields || jsonb_build_object(
            'career_interest', jsonb_build_object(
                'old', OLD.career_interest,
                'new', NEW.career_interest
            )
        );
    END IF;

    -- Only insert audit row if at least one field changed
    IF v_changed_fields != '{}' THEN
        INSERT INTO student_audit_log (student_id, action, changed_fields, changed_by)
        VALUES (NEW.student_id, 'UPDATE', v_changed_fields, NEW.cognito_sub);
    END IF;

    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION audit_student_changes IS
'Trigger function that writes a detailed JSONB diff of changed fields to the audit log.';


-- =============================================================================
-- TRIGGER: student_audit_trigger
-- Fires: AFTER UPDATE on the students table
-- Purpose: Record exactly which fields changed and their before/after values.
-- =============================================================================

DROP TRIGGER IF EXISTS student_audit_trigger ON students;

CREATE TRIGGER student_audit_trigger
    AFTER UPDATE ON students
    FOR EACH ROW
    EXECUTE FUNCTION audit_student_changes();

COMMENT ON TRIGGER student_audit_trigger ON students IS
'Writes a JSONB diff of changed fields to student_audit_log after every UPDATE.';


-- =============================================================================
-- FUNCTION: prevent_email_change()
-- Purpose: Prevent the email column from being updated after initial creation.
--          Email is immutable — tied to Cognito account.
-- =============================================================================

CREATE OR REPLACE FUNCTION prevent_email_change()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.email IS DISTINCT FROM NEW.email THEN
        RAISE EXCEPTION 'Email address cannot be changed after account creation.'
            USING ERRCODE = 'raise_exception';
    END IF;
    RETURN NEW;
END;
$$;


-- =============================================================================
-- TRIGGER: immutable_email_trigger
-- Fires: BEFORE UPDATE on students — prevents email modification
-- =============================================================================

DROP TRIGGER IF EXISTS immutable_email_trigger ON students;

CREATE TRIGGER immutable_email_trigger
    BEFORE UPDATE ON students
    FOR EACH ROW
    EXECUTE FUNCTION prevent_email_change();

COMMENT ON TRIGGER immutable_email_trigger ON students IS
'Raises an exception if any UPDATE tries to change the email column.';
