"""Learner view for admin-managed, externally hosted activities:
H5P links, external quiz/assessment links, embedded activities, videos and documents.

What we track honestly
----------------------
For these activity types we persist what we can genuinely observe — that the learner ACCESSED and
LAUNCHED the activity, with timestamps and counts (in PostgreSQL via services/tracking_service.py).
We do NOT claim a score or completion here: the UI states plainly that marks/completion are not
received from the provider unless a supported integration (xAPI/LTI-AGS) is configured and
confirmed. Uploaded .h5p packages played through the companion still track via xAPI as before.
"""
import streamlit as st
import streamlit.components.v1 as components

from components import styling
from services import tracking_service as T
from services import url_safety


def _access_once(learner_id, activity):
    """Log ACCESS exactly once per opened activity in this Streamlit session (reruns are frequent)."""
    key = f"_accessed_{activity['id']}"
    if not st.session_state.get(key):
        T.touch_access(learner_id, activity_id=activity["id"], code=activity["code"], track=activity["track"])
        st.session_state[key] = True


def _tracking_note(activity_type):
    st.markdown(
        '<div class="panel warn"><h4>How this activity is tracked</h4>'
        '<p>We record that you <b>opened and launched</b> this activity, with the date and time. '
        'Your <b>score and completion are not received from the external provider</b> and are shown '
        'as “not available”, unless your administrator has configured and confirmed a supported '
        'integration (for example xAPI or LTI&nbsp;1.3 grade services).</p></div>',
        unsafe_allow_html=True,
    )


def render():
    code = st.session_state["act_code"]
    track = st.session_state["track"]
    learner = st.session_state["learner"]
    styling.top_bar("Better Repairs Programme · PRINCE2 practice",
                    f'Learner: <b>{learner.get("display_name") or "—"}</b>')
    if st.button("← Back", key="launch_back"):
        st.session_state["view"] = "activity"
        st.rerun()
    styling.fictional_notice()

    from services import progress_service as P
    d = P.activity_detail(learner["id"], code, track)
    if not d:
        st.error("Activity not found.")
        return
    a = d["activity"]
    atype = a["activity_type"]

    st.markdown(f"# {a['code']} — {a['title']}")
    if a.get("category"):
        st.caption(f"Category: {a['category']}  ·  Type: {atype}")
    if a.get("description"):
        st.markdown(f'<p class="doc-b">{a["description"]}</p>', unsafe_allow_html=True)
    if a.get("instructions"):
        st.markdown(f'<div class="panel method"><h4>Instructions</h4><p>{a["instructions"]}</p></div>',
                    unsafe_allow_html=True)
    meta = []
    if a.get("pass_mark") is not None:
        meta.append(f"Pass mark: {a['pass_mark']}%")
    if a.get("due_date"):
        meta.append(f"Due: {a['due_date']:%Y-%m-%d %H:%M}")
    if meta:
        st.caption(" · ".join(meta))

    _access_once(learner["id"], a)

    # ── DOCUMENT uploaded as a file: offer a download (and track the launch on click) ──
    if atype == "DOCUMENT" and not (a.get("url") or a.get("embed_url")):
        from services.admin_service import get_activity_admin  # lazy to avoid cycles
        full = get_activity_admin(a["id"])
        from database.connection import session_scope
        from database.models import Activity
        with session_scope() as s:
            row = s.query(Activity).filter_by(id=a["id"]).one_or_none()
            data = bytes(row.file_bytes) if row and row.file_bytes else None
            fname = row.file_name if row else "document"
            mime = row.file_mime if row else "application/octet-stream"
        if data:
            if st.download_button("Download / open document", data=data, file_name=fname or "document",
                                  mime=mime or "application/octet-stream", type="primary", key="doc_dl"):
                T.record_launch(learner["id"], activity_id=a["id"], code=code, track=track,
                                detail={"action": "download", "file": fname})
        else:
            st.info("No file has been uploaded for this document activity yet.")
        _tracking_note(atype)
        _show_progress(d.get("external"))
        return

    target = a.get("embed_url") or a.get("url")
    if not target:
        st.info("This activity has no link configured yet. Please check back later.")
        return

    # ── EMBED (iframe) — only for approved hosts ──
    if a.get("open_mode") == "EMBED":
        if not url_safety.is_allowed_embed(target):
            st.warning("This activity cannot be embedded here (its host is not on the approved "
                       "allowlist). Use the link below to open it in a new tab instead.")
            st.link_button("Open activity in a new tab →", target, type="primary")
            T_launch_once(learner["id"], a, code, track)
        else:
            T_launch_once(learner["id"], a, code, track)
            safe = target.replace('"', "%22")
            components.html(
                f'<iframe src="{safe}" style="width:100%;height:600px;border:1px solid #d9e0e6;'
                f'border-radius:10px" allow="autoplay; fullscreen" '
                f'referrerpolicy="no-referrer" '
                f'sandbox="allow-scripts allow-same-origin allow-forms allow-popups"></iframe>',
                height=640, scrolling=True,
            )
    else:
        # ── NEW_TAB link ──
        st.link_button("Launch activity in a new tab →", target, type="primary")
        T_launch_once(learner["id"], a, code, track)

    _tracking_note(atype)
    _show_progress(d.get("external"))


def T_launch_once(learner_id, activity, code, track):
    """Record a LAUNCH once per session for this activity (button render == intent to open)."""
    key = f"_launched_{activity['id']}"
    if not st.session_state.get(key):
        T.record_launch(learner_id, activity_id=activity["id"], code=code, track=track,
                        detail={"open_mode": activity.get("open_mode"), "provider": activity.get("provider")})
        st.session_state[key] = True


def _show_progress(ext):
    if not ext:
        return
    st.markdown("### Your record for this activity")
    launches = ext.get("launch_count") or 0
    last = ext.get("last_access_at")
    first = ext.get("first_access_at")
    score_txt = "Not available"
    if ext.get("score_verified") and ext.get("best_score") is not None:
        mx = ext.get("best_max_score")
        score_txt = f'{ext["best_score"]}{("/" + str(mx)) if mx else ""} (verified)'
    rows = [
        ("Status", ext.get("completion_status") or "NOT_STARTED"),
        ("Launches", launches),
        ("First opened", f"{first:%Y-%m-%d %H:%M}" if first else "—"),
        ("Last opened", f"{last:%Y-%m-%d %H:%M}" if last else "—"),
        ("Score", score_txt),
    ]
    html = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in rows)
    st.markdown(f'<table class="simple"><tbody>{html}</tbody></table>', unsafe_allow_html=True)
