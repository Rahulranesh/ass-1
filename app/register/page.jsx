"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { authService } from "@/services/AuthService";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    fullName: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const validate = () => {
    const e = {};
    if (!form.fullName.trim()) e.fullName = "Full name is required.";
    if (!form.email.trim() || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.email))
      e.email = "A valid email address is required.";
    if (form.password.length < 8)
      e.password = "Password must be at least 8 characters.";
    if (!/[A-Z]/.test(form.password))
      e.password = (e.password || "") + " Must include an uppercase letter.";
    if (!/[0-9]/.test(form.password))
      e.password = (e.password || "") + " Must include a number.";
    if (form.password !== form.confirmPassword)
      e.confirmPassword = "Passwords do not match.";
    return e;
  };

  const handleChange = (e) => {
    setErrors((prev) => ({ ...prev, [e.target.name]: "" }));
    setServerError("");
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
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
      await authService.register({
        email: form.email,
        password: form.password,
        fullName: form.fullName,
      });
      // Redirect to email confirmation page
      // No email confirmation needed — account is immediately active
      router.push(`/login?registered=1`);
    } catch (err) {
      setServerError(err.message || "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-center">
      <div className="auth-wrapper animate-fade-up">
        <div className="glass-card auth-card">
          {/* Header */}
          <div className="auth-header">
            <div className="auth-logo" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
                <line x1="19" y1="8" x2="19" y2="14" />
                <line x1="22" y1="11" x2="16" y2="11" />
              </svg>
            </div>
            <h1 className="auth-title">Create account</h1>
            <p className="auth-subtitle">Start your academic journey today</p>
          </div>

          {/* Server Error */}
          {serverError && (
            <div className="alert alert-error" role="alert" aria-live="polite"
              style={{ marginBottom: "var(--space-lg)" }}>
              <span aria-hidden="true">⚠️</span> {serverError}
            </div>
          )}

          <form className="auth-form" onSubmit={handleSubmit} noValidate
            aria-label="Create account form">

            {/* Full Name */}
            <div className="form-group">
              <label htmlFor="reg-fullname" className="form-label">Full name</label>
              <input
                id="reg-fullname"
                name="fullName"
                type="text"
                autoComplete="name"
                className="form-input"
                placeholder="Jane Smith"
                value={form.fullName}
                onChange={handleChange}
                required
                aria-required="true"
                aria-describedby={errors.fullName ? "err-fullname" : undefined}
                disabled={loading}
                enterKeyHint="next"
              />
              {errors.fullName && (
                <span id="err-fullname" className="form-error" role="alert">
                  <span aria-hidden="true">⚠</span> {errors.fullName}
                </span>
              )}
            </div>

            {/* Email */}
            <div className="form-group">
              <label htmlFor="reg-email" className="form-label">Email address</label>
              <input
                id="reg-email"
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
                aria-describedby={errors.email ? "err-email" : undefined}
                disabled={loading}
                enterKeyHint="next"
              />
              {errors.email && (
                <span id="err-email" className="form-error" role="alert">
                  <span aria-hidden="true">⚠</span> {errors.email}
                </span>
              )}
            </div>

            {/* Password */}
            <div className="form-group">
              <label htmlFor="new-password" className="form-label">Password</label>
              <div className="input-wrapper">
                <input
                  id="new-password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="new-password"
                  className="form-input"
                  placeholder="Min. 8 characters"
                  value={form.password}
                  onChange={handleChange}
                  required
                  aria-required="true"
                  aria-describedby="password-hint err-password"
                  disabled={loading}
                  enterKeyHint="next"
                />
                <button
                  type="button"
                  className="toggle-password"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  aria-pressed={showPassword}
                >
                  {showPassword ? "🙈" : "👁️"}
                </button>
              </div>
              <span id="password-hint" className="form-hint">
                At least 8 characters, one uppercase letter and one number.
              </span>

              {/* Password strength indicator */}
              {form.password && (
                <PasswordStrength password={form.password} />
              )}

              {errors.password && (
                <span id="err-password" className="form-error" role="alert">
                  <span aria-hidden="true">⚠</span> {errors.password}
                </span>
              )}
            </div>

            {/* Confirm Password */}
            <div className="form-group">
              <label htmlFor="confirm-password" className="form-label">Confirm password</label>
              <input
                id="confirm-password"
                name="confirmPassword"
                type="password"
                autoComplete="new-password"
                className="form-input"
                placeholder="Re-enter your password"
                value={form.confirmPassword}
                onChange={handleChange}
                required
                aria-required="true"
                aria-describedby={errors.confirmPassword ? "err-confirm" : undefined}
                disabled={loading}
                enterKeyHint="done"
              />
              {errors.confirmPassword && (
                <span id="err-confirm" className="form-error" role="alert">
                  <span aria-hidden="true">⚠</span> {errors.confirmPassword}
                </span>
              )}
            </div>

            <button
              id="btn-create-account"
              type="submit"
              className={`btn btn-primary btn-full${loading ? " btn-loading" : ""}`}
              disabled={loading}
              aria-busy={loading}
            >
              <span className="btn-text">{loading ? "Creating account…" : "Create Account →"}</span>
            </button>
          </form>

          <p className="auth-footer">
            Already have an account?{" "}
            <Link href="/login" id="link-to-login">Sign in →</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

/* Password strength meter sub-component */
function PasswordStrength({ password }) {
  const checks = [
    { label: "8+ characters", pass: password.length >= 8 },
    { label: "Uppercase", pass: /[A-Z]/.test(password) },
    { label: "Number", pass: /[0-9]/.test(password) },
    { label: "Symbol", pass: /[^A-Za-z0-9]/.test(password) },
  ];
  const score = checks.filter((c) => c.pass).length;
  const colors = ["var(--color-error)", "var(--color-warning)", "hsl(60,80%,55%)", "var(--color-success)"];
  const labels = ["Weak", "Fair", "Good", "Strong"];

  return (
    <div style={{ marginTop: "var(--space-xs)" }} aria-live="polite" aria-label={`Password strength: ${labels[score - 1] || "Weak"}`}>
      <div style={{ display: "flex", gap: 4, marginBottom: 6 }}>
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            style={{
              flex: 1,
              height: 4,
              borderRadius: 99,
              background: i < score ? colors[score - 1] : "var(--color-bg-elevated)",
              transition: "background 0.3s ease",
            }}
          />
        ))}
      </div>
      <div style={{ display: "flex", gap: "var(--space-sm)", flexWrap: "wrap" }}>
        {checks.map((c) => (
          <span key={c.label} style={{
            fontSize: "0.72rem",
            fontWeight: 600,
            color: c.pass ? "var(--color-success)" : "var(--color-text-muted)",
            display: "flex", alignItems: "center", gap: 3,
          }}>
            {c.pass ? "✓" : "○"} {c.label}
          </span>
        ))}
      </div>
    </div>
  );
}
