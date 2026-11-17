# RentWise verification log

**Updated:** 17 November 2026  
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

## v0.2 — manually observed local walkthrough, 16 November 2026

The author shared screenshots of a local v0.2 instance with **fictional demonstration records**. The screenshots were examined during the walkthrough, but have not been added to this public repository. These observations should not be described as an independent technical assessment.

| Test | Observed result | Status |
|---|---|---|
| Start updated application | "Rent bills" and "Activity log" appeared in the sidebar | Observed |
| Add fictional property and change its name | "Sunrise Residency" subsequently appeared in the lease billing table; author reported the Edit feature worked | Author-reported edit; final name independently visible in screenshot |
| Create a fictional tenant and active lease | One monthly bill for Sunrise Residency / Rahul Kumar, rent ₹15,000, was shown | Observed |
| Record November 2026 partial payment | Rent due ₹15,000; allocated ₹5,000; balance ₹10,000; unallocated ₹0; status "partial" | Observed |
| Correct payment amount | The payment ledger showed **one** recorded payment of ₹7,000 allocated to 2026-11 | Observed |
| Recalculate after correction | Rent due ₹15,000; allocated ₹7,000; balance ₹8,000; unallocated ₹0; status "partial" | Observed |
| Check activity log | A `payment` / `corrected` event for record ID 1 appeared after the original `created` event | Observed |

These manual checks support the narrow claim that the local prototype's **demonstrated** partial-payment calculation and correction flow functioned as expected with the sample data. They do not establish production-grade financial accuracy or real customer adoption.

### Further manual checks still required

- [ ] Restore the original v0.1 SQLite database from a backup and review legacy unallocated payments
- [ ] Correct an expired lease's dates without creating a duplicate
- [x] Record a ₹5,000 payment toward ₹15,000 rent and verify ₹10,000 balance (new fictional test dataset)
- [ ] Record a payment in November allocated to December; confirm that November cash received changes but November's rent allocation does not
- [x] Correct ₹5,000 to ₹7,000; verify ₹8,000 balance and a `corrected` activity entry
- [ ] Void a payment and verify its effect on the rent balance and log
- [ ] Check Rent bills for a different month
- [ ] Inspect the interface at a narrower screen width and keyboard navigation

Do **not** expose real tenant information, credentials, or personal details in public screenshots.

## Hosted Railway demo — manual verification and redeploy regression, 16 November 2026

A screenshot showed the hosted website at `https://rentwise-rental-management-production.up.railway.app` with RentWise v0.2, an authenticated session, and one fictional property. The author subsequently clarified this sequence:

1. **Before a later manual Railway redeploy:** They could sign out and sign back in successfully.
2. **After the redeploy:** The previously working login no longer succeeded.

This is a **reported regression across redeployment**. The exact error message, whether the account record remains present, and the application database path/volume/secret configuration have **not been confirmed**. A likely explanation is that the app used ephemeral or different storage across deployments, but this remains a hypothesis, not a verified root cause.

**Do not mark persistent-storage testing as passed.** Verify the service's attached volume mount path is exactly `/data`; verify `RENTWISE_DATABASE_URL=sqlite:////data/rentwise.sqlite3` and a stable `RENTWISE_SESSION_SECRET` are present in the deployed environment; inspect the precise login error before any further redeploy. Do not delete the volume or use real customer data.

## Hosted Railway demo — successful session test, 17 November 2026

The author accessed the distinct Railway project **`authentic-mercy`**, generated a public HTTPS domain for the service, and showed a screenshot of the RentWise v0.2 dashboard at:

https://rentwise-rental-management-production-4594abfb.up.railway.app

The author reported successfully signing out and signing back into the hosted account. A screenshot taken afterward displayed **1 saved fictional property** in the dashboard. This is evidence of a **successful browser-session login and saved-property retrieval test** in that specific deployment. The screenshot itself has not been added to this repository.

The author showed the volume settings in `authentic-mercy` with the volume mounted at **`/data`** and confirmed the database URL `sqlite:////data/rentwise.sqlite3` was configured. However, **persistence through a service restart or redeployment has not been tested successfully** on this deployment; do not claim otherwise.

An **earlier deployment under a different Railway project, `joyful-liberation`,** experienced a SQLite startup error `sqlite3.OperationalError: unable to open database file`, and earlier logins were disrupted around redeployment/configuration changes. These projects must not be conflated.

**Security and evidence limitations:** This remains an AI-assisted, fictional-data-only prototype without external penetration testing, verified production controls, real user adoption, or an independent code review. Avoid uploading real tenant or payment details. Do not risk further redeployment merely to make a portfolio claim.

## Hosted Railway demo — verified persistence and backup checks, 17 November 2026

For the correct Railway project, `authentic-mercy`, the author supplied a deployment screenshot showing an **ACTIVE / deployment successful** result after a documentation commit was automatically deployed. The author then confirmed that the same **one fictional property remained visible** in RentWise, demonstrating persistence across that specific redeployment.

The author disabled automatic deployment afterward (Railway Settings displayed `Auto deploy is disabled`).

A backup was created using the SQLite Online Backup API in the Railway Console, returning `Backup check: ok`. The separate `rentwise-backup-2026-11-17.sqlite3` file was downloaded and inspected in read-only mode. It was **52 KB**, `PRAGMA integrity_check` returned `ok`, and it contained **one account, one fictional property and one audit event**; tenants, leases and payments were empty. Backup file contents, emails, IDs, and hashes are **not** committed to GitHub.

**Scope:** A successful single redeployment and backup integrity check does not establish disaster-recovery reliability. A restore to a disposable database copy, a backup schedule, and security/abuse testing remain incomplete. The hosted app must remain a fictional-data demonstration.

## Portfolio use

The 2022 graduation project was collaborative. This repository documents a **new, AI-assisted 2026 prototype**, technical progress and limited test results. The public repository and the author's manual test record do not, by themselves, show independent recognition or practical adoption. An external reviewer should evaluate the actual code or demonstration before signing any assessment.
