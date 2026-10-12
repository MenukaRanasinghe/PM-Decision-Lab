# Activity management & tracking — what is and isn't tracked

This release lets administrators publish several activity **types** and tracks learner interaction
for all of them, persisting everything in PostgreSQL. It is deliberately honest about the limits of
tracking externally hosted content.

## Activity types an admin can create (Admin → Activities)

| Type | How learners open it | What we can track |
|---|---|---|
| `NATIVE` | built-in branching mission (I12/I14) | Full, server-side: decisions, score, completion |
| `H5P` | uploaded `.h5p`, played via the companion | **Verified** score/completion via xAPI (companion required) |
| `H5P_LINK` | a published H5P.com link/embed | Launch/access only, unless an integration is configured |
| `EXTERNAL_QUIZ` | external quiz/assessment link | Launch/access only |
| `EMBED` | iframe from an approved domain | Launch/access only |
| `VIDEO` | video link or approved embed | Launch/access only |
| `DOCUMENT` | external link **or** an uploaded file (stored in the DB) | Launch/access + download |
| `LINK` | any approved external resource | Launch/access only |

Each activity carries: title, description, type, URL or embed URL, instructions, category,
publication status (`DRAFT`/`PUBLISHED`/`UNPUBLISHED`/`ARCHIVED`), optional due date, optional pass
mark and optional max score. Admins can **preview** before publishing.

### Safety
- Only **https** URLs are accepted.
- Iframes are allowed **only** for hosts on `EMBED_ALLOWED_DOMAINS`; anything else is offered as an
  "open in a new tab" link instead. We never execute uploaded HTML/JS.
- Uploaded documents are stored as bytes in PostgreSQL (so they persist on Railway) and served back
  as a download — never executed.

## What we persist (PostgreSQL)

- **Learner identity** — from a verified LMS launch, or the self-declared email fallback (clearly
  marked unverified), keyed by `(issuer, email/external id)` so the same person maps to the same
  record on return.
- **`activity_events`** — append-only log: ACCESS, LAUNCH, VIEW, START/RESUME/COMPLETE, SUBMIT,
  ABANDON, ERROR, SCORE, with source (UI/LTI/XAPI/AGS), timestamps, and (for verified events)
  score/max/success.
- **`activity_progress`** — one durable row per (learner, activity) for non-native types: first/last
  access, launch/view/attempt counts, best score, pass/fail, progress %, time, and a
  `score_verified` flag. Upserted, so refreshes/returns never create duplicates.
- Native missions and uploaded H5P continue to use `mission_attempts` / `decision_events` /
  `learner_progress` exactly as before.

## The honesty rule (important)

> We **never** claim a score or completion for an external activity unless a trusted integration
> actually supplied it.

- A plain link or iframe can only ever produce **launch/access** events. In the learner UI the score
  shows as “Not available”, and in admin reports the **Verified** column is a dash.
- A score/completion is stored (and shown as **verified**) **only** when it arrives through a trusted
  path: today that is xAPI from the companion for uploaded `.h5p` packages
  (`record_verified_result(..., source="XAPI")`). The design is extensible — `services/tracking_service.py`
  exposes the same entry point for a future **LTI 1.3 Assignment & Grade Services (AGS)** or
  provider callback, which must authenticate before writing a verified score.
- Admin → **Tracking & limits** lists exactly which activities cannot return verified scores and
  shows recent tracking errors, so nothing is over-claimed.

## Reports & export (Admin → Reports)

Filter by activity, track, learner (email/name/id), date range and status; toggle "only
incomplete"; and **export to CSV**. Every row comes from persisted records, and each row states
whether its score is verified.
