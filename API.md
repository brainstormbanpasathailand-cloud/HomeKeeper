# API

Base URL: `/api/v1`. Interactive OpenAPI docs at `/docs`, schema at
`/api/v1/openapi.json`.

## Conventions

- **Auth:** `Authorization: Bearer <access_token>` header, or the `access_token`
  HttpOnly cookie (browser). Access tokens expire in 15 min; refresh via
  `/auth/refresh` (refresh tokens rotate on every use).
- **Pagination:** list endpoints that can grow accept `?page=<n>&size=<1..100>`
  and return `{ items, total, page, size, pages }`.
- **Filtering / sorting:** e.g. `GET /jobs?status=in_progress`,
  `GET /admin/users?role=technician`. Lists are returned newest-first.
- **Idempotency:** `POST /jobs` honours an `Idempotency-Key` header — repeating
  the same key for the same customer returns the original job instead of a duplicate.
- **Rate limiting:** auth endpoints are limited (default `10/minute` per IP, via
  `RATE_LIMIT_AUTH`). Exceeding returns `429`.
- **Errors:** `{ "detail": "message" }` for handled 4xx (FastAPI/HTTPException);
  `{ "error": "internal_error", "detail": "..." }` for unhandled 5xx.
- **Audit:** sensitive actions (login, OAuth, assignment, role change, moderation)
  are written to `audit_logs`.

## Auth
| Method | Path | Role | Notes |
|--------|------|------|-------|
| POST | `/auth/register` | public | email + password; issues token pair |
| POST | `/auth/login` | public | rate-limited |
| POST | `/auth/refresh` | public | rotates refresh token |
| POST | `/auth/logout` | auth | revokes current session |
| POST | `/auth/logout-all` | auth | revokes all sessions |
| GET | `/auth/me` | auth | current user |
| POST | `/auth/onboarding` | auth | requires ToS + Privacy acceptance |
| GET | `/auth/identities` | auth | linked login channels |
| DELETE | `/auth/identities/{id}` | auth | cannot remove the last one |
| GET | `/auth/sessions` | auth | active devices/sessions |

## OAuth (LINE / Google / Facebook)
| Method | Path | Notes |
|--------|------|-------|
| GET | `/auth/oauth/{provider}/start` | backend builds the authorization URL + signed state |
| POST | `/auth/oauth/{provider}/callback` | backend exchanges code, **verifies with provider**, upserts user |
| POST | `/auth/oauth/{provider}/link` | link an extra provider to the logged-in account |

See [AUTHENTICATION.md](AUTHENTICATION.md).

## Service Categories
| Method | Path | Role |
|--------|------|------|
| GET | `/service-categories` | public (`?include_inactive=true` for admin) |
| POST | `/service-categories` | admin |
| PATCH | `/service-categories/{id}` | admin |
| POST | `/service-categories/{id}/close` | admin |
| POST | `/service-categories/reorder` | admin |

## Properties & Assets (customer)
| Method | Path |
|--------|------|
| GET/POST | `/properties` |
| GET/PATCH/DELETE | `/properties/{id}` |
| GET/POST | `/properties/{id}/assets` |
| PATCH/DELETE | `/properties/{id}/assets/{asset_id}` |

## Jobs
| Method | Path | Role | Notes |
|--------|------|------|-------|
| POST | `/jobs` | customer | supports `Idempotency-Key` |
| GET | `/jobs` | auth | scoped by role (customer=own, tech=assigned, admin=all) |
| GET | `/jobs/{id}` | participant/admin | |
| POST | `/jobs/{id}/status` | tech/customer/admin | validated against status machine |
| POST | `/jobs/{id}/respond` | technician | accept/reject an assignment |
| POST | `/jobs/{id}/media` | participant | before/during/after evidence |

## Quotations
| Method | Path | Role |
|--------|------|------|
| POST | `/jobs/{id}/quotations` | technician |
| GET | `/jobs/{id}/quotations` | participant/admin |
| POST | `/quotations/{id}/decision` | customer (`approve`/`reject`/`revision`) |

## Technicians
| Method | Path | Role |
|--------|------|------|
| POST | `/technicians/apply` | auth |
| GET | `/technicians/me` | technician |
| GET | `/technicians/pending` | admin |
| POST | `/technicians/{id}/review` | admin (approve/reject → promotes role) |

## Home Health Records
| Method | Path | Role |
|--------|------|------|
| GET | `/health-records` | auth (`?property_id=`, `?asset_id=`) |
| GET | `/health-records/summary` | auth (cost totals, by year) |
| GET | `/health-records/{id}` | participant/admin |

## Warranty & Reviews
| Method | Path | Role |
|--------|------|------|
| POST/GET | `/warranty-claims` | customer / (admin sees all) |
| POST | `/warranty-claims/{id}/status` | admin |
| POST | `/jobs/{id}/review` | customer (completed jobs only) |
| GET | `/technicians/{id}/reviews` | public |
| POST | `/reviews/{id}/flag` | auth |
| POST | `/reviews/{id}/moderate` | admin |

## Notifications
| Method | Path |
|--------|------|
| GET | `/notifications` (`?unread_only=true`) |
| GET | `/notifications/unread-count` |
| POST | `/notifications/{id}/read` |
| POST | `/notifications/read-all` |

## Admin
| Method | Path | Role |
|--------|------|------|
| GET | `/admin/dashboard` | admin/dispatcher |
| GET | `/admin/users` | admin (`?role=`) |
| POST | `/admin/users/{id}/suspend` | admin |
| POST | `/admin/users/{id}/role` | super_admin |
| POST | `/admin/jobs/{id}/assign` | admin/dispatcher |
| GET | `/admin/audit-logs` | admin |

## Meta
| Method | Path |
|--------|------|
| GET | `/health` | liveness/readiness probe |
