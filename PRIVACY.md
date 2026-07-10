# PRIVACY

HomeKeeper processes personal data to connect customers with technicians and to
maintain each property's service history. This document summarizes how data is
handled in the platform's design.

## Data we store

| Category | Examples | Source |
|----------|----------|--------|
| Account | name, email, phone, language, region | user / social provider |
| Identity links | provider, provider_user_id, provider_email, avatar | LINE/Google/Facebook (verified) |
| Technician KYC | legal name, national ID/passport, DOB, ID document images, selfie | technician (for verification) |
| Property & assets | addresses, geo-coordinates, appliances, serials, receipts | customer |
| Jobs | descriptions, photos/videos, geo, contact phone | customer / technician |
| Service history | Home Health Records, warranties, costs, before/after photos | generated from jobs |
| Reviews | ratings, comments, photos | customer |
| Security | session IP/user-agent, audit logs, ToS/Privacy acceptance | system |

## Principles

- **Minimal scope.** Social login requests only `openid`/`profile`/`email` (or
  `public_profile,email`). We store the provider user ID and basic profile, and
  do not retain provider access tokens beyond what's needed.
- **Purpose limitation.** KYC documents are used solely for technician
  verification; geo-coordinates for dispatch/nearby matching.
- **Consent.** Onboarding records explicit acceptance of the Terms of Service and
  Privacy Policy (`terms_acceptances`, with version, timestamp, IP).
- **Security.** See [SECURITY.md](SECURITY.md) — hashed passwords, hashed refresh
  tokens, HTTPS, RBAC, audit logging.
- **Access control.** Customers see only their own data; technicians see only
  their assigned jobs; staff access is role-gated and audited.

## Retention & user rights

- Users can view linked login channels and active sessions, unlink providers,
  and log out of all devices from the **Security** page.
- Account deletion / data export and formal retention schedules are part of the
  compliance roadmap (PDPA/GDPR-aligned). Health records tied to a property may
  be retained for warranty and service-history purposes per policy.

## Third parties

- **OAuth providers:** LINE, Google, Facebook (authentication).
- **Storage:** Cloudinary or S3-compatible (media/documents).
- **Email:** SMTP provider (notifications).
- **Hosting:** Render (application + PostgreSQL).

Sub-processors are configured via environment variables and may change; the
production Privacy Policy should enumerate the live set.

## Contact

Privacy questions: the workspace/organization operating this HomeKeeper
deployment is the data controller and should publish a contact address in the
production Privacy Policy.
