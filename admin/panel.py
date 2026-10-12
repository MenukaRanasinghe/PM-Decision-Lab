"""In-page administrator interface. Reached via the "Admin Login" control in the top nav.
Admin identity lives in st.session_state['admin'] (set only after a verified password login);
learners never get it, and admin actions check it server-side in admin_service."""
import streamlit as st

from services import admin_service as A
from auth.tokens import issue_admin_session, verify_admin_session
from content.registry import TRACK_CODES, TRACKS
from database.models import ACTIVITY_TYPES, ACTIVITY_STATUSES, OPEN_MODES, COMPLETION_STATUSES


def is_admin():
    return bool(st.session_state.get("admin"))


def render_login():
    from components import styling
    styling.top_bar("Administrator access")
    if st.button("← Back to learner view", key="adm_back"):
        st.session_state["view"] = "dashboard"
        st.rerun()
    st.markdown("## Administrator sign in")
    st.caption("Separate from learner/LMS access. Learners do not sign in here.")
    with st.form("admin_login"):
        email = st.text_input("Email")
        pw = st.text_input("Password", type="password")
        ok = st.form_submit_button("Sign in", type="primary")
    if ok:
        admin = A.authenticate_admin(email, pw)
        if not admin:
            st.error("Email or password is incorrect.")
        else:
            st.session_state["admin"] = admin
            st.session_state["admin_token"] = issue_admin_session(admin["id"])
            st.session_state["view"] = "admin"
            st.rerun()


def render_panel():
    from components import styling
    admin = st.session_state["admin"]
    styling.top_bar("Administrator", f'Signed in as <b>{admin["display_name"] or admin["email"]}</b>')
    c1, c2 = st.columns([0.8, 0.2])
    with c2:
        if st.button("Sign out", key="adm_out"):
            st.session_state.pop("admin", None)
            st.session_state.pop("admin_token", None)
            st.session_state["view"] = "dashboard"
            st.rerun()
    with c1:
        if st.button("← Learner view", key="adm_learner"):
            st.session_state["view"] = "dashboard"
            st.rerun()

    tabs = st.tabs(["Dashboard", "Learners", "Activities", "H5P", "Reports", "Tracking & limits"])
    with tabs[0]:
        _overview()
    with tabs[1]:
        _learners()
    with tabs[2]:
        _activities()
    with tabs[3]:
        _h5p()
    with tabs[4]:
        _results()
    with tabs[5]:
        _integration()


def _overview():
    o = A.overview()
    cols = st.columns(4)
    for col, (lbl, val) in zip(cols, [
        ("Total learners", o["learners"]), ("Total activities", o["activities"]),
        ("Total completions", o["completions"]),
        ("Avg practice score", o["average_practice_score"] if o["average_practice_score"] is not None else "—"),
    ]):
        col.markdown(f'<div class="kpi"><div class="l">{lbl}</div><div class="v">{val}</div></div>', unsafe_allow_html=True)
    st.markdown("### Recent learner activity")
    rows = "".join(
        f'<tr><td>{r["learner"]}</td><td>{r["track"]}</td><td>{r["activity"]}</td>'
        f'<td>{r["score"]}</td><td>{r["status"]}</td><td>{r["last_accessed_at"]:%Y-%m-%d %H:%M}</td></tr>'
        for r in o["recent"]) or '<tr><td colspan="6">No activity yet.</td></tr>'
    st.markdown(f'<table class="simple"><thead><tr><th>Learner</th><th>Track</th><th>Activity</th>'
                f'<th>Score</th><th>Status</th><th>Last accessed</th></tr></thead><tbody>{rows}</tbody></table>',
                unsafe_allow_html=True)


