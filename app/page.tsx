import Link from "next/link";

export const metadata = {
  title: "Student Portal — Register, Learn, Succeed",
  description: "Create your student profile and manage your academic journey.",
};

export default function HomePage() {
  return (
    <div className="page-center" style={{ flexDirection: "column", gap: "var(--space-3xl)" }}>
      {/* Hero Section */}
      <section
        className="animate-fade-up"
        style={{ textAlign: "center", maxWidth: "680px" }}
        aria-labelledby="hero-title"
      >
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "var(--space-sm)",
            padding: "0.4rem 1.2rem",
            background: "hsla(217, 85%, 58%, 0.12)",
            border: "1px solid hsla(217, 85%, 58%, 0.25)",
            borderRadius: "var(--radius-full)",
            fontSize: "0.8rem",
            fontWeight: 600,
            color: "hsl(217, 85%, 72%)",
            marginBottom: "var(--space-lg)",
            letterSpacing: "0.04em",
            textTransform: "uppercase",
          }}
          role="status"
        >
          <span aria-hidden="true">🚀</span> Powered by AWS Cloud
        </div>

        <h1
          id="hero-title"
          style={{
            fontSize: "clamp(2.5rem, 6vw, 4rem)",
            fontWeight: 800,
            lineHeight: 1.1,
            marginBottom: "var(--space-lg)",
          }}
        >
          Your Academic
          <br />
          <span className="gradient-text">Journey Starts Here</span>
        </h1>

        <p
          style={{
            fontSize: "1.1rem",
            color: "var(--color-text-secondary)",
            maxWidth: "500px",
            margin: "0 auto var(--space-xl)",
            lineHeight: 1.7,
          }}
        >
          Register, build your student profile, track your GPA and career goals —
          all secured with enterprise-grade AWS authentication.
        </p>

        <div
          style={{
            display: "flex",
            gap: "var(--space-md)",
            justifyContent: "center",
            flexWrap: "wrap",
          }}
        >
          <Link href="/register" className="btn btn-primary" id="cta-register">
            Create Account →
          </Link>
          <Link href="/login" className="btn btn-secondary" id="cta-login">
            Sign In
          </Link>
        </div>
      </section>

      {/* Feature Cards */}
      <section
        aria-labelledby="features-title"
        style={{ width: "100%", maxWidth: "900px" }}
      >
        <h2 id="features-title" className="sr-only">Features</h2>
        <div
          className="stagger"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
            gap: "var(--space-md)",
          }}
        >
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="glass-card animate-fade-up"
              style={{ padding: "var(--space-xl)" }}
            >
              <div
                style={{
                  fontSize: "2rem",
                  marginBottom: "var(--space-md)",
                  display: "block",
                }}
                role="img"
                aria-label={f.title}
              >
                {f.icon}
              </div>
              <h3
                style={{
                  fontSize: "1.05rem",
                  fontWeight: 700,
                  marginBottom: "var(--space-xs)",
                }}
              >
                {f.title}
              </h3>
              <p style={{ fontSize: "0.875rem", color: "var(--color-text-secondary)" }}>
                {f.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* AWS Tech Stack Pills */}
      <section aria-label="Technology stack" style={{ textAlign: "center" }}>
        <p
          style={{
            fontSize: "0.8rem",
            fontWeight: 600,
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            color: "var(--color-text-muted)",
            marginBottom: "var(--space-md)",
          }}
        >
          Built on AWS
        </p>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "var(--space-sm)",
            justifyContent: "center",
          }}
        >
          {AWS_SERVICES.map((svc) => (
            <span key={svc} className="badge badge-primary">
              {svc}
            </span>
          ))}
        </div>
      </section>
    </div>
  );
}

const FEATURES = [
  {
    icon: "🔐",
    title: "Secure Authentication",
    description:
      "Enterprise-grade login with AWS Cognito — email verification, JWT tokens, and password policies built in.",
  },
  {
    icon: "📋",
    title: "Student Profile",
    description:
      "Record your school, grade, GPA, and career interests. Stored safely in PostgreSQL RDS with stored procedures.",
  },
  {
    icon: "☁️",
    title: "Cloud Native",
    description:
      "Serverless Lambda backend, CloudFront CDN, and DynamoDB sessions — infinitely scalable at near-zero cost.",
  },
  {
    icon: "🎯",
    title: "Career Tracking",
    description:
      "Choose from a curated set of career paths and build your academic roadmap towards your dream profession.",
  },
];

const AWS_SERVICES = [
  "Cognito",
  "Lambda",
  "API Gateway",
  "RDS PostgreSQL",
  "DynamoDB",
  "S3",
  "CloudFront",
];
