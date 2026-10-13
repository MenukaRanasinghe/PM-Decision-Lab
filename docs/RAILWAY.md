# Deploying to Railway with your existing PostgreSQL database

This app is a **Python/Streamlit** application (not Next.js/Prisma). It reuses your **existing
Railway PostgreSQL** database — it never creates another one and never drops or resets your data.
On startup it creates any missing tables and applies small, additive, in-place migrations
(new columns only), then seeds the built-in activity catalogue if absent.

---

## 1. Local development on Windows

```bat
cd decision-lab-python
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and set **`DATABASE_URL` to your Railway PUBLIC URL** (so your Windows machine can
reach it). In Railway: open your **Postgres service → Variables → `DATABASE_PUBLIC_URL`** and copy
it. It looks like:

```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@YOUR_HOST.proxy.rlwy.net:5432/railway
```

> The app automatically rewrites a legacy `postgres://` scheme to `postgresql+psycopg://`.
> Do **not** use the `postgres.railway.internal` host locally — it only resolves inside Railway, and
> the app will refuse it with a clear message. If your network needs it, add `DB_SSLMODE=require`.

Create the first administrator, then run the app:

```bat
python -m tools.create_admin           REM reads ADMIN_EMAIL / ADMIN_PASSWORD from .env
streamlit run app.py
```

Open http://localhost:8501. With `DEV_MODE=true` you also get a sample-learner picker and the
first-visit email page, so you can try the learner side without the LMS.

(macOS/Linux: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && cp .env.example .env && python -m tools.create_admin && streamlit run app.py`)

---

## 2. Deploy the Streamlit app on Railway

1. Push this project to a Git repo and **New Project → Deploy from GitHub** (or `railway up`).
2. Add your **existing Postgres** to the project (or it is already there). Do **not** add a new one.
3. In the app service **Variables**, set:
   - `DATABASE_URL = ${{Postgres.DATABASE_URL}}` — references the private URL at runtime (never in Git).
   - `APP_ENV = production`
   - `DEV_MODE = false`
   - `SESSION_SECRET`, `ADMIN_SECRET`, `LAUNCH_TOKEN_SECRET` — 32+ random bytes each
     (`python -c "import secrets;print(secrets.token_hex(32))"`).
   - `ADMIN_EMAIL`, `ADMIN_PASSWORD` — for the first admin (or run the one-off command below).
   - Optional: `ALLOW_EMAIL_IDENTITY`, `EMBED_ALLOWED_DOMAINS`, `LINK_ALLOWED_DOMAINS`, the `LTI_*`
     and `COMPANION_URL` values if you use H5P/LTI.
4. Railway uses `railway.json` / `Procfile`: the start command is
   `streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`
   and the healthcheck path is `/_stcore/health`.
5. First deploy auto-creates/migrates tables. Create the admin once, e.g. from the Railway shell:
   `python -m tools.create_admin you@org.com 'a-strong-password' "Your Name"`.

The app binds `0.0.0.0` on Railway's assigned `$PORT`. Tables are created and migrated safely on
every boot (no data loss).

---

## 3. (Optional) The LTI 1.3 + H5P companion as a second service

Streamlit cannot receive an LTI `form_post` or host the xAPI endpoint, so those live in a small
FastAPI companion. Deploy it as a **second Railway service** in the same project (same repo), with:

- Start command: `uvicorn companion.lti_app:app --host 0.0.0.0 --port $PORT`
- The same `DATABASE_URL` (`${{Postgres.DATABASE_URL}}`) and the same `LAUNCH_TOKEN_*` secrets.
- Set `STREAMLIT_URL` (public URL of the app service), `COMPANION_PUBLIC_URL` (this service's public
  URL) and, on the app service, `COMPANION_URL` to this service's public URL.

See `docs/H5P-AND-LTI.md` for the LMS registration details. If you do not use H5P/LTI, skip this.

---

## 4. Environment variables you must configure (summary)

| Variable | Where | Required | Notes |
|---|---|---|---|
| `DATABASE_URL` | app (+ companion) | ✅ | `${{Postgres.DATABASE_URL}}` on Railway; public `*.proxy.rlwy.net` URL locally |
| `APP_ENV` | app | ✅ | `production` on Railway |
| `DEV_MODE` | app | ✅ | `false` in production |
| `SESSION_SECRET` | app | ✅ | 32+ random bytes |
| `ADMIN_SECRET` | app | ✅ | 32+ random bytes |
| `LAUNCH_TOKEN_SECRET` | app (+ companion) | ✅ | 32+ random bytes; **must match** the companion |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | app | ⬤ | only for `tools.create_admin` |
| `ALLOW_EMAIL_IDENTITY` | app | optional | default true — first-visit email fallback |
| `EMBED_ALLOWED_DOMAINS` | app | optional | iframe allowlist (blank = sensible default) |
| `LINK_ALLOWED_DOMAINS` | app | optional | blank = allow any https link |
| `DB_SSLMODE` | app | optional | e.g. `require` for the public proxy |
| `COMPANION_URL` | app | optional | public URL of the companion (H5P) |
| `STREAMLIT_URL`, `COMPANION_PUBLIC_URL`, `LTI_*` | companion | optional | LTI 1.3 |

**Never commit real secrets.** `.gitignore` already excludes `.env`, `*.db` and `.streamlit/secrets.toml`.
