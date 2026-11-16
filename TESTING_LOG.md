# RentWise verification log

**Updated:** 16 November 2026  
**Project:** A new 2026 local prototype inspired by a 2022 undergraduate **group** project (not its original source code).

## v0.1 — local, observed through the author's demonstration

The following results were observed in screenshots shared during the local walkthrough. They are **manual demonstrations**, not independent user-adoption metrics or a formal test report.

| Flow | Observation | Outcome |
|---|---|---|
| Registration and sign-in | Local account reached dashboard | Observed |
| Add property | Total properties changed from 0 to 1 | Observed |
| Add fictional tenant | Tenant appeared in directory | Observed |
| Add lease with past dates | Lease saved, active leases remained 0 | Observed |
| Add current lease | Active leases became 1, month balance ₹15,000 | Observed |
| Record synthetic ₹15,000 cash payment | November cash received became ₹15,000 and displayed outstanding became ₹0 | Observed |

### Issues found during the walkthrough

1. A lease date was entered incorrectly. The original version had no correction interface.
2. A full ₹15,000 transaction was labelled *partial payment* in its note; the original version had no correction interface.
3. The original dashboard subtracted payments according to **payment date**, not the month of rent they covered. That could misstate rent-month balances.

These findings motivated the v0.2 changes.

## v0.2 — automated checks

- API regression suite exercises owner isolation, overlapping lease rejection for single-unit properties, billed-month allocation, partial payment balances, correcting transactions, voiding records and edit/delete permissions.
- GitHub Actions additionally checks browser JavaScript **syntax**.
- The code retains older local SQLite records, with v0.1 payments marked **unallocated** until their actual rent month is reviewed and assigned.
- **Scope:** Passing automated tests does not prove browser usability, production security, financial compliance, or independent adoption.

**CI results:** See [GitHub Actions](https://github.com/devanandha/rentwise-rental-management/actions).

## v0.2 — manual retest still required

Using a **backup of the original local SQLite file**, test:

- [ ] Review v0.1 payments and assign billing month via Rent ledger → Edit
- [ ] Correct an expired lease's dates, without creating a duplicate
- [ ] Record a ₹5,000 payment toward a ₹15,000 current-month rent bill and verify ₹10,000 balance
- [ ] Record a payment in November allocated to December; November cash received changes but November rent allocation should not
- [ ] Correct and void a mistaken payment; confirm the balance and Activity log update
- [ ] Check Rent bills for a different month
- [ ] Inspect the interface at a narrower screen width and keyboard navigation

All demo accounts and property details should be fictional. Do **not** expose real tenant information or passwords in screenshots.

## Portfolio use

The 2022 graduation project was collaborative. This repository documents a **new, AI-assisted 2026 prototype**, technical progress and limited test results. The public repository and the author's manual test record do not, by themselves, show independent recognition or practical adoption. An external reviewer should evaluate the actual code or demonstration before signing any assessment.