def _learners():
    q = st.text_input("Search learners by email, name or LMS id", key="learner_search")
    rows = A.search_learners(q) if q else A.list_learners()
    st.markdown(f"### Learners ({len(rows)})")
    for l in rows:
        c1, c2 = st.columns([0.85, 0.15])
        c1.markdown(f'**{l["display_name"] or "—"}** · {l["email"] or "—"} · {l["attempts"]} attempts · '
                    f'{l["total_points"]} pts · {l["completed_missions"]} completed')
        if c2.button("View", key=f"lv_{l['id']}"):
            st.session_state["admin_learner"] = l["id"]
            st.rerun()
    lid = st.session_state.get("admin_learner")
    if lid:
        d = A.learner_detail(lid)
        if d:
            st.markdown("---")
            st.markdown(f'### {d["learner"]["display_name"] or d["learner"]["email"]}')
            st.caption(f'LMS id: {d["learner"]["external_learner_id"]} · issuer: {d["learner"]["issuer"]}')
            cols = st.columns(2)
            for col, code in zip(cols, TRACK_CODES):
                bt = d["by_track"][code]
                col.markdown(f'<div class="kpi"><div class="l">{TRACKS[code]["name"]}</div>'
                             f'<div class="v" style="font-size:18px">{bt["completed"]}/{bt["attempted"]} · {bt["points"]} pts</div></div>',
                             unsafe_allow_html=True)
            rows = "".join(
                f'<tr><td>{a["mission_id"]}</td><td>{a["track"]}</td><td>{a["attempt_number"]}</td>'
                f'<td>{a["score"]}/{a["max_score"]}</td><td>{a["status"]}</td>'
                f'<td>{", ".join(a["feedback_tags"]) or "—"}</td></tr>' for a in d["attempts"]) or '<tr><td colspan="6">No attempts.</td></tr>'
            st.markdown(f'<table class="simple"><thead><tr><th>Activity</th><th>Track</th><th>#</th><th>Score</th>'
                        f'<th>Status</th><th>Tags</th></tr></thead><tbody>{rows}</tbody></table>', unsafe_allow_html=True)
            if st.button("Close learner", key="lclose"):
                st.session_state.pop("admin_learner", None)
                st.rerun()


_EXTERNAL_TYPES = [t for t in ACTIVITY_TYPES if t not in ("NATIVE", "H5P")]


def _activity_form(prefix, existing=None):
    """Render the create/edit form. Returns a data dict on submit, else None."""
    e = existing or {}
    types = _EXTERNAL_TYPES if not existing or existing.get("managed") else list(ACTIVITY_TYPES)
    with st.form(f"{prefix}_form", clear_on_submit=(existing is None)):
        c1, c2 = st.columns(2)
        title = c1.text_input("Title", value=e.get("title", ""))
        track = c2.selectbox("Track", TRACK_CODES,
                             index=(TRACK_CODES.index(e["track"]) if e.get("track") in TRACK_CODES else 0))
        c3, c4 = st.columns(2)
        atype = c3.selectbox("Activity type", types,
                            index=(types.index(e["activity_type"]) if e.get("activity_type") in types else 0))
        open_mode = c4.selectbox("Open mode", OPEN_MODES,
                                index=(OPEN_MODES.index(e.get("open_mode")) if e.get("open_mode") in OPEN_MODES else 0))
        url = st.text_input("Launch URL (https) — used when Open mode = NEW_TAB", value=e.get("url") or "")
        embed_url = st.text_input("Embed URL (https, approved domains) — used when Open mode = EMBED",
                                  value=e.get("embed_url") or "")
        description = st.text_area("Short description", value=e.get("description") or "", height=70)
        instructions = st.text_area("Instructions for learners", value=e.get("instructions") or "", height=70)
        c5, c6, c7 = st.columns(3)
        category = c5.text_input("Category", value=e.get("category") or "")
        provider = c6.text_input("Provider (e.g. H5P.COM, YOUTUBE)", value=e.get("provider") or "")
        due = c7.text_input("Due date (YYYY-MM-DD or blank)",
                            value=(e["due_date"].strftime("%Y-%m-%d") if e.get("due_date") else ""))
        c8, c9, c10 = st.columns(3)
        pass_mark = c8.number_input("Pass mark (%)", min_value=0, max_value=100,
                                    value=int(e["pass_mark"]) if e.get("pass_mark") is not None else 0)
        max_points = c9.number_input("Max score", min_value=0,
                                     value=int(e["max_points"]) if e.get("max_points") is not None else 0)
        status = c10.selectbox("Status", ACTIVITY_STATUSES,
                              index=(ACTIVITY_STATUSES.index(e.get("status")) if e.get("status") in ACTIVITY_STATUSES else 0))
        up = None
        if atype == "DOCUMENT":
            up = st.file_uploader("Optional document upload (stored in the database)",
                                  type=["pdf", "docx", "pptx", "xlsx", "txt", "csv", "png", "jpg", "jpeg"])
        submit = st.form_submit_button("Save activity", type="primary")
    if not submit:
        return None
    data = {
        "title": title, "track": track, "activity_type": atype, "open_mode": open_mode,
        "url": url.strip() or None, "embed_url": embed_url.strip() or None,
        "description": description, "instructions": instructions,
        "category": category.strip() or None, "provider": provider.strip() or None,
        "due_date": due.strip() or None,
        "pass_mark": int(pass_mark) if pass_mark else None,
        "max_points": int(max_points) if max_points else None,
        "status": status,
    }
    if up is not None:
        data["_file"] = (up.name, up.getvalue(), up.type or "application/octet-stream")
    return data


