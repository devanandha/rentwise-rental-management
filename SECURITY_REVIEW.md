# RentWise v0.2 — preliminary source security review

**Date:** 17 November 2026  
**Scope:** Repository source review of `app/main.py`, `app/static/app.js`, `Dockerfile`, `requirements.txt`, tests and documented Railway setup.  
**Status:** **Preliminary code review; NOT a penetration test, audit certification, compliance approval, or production-readiness sign-off.** No access to the private Railway variables or deployment filesystem was used for this review.

## Summary

RentWise is a publicly reachable **fictional-data-only** rental-management prototype. It has some useful security foundations (PBKDF2 password hashing, signed sessions, owner-scoped record queries and escaping of displayed user strings), but **public self-registration, login abuse protection, CSRF protection and recovery controls are incomplete**.

### Findings by priority

| ID | Severity / priority | Verified observation from source | Action before allowing external sign-ups |
|---|---|---|---|
| SEC-01 | **High** | `POST /api/register` accepts any valid new email; no invitation/allowlist or registration disable switch. The public URL is accessible to anyone. | Add an invite-only registration mechanism or disable public signup; share a limited, controlled demo with invited reviewers. |
| SEC-02 | **High** | `POST /api/login` performs password verification with **no application login throttling or backoff**. | Add tested, proxy-aware, persistent or managed rate limits; avoid a naïve per-account lockout that could be used to deny access to legitimate users. |
| SEC-03 | **High** | State-changing authenticated JSON endpoints have **no explicit CSRF token or Origin/Referer verification**. The session cookie uses `same_site="lax"`, which helps but is a defence-in-depth measure, not universal CSRF protection. | Apply a tested CSRF strategy (for example strict Origin checks plus a CSRF token or custom request header) to all state-changing routes including logout and account actions. |
| SEC-04 | **Medium** | `SessionMiddleware` defaults to a **14-day** signed session unless configured otherwise; app defaults to a **random session secret** when `RENTWISE_SESSION_SECRET` is missing. Session keys may rotate on restart if not set. | Fail fast when production mode lacks a strong configured secret; shorten session lifetime for demo reviewers; document secret rotation and cookie expiry. |
| SEC-05 | **Medium** | Session cookies use Starlette's `HttpOnly` and `SameSite=Lax` defaults. The `Secure` flag is enabled only when `RENTWISE_HTTPS_ONLY=1`. | Verify `RENTWISE_HTTPS_ONLY=1` in the actual hosted service and test browser cookies. Never disclose session secret values. |
| SEC-06 | **Medium** | Deployment image uses `python:3.12-slim` with no dedicated non-root `USER`; packages have broad version ranges and no lockfile or vulnerability scanning stage. | Plan least-privilege volume ownership, pin and scan dependencies, and implement dependency-update testing before a real pilot. |
| SEC-07 | **Medium** | Tenant phone/email and audit change payloads are stored in SQLite; the audit function stores before/after field values. There is no documented retention/deletion policy or production-grade privacy mechanism. | Restrict to synthetic data until privacy, retention, backup access, deletion and consent policies are designed. |
| SEC-08 | **Medium** | Backups are **manual**; there is no automated recovery schedule or documented restore drill. | Maintain a private off-volume backup and independently test a restore to a disposable local copy. |
| SEC-09 | **Low / medium** | FastAPI's interactive OpenAPI docs are exposed by default at `/docs` (source does not disable them). This reveals API structure, not passwords. | Disable or restrict docs if the deployment becomes a production service. |

### Existing safeguards observed

- `User.password_hash` stores **salted PBKDF2-HMAC-SHA256** digests; cleartext passwords are not stored by the application.
- Authentication uses Starlette's **signed cookie-backed sessions**. The cookie is `HttpOnly` by the middleware. Cookies are signed, **not encrypted**, so do not place secrets in session payloads.
- `get_owned()` checks `owner_id` on record operations, and list endpoints filter by `owner_id`; automated tests exercise cross-account access isolation. This is a useful baseline, **not proof** against all insecure direct object reference defects.
- SQLAlchemy's query construction uses bound SQL rather than direct string-concatenated SQL for user-facing filters reviewed.
- The browser UI calls `escapeHtml()` when rendering tenant, property and account strings from API responses. This reduces the observed DOM XSS risk, although no full browser security test was performed.
- Online Railway service in `authentic-mercy` uses a persistent `/data` volume, a configured database path and a working HTTPS domain; user reported the fictional property surviving an automatic redeployment on **17 November 2026**.

### Host and business logic caveats

- **Not a payment processor**: rent entries represent manually recorded offline payments; no gateway is connected.
- The rent calculation deliberately assumes full-month charges for leases touching the month; **proration, deposits, refunds, credit carry-forward and legally valid invoicing are incomplete**.
- Multi-unit occupancy conflicts are not fully modelled.
- Running a small SQLite database on one Railway volume is not a horizontally scalable production architecture.
- Existing `AuditEvent` is a local change record, **not a tamper-proof compliance ledger**.

## Priority remediation plan (not implemented by this review)

1. Protect external demos with **invited-only registration**, plus explicit consent and test-only instructions.
2. Implement **CSRF protection** and regression tests for same-origin browser requests, malicious cross-origin requests and authenticated writes.
3. Implement **login throttling**, application-side abuse controls and tests; check for proxy/IP forwarding pitfalls.
4. Enforce explicit production session secret, HTTPS cookies, shorter max-age, standard security headers, and error handling.
5. Pin/scan dependencies, review least-privilege filesystem access, document backup/restore rehearsal.
6. Run automated security tests and have an **independent human** assess the source and a controlled demo before claiming security readiness.

## Safe review mode for Dr Regitha

Until the high-priority issues are addressed, prefer a **screen-shared walkthrough** of the live fictional-data demo plus public GitHub code/tests, rather than asking a reviewer to register and use a personal password or real data. Invite only with clear permission; screenshots must not expose email, passwords, session secrets or tenant information.

## Review basis and references

- Source: [`app/main.py`](app/main.py), [`app/static/app.js`](app/static/app.js), [`requirements.txt`](requirements.txt), [`Dockerfile`](Dockerfile).
- Tests: [`tests/`](tests/).
- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html).
- [Starlette SessionMiddleware documentation](https://www.starlette.io/middleware/).
- [Railway volume and backup documentation](https://docs.railway.com/volumes/backups).

**Disclosure:** This is a guided preliminary review performed with AI assistance. The findings are not equivalent to an independently performed external security assessment.
