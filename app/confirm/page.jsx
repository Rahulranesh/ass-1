"use client";
import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { authService } from "@/services/AuthService";

function ConfirmForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const emailFromQuery = searchParams.get("email") || "";

  const [email, setEmail] = useState(emailFromQuery);
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!code.trim() || code.trim().length < 6) {
      setError("Please enter the 6-digit confirmation code sent to your email.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await authService.confirmEmail(email, code);
      setSuccess(true);
      setTimeout(() => router.push("/login"), 2500);
    } catch (err) {
      setError(err.message || "Invalid code. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="glass-card auth-card" style={{ textAlign: "center" }}>
        <div style={{ fontSize: "3rem", marginBottom: "var(--space-md)" }} aria-hidden="true">🎉</div>
        <h1 className="auth-title" style={{ marginBottom: "var(--space-sm)" }}>
          Email Confirmed!
        </h1>
        <p className="auth-subtitle">Your account is active. Redirecting you to sign in…</p>
        <div className="alert alert-success" style={{ marginTop: "var(--space-lg)" }} role="status">
          ✓ Verification successful
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card auth-card">
      <div className="auth-header">
        <div className="auth-logo" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
            strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
            <polyline points="22,6 12,13 2,6" />
          </svg>
        </div>
        <h1 className="auth-title">Check your email</h1>
        <p className="auth-subtitle">
          We sent a 6-digit code to <strong style={{ color: "var(--color-text-primary)" }}>{email || "your email"}</strong>
        </p>
      </div>

      {error && (
        <div className="alert alert-error" role="alert" aria-live="polite"
          style={{ marginBottom: "var(--space-lg)" }}>
          <span aria-hidden="true">⚠️</span> {error}
        </div>
      )}

      <form className="auth-form" onSubmit={handleSubmit} noValidate
        aria-label="Email confirmation form">

        {!emailFromQuery && (
          <div className="form-group">
            <label htmlFor="confirm-email" className="form-label">Email address</label>
            <input
              id="confirm-email"
              type="email"
              autoComplete="username"
              inputMode="email"
              className="form-input"
              placeholder="you@university.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
              enterKeyHint="next"
            />
          </div>
        )}

        <div className="form-group">
          <label htmlFor="confirm-code" className="form-label">Confirmation code</label>
          <input
            id="confirm-code"
            type="text"
            inputMode="numeric"
            autoComplete="one-time-code"
            className="form-input"
            placeholder="Enter 6-digit code"
            value={code}
            onChange={(e) => { setError(""); setCode(e.target.value.replace(/\D/g, "").slice(0, 6)); }}
            required
            aria-required="true"
            maxLength={6}
            disabled={loading}
            enterKeyHint="done"
            style={{
              letterSpacing: "0.3em",
              fontSize: "1.3rem",
              textAlign: "center",
              fontWeight: 700,
            }}
          />
          <span className="form-hint">Check your spam folder if you don&apos;t see it.</span>
        </div>

        <button
          id="btn-confirm-email"
          type="submit"
          className={`btn btn-primary btn-full${loading ? " btn-loading" : ""}`}
          disabled={loading || code.length < 6}
          aria-busy={loading}
        >
          <span className="btn-text">{loading ? "Verifying…" : "Confirm Email →"}</span>
        </button>
      </form>

      <p className="auth-footer">
        Didn&apos;t get the code?{" "}
        <Link href="/register" id="link-back-to-register">Back to Register</Link>
      </p>
    </div>
  );
}

export default function ConfirmPage() {
  return (
    <div className="page-center">
      <div className="auth-wrapper animate-fade-up">
        <Suspense fallback={<div className="glass-card auth-card"><div className="skeleton" style={{ height: 300 }} /></div>}>
          <ConfirmForm />
        </Suspense>
      </div>
    </div>
  );
}
