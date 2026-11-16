# RentWise — Rental Management Prototype

**Status: Functional local MVP (November 2026). Not deployed or independently validated. Not production-ready.**

A new Python/FastAPI + SQLite web application demonstrating landlord-facing property, tenant, lease and rent-ledger workflows. The app has a responsive, custom dashboard and uses synthetic or user-entered local data.

## Why this project exists

This is an **independently maintained successor project** inspired by a 2022 final-year *group* presentation, **House Rental Payment Web App**, completed at Sacred Heart College, Thevara by **Devanandha VS and Rinsha Basheer**. The original presentation proposed a Python/Django/MySQL rental system with homeowner registration, building and tenant management, payment records and rental listings. The 2026 implementation is new code and is **not** represented as the original group project's source code or as a product reviewed by the college in 2022.

This project was initially scaffolded with AI assistance and should be developed, evaluated and documented through subsequent engineering work. Do not represent generated code alone as independent innovation or external recognition.

## Implemented in this MVP

- Local signup and login; password hashes using PBKDF2 and signed session cookies
- Owner-scoped property and tenant records
- Lease records linking a tenant, property, dates and monthly rent
- Manual/offline rent payment recording with method, date and note
- Dashboard showing estimated expected, recorded and outstanding amounts for the current month
- Responsive browser UI with empty states, forms and activity tables
- API documentation at `/docs` and automated API smoke tests

**Not implemented:** actual payment gateway, reminders, bank reconciliation, recurring invoices, rent proration, automatic late fees, rent forecasting, production hosting, identity verification, audit trails, PDF receipts or tenant self-service. **Payments are records only; no money is moved.**

The monthly dashboard is a **simplified operational indicator**, not an invoice or accounting statement: it assumes full monthly rent for each lease active in that month and subtracts payments recorded in that month regardless of which billing period they cover. It does not account for credits, deposits, rent proration or refunds.

## Getting started

Install Python 3.11+ and run:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 and create your own local account. No demo credentials are shipped. The SQLite database is created at `rentwise.sqlite3` and is ignored by Git.

For a stable local login cookie across restarts, set `RENTWISE_SESSION_SECRET` to a strong secret environment variable. For deployment on HTTPS, set `RENTWISE_HTTPS_ONLY=1`. The default session secret is ephemeral and sessions reset upon server restart.

Run the automated tests:

```bash
python -m pip install pytest httpx
pytest -q
```

## Security & privacy

**Portfolio prototype only. Do not put real tenant details, payment information or sensitive IDs into this app.** Before a real pilot it needs a threat model, proper CSRF and abuse protections, password-reset and rate-limiting functionality, audit events, legal/privacy analysis, security review, HTTPS deployment and database backups. Demo with synthetic records only. Never commit `.env`, secrets or the local database.

## Potential next milestones (not yet completed)

1. Proper rental invoicing and allocation of partial payments to billing periods.
2. Unit-level occupancy, tenant invitations and role separation.
3. Data export, transaction audit log, negative/error-path tests and accessibility review.
4. A tightly scoped pilot with a consenting landlord, documented permission and anonymised usage feedback.
5. Only then, consider independently evaluated prediction/automation features if appropriate data exists.

## Evidence / provenance

| Claim | Evidence | Current status |
|---|---|---|
| Original 2022 group project | Undergraduate presentation and university transcript | Historic academic work (separate from this code) |
| 2026 successor implementation | This repository's commit history and source files | Prototype; not yet reviewed by Dr Regitha |
| Functional tests | `tests/test_api.py` | Local test results, not third-party validation |
| Independent adoption or impact | Pilot logs, feedback, external code reviews | **Not yet established** |

**Global Talent documentation note:** A public repository can document technical progression, but is not on its own independent recognition. Dr Regitha can describe her *actual 2022 assessment* of the group project. Any remarks about this 2026 successor should only be included after she has personally reviewed its code or demonstration, and should accurately state what she saw.