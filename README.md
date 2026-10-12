# Kestrelford Repairs Decision Lab — Python / Streamlit

A faithful Python port of the original Node/Express/Prisma/PostgreSQL Decision Lab. Same tracks,
activities, I12/I14 branching missions, scoring rules, progress model, admin portal and H5P
pipeline — rebuilt on **Streamlit + SQLAlchemy + SQLite**, runnable on Windows with no Docker or
database server.

> **FICTIONAL TRAINING SCENARIO — NOT A REAL HOUSING PROVIDER OR LIVE SERVICE.**

## What's inside

- **Learner portal** — launch from the LMS → dashboard with the two track cards (PRINCE2
  Foundation / PRINCE2 Practitioner), per-track activity lists, activity pages, and a Practice
  Record with PDF download. Shows the learner's real name and email from the launch.
- **Missions I12 and I14** — the full branching flow (Brief → Evidence → Decide → Consequence →
  Repair → Triage/Sequence → Method → Record), both levels, with the original wording.
- **Scoring** — identical rules: 2 = aligned first time, 1 = repaired, 0 = unresolved; misconception
  tags; the five consequence echoes. All scoring is server-side in Python (`content/scoring.py`).
- **Progress** — persisted in SQLite via SQLAlchemy, keyed to LMS identity; survives refresh and
  return; one learner never sees another's data.
- **Admin** — in-page **Admin Login** in the top nav → dashboard, learners (with drill-down),
  activities, **H5P upload → validate → publish → unpublish**, results. Bcrypt passwords, server-
  side authorization, immutable published H5P versions.
- **Companion** (optional, production) — a small FastAPI service for the two things Streamlit
  can't do itself: true **LTI 1.3** launch and reliable **H5P xAPI** tracking. See
  `docs/H5P-AND-LTI.md`.

