"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { authService } from "@/services/AuthService";

export default function LoginPage() {
  const router = useRouter();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleChange = (e) => {
    setError("");
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await authService.login({ email: form.email, password: form.password });
      router.push("/profile/view");
    } catch (err) {
      setError(err.message || "Login failed. Please check your credentials.");
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
                <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
                <path d="M6 12v5c3 3 9 3 12 0v-5" />
              </svg>
            </div>
            <h1 className="auth-title">Welcome back</h1>
            <p className="auth-subtitle">Sign in to your student account</p>
          </div>

          {/* Error */}
          {error && (
            <div className="alert alert-error" role="alert" aria-live="polite" style={{ marginBottom: "var(--space-lg)" }}>
              <span aria-hidden="true">⚠️</span> {error}
            </div>
          )}

          {/* Form */}
          <form
            className="auth-form"
            onSubmit={handleSubmit}
            noValidate
            aria-label="Sign in form"
          >
            <div className="form-group">
              <label htmlFor="login-email" className="form-label">
                Email address
              </label>
              <input
                id="login-email"
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
                disabled={loading}
                enterKeyHint="next"
              />
            </div>

            <div className="form-group">
              <label htmlFor="current-password" className="form-label">
                Password
              </label>
              <div className="input-wrapper">
                <input
                  id="current-password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  className="form-input"
                  placeholder="Enter your password"
                  value={form.password}
                  onChange={handleChange}
                  required
                  aria-required="true"
                  disabled={loading}
                  enterKeyHint="done"
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
              <div style={{ textAlign: "right" }}>
                <a
                  href="#forgot-password"
                  style={{
                    fontSize: "0.8rem",
                    color: "hsl(217, 85%, 68%)",
                    textDecoration: "none",
                    fontWeight: 600,
                  }}
                >
                  Forgot password?
                </a>
              </div>
            </div>

            <button
              id="btn-sign-in"
              type="submit"
              className={`btn btn-primary btn-full${loading ? " btn-loading" : ""}`}
              disabled={loading}
              aria-busy={loading}
            >
              <span className="btn-text">{loading ? "Signing in…" : "Sign In"}</span>
            </button>
          </form>

          <p className="auth-footer">
            Don&apos;t have an account?{" "}
            <Link href="/register" id="link-to-register">
              Create one →
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
