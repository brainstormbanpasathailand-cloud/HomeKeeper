# BUSINESS RULES

## Roles

`customer` → default for everyone. `technician` → after admin approval of a
`technician_profile`. `admin` / `super_admin` / `support` / `dispatcher` →
staff. Only `super_admin` can change another user's role. A `super_admin`
cannot be suspended.

## Technician onboarding

1. Any user can `POST /technicians/apply` (creates a `technician_profile` with
   `verification_status = submitted`; the user is **not** a technician yet).
2. Admin reviews via `POST /technicians/{id}/review`.
   - **Approve** → `verification_status = approved`, `approved_at`/`approved_by`
     recorded, and the underlying user's role becomes `technician`. A
     `technician_approved` notification is sent.
   - **Reject** → `verification_status = rejected`.
3. A technician can only be assigned to jobs after approval.

## Service categories

Admin-managed only. They can be created, edited, closed (soft-disable via
`is_active = false`), and reordered (`sort_order`). Categories are **never
hard-coded in the frontend** — the UI reads `GET /service-categories`. The seed
script installs 33 default Thai categories.

## Job lifecycle (status machine)

Statuses: `draft, requested, reviewing, searching, assigned, accepted,
rejected, traveling, arrived, inspecting, quoted, quotation_revision_requested,
approved, in_progress, paused, completed, customer_confirmed, cancelled,
disputed, warranty_claim, closed`.

Transitions are enforced in `app/services/jobs.py::ALLOWED_TRANSITIONS`. A
non-admin transition that isn't allowed returns `409`. Admin/dispatcher actions
may `force` a transition (e.g. assignment, reassignment).

```
requested → (reviewing|searching|assigned) → assigned → accepted
accepted → traveling → arrived → inspecting → (quoted | in_progress)
quoted → (approved | quotation_revision_requested | cancelled)
quotation_revision_requested → quoted
approved → in_progress → (paused | completed)
completed → (customer_confirmed | disputed) → closed
```

### Who may drive which transition
- **Technician** (own job only): `traveling, arrived, inspecting, in_progress,
  paused, completed`.
- **Customer** (own job only): `customer_confirmed, cancelled, disputed`.
- **Admin/dispatcher:** may set any status (assignment, corrections).

### MVP dispatch
The admin/dispatcher assigns a technician (`POST /admin/jobs/{id}/assign`),
which creates a `job_assignment` (status `offered`) and moves the job to
`assigned`. The technician accepts/rejects via `POST /jobs/{id}/respond`:
- accept → assignment `accepted`, job `accepted`, customer notified.
- reject → assignment `rejected`, job returns to `searching`, `assigned_technician_id` cleared.

## Quotation rules

- Only the **assigned technician** can create a quotation. Each new quote gets an
  incrementing `version`.
- Total is computed server-side:
  `labor + travel + inspection + emergency + other + Σ(items) + Σ(parts) +
  platform_fee + vat − discount`.
- Creating a quote moves the job to `quoted` and notifies the customer.
- The **customer** decides: `approve` (job → `approved`, technician notified),
  `reject`, or `revision` (job → `quotation_revision_requested`).
- **A technician cannot start chargeable work (`in_progress`) until a quotation
  is approved** — enforced in `POST /jobs/{id}/status` (returns `409` otherwise).

## Parts

Each part records authenticity: `genuine | oem | compatible | used`, plus
brand, quantity, unit price, supplier, warranty period, and optional serial.

## Before/After evidence

Technicians upload `before`, optional `during`, and `after` media via
`POST /jobs/{id}/media`. These photos feed directly into the Home Health Record.

## Home Health Record (automatic)

When a job reaches **`completed`**, `_on_completed` in `app/services/jobs.py`
**auto-creates a `health_records` row** (idempotent — one per job) capturing:
service date, issue, diagnosis, work performed, technician, parts used, labor/
parts/total cost, before & after photos, and warranty window. It also creates a
default **`warranties`** row (30 days, covers labor; covers parts if parts were
used) and links the warranty window back onto the record. The customer is
notified.

The customer's Home Health view shows a care **timeline**, per-asset history,
cost summary by year, warranty windows, next-maintenance dates, and evidence.

## Warranty claims

A customer can `POST /warranty-claims` against an original job **only if that
job has an active warranty**. Claims move through
`submitted → reviewing → approved/rejected → resolved` (admin-driven), with the
customer notified on each update.

## Reviews

Only the customer of a **completed** job may review, **once**. Ratings cover
quality, punctuality, politeness, cleanliness, value, communication; the overall
is their average and the technician's `average_rating` is recomputed. Reviews
can be flagged by anyone and hidden by an admin.

## Notifications

In-app notifications are created for: account creation, technician approval, new
job assignment, job accepted, traveling/arrived, quotation created/approved, job
completed, warranty claim updates. The service is structured so Email, LINE
Messaging API, SMS, and Web Push can be added as additional channels without
changing call sites.

## Idempotency

`POST /jobs` accepts an `Idempotency-Key` header; a repeat with the same key for
the same customer returns the original job. `payments` carries the same field
for when payment processing is added.
