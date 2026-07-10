# HomeKeeper

**Operating System สำหรับบ้าน** — แพลตฟอร์มดูแลบ้าน รถ คอนโด สวน เครื่องใช้ไฟฟ้า
งานทำความสะอาด งานต่อเติมและรีโนเวต ไม่ใช่แค่ Marketplace เรียกช่าง แต่เป็นแพลตฟอร์ม
ดูแลทรัพย์สินตลอดอายุการใช้งาน พร้อม **Home Health Record** ที่เก็บประวัติการติดตั้ง
การซ่อม การบำรุงรักษา อะไหล่ ค่าใช้จ่าย รูปก่อน/หลัง ช่างผู้ให้บริการ การรับประกัน
และกำหนดการตรวจครั้งต่อไป

Responsive Web Application + Progressive Web App (PWA)

---

## Technology Stack

| Layer | Tech |
|-------|------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, React Router, TanStack Query, React Hook Form, Zod, PWA |
| Backend | Python, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2 |
| Database | PostgreSQL (SQLite for local/tests) |
| Auth | JWT (access + rotating refresh), OAuth 2.0 / OIDC (LINE, Google, Facebook) |
| Hosting | Render (Web Service + Static Site + PostgreSQL) |
| Storage | Cloudinary / S3-compatible (pluggable) |

## Repository Structure

```
HomeKeeper/
├── backend/            FastAPI application
│   ├── app/
│   │   ├── models/     SQLAlchemy models (see DATABASE.md)
│   │   ├── schemas/    Pydantic request/response models
│   │   ├── api/routes/ REST endpoints (see API.md)
│   │   ├── services/   Business logic (auth, oauth, job lifecycle, notifications)
│   │   ├── core/       Pagination, rate limiting
│   │   ├── config.py   Settings from environment
│   │   ├── security.py JWT + password/token hashing
│   │   └── main.py     App entrypoint
│   ├── alembic/        Database migrations
│   ├── scripts/seed.py Seed super admin + service categories
│   ├── tests/          Pytest suite
│   └── Dockerfile
├── frontend/           React + Vite PWA
│   └── src/
│       ├── pages/      Screens (customer / technician / admin)
│       ├── components/ Layout, ProtectedRoute, StatusBadge, SocialButtons
│       ├── auth/       Auth context
│       ├── i18n/       Thai / English
│       └── lib/        API client, types
├── render.yaml         Render blueprint
├── DATABASE.md  API.md  AUTHENTICATION.md  BUSINESS_RULES.md
├── SECURITY.md  PRIVACY.md  DEPLOYMENT.md   LOCAL_DEVELOPMENT.md
```

## Quick Start

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                 # then edit
alembic upgrade head
python -m scripts.seed               # super admin + service categories
python -m scripts.seed_demo          # (optional) realistic demo data — see below
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
cp .env.example .env
npm run dev                          # http://localhost:5173
```

API docs live at `http://localhost:8000/docs`.

See **[LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md)** for the full setup and
**[DEPLOYMENT.md](DEPLOYMENT.md)** for deploying to Render.

### Demo data

`python -m scripts.seed_demo` populates the platform as if it were in real use:
2 customers with properties/assets, 2 approved technicians with skills, and 4
jobs across statuses — including one fully completed job that flows through the
real completion logic to auto-generate a Home Health Record + warranty + review.
It is idempotent and prints the login accounts (all share password
`Demo123456`). Delete or change these accounts before any real launch.

## Roles

`customer` · `technician` · `admin` · `super_admin` · `support` · `dispatcher`

ทุกคนเริ่มเป็น `customer`. การเป็นช่างต้องสร้าง `technician_profile` และผ่านการอนุมัติจากแอดมิน.

## MVP Feature Status

- [x] Register / login (email + password), rotating refresh tokens, sessions
- [x] Social login scaffolding (LINE / Google / Facebook) with backend token verification
- [x] Role-based access control + account linking (`auth_identities`)
- [x] Customer onboarding (phone, region, language, ToS/Privacy acceptance)
- [x] Properties & assets (house, condo, car, appliances, warranty tracking)
- [x] Service categories (admin-managed, orderable, not hard-coded)
- [x] Job requests with urgency, idempotency key
- [x] Admin/dispatcher assignment; technician accept/reject; status machine
- [x] Quotations (labor, parts, travel, fees, VAT) + customer approve/reject/revision
- [x] Before/after evidence upload
- [x] **Auto-generated Home Health Record + Warranty on completion**
- [x] Warranty claims, reviews (multi-dimension), notifications
- [x] Admin dashboard, user management, audit logs
- [x] Responsive mobile-first UI + PWA (installable, offline shell)
- [x] Thai / English i18n

Deferred to later phases (data model already supports): real-time GPS, AI
matching, promotions/loyalty, payments/payouts, LINE Messaging / SMS / Web Push.

## Testing

```bash
cd backend && source .venv/bin/activate && pytest
```

Covers authentication, OAuth callbacks (mocked providers), RBAC, the full job
lifecycle, quotations, Home Health Record generation, warranty claims, and
idempotency.

## Documentation

| Doc | Contents |
|-----|----------|
| [DATABASE.md](DATABASE.md) | Schema, tables, relationships, future-proofing |
| [API.md](API.md) | REST endpoints, conventions, error format |
| [AUTHENTICATION.md](AUTHENTICATION.md) | JWT, OAuth flows, account linking, sessions |
| [BUSINESS_RULES.md](BUSINESS_RULES.md) | Job status machine, quotation & warranty rules |
| [SECURITY.md](SECURITY.md) | Threat model, secrets, rate limiting, audit |
| [PRIVACY.md](PRIVACY.md) | Data handling, PII, retention |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Render deployment (backend, frontend, PostgreSQL) |
| [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md) | Local setup |
