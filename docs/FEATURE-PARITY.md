# Feature parity — Node original vs Python/Streamlit port

Compared against the supplied `kestrelford-decision-lab` (Node/Express/Prisma/PostgreSQL).

| Area | Original (Node) | This port (Python/Streamlit) | Parity |
|---|---|---|---|
| Two tracks (Foundation/Practitioner), both open | `tracks.js`, `canAccessTrack` | `content/registry.py`, `can_access_track()` | ✅ full |
| 16-activity register, I12 & I14 playable | `registry.js`, `I12.js`, `I14.js` | `content/registry.py`, `missions/i12.py`, `i14.py` | ✅ full (same wording) |
| Branching mission flow | custom JS engine | `learner/mission_player.py` (session_state step flow) | ✅ full |
| Scoring 2/1/0, repair→1, tags, echoes | `keys.js`, `scoring.js` | `content/scoring.py` | ✅ identical rules |
| Progress persistence, resume, isolation | Prisma/Postgres | SQLAlchemy/SQLite | ✅ full |
| Practice record + PDF | pdfkit | `services/pdf_service.py` (reportlab) | ✅ full |
| Admin: login, learners, activities, results | Express routes + admin HTML | `admin/panel.py` (in-page) | ✅ full |
| Admin password security | bcrypt | bcrypt (`auth/passwords.py`) | ✅ full |
| H5P upload → validate → publish → unpublish, immutable versions | `h5pAdmin.js` | `services/admin_service.py` + admin H5P tab | ✅ full |
| H5P stored in DB, served from bytes | Postgres bytea | SQLite BLOB, `services/h5p_service.py` | ✅ full |
| H5P xAPI → progress | Express `/h5p/event` | **companion** `POST /h5p/event` | ⚠ via companion (see below) |
| LTI 1.3 launch | Express `/lti/login`,`/lti/launch` | **companion** FastAPI | ⚠ via companion (see below) |
| Signed-token launch fallback | Express `/launch?token=` | Streamlit `?launch=<jwt>` | ✅ full |
| Dev launch (no LMS) | `/dev/launch` | sample-learner picker + `?dev=` + `tools.make_dev_link` | ✅ full |
| Single deployment | one Railway service | `streamlit run app.py` (+ companion for LTI/H5P) | ◑ see below |
| DB entities/enums/relationships | Prisma schema | `database/models.py` (faithful) | ✅ full |

## Differences and why

1. **LTI 1.3 and H5P xAPI run in a companion FastAPI process, not inside Streamlit.**
   Streamlit cannot receive an OIDC `form_post` or host an xAPI POST endpoint — it only runs a
   script per interaction. The companion (`companion/lti_app.py`) handles exactly those two,
   sharing the same DB/models/services, so results remain server-authoritative. Native missions,
   the portal, admin and the signed-token launch need no companion. This is the "closest functional
   alternative", documented in `docs/H5P-AND-LTI.md`.

2. **Identity survives refresh via a signed `?s=` token in the URL**, because Streamlit
   `session_state` is per-connection and is lost on a hard refresh. The token is signed and
   short-lived (not a trusted raw parameter); progress always comes from the database.

3. **Deployment is two processes in production** (Streamlit + companion) rather than one. For a
   learner/admin-only pilot without LTI/H5P, a single `streamlit run app.py` is enough. SQLite is
   the default store; swap `DATABASE_URL` for PostgreSQL in production (the data layer is isolated).

4. **Visual fidelity is close, not pixel-identical.** The palette, typography, cards, panels,
   evidence/doc styling and step chips are ported (`components/styling.py`), but interactive
   controls are native Streamlit widgets (buttons/checkboxes/selects) styled to match, rather than
   the original bespoke HTML/JS controls. Behaviour and content are preserved.

## Not ported (intentionally, matching the brief)
- No new course enrolment or payment features (the two-course model is unchanged).
- Only I12 and I14 have full native content; the other 14 activities are registered and listed
  ("in build"), exactly as in the source. They become playable by adding a `content/missions/iXX.py`
  plus a `KEYS['IXX']` entry, or by publishing an H5P package against them.