## Requirements
- Python 3.10–3.12 (3.13 works; you'll see harmless `utcnow()` deprecation warnings).

## Quick start (Windows)

```bat
cd decision-lab-python
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m tools.create_admin            REM reads ADMIN_EMAIL/ADMIN_PASSWORD from .env
streamlit run app.py
```

(macOS/Linux: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && cp .env.example .env && python -m tools.create_admin && streamlit run app.py`.)

The app opens at `http://localhost:8501`. SQLite initialises automatically and seeds the two
tracks' activities on first run.

### Try it as a learner (no LMS)
With `DEV_MODE=true`, the launch gate shows a **sample-learner picker** — pick Alex/Priya/Sam and
click *Launch as this learner*. Or generate a signed dev launch URL that simulates an LMS
signed-token launch:

```
python -m tools.make_dev_link dev-learner-A "Alex Learner" alex@example.com
# open the printed http://localhost:8501/?launch=... URL
```

Open **PRINCE2 Foundation → I12** (or I14), play through, then refresh — your progress is restored
from the database (identity rides in the signed `?s=` token in the URL).

### Try the admin
Top nav → **Admin Login** → sign in with the `ADMIN_EMAIL`/`ADMIN_PASSWORD` you seeded →
Dashboard / Learners / Activities / H5P / Results. Return to the learner view with **← Learner view**.

### Upload an H5P activity
Admin → H5P → pick an activity + track, upload a `.h5p`, **Validate → Publish**. The activity
flips to an H5P activity. Learner playback + score tracking needs the companion running (below).

## Companion (LTI 1.3 + H5P tracking)

```bat
uvicorn companion.lti_app:app --host 0.0.0.0 --port 8000
```
Then set `COMPANION_URL=http://localhost:8000` (and the `LTI_*`, `STREAMLIT_URL`,
`COMPANION_PUBLIC_URL` values) in `.env`. Full configuration and the reason this is needed are in
`docs/H5P-AND-LTI.md`.

## Tests

```bash
pytest -q
```
Covers scoring rules, a full I12/I14 attempt through the service layer, learner isolation, resume,
consequence echoes, and the H5P validate/publish flow. The UI is additionally exercised with
Streamlit's `AppTest` harness (see `tests/`), which runs the real script through gate → dashboard →
track → activity → mission.

## Project structure
```
decision-lab-python/
  app.py                     Streamlit entry + identity + routing
  config.py  requirements.txt  .env.example
  database/    connection.py  models.py  init_db.py      (SQLAlchemy, mirrors the Prisma schema)
  content/     registry.py  scoring.py  missions/i12.py  missions/i14.py
  services/    activity_service.py  progress_service.py  admin_service.py  h5p_service.py  pdf_service.py
  auth/        tokens.py  passwords.py  learner_identity.py  dev_login.py
  learner/     portal.py  mission_player.py  practice_record.py  h5p_player.py
  admin/       panel.py
  components/  styling.py
  companion/   lti_app.py                                  (FastAPI: LTI 1.3 + H5P/xAPI)
  tools/       create_admin.py  make_dev_link.py
  tests/
  docs/        H5P-AND-LTI.md  FEATURE-PARITY.md
```

## What's new in this update
- **Railway PostgreSQL**: reuses your existing Railway database via `DATABASE_URL`. The connection
  layer normalises `postgres://` → `postgresql+psycopg://`, enables `pool_pre_ping`/recycle for
  Railway's idle cycles, and refuses the private `*.railway.internal` host when run locally. Startup
  runs **safe, additive, in-place migrations** (new columns only) — it never drops or resets data.
  See **[docs/RAILWAY.md](docs/RAILWAY.md)**.
- **Admin-only login, LMS learner identity, email fallback**: still no learner login. If the LMS
  can't hand us a verified identity, a first-visit **email page** (self-declared, clearly marked
  **unverified**) saves progress, carried by the signed session token — never by an editable field.
- **Activity management**: admins can create/edit/publish/unpublish H5P links, external quiz links,
  embedded activities (approved domains only), videos, documents (link or uploaded file) and other
  links — with instructions, category, status, due date, pass mark and max score, plus preview.
- **Persistent tracking for every type**: launches/access/attempts/progress/timestamps are stored in
  PostgreSQL (`activity_events` + `activity_progress`), deduplicated per learner+activity. Scores are
  stored **only when a trusted integration supplies them** and are clearly marked *verified* vs a
  mere launch/access. See **[docs/ACTIVITY-TRACKING.md](docs/ACTIVITY-TRACKING.md)**.
- **Dashboards & reports**: the learner dashboard shows recently-opened activities and saved
  progress; the admin side adds learner search, filterable reports (activity/learner/date/status),
  an incomplete view, **CSV export**, and a “Tracking & limits” tab that is transparent about what
  cannot be verified.

## Production notes
- Set `APP_ENV=production`, `DEV_MODE=false`, strong secrets, and your Railway Postgres
  `DATABASE_URL`. The data layer is isolated in `database/` + `services/`; `init_db()` creates
  missing tables and applies the additive migrations in `database/migrations.py` on every boot.
- Deploy with the included `Procfile` / `railway.json` (Streamlit binds `0.0.0.0` on `$PORT`).
- Put Streamlit behind HTTPS. Keep admin secrets server-side only (they are never sent to the UI).

## Troubleshooting
- *"No active session" / stuck on the gate*: in dev, use the sample-learner picker; in production,
  launch from the LMS (a bare visit has no identity by design).
- *H5P plays but nothing is recorded*: the companion isn't running or `COMPANION_URL` is unset —
  see `docs/H5P-AND-LTI.md`.
- *Admin can't sign in*: run `python -m tools.create_admin` (needs `ADMIN_EMAIL`/`ADMIN_PASSWORD`).
- *bcrypt/SQLAlchemy warnings on Python 3.13*: harmless deprecation notices; use 3.10–3.12 to avoid.
