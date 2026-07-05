# Student Portal — Full-Stack AWS Application

[![Deploy Frontend](https://github.com/your-org/student-portal/actions/workflows/deploy-frontend.yml/badge.svg)](https://github.com/your-org/student-portal/actions/workflows/deploy-frontend.yml)
[![Deploy Backend](https://github.com/your-org/student-portal/actions/workflows/deploy-backend.yml/badge.svg)](https://github.com/your-org/student-portal/actions/workflows/deploy-backend.yml)

> A production-ready full-stack student registration and profile management application  
> built with **Next.js**, **AWS Cognito**, **Lambda**, **PostgreSQL RDS**, **DynamoDB**, **S3**, and **CloudFront**.

---

## 📐 Architecture Overview

```
Browser → CloudFront CDN → S3 (Next.js Static Export)
                        ↓
                   API Gateway (REST)
                        ↓
              AWS Cognito (JWT Authorizer)
                        ↓
              Lambda Functions (Python 3.12)
              ├── AuthHandler      → Cognito
              ├── StudentHandler   → RDS PostgreSQL (Stored Procedures)
              └── ProfileHandler   → RDS PostgreSQL
                        ↓
              ┌─────────────────────────┐
              │  RDS PostgreSQL          │
              │  - Stored Procedures     │
              │  - Triggers (3)          │
              │  - Audit Log Table       │
              └─────────────────────────┘
              DynamoDB (Session Cache)
              S3 (Profile Images)
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full Excalidraw diagram and component explanations.

---

## 🗂️ Project Structure

```
student-portal/
├── app/                          # Next.js App Router pages
│   ├── page.tsx                  # Landing / home page
│   ├── login/page.jsx            # Login form
│   ├── register/page.jsx         # Registration form
│   ├── confirm/page.jsx          # Email OTP confirmation
│   └── profile/
│       ├── create/page.jsx       # Create / edit student profile
│       └── view/page.jsx         # Read-only profile view
│
├── components/
│   └── Navbar.jsx                # Sticky authenticated navigation
│
├── services/                     # OOP service layer
│   ├── APIClient.js              # Abstract base (Encapsulation)
│   ├── AuthService.js            # extends APIClient (Inheritance)
│   └── StudentService.js         # extends APIClient (Inheritance)
│
├── backend/                      # Python Lambda functions
│   ├── handlers/
│   │   ├── base_handler.py       # Abstract base class
│   │   ├── auth_handler.py       # Cognito auth (Inheritance)
│   │   └── student_handler.py    # Profile CRUD (Inheritance)
│   ├── models/
│   │   ├── student_model.py      # Encapsulated domain model
│   │   ├── undergraduate.py      # Inheritance + Polymorphism
│   │   └── graduate.py           # Inheritance + Polymorphism
│   ├── db/
│   │   ├── connection.py         # DB pool (Encapsulation)
│   │   └── procedures.py         # Stored procedure callers
│   ├── utils/
│   │   └── response_builder.py   # Polymorphic responses
│   ├── tests/
│   │   ├── test_student_model.py
│   │   └── test_handlers.py
│   └── requirements.txt
│
├── infrastructure/
│   ├── template.yaml             # AWS SAM template (full infra)
│   ├── samconfig.toml
│   └── sql/
│       ├── schema.sql            # Tables + indexes
│       ├── procedures.sql        # 4 stored procedures
│       └── triggers.sql          # 3 triggers
│
├── .github/workflows/
│   ├── deploy-frontend.yml       # S3 + CloudFront CI/CD
│   └── deploy-backend.yml        # SAM + DB migration CI/CD
│
└── docs/
    ├── API.md                    # REST API reference
    ├── DATABASE.md               # Schema + stored procedures
    ├── OOP.md                    # OOP concepts reference
    ├── DEPLOYMENT.md             # Step-by-step deployment guide
    └── ARCHITECTURE.md           # AWS architecture diagram
```

---

## 🚀 Quick Start (Local Development)

### Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Node.js | ≥ 20 | [nodejs.org](https://nodejs.org) |
| Python | 3.12 | [python.org](https://python.org) |
| AWS CLI | ≥ 2.x | [aws.amazon.com/cli](https://aws.amazon.com/cli) |
| AWS SAM CLI | ≥ 1.116 | [aws.amazon.com/serverless/sam](https://aws.amazon.com/serverless/sam) |

### 1. Clone and Install

```bash
git clone https://github.com/your-org/student-portal.git
cd student-portal
npm install          # Install Next.js dependencies
```

### 2. Environment Variables

Create `.env.local` in the project root:

```env
NEXT_PUBLIC_API_URL=https://<api-id>.execute-api.us-east-1.amazonaws.com/dev
NEXT_PUBLIC_COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
NEXT_PUBLIC_COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
NEXT_PUBLIC_AWS_REGION=us-east-1
```

### 3. Run the Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### 4. Run Backend Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v --cov=. --cov-report=term-missing
```

---

## ☁️ AWS Deployment

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for the complete step-by-step guide.

**One-command deploy (after AWS credentials configured):**

```bash
# Deploy infrastructure
cd infrastructure
sam build && sam deploy \
  --parameter-overrides Environment=dev DBPassword=<your-password>

# Deploy frontend
npm run build
aws s3 sync out/ s3://<your-bucket>/ --delete
aws cloudfront create-invalidation --distribution-id <dist-id> --paths "/*"
```

---

## 🎓 OOP Concepts Reference

See [`docs/OOP.md`](docs/OOP.md) for detailed explanations. Summary:

| Concept | Where Used |
|---------|-----------|
| **Abstraction** | `BaseHandler` (abstract `handle()`, `validate_input()`), `APIClient` (protected `_get()`, `_post()`) |
| **Encapsulation** | `StudentModel` (private `__data` dict), `DatabaseConnection` (private pool), `AuthService` (private `#currentUser`) |
| **Inheritance** | `AuthHandler → BaseHandler`, `StudentHandler → BaseHandler`, `AuthService → APIClient`, `StudentService → APIClient`, `UndergraduateStudent → StudentModel`, `GraduateStudent → StudentModel` |
| **Polymorphism** | `to_dict()` returns different shapes per subclass, `ResponseBuilder` class methods return uniform structure for different scenarios, `handle()` dispatches differently per HTTP method |

---

## 🗃️ Database

**All queries use stored procedures.** No raw SQL in application code.

| Stored Procedure | Purpose |
|-----------------|---------|
| `insert_student()` | Insert new profile with validation |
| `get_student_by_cognito_sub()` | Fetch profile by Cognito UUID |
| `list_all_students()` | Admin listing |
| `update_student_profile()` | Update mutable fields |

**Triggers:**

| Trigger | Event | Purpose |
|---------|-------|---------|
| `update_student_timestamp` | BEFORE UPDATE | Auto-refresh `updated_at` |
| `student_audit_trigger` | AFTER UPDATE | JSONB diff audit trail |
| `immutable_email_trigger` | BEFORE UPDATE | Prevent email changes |

---

## 🔐 Security

- Passwords never stored — delegated to AWS Cognito
- JWT access tokens stored in `sessionStorage` (not cookies or localStorage)
- RDS is in a private VPC subnet — not publicly accessible
- Lambda connects via VPC Security Groups
- All S3 buckets have public access blocked; served via CloudFront with OAC
- DB credentials passed via environment variables (never hardcoded)

---

## 📚 Documentation

| Doc | Contents |
|-----|---------|
| [API.md](docs/API.md) | All REST endpoints with request/response examples |
| [DATABASE.md](docs/DATABASE.md) | Full schema, stored procedures, triggers with SQL |
| [OOP.md](docs/OOP.md) | OOP concepts mapped to code with examples |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Step-by-step AWS deployment guide |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture + Excalidraw diagram |

---

## 👨‍💻 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, Vanilla CSS, Google Fonts (Inter + Outfit) |
| Auth | AWS Cognito User Pool |
| API | AWS API Gateway REST (JWT Authorizer) |
| Backend | AWS Lambda (Python 3.12), OOP class hierarchy |
| Database | Amazon RDS PostgreSQL 15 (stored procedures + triggers) |
| Cache | Amazon DynamoDB |
| CDN | Amazon CloudFront (OAC + HTTPS) |
| Storage | Amazon S3 |
| CI/CD | GitHub Actions |
| IaC | AWS SAM (CloudFormation) |
