# RentWise v0.2 — guided academic review pack

**Prepared:** 17 November 2026  
**Live demonstration (fictional data only):** https://rentwise-rental-management-production-4594abfb.up.railway.app  
**Source:** https://github.com/devanandha/rentwise-rental-management

## Purpose and boundaries

The purpose of the review is to let an academic referee **independently assess** the technical progression from the **2022 undergraduate group project** to a new **AI-assisted 2026 rental-management prototype**. This is **not** a request for a prewritten positive endorsement, an independent adoption claim, an engineering accreditation or a production security certification.

**Until the high-priority security findings in [SECURITY_REVIEW.md](SECURITY_REVIEW.md) are remediated, conduct the demonstration by screen share.** The referee does not need to create an account, share a password, or supply personal details. Never place real property, tenancy, banking or payment information into RentWise.

## Evidence to send before the meeting

1. [Academic technical review brief](ACADEMIC_REVIEW_BRIEF.md) — scope, provenance and assessment prompts.
2. [Public source and setup](README.md), with [code](app/) and [regression tests](tests/).
3. [Testing log](TESTING_LOG.md) — explicit distinction between local screenshots, automated checks and the hosted demonstration.
4. The **2022 group project slides** and **official academic transcript**, shared privately by the author where appropriate, rather than published unredacted on GitHub.
5. [Preliminary security review](SECURITY_REVIEW.md) — outstanding issues and limitations.

## Suggested 10-minute screen-share walkthrough

| Minutes | Evidence | Reviewer can independently check |
|---|---|---|
| 0–2 | Show 2022 group slides and attribution to both authors | Project scope and what the supervisor genuinely observed in 2022 |
| 2–3 | Open current GitHub repository, identify FastAPI/SQLite and the tests | Actual 2026 source and evolution; code is distinct from the 2022 slides |
| 3–5 | Log into a fictional demo account; show property, tenant and lease | Whether basic author-scoped rental workflows operate |
| 5–7 | Set a fictional ₹15,000 monthly rent; record a ₹5,000 payment and inspect ₹10,000 outstanding | Whether rent-month allocation is understandable and correct in this example |
| 7–8 | Correct payment from ₹5,000 to ₹7,000, confirm ₹8,000 balance | Whether correction avoids duplicating a transaction |
| 8–9 | Open Activity log and discuss editing, voiding and ownership checks | Evidence of change tracking, with limits of non-tamper-proof logging |
| 9–10 | Discuss incomplete features and security review | Whether technical decisions and limitations are explained transparently |

The reviewer can also inspect different features independently if they wish. Do **not** prepopulate their opinion or describe a demonstration they have not seen.

## Reviewer feedback questions

- What parts of the **2022 group project** did you personally supervise, teach, examine or evaluate, and over what period?
- What did you observe of Devanandha's individual contribution at that time, while recognising co-author ownership?
- Which files, pages or workflows of the **2026 prototype** did you personally inspect and when?
- What technical strengths and weaknesses did you independently observe in the newer application?
- Is there evidence of growth in software design, data modelling, testing, debugging and responsible communication of limitations?
- What would you recommend improving before anyone uses it beyond fictional demonstration data?

## Suggested factual feedback format (optional)

> On [review date], I examined [specific files/screens/workflow] of RentWise v0.2. I observed [specific technical example], and I noted [specific limitation or recommendation]. My earlier experience with the student comes from [first-hand academic role and dates], including [actual 2022 group project supervision or assessment if confirmed]. In my assessment [reviewer's own independent views].

This is a **prompt**, not text the reviewer must sign or a claim that a review has already happened.

## How to record the review ethically

- Record **date**, **reviewer role**, **specific artifacts examined**, **method** (code inspection, live walkthrough, tests), **genuine technical feedback**, and **permission to quote or attach it**.
- Ask the reviewer to write in their own words and approve any quotations.
- Don't convert a supportive comment into a claim of external industry recognition without evidence.
- Keep any private correspondence separate from the public repository until the reviewer consents to publication.

## Current limits

The live demo is online and its fictional test property was reported to survive a successful Railway redeployment on 17 November 2026. This is **not** proof of production security or independent industry adoption. Public signup and login security controls remain incomplete; prefer a **screen-shared evaluation** over creating external accounts.

See [SECURITY_REVIEW.md](SECURITY_REVIEW.md) for the documented gaps.
