# DEPLOYMENT (Render)

HomeKeeper deploys as three Render resources defined in [`render.yaml`](render.yaml):

1. **homekeeper-db** — Render PostgreSQL
2. **homekeeper-api** — FastAPI backend (Docker Web Service, `rootDir: backend`)
3. **homekeeper-web** — React static site (`rootDir: frontend`)

## Option A — Blueprint (recommended)

1. Push this repo to GitHub.
2. In Render: **New → Blueprint**, select the repo. Render reads `render.yaml`
   and provisions the database, backend, and frontend.
3. Fill the `sync: false` secrets in the dashboard (see below).
4. Set the frontend `VITE_API_BASE_URL` to
   `https://homekeeper-api.onrender.com/api/v1` (your API host + `/api/v1`).
5. Deploy. The backend container runs `alembic upgrade head` on start.
6. Seed once (super admin + categories): open the backend service **Shell** and run
   ```bash
   python -m scripts.seed
   ```

## Option B — Manual

**PostgreSQL:** New → PostgreSQL. Copy the *Internal Connection String*.

**Backend:** New → Web Service → Docker, root directory `backend`.
- Health check path: `/health`
- Env vars: `DATABASE_URL` (from the DB), `JWT_SECRET` (generate), `ENV=production`,
  `FRONTEND_URL`, `BACKEND_URL`, `CORS_ORIGINS` (= frontend URL),
  `COOKIE_SECURE=true`, `COOKIE_SAMESITE=none`, plus OAuth/storage/email secrets.
- Start is handled by the Dockerfile (`alembic upgrade head && uvicorn …`).

**Frontend:** New → Static Site, root directory `frontend`.
- Build: `npm ci && npm run build` · Publish: `dist`
- Env: `VITE_API_BASE_URL=https://<api-host>/api/v1`
- Add a rewrite rule `/* → /index.html` (SPA routing) — already in `render.yaml`.

## Required environment variables

Backend (see `backend/.env.example` for the full list):

| Variable | Notes |
|----------|-------|
| `DATABASE_URL` | from Render PostgreSQL |
| `JWT_SECRET` | generate; keep secret |
| `JWT_ACCESS_EXPIRE_MINUTES` / `JWT_REFRESH_EXPIRE_DAYS` | token lifetimes |
| `FRONTEND_URL` / `BACKEND_URL` / `CORS_ORIGINS` | public URLs |
| `COOKIE_SECURE=true`, `COOKIE_SAMESITE=none` | cross-site cookies |
| `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` | first super admin |
| `LINE_CHANNEL_ID/SECRET/CALLBACK_URL` | LINE Login |
| `GOOGLE_CLIENT_ID/SECRET/CALLBACK_URL` | Google |
| `FACEBOOK_APP_ID/SECRET/CALLBACK_URL` | Facebook |
| `CLOUDINARY_URL` or `STORAGE_*` | media storage |
| `EMAIL_HOST/PORT/USERNAME/PASSWORD/FROM` | notifications |

Frontend: `VITE_API_BASE_URL`.

## OAuth callback URLs

Register each provider's redirect URI as
`https://<frontend-host>/auth/callback/{line|google|facebook}` and set the
matching `*_CALLBACK_URL` backend env var to the same value.

## Post-deploy checklist
- [ ] `GET https://<api-host>/health` returns `{"status":"ok"}`
- [ ] `python -m scripts.seed` run once
- [ ] Change the seeded admin password
- [ ] Frontend loads, PWA installable, `/api` reaches the backend
- [ ] CORS origin matches the frontend URL exactly
- [ ] OAuth redirect URIs match on both provider console and backend env

## Notes
- Render's **free** PostgreSQL and services sleep/expire; use paid plans for
  production persistence.
- Migrations run automatically on backend deploy; to run manually use the
  service Shell: `alembic upgrade head`.