def _save_document_file(activity_id, file_tuple):
    """Persist an uploaded DOCUMENT file's bytes onto the activity row (kept in the DB)."""
    from database.connection import session_scope
    from database.models import Activity
    name, data, mime = file_tuple
    with session_scope() as s:
        a = s.query(Activity).filter_by(id=activity_id).one_or_none()
        if a:
            a.file_name, a.file_bytes, a.file_mime = name, data, mime


def _activities():
    st.markdown("### Activities")
    st.caption("Create and manage H5P links, external quizzes/assessments, embedded activities, "
               "videos, documents and other approved resources. Built-in missions (I12/I14) and "
               "uploaded .h5p packages are managed here too, but kept read-only where appropriate.")

    with st.expander("➕ Create a new activity", expanded=False):
        data = _activity_form("create")
        if data:
            fileinfo = data.pop("_file", None)
            try:
                res = A.create_activity(st.session_state["admin"]["id"], data)
                if fileinfo:
                    _save_document_file(res["id"], fileinfo)
                st.success(f'Created {res["code"]} ({res["track"]}) — status {res["status"]}.')
                st.rerun()
            except ValueError as ex:
                st.error(str(ex))

    acts = A.list_activities_admin()
    st.markdown(f"#### Existing activities ({len(acts)})")
    rows = "".join(
        f'<tr><td>{a["code"]}</td><td>{a["track"]}</td><td>{a["title"]}</td>'
        f'<td>{a.get("activity_type") or a["kind"]}</td><td>{a.get("status") or "—"}</td>'
        f'<td>{"Yes" if a["available"] else "No"}</td><td>{len(a["versions"])}</td></tr>' for a in acts)
    st.markdown(f'<table class="simple"><thead><tr><th>Code</th><th>Track</th><th>Title</th><th>Type</th>'
                f'<th>Status</th><th>Available</th><th>H5P versions</th></tr></thead>'
                f'<tbody>{rows}</tbody></table>', unsafe_allow_html=True)

    # Manage one activity (edit / publish / unpublish / preview)
    managed = [a for a in acts if a.get("managed")]
    if managed:
        st.markdown("#### Manage a custom activity")
        labels = {f'{a["code"]} · {a["track"]} · {a["title"]} [{a.get("status")}]': a["id"] for a in managed}
        pick = st.selectbox("Select", list(labels.keys()), key="manage_pick")
        aid = labels[pick]
        full = A.get_activity_admin(aid)
        b = st.columns(5)
        if b[0].button("Publish", key="mg_pub"):
            A.set_activity_status(aid, "PUBLISHED"); st.rerun()
        if b[1].button("Unpublish", key="mg_unp"):
            A.set_activity_status(aid, "UNPUBLISHED"); st.rerun()
        if b[2].button("Set draft", key="mg_draft"):
            A.set_activity_status(aid, "DRAFT"); st.rerun()
        if b[3].button("Archive", key="mg_arch"):
            A.set_activity_status(aid, "ARCHIVED"); st.rerun()
        if b[4].button("Delete", key="mg_del"):
            res = A.delete_activity(aid)
            st.warning(res.get("message") or ("Deleted." if res.get("deleted") else "Archived."))
            st.rerun()

        with st.expander("👁 Preview (admin)", expanded=False):
            _preview_activity(full)
        with st.expander("✏️ Edit", expanded=False):
            data = _activity_form(f"edit_{aid}", existing=full)
            if data:
                fileinfo = data.pop("_file", None)
                try:
                    A.update_activity(aid, data)
                    if fileinfo:
                        _save_document_file(aid, fileinfo)
                    st.success("Saved."); st.rerun()
                except ValueError as ex:
                    st.error(str(ex))


