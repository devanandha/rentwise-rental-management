# RentWise — Rental Management Prototype

**Status: Local v0.2 prototype (November 2026). API regression tests run in GitHub Actions. Not deployed, independently validated or production-ready.**

A new Python/FastAPI + SQLite web application demonstrating landlord-facing property, tenant, lease, billing-month and rent-ledger workflows. The app has a responsive, custom dashboard and uses synthetic or user-entered local data.

## Why this project exists

This is an **independently maintained successor project** inspired by a 2022 final-year *group* presentation, **House Rental Payment Web App**, completed at Sacred Heart College, Thevara by **Devanandha VS and Rinsha Basheer**. The original presentation proposed a Python/Django/MySQL rental system with homeowner registration, building and tenant management, payment records and rental listings. The 2026 implementation is new code and is **not** represented as the original group project's source code or as a product reviewed by the college in 2022.

This project was initially scaffolded with AI assistance and should be developed, evaluated and documented through subsequent engineering work. Do not represent generated code alone as independent innovation or external recognition.

## Implemented in v0.2

- Local signup and login; password hashes using PBKDF2 and signed session cookies
- Owner-scoped property and tenant records, with editing and guarded deletion
- Lease creation and editing; prevent overlapping leases for single-unit properties
- Manually record offline rent payments, assign a billing month, and correct the amount, date, month, method or note
- Void payment records with a reason, without deleting their historical record
- Computed monthly rent bills: rent charged, allocated payments, remaining balance and overpayment credit by lease
- Distinguish cash recorded during a calendar month from payments allocated to that rent month
- Local activity log for create/edit/delete/correct/void events (not a tamper-proof audit)
- Responsive browser interface, monthly billing tab and API documentation at `/docs`
- Automated regression tests for access isolation, overlapping leases, corrections and payment month allocation

**Not implemented:** actual payment gateway, automatic reminders, bank reconciliation, numbered tax invoices, PDF statements/receipts, refund accounting, proration, late fees, forecasting, production hosting, identity verification or tenant self-service. **Payments are records only; no money is moved.**

**Rent-bill calculation:** The app charges the **full monthly rent** when a lease overlaps any part of that month (no proration). Payments have an explicit `billing_month` and reduce that month's bill, even if paid in another month. Cash received uses the actual payment date. Remaining bill balances do not go negative; excess is shown separately as an unapplied credit and is **not** automatically carried to another month. It is a demonstration ledger, not an accounting statement or tax invoice.

**Legacy migration:** Payments recorded in v0.1 did not store a rent month. When opening v0.2 with the existing SQLite database, those payments remain intact but **unallocated**. Open **Rent ledger → Edit** to assign each one to its correct rent month; until then it is excluded from billed-month allocations. Never assume the payment date is the month it was intended to cover.

**Record restrictions:** A property or tenant with leases cannot be deleted; a lease with payment records cannot be deleted. For multi-unit properties, unit-specific occupancy is not yet modelled, so overlapping tenancies require manual review. The activity log is held locally and is not tamper-proof.

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

### Upgrading an existing v0.1 local test installation

1. Stop the running server with **Ctrl+C** in Command Prompt.
2. **Back up `rentwise.sqlite3`** (in the old project folder) somewhere safe before making changes.
3. Download the latest GitHub ZIP and replace the **source files** (`app/`, `tests/`, `README.md`, etc.) in the existing project folder. **Do not overwrite/delete `rentwise.sqlite3` or your existing `.venv` environment.** An alternative is to extract a fresh project and copy your backed-up SQLite database into that new folder.
4. Restart the app with the same `python -m uvicorn app.main:app --reload` command. At startup, the local SQLite schema receives extra columns without clearing old records.
5. In **Rent ledger**, assign every old payment to its actual rent month using **Edit**. Verify **Rent bills** and **Overview** afterward.

For Windows Command Prompt, if your virtual environment remains one folder above the project, use `..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload` from the folder containing `requirements.txt`.

Run the automated tests:

```bash
python -m pip install pytest httpx
pytest -q
```

## Security & privacy

**Portfolio prototype only. Do not put real tenant details, payment information or sensitive IDs into this app.** Before a real pilot it needs a threat model, proper CSRF and abuse protections, password-reset and rate-limiting functionality, audit events, legal/privacy analysis, security review, HTTPS deployment and database backups. Demo with synthetic records only. Never commit `.env`, secrets or the local database.

## Potential next milestones (not yet completed)

1. Numbered invoices, due dates, reminders and printable receipts (with appropriate legal and tax review).
2. Unit-level occupancy, refunds, deposit handling and explicit credits carried to other billing months.
3. Stronger security: CSRF protection, rate limiting, production hosting controls and backups.
4. Browser end-to-end tests, accessibility review, comprehensive schema migrations and export functionality.
5. A tightly scoped pilot with a consenting landlord and anonymised usage feedback; consider prediction features only if appropriately evaluated.

## Test evidence and academic review

See [TESTING_LOG.md](TESTING_LOG.md) for the observed v0.1 and v0.2 manual workflows, including the ₹15,000 rent / ₹5,000 then ₹7,000 corrected-payment test, and remaining test cases. These are local prototype observations, not independent adoption or endorsement.

The [academic technical review brief](ACADEMIC_REVIEW_BRIEF.md) explains the relationship to the 2022 undergraduate group project, gives a reproducible walkthrough, and lists questions for a referee to assess from their own first-hand knowledge. It is not a pre-written endorsement.

## Evidence / provenance

| Claim | Evidence | Current status |
|---|---|---|
| Original 2022 group project | Undergraduate presentation and university transcript | Historic academic work (separate from this code) |
| 2026 successor implementation | This repository's commit history and source files | v0.2 local prototype; not yet reviewed by Dr Regitha |
| Functional tests | `tests/test_api.py`, `tests/test_v02.py`, GitHub Actions | Automated regression checks; not a third-party audit |
| Independent adoption or impact | Pilot logs, feedback, external code reviews | **Not yet established** |

**Global Talent documentation note:** A public repository can document technical progression, but is not on its own independent recognition. Dr Regitha can describe her *actual 2022 assessment* of the group project. Any remarks about this 2026 successor should only be included after she has personally reviewed its code or demonstration, and should accurately state what she saw.
