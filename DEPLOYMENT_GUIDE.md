# Hosting RentWise for invited reviewers (demo only)

**Prepared 16 November 2026 · No deployment has been created.**

RentWise currently runs locally at `http://127.0.0.1:8000`. That address is only available on the user's own computer. A hosted web service provides a shareable HTTPS URL so reviewers can access the app through any normal browser, including a smartphone.

**Scope:** This is a temporary, **fictional-data-only reviewer demo**. RentWise v0.2 is not ready for real tenants, financial transactions, or open public registration at scale. Additional controls (CSRF protection, login rate limits, account recovery, privacy review, tested backups and production migrations) are needed before production use.

## Suggested platform: Railway, web service + mounted storage volume

Documentation: https://railway.com/guides/fastapi and https://docs.railway.com/volumes

1. Create or log into a Railway account: https://railway.com .
2. Start a **New Project → Deploy from GitHub repo** and connect/select `devanandha/rentwise-rental-management`. Keep it private/unshared while setting it up. Railway may request account verification or a plan.
3. In the service **Settings → Deploy**, set the **Start Command**:
   ```sh
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
   The app's ASGI target is `app.main:app`, **not** `main:app`. The command must bind to Railway's provided port.
4. Add **one persistent volume** to the service, mounted at **`/data`**. This is essential for preserving SQLite data after restarts/deploys. Mounting at `/data` is independent of the code directory.
5. In the service's **Variables**, add:
   - `RENTWISE_DATABASE_URL` = `sqlite:////data/rentwise.sqlite3`
   - `RENTWISE_HTTPS_ONLY` = `1`
   - `RENTWISE_SESSION_SECRET` = a long, securely generated random value (40+ characters, kept private and stable). **Do not publish it in GitHub, screenshots, or messages.**
6. Apply/redeploy the staged configuration and inspect the deployment logs. On success, go to **Settings → Networking → Generate Domain** to obtain the publicly reachable HTTPS link. Test sign-in and the rental dashboard from a private/incognito browser.
7. Share the URL only with invited reviewers. Create fictional test data or let each reviewer register their own sandbox account. Ask them not to enter real names, phone numbers, identity details, banking information or actual payment data.
8. Monitor any applicable hosting/volume charges and take occasional backups. Shut down the service when no longer required.

Railway's published pricing and trial terms may change. Check https://railway.com/pricing and https://docs.railway.com/pricing/free-trial **before** clicking through to any billed plan.

### What happens to the existing local account?

The public service begins with a **separate, empty database** on the Railway volume. Your `rentwise.sqlite3` file remains on your laptop. **Local accounts and test records do not automatically appear online.** The simplest safe demo uses newly created test accounts and fictional records.

### What if login works but then logs out after restarting?

Check that `RENTWISE_SESSION_SECRET` is defined on the web service and remains unchanged. The current local default generates a new random secret whenever the process starts.

### What if data disappears?

Check that the volume is attached and the database URL is exactly `sqlite:////data/rentwise.sqlite3` (four slashes following `sqlite:` because this is an absolute path). Without the volume, the app writes into an ephemeral container filesystem and records may vanish on redeploy.

### Does this make RentWise a mobile app?

The hosted site will work through a phone's web browser. A home-screen shortcut is possible, but it is not a native Android/iPhone app or an installable PWA yet. A proper PWA could be a separate future milestone.

## Alternative: Render

Render supports FastAPI and free web services: https://render.com/docs/deploy-fastapi . To start this repository, use `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

**Important:** Render's free service has an ephemeral filesystem; the SQLite data may disappear on restart or deploy. Persistent disk storage requires a paid service, or you can migrate to a managed database. See https://render.com/docs/disks . For reviewers who need accounts to survive, prefer Railway with an attached volume or another service with persistent storage.

## Security limitations and accurate claims

- Online deployment alone is **not** a security certification, an independent endorsement, professional adoption or proof of innovation.
- Existing PBKDF2 password hashes and signed sessions are a baseline, but do not replace security review. Login rate limits, CSRF defence, consent/privacy notices and secure backup/restore are incomplete.
- The UI's "rent payments" are offline records only; the app cannot charge cards or transfer money.
- SQLite with one mounted volume is for a small, single-instance demo only; do not run multiple replicas against it.
- A reviewer should be told which features were actually tested, which were not, and that the application was initially AI-assisted.

## References

- [Project README](README.md)
- [Testing log](TESTING_LOG.md)
- [Academic reviewer brief](ACADEMIC_REVIEW_BRIEF.md)
