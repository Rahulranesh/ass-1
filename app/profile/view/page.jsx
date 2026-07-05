"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { studentService } from "@/services/StudentService";
import { authService } from "@/services/AuthService";

export default function ViewProfilePage() {
  const router = useRouter();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      router.push("/login");
      return;
    }
    fetchProfile();
  }, [router]);

  const fetchProfile = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await studentService.getProfile();
      setProfile(data?.data || data);
    } catch (err) {
      if (err.statusCode === 404) {
        router.push("/profile/create");
      } else {
        setError(err.message || "Failed to load profile.");
      }
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <ProfileSkeleton />;

  if (error) {
    return (
      <div className="page-center">
        <div className="profile-wrapper animate-fade-up">
          <div className="glass-card profile-view-card">
            <div className="alert alert-error" role="alert">{error}</div>
            <button
              className="btn btn-secondary"
              onClick={fetchProfile}
              style={{ marginTop: "var(--space-lg)" }}
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!profile) return null;

  const initials = profile.full_name
    ? profile.full_name.split(" ").map((n) => n[0]).slice(0, 2).join("").toUpperCase()
    : "??";

  const gpa = parseFloat(profile.gpa || 0);
  const gpaColor =
    gpa >= 3.5 ? "var(--color-success)" : gpa >= 2.5 ? "hsl(38, 92%, 58%)" : "var(--color-error)";

  const fields = [
    { label: "School / Institution", value: profile.school, icon: "🏫" },
    { label: "Grade Level", value: profile.grade, icon: "📚" },
    { label: "Career Interest", value: profile.career_interest, icon: "🎯" },
    {
      label: "Member Since",
      value: profile.created_at
        ? new Date(profile.created_at).toLocaleDateString("en-US", {
            year: "numeric", month: "long", day: "numeric",
          })
        : "—",
      icon: "📅",
    },
  ];

  return (
    <div className="page-center" style={{ padding: "var(--space-2xl) var(--space-xl)" }}>
      <div className="profile-wrapper animate-fade-up">
        <div className="glass-card profile-view-card">

          {/* Profile Header */}
          <div className="profile-view-header">
            <div className="avatar" aria-hidden="true">{initials}</div>
            <div style={{ flex: 1 }}>
              <h1 className="profile-name">{profile.full_name}</h1>
              <p className="profile-email">{profile.email}</p>
              <div style={{ marginTop: "var(--space-sm)", display: "flex", gap: "var(--space-sm)", flexWrap: "wrap" }}>
                <span className="badge badge-primary">🎓 Student</span>
                {profile.student_type && (
                  <span className="badge badge-success" style={{ textTransform: "capitalize" }}>
                    {profile.student_type}
                  </span>
                )}
              </div>
            </div>

            <Link
              href="/profile/create"
              className="btn btn-secondary btn-sm"
              aria-label="Edit your profile"
              id="btn-edit-profile"
            >
              ✏️ Edit
            </Link>
          </div>

          {/* GPA Feature Box */}
          <div
            className="animate-fade-in"
            style={{
              background: "var(--gradient-surface)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-lg)",
              padding: "var(--space-xl)",
              marginBottom: "var(--space-xl)",
              display: "flex",
              alignItems: "center",
              gap: "var(--space-xl)",
              flexWrap: "wrap",
            }}
            aria-label={`GPA: ${gpa.toFixed(2)} out of 4.0`}
          >
            <div>
              <p style={{ fontSize: "0.75rem", fontWeight: 600, textTransform: "uppercase",
                letterSpacing: "0.06em", color: "var(--color-text-muted)", marginBottom: "var(--space-xs)" }}>
                Grade Point Average
              </p>
              <div className="gpa-display">{gpa.toFixed(2)}</div>
              <p style={{ fontSize: "0.8rem", color: "var(--color-text-muted)", marginTop: 4 }}>out of 4.0</p>
            </div>
            <div style={{ flex: 1, minWidth: 160 }}>
              <div style={{ display: "flex", justifyContent: "space-between",
                fontSize: "0.78rem", color: "var(--color-text-muted)", marginBottom: 6 }}>
                <span>0.0</span><span>4.0</span>
              </div>
              <div className="gpa-bar-track">
                <div
                  className="gpa-bar-fill"
                  style={{ width: `${(gpa / 4) * 100}%`, background: gpaColor }}
                  role="progressbar"
                  aria-valuenow={gpa}
                  aria-valuemin={0}
                  aria-valuemax={4}
                  aria-label={`GPA ${gpa.toFixed(2)} of 4.0`}
                />
              </div>
              <GPALabel gpa={gpa} />
            </div>
          </div>

          {/* Info Fields Grid */}
          <div className="profile-grid stagger" role="list" aria-label="Profile details">
            {fields.map((f) => (
              <div key={f.label} className="profile-field animate-fade-up" role="listitem">
                <p className="profile-field-label">
                  <span aria-hidden="true">{f.icon} </span>{f.label}
                </p>
                <p className="profile-field-value">{f.value || "—"}</p>
              </div>
            ))}
          </div>

          {/* Action Row */}
          <div style={{ marginTop: "var(--space-xl)", display: "flex", gap: "var(--space-md)",
            flexWrap: "wrap" }}>
            <Link href="/profile/create" className="btn btn-primary" id="btn-update-profile">
              Update Profile
            </Link>
            <button
              className="btn btn-ghost"
              onClick={() => { authService.logout(); router.push("/login"); }}
              id="btn-logout-profile"
              aria-label="Sign out of your account"
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function GPALabel({ gpa }) {
  const labels = [
    { min: 3.7, text: "Exceptional 🌟", color: "var(--color-success)" },
    { min: 3.3, text: "Excellent ✨", color: "var(--color-success)" },
    { min: 3.0, text: "Very Good 👍", color: "hsl(90, 60%, 50%)" },
    { min: 2.5, text: "Good", color: "hsl(38, 92%, 58%)" },
    { min: 2.0, text: "Satisfactory", color: "hsl(38, 75%, 55%)" },
    { min: 0, text: "Needs Improvement", color: "var(--color-error)" },
  ];
  const label = labels.find((l) => gpa >= l.min) || labels[labels.length - 1];
  return (
    <p style={{ fontSize: "0.8rem", fontWeight: 700, color: label.color, marginTop: 6 }}>
      {label.text}
    </p>
  );
}

function ProfileSkeleton() {
  return (
    <div className="page-center" style={{ padding: "var(--space-2xl) var(--space-xl)" }}>
      <div className="profile-wrapper">
        <div className="glass-card profile-view-card" aria-busy="true" aria-label="Loading profile">
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-lg)",
            marginBottom: "var(--space-xl)", paddingBottom: "var(--space-xl)",
            borderBottom: "1px solid var(--color-border)" }}>
            <div className="skeleton" style={{ width: 80, height: 80, borderRadius: "50%" }} />
            <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "var(--space-sm)" }}>
              <div className="skeleton" style={{ height: 24, width: "60%" }} />
              <div className="skeleton" style={{ height: 16, width: "40%" }} />
              <div className="skeleton" style={{ height: 22, width: 100, borderRadius: 99 }} />
            </div>
          </div>
          <div className="skeleton" style={{ height: 120, borderRadius: "var(--radius-lg)",
            marginBottom: "var(--space-xl)" }} />
          <div className="profile-grid">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="skeleton" style={{ height: 80, borderRadius: "var(--radius-md)" }} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