def _preview_activity(a):
    import streamlit.components.v1 as components
    from services import url_safety
    st.markdown(f"**{a['code']} — {a['title']}** · {a.get('activity_type')}")
    if a.get("description"):
        st.write(a["description"])
    if a.get("instructions"):
        st.caption(a["instructions"])
    target = a.get("embed_url") or a.get("url")
    if a.get("open_mode") == "EMBED" and target and url_safety.is_allowed_embed(target):
        components.html(
            f'<iframe src="{target}" style="width:100%;height:420px;border:1px solid #d9e0e6;'
            f'border-radius:10px" sandbox="allow-scripts allow-same-origin allow-forms allow-popups">'
            f'</iframe>', height=440, scrolling=True)
    elif target:
        st.link_button("Open target in a new tab →", target)
        if a.get("open_mode") == "EMBED":
            st.info("This host is not on the embed allowlist, so it would open in a new tab for learners.")
    else:
        st.info("No URL configured yet.")


def _h5p():
    st.markdown("### H5P activities")
    st.caption("Workflow: Upload → Validate → Publish. Publishing supersedes the previous version; "
               "published versions are never overwritten.")
    acts = A.list_activities_admin()
    options = {f'{a["code"]} · {a["track"]} · {a["title"]}': (a["code"], a["track"]) for a in acts}

    with st.form("h5p_upload", clear_on_submit=True):
        sel = st.selectbox("Activity & track", list(options.keys()))
        title = st.text_input("Title (optional)")
        up = st.file_uploader("Upload .h5p package", type=["h5p"])
        submit = st.form_submit_button("Upload", type="primary")
    if submit:
        if not up:
            st.error("Choose a .h5p file.")
        else:
            code, track = options[sel]
            try:
                r = A.h5p_upload(st.session_state["admin"]["id"], code, track, up.name, up.getvalue(), title or None)
                if r["validated_ok"]:
                    st.success(f'Uploaded v{r["version"]} — package looks valid. You can Publish it below.')
                else:
                    st.warning(f'Uploaded v{r["version"]} — validation: {r["validation"]}')
            except ValueError as e:
                st.error(str(e))

    st.markdown("---")
    for a in A.list_activities_admin():
        if not a["versions"]:
            continue
        st.markdown(f'**{a["code"]} · {a["track"]} — {a["title"]}**')
        for v in a["versions"]:
            cols = st.columns([0.1, 0.18, 0.3, 0.42])
            cols[0].markdown(f'v{v["version"]}')
            cols[1].markdown(f'<span class="badge">{v["status"]}</span>', unsafe_allow_html=True)
            cols[2].markdown(f'{v["file_name"]} ({round(v["file_size"]/1024)} KB)')
            with cols[3]:
                b = st.columns(4)
                if b[0].button("Validate", key=f"val_{v['id']}"):
                    try:
                        A.h5p_validate(v["id"]); st.rerun()
                    except ValueError as e:
                        st.error(str(e))
                if v["status"] != "PUBLISHED":
                    if b[1].button("Publish", key=f"pub_{v['id']}"):
                        try:
                            A.h5p_publish(v["id"]); st.rerun()
                        except ValueError as e:
                            st.error(str(e))
                else:
                    if b[1].button("Unpublish", key=f"unp_{v['id']}"):
                        A.h5p_unpublish(v["id"]); st.rerun()
                if b[2].button("Results", key=f"res_{v['id']}"):
                    att = A.h5p_version_attempts(v["id"])
                    st.info("\n".join(f'{r["learner"]}: {r["score"]}/{r["max_score"]} ({r["status"]})' for r in att) or "No attempts yet.")


_REPORT_STATUSES = ["(any)", "NOT_STARTED", "ACCESSED", "IN_PROGRESS", "COMPLETED"]


