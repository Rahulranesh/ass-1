"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { studentService } from "@/services/StudentService";
import { authService } from "@/services/AuthService";

const CAREER_INTERESTS = [
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
];

const GRADE_OPTIONS = [
  { group: "High School", options: ["Grade 9", "Grade 10", "Grade 11", "Grade 12"] },
  {
    group: "College / University",
    options: [
      "Freshman (Year 1)",
      "Sophomore (Year 2)",
      "Junior (Year 3)",
      "Senior (Year 4)",
    ],
  },
  { group: "Graduate", options: ["Graduate / Masters", "Doctoral"] },
];

export default function CreateProfilePage() {
  const router = useRouter();
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    school: "",
    grade: "",
    gpa: "",
    career_interest: "",
  });
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  // Pre-fill name/email from JWT
  useEffect(() => {
    if (!authService.isAuthenticated()) {
      router.push("/login");
      return;
    }
    const user = authService.getCurrentUser();
    if (user) {
      setForm((prev) => ({
        ...prev,
        full_name: user.name || "",
        email: user.email || "",
      }));
    }
  }, [router]);

  const validate = () => {
    const e = {};
    if (!form.full_name.trim()) e.full_name = "Full name is required.";
    if (!form.email.trim()) e.email = "Email is required.";
    if (!form.school.trim()) e.school = "School / institution name is required.";
    if (!form.grade) e.grade = "Please select your grade level.";
    const gpa = parseFloat(form.gpa);
    if (form.gpa === "" || isNaN(gpa)) e.gpa = "GPA is required.";
    else if (gpa < 0 || gpa > 4) e.gpa = "GPA must be between 0.0 and 4.0.";
    if (!form.career_interest) e.career_interest = "Please select a career interest.";
    return e;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setErrors((prev) => ({ ...prev, [name]: "" }));
    setServerError("");
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationErrors = validate();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    setLoading(true);
    try {
      await studentService.createProfile({
        ...form,
        gpa: parseFloat(form.gpa),
      });
      setSuccess(true);
      setTimeout(() => router.push("/profile/view"), 1800);
    } catch (err) {
      setServerError(err.message || "Failed to save profile. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="page-center">
        <div className="profile-wrapper animate-fade-up">
          <div className="glass-card profile-card" style={{ textAlign: "center" }}>
            <div style={{ fontSize: "3.5rem", marginBottom: "var(--space-md)" }} aria-hidden="true">🎓</div>
            <h1 className="auth-title" style={{ marginBottom: "var(--space-sm)" }}>
              Profile Created!
            </h1>
            <p className="auth-subtitle">Redirecting to your profile view…</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page-center" style={{ padding: "var(--space-2xl) var(--space-xl)" }}>
      <div className="profile-wrapper animate-fade-up">
        <div className="glass-card profile-card">
          {/* Header */}
          <div className="profile-header">
            <p className="profile-step">Step 1 of 1</p>
            <h1 className="profile-title">
              Build your <span className="gradient-text">Student Profile</span>
            </h1>
            <p className="profile-subtitle">
              Tell us about yourself — this information powers your academic dashboard.
            </p>
          </div>

          {serverError && (
            <div className="alert alert-error" role="alert" aria-live="polite"
              style={{ marginBottom: "var(--space-lg)" }}>
              <span aria-hidden="true">⚠️</span> {serverError}
            </div>
          )}

          <form className="profile-form" onSubmit={handleSubmit} noValidate
            aria-label="Student profile creation form">

            {/* Name + Email Row */}
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="prof-fullname" className="form-label">Full Name</label>
                <input
                  id="prof-fullname"
                  name="full_name"
                  type="text"
                  autoComplete="name"
                  className="form-input"
                  placeholder="Jane Smith"
                  value={form.full_name}
                  onChange={handleChange}
                  required
                  aria-required="true"
                  aria-describedby={errors.full_name ? "err-pname" : undefined}
                  disabled={loading}
                />
                {errors.full_name && (
                  <span id="err-pname" className="form-error" role="alert">⚠ {errors.full_name}</span>
                )}
              </div>

              <div className="form-group">
                <label htmlFor="prof-email" className="form-label">Email Address</label>
                <input
                  id="prof-email"
                  name="email"
                  type="email"
                  autoComplete="username"
                  inputMode="email"
                  className="form-input"
                  placeholder="you@university.edu"
                  value={form.email}
                  onChange={handleChange}
                  required
                  aria-required="true"
                  aria-describedby={errors.email ? "err-pemail" : undefined}
                  disabled={loading}
                />
                {errors.email && (
                  <span id="err-pemail" className="form-error" role="alert">⚠ {errors.email}</span>
                )}
              </div>
            </div>

            {/* School */}
            <div className="form-group">
              <label htmlFor="prof-school" className="form-label">School / Institution</label>
              <input
                id="prof-school"
                name="school"
                type="text"
                autoComplete="organization"
                className="form-input"
                placeholder="e.g. MIT, Harvard, Jefferson High School"
                value={form.school}
                onChange={handleChange}
                required
                aria-required="true"
                aria-describedby={errors.school ? "err-school" : undefined}
                disabled={loading}
              />
              {errors.school && (
                <span id="err-school" className="form-error" role="alert">⚠ {errors.school}</span>
              )}
            </div>

            {/* Grade + GPA Row */}
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="prof-grade" className="form-label">Grade Level</label>
                <select
                  id="prof-grade"
                  name="grade"
                  className="form-input"
                  value={form.grade}
                  onChange={handleChange}
                  required
                  aria-required="true"
                  aria-describedby={errors.grade ? "err-grade" : undefined}
                  disabled={loading}
                >
                  <option value="">Select grade…</option>
                  {GRADE_OPTIONS.map((grp) => (
                    <optgroup key={grp.group} label={grp.group}>
                      {grp.options.map((opt) => (
                        <option key={opt} value={opt}>{opt}</option>
                      ))}
                    </optgroup>
                  ))}
                </select>
                {errors.grade && (
                  <span id="err-grade" className="form-error" role="alert">⚠ {errors.grade}</span>
                )}
              </div>

              <div className="form-group">
                <label htmlFor="prof-gpa" className="form-label">GPA (0.0 – 4.0)</label>
                <input
                  id="prof-gpa"
                  name="gpa"
                  type="number"
                  inputMode="decimal"
                  min="0"
                  max="4"
                  step="0.01"
                  className="form-input"
                  placeholder="e.g. 3.75"
                  value={form.gpa}
                  onChange={handleChange}
                  required
                  aria-required="true"
                  aria-describedby={errors.gpa ? "err-gpa" : "gpa-hint"}
                  disabled={loading}
                />
                <span id="gpa-hint" className="form-hint">Enter on a 4.0 scale.</span>
                {errors.gpa && (
                  <span id="err-gpa" className="form-error" role="alert">⚠ {errors.gpa}</span>
                )}
              </div>
            </div>

            {/* Career Interest */}
            <div className="form-group">
              <label htmlFor="prof-career" className="form-label">Career Interest</label>
              <select
                id="prof-career"
                name="career_interest"
                className="form-input"
                value={form.career_interest}
                onChange={handleChange}
                required
                aria-required="true"
                aria-describedby={errors.career_interest ? "err-career" : undefined}
                disabled={loading}
              >
                <option value="">Select a career path…</option>
                {CAREER_INTERESTS.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
              {errors.career_interest && (
                <span id="err-career" className="form-error" role="alert">⚠ {errors.career_interest}</span>
              )}
            </div>

            {/* GPA Live Preview */}
            {form.gpa !== "" && !errors.gpa && (
              <div className="animate-fade-in" aria-live="polite" aria-label={`GPA preview: ${parseFloat(form.gpa).toFixed(2)} out of 4.0`}>
                <GPAPreview gpa={parseFloat(form.gpa)} />
              </div>
            )}

            <button
              id="btn-save-profile"
              type="submit"
              className={`btn btn-primary btn-full${loading ? " btn-loading" : ""}`}
              disabled={loading}
              aria-busy={loading}
            >
              <span className="btn-text">{loading ? "Saving profile…" : "Save Profile →"}</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

function GPAPreview({ gpa }) {
  const pct = Math.min((gpa / 4) * 100, 100);
  const color =
    gpa >= 3.5
      ? "var(--color-success)"
      : gpa >= 2.5
      ? "hsl(38, 92%, 58%)"
      : "var(--color-error)";

  return (
    <div
      style={{
        background: "var(--color-bg-elevated)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-md)",
        padding: "var(--space-md) var(--space-lg)",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "var(--space-sm)",
        }}
      >
        <span style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--color-text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
          GPA Preview
        </span>
        <span style={{ fontSize: "1.4rem", fontWeight: 800, color }}>{gpa.toFixed(2)}</span>
      </div>
      <div className="gpa-bar-track">
        <div className="gpa-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}
