# RentWise — academic technical review brief

**Prepared:** 16 November 2026  
**Audience:** An academic or independent technical reviewer, including Dr Regitha if she agrees to review the 2026 work.

## What is being reviewed

**RentWise v0.2** is a new locally run Python/FastAPI + SQLite rental-management prototype. It implements landlord accounts, property and tenant records, lease records, rent-month allocations, payment correction and voiding, monthly billing summaries, and a local activity log.

Repository: https://github.com/devanandha/rentwise-rental-management

- [Source code](app/)
- [Automated regression tests](tests/)
- [Manual test observations and remaining test cases](TESTING_LOG.md)
- [Technical limitations and setup](README.md)
- [Project provenance](PROJECT_EVIDENCE.md)

**Development status:** Local research/portfolio prototype, not a deployed service or production accounting product. The project was initially scaffolded with AI assistance and has been iterated through test feedback. No claims are made about external adoption, revenue or independently measured impact.

## Connection to the 2022 undergraduate project

The original **House Rental Payment Web App** was a *group project* presented by **Devanandha VS and Rinsha Basheer** for the 2019–2022 BSc Computer Applications (Triple Main) programme at Sacred Heart College, Thevara. The original slides describe a *proposed* rental-management application with Python/Django/MySQL and web technologies. The academic transcript records **88/100** for the final-year project and an **overall CGPA of 8.55/10 (A+)**.

RentWise's 2026 code is **not** the 2022 source code, and the original project should not be attributed solely to one team member. Dr Regitha reportedly monitored and reviewed the original group work; she should confirm her exact supervisory and assessment role from her own records and recollection.

## Technical progression to assess

| Dimension | 2022 presentation | RentWise v0.2 |
|---|---|---|
| Context | Undergraduate group project | New independently maintained, AI-assisted prototype |
| Technology | Proposed Python/Django/MySQL, HTML/CSS/JavaScript | Python/FastAPI/SQLite, HTML/CSS/JavaScript |
| Functional outline | Proposed owner, property, tenant and rental-payment modules | Implemented local forms, accounts, leases, offline payment records and monthly rent bills |
| Data and business rules | Conceptual workflow in project slides | Lease overlap check for single-unit properties, owner-scoped records, rent-month allocation and corrections |
| Evaluation evidence | Project mark in official transcript | Public tests and limited local screenshot-based walkthrough |
| Current limitations | Implementation level cannot be established from slides alone | No deployment, no gateway, incomplete accounting features and security hardening required |

This comparison does not establish that the 2026 prototype is commercially innovative or used by real landlords.

## Specific review questions for the academic referee

A useful, independent review could address:

1. Which classes, exercises, project presentations or assessments did the referee personally teach, monitor or assess during the **2019–2022** degree?
2. During the 2022 group project, what did the referee **personally observe** about Devanandha's design thinking, communication, programming understanding, problem solving, or responses to feedback? Avoid assigning unspecified work to one group member.
3. Which code paths or screens of the 2026 RentWise repository did the referee **actually inspect**, and on what date?
4. Compared with the student's undergraduate work, what concrete technical progress is evident, and what limitations remain?
5. What is the referee's own balanced assessment of the applicant's potential for further contribution to applied digital technology?

A reviewer can use the source, run the tests, or request a live demonstration. They should not describe a review they have not performed.

## Suggested short hands-on demonstration

Using *fictional data only*, create a property, a tenant and a ₹15,000/month lease for November 2026, then record a ₹5,000 payment for November and inspect the ₹10,000 balance. Correct the payment to ₹7,000, confirm the new ₹8,000 balance, and view the correction event in **Activity log**.

This workflow has been observed in a local walkthrough and is documented in [TESTING_LOG.md](TESTING_LOG.md). Further tests of real-world security, correct rent proration, multi-unit occupancy, refunds and accounting rules are still needed.

**Please do not upload live customer, identity, banking, or payment information to this prototype.**
