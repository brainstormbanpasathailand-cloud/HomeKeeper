# DATABASE

HomeKeeper uses **SQLAlchemy 2** models with **Alembic** migrations. Types are
kept portable (String, JSON, Numeric, Float, Date, DateTime) so the same schema
runs on **PostgreSQL** (production) and **SQLite** (local/tests). Enum-like
fields are stored as strings and validated at the Pydantic/service layer, which
lets us add values (e.g. a new job status) without an enum migration.

Every table inherits `created_at` and `updated_at` from the declarative `Base`.

## Migrations

```bash
cd backend
alembic upgrade head                              # apply
alembic revision --autogenerate -m "描述"          # after model changes
```

The initial migration lives in `backend/alembic/versions/`.

## Tables

### Identity & Auth
| Table | Purpose | Key columns |
|-------|---------|-------------|
| `users` | One HomeKeeper account per person | email, phone, password_hash, role, language, onboarding_completed, is_suspended |
| `auth_identities` | Linked login channels | provider, provider_user_id, provider_email — **UNIQUE(provider, provider_user_id)** |
| `user_sessions` | Refresh-token sessions | refresh_token_hash (SHA-256), user_agent, ip_address, expires_at, revoked |
| `user_addresses` | Saved addresses | address, province, district, latitude, longitude, is_default |
| `terms_acceptances` | ToS / Privacy acceptance audit | document, version, accepted_at, ip_address |

### Technicians
| Table | Purpose |
|-------|---------|
| `technician_profiles` | Verification, identity docs, geo (latitude, longitude, service_radius_km), online_status, availability_status, ratings, acceptance/cancellation rates |
| `technician_certificates` | Certificates with verification_status, verified_by |
| `technician_service_categories` | Which categories a tech serves, skill level, min call fee, emergency/scheduled acceptance |
| `technician_availability` | Weekly working hours |

### Catalogue
| Table | Purpose |
|-------|---------|
| `service_categories` | Admin-managed, slug, name_th/name_en, sort_order, is_active, requires_certification |
| `service_subcategories` | Optional finer breakdown |

### Property & Assets
| Table | Purpose |
|-------|---------|
| `properties` | house/condo/building/shop/office/car/motorcycle; address, geo, floor, unit, area, photos |
| `assets` | brand, model, serial_number, purchase/installation dates, warranty_start/end, receipt/manual URLs, maintenance_interval_days, next_maintenance_date |

### Jobs
| Table | Purpose |
|-------|---------|
| `job_requests` | job_number, customer, property, asset, category, urgency, geo, budget, requirements, status, assigned_technician_id, idempotency_key |
| `job_assignments` | Offer/accept/reject/reassign history, assigned_by |
| `job_status_history` | Every status transition (from, to, changed_by, note) |
| `job_media` | before/during/after/document/request evidence |

### Quotation & Parts
| Table | Purpose |
|-------|---------|
| `quotations` | version, labor/travel/inspection/emergency/other, discount, platform_fee, vat, total, valid_until, status |
| `quotation_items` | Line items |
| `parts` | part_name, brand, quantity, unit_price, supplier, warranty, authenticity (genuine/oem/compatible/used) |

### Home Health Record & Warranty
| Table | Purpose |
|-------|---------|
| `health_records` | **Auto-created on job completion.** service_date, issue, diagnosis, work_performed, parts_used (JSON), costs, before/after photos, warranty window, next_inspection/maintenance_date |
| `warranties` | has_warranty, warranty_days, covers_labor/parts, exclusions, start/end |
| `warranty_claims` | original_job_id, reason, evidence, status, resolution, cost_responsibility |

### Engagement & Ops
| Table | Purpose |
|-------|---------|
| `reviews` | Multi-dimension ratings (quality/punctuality/politeness/cleanliness/value/communication), overall, photos, flag/hide moderation |
| `coupons`, `coupon_redemptions` | Promotions (schema ready for Phase 4) |
| `notifications` | In-app notification center |
| `payments`, `payouts`, `disputes` | Financial rails (schema ready) |
| `audit_logs` | actor, action, entity, detail (JSON), ip, user_agent |

## Future-Proofing (Phase 2+)

The schema already carries fields for features deferred out of the MVP so no
migration churn is needed later:

- **Geo / dispatch:** `technician_profiles.latitude/longitude/location_updated_at/service_radius_km`, `online_status`, `availability_status`; `job_requests.latitude/longitude`.
- **AI matching:** ratings, acceptance_rate, cancellation_rate, category skills, certificate status.
- **Payments:** `payments`, `payouts`, `disputes`, quotation `platform_fee`/`vat`.
- **Loyalty:** `coupons`, `coupon_redemptions`.

## Entity Relationships (summary)

```
users 1─* auth_identities
users 1─* user_sessions
users 1─1 technician_profiles 1─* technician_certificates
                              1─* technician_service_categories
users(customer) 1─* properties 1─* assets
users(customer) 1─* job_requests *─1 service_categories
job_requests 1─* job_assignments
job_requests 1─* job_status_history
job_requests 1─* job_media
job_requests 1─* quotations 1─* quotation_items
                            1─* parts
job_requests 1─1 health_records
job_requests 1─* warranties
job_requests 1─* warranty_claims
job_requests 1─* reviews
```
