# LOCAL DEVELOPMENT

## Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 14+ (optional locally — SQLite works out of the box)

## Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# For a zero-dependency start, set in .env:
#   DATABASE_URL=sqlite:///./homekeeper.db

alembic upgrade head                 # create tables
python -m scripts.seed               # super admin + 33 service categories
uvicorn app.main:app --reload        # http://localhost:8000
```

- OpenAPI docs: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>
- Default super admin: `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` from `.env`
  (defaults `admin@homekeeper.local` / `ChangeMe!123` — change these).

### Using PostgreSQL locally
```bash
createdb homekeeper
# .env:
# DATABASE_URL=postgresql://<user>:<pass>@localhost:5432/homekeeper
alembic upgrade head && python -m scripts.seed
```

### Tests / lint
```bash
pytest                               # full suite
python -m compileall app scripts     # syntax check
```

## Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev                          # http://localhost:5173
```

`vite.config.ts` proxies `/api` to `http://localhost:8000` (override with
`VITE_PROXY_TARGET`), so run the backend alongside.

```bash
npm run build                        # type-check + production build + PWA
npm run lint
npm run preview                      # serve the production build
```

## Configuring social login locally (optional)

Fill the provider credentials in `backend/.env`:

- **Google:** create OAuth credentials at <https://console.cloud.google.com>,
  authorized redirect `http://localhost:5173/auth/callback/google`. Set
  `GOOGLE_CLIENT_ID/SECRET/CALLBACK_URL`.
- **LINE:** create a LINE Login channel, callback
  `http://localhost:5173/auth/callback/line`. Set `LINE_CHANNEL_ID/SECRET/CALLBACK_URL`.
- **Facebook:** create an app with Facebook Login, redirect
  `http://localhost:5173/auth/callback/facebook`. Set `FACEBOOK_APP_ID/SECRET/CALLBACK_URL`.

Without credentials the social buttons return a friendly "not configured"
message; email/password login works regardless.

## Typical flow to try
1. Register a customer → complete onboarding.
2. As a second user, `POST /technicians/apply`.
3. Log in as the seeded super admin → approve the technician
   (`/technicians/pending` → `/technicians/{id}/review`).
4. Customer creates a job → admin assigns → technician accepts → quotes →
   customer approves → technician completes → **Home Health Record appears**.