def _results():
    st.markdown("### Reports")
    st.caption("All rows come from persisted PostgreSQL records. ‘Score verified’ marks a real "
               "score from a trusted integration (native missions, uploaded H5P/xAPI); a dash means "
               "only launch/access was observed.")

    acts = A.list_activities_admin()
    codes = ["(all)"] + sorted({a["code"] for a in acts})
    f1, f2, f3 = st.columns(3)
    code = f1.selectbox("Activity", codes, key="rep_code")
    track = f2.selectbox("Track", ["(all)"] + list(TRACK_CODES), key="rep_track")
    status = f3.selectbox("Status", _REPORT_STATUSES, key="rep_status")
    g1, g2, g3 = st.columns(3)
    learner_q = g1.text_input("Learner (email/name/id)", key="rep_learner")
    date_from = g2.text_input("From (YYYY-MM-DD)", key="rep_from")
    date_to = g3.text_input("To (YYYY-MM-DD)", key="rep_to")
    only_incomplete = st.checkbox("Only incomplete activities", key="rep_incomplete")

    filters = dict(
        activity_code=None if code == "(all)" else code,
        track=None if track == "(all)" else track,
        status=None if status == "(any)" else status,
        learner_q=learner_q or None,
        date_from=date_from or None, date_to=date_to or None,
    )
    rows = A.incomplete_report(**filters) if only_incomplete else A.report_rows(**filters)

    st.markdown(f"**{len(rows)} record(s)**")
    csv_data = A.tracking_csv(**filters)
    st.download_button("⬇ Export to CSV", data=csv_data, file_name="decision-lab-tracking.csv",
                       mime="text/csv", key="rep_csv")

    def _score(r):
        if r["score"] is None:
            return "—"
        base = f'{r["score"]}/{r["max_score"]}' if r["max_score"] is not None else str(r["score"])
        return base + ("" if r["score_verified"] else " (unverified)")

    html = "".join(
        f'<tr><td>{r["learner"]}</td><td>{r["email"] or "—"}</td><td>{r["code"]}</td>'
        f'<td>{r["type"]}</td><td>{r["track"]}</td><td>{r["status"]}</td><td>{_score(r)}</td>'
        f'<td>{"✓" if r["score_verified"] else "—"}</td>'
        f'<td>{r["last_accessed_at"]:%Y-%m-%d %H:%M}</td></tr>'
        for r in rows[:500]) or '<tr><td colspan="9">No records match these filters.</td></tr>'
    st.markdown(f'<table class="simple"><thead><tr><th>Learner</th><th>Email</th><th>Activity</th>'
                f'<th>Type</th><th>Track</th><th>Status</th><th>Score</th><th>Verified</th>'
                f'<th>Last accessed</th></tr></thead><tbody>{html}</tbody></table>', unsafe_allow_html=True)


def _integration():
    st.markdown("### Tracking coverage & limitations")
    st.caption("Be transparent about what is and isn't tracked, so scores are never over-claimed.")
    data = A.integration_limitations()
    lim = data["limited_activities"]
    st.markdown("#### Activities without verified score tracking")
    if lim:
        html = "".join(
            f'<tr><td>{r["code"]}</td><td>{r["track"]}</td><td>{r["title"]}</td><td>{r["type"]}</td>'
            f'<td>{r["status"]}</td><td>{"Yes" if r["has_verified_scores"] else "No"}</td></tr>'
            for r in lim)
        st.markdown(f'<table class="simple"><thead><tr><th>Code</th><th>Track</th><th>Title</th>'
                    f'<th>Type</th><th>Status</th><th>Has verified scores?</th></tr></thead>'
                    f'<tbody>{html}</tbody></table>', unsafe_allow_html=True)
        st.info("For these activity types we record launch/access only. A score or completion is "
                "stored just for those with a confirmed integration (xAPI / LTI-AGS).")
    else:
        st.write("No external activities configured yet.")

    st.markdown("#### Recent tracking errors")
    errs = data["errors"]
    if errs:
        html = "".join(f'<tr><td>{e["when"]:%Y-%m-%d %H:%M}</td><td>{e["code"] or "—"}</td>'
                       f'<td>{e["message"] or "—"}</td></tr>' for e in errs)
        st.markdown(f'<table class="simple"><thead><tr><th>When</th><th>Activity</th><th>Message</th>'
                    f'</tr></thead><tbody>{html}</tbody></table>', unsafe_allow_html=True)
    else:
        st.write("No tracking errors recorded.")
