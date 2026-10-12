"""Learner portal views: dashboard (two track cards + KPIs), per-track activity list, and the
activity detail page. Simple and consistent with the original design."""
import streamlit as st

from content.registry import TASK_BY_ID
from services import progress_service as P
from components import styling
from learner import mission_player


def _who_html():
    l = st.session_state["learner"]
    return f'Learner: <b>{l.get("display_name") or "—"}</b><br>{l.get("email") or ""}'


def render_dashboard():
    styling.top_bar("Better Repairs Programme · PRINCE2 practice", _who_html())
    styling.fictional_notice()
    st.markdown("# Kestrelford Repairs Decision Lab")

    tp = P.track_progress(st.session_state["learner"]["id"])
    F, Pr = tp["FOUNDATION"], tp["PRACTITIONER"]

    k = st.columns(4)
    kpis = [
        ("Activities completed", F["completed"] + Pr["completed"]),
        ("Activities attempted", F["attempted"] + Pr["attempted"]),
        ("Foundation", f'{F["completed"]}/{F["activities_available"]}'),
        ("Practitioner", f'{Pr["completed"]}/{Pr["activities_available"]}'),
    ]
    for col, (lbl, val) in zip(k, kpis):
        col.markdown(f'<div class="kpi"><div class="l">{lbl}</div><div class="v">{val}</div></div>', unsafe_allow_html=True)

    try:
        from auth.email_identity import is_unverified_identity
        if is_unverified_identity(st.session_state["learner"]):
            st.caption("ℹ️ You're signed in with a self-declared email (unverified). Your progress is "
                       "saved to this email; it is not a verified identity.")
    except Exception:
        pass

    st.write("")
    c1, c2 = st.columns(2)
    _track_card(c1, "FOUNDATION", F, "f")
    _track_card(c2, "PRACTITIONER", Pr, "p")

    recent = P.recently_opened(st.session_state["learner"]["id"], limit=8)
    if recent:
        st.markdown("### Recently opened activities")
        rows = ""
        for r in recent:
            when = f'{r["last_accessed_at"]:%Y-%m-%d %H:%M}' if r.get("last_accessed_at") else "—"
            if r.get("score") is not None and r.get("score_verified"):
                sc = f'{r["score"]}/{r["max_score"]}' if r.get("max_score") is not None else str(r["score"])
            else:
                sc = "—"
            statusword = {"COMPLETED": "Completed", "IN_PROGRESS": "In progress",
                          "ACCESSED": "Opened"}.get(r.get("status"), r.get("status") or "—")
            rows += (f'<tr><td><b>{r["code"]}</b> {r["title"]}</td>'
                     f'<td>{"Foundation" if r["track"]=="FOUNDATION" else "Practitioner"}</td>'
                     f'<td>{statusword}</td><td>{sc}</td><td>{when}</td></tr>')
        st.markdown(f'<table class="simple"><thead><tr><th>Activity</th><th>Track</th>'
                    f'<th>Status</th><th>Score</th><th>Last opened</th></tr></thead>'
                    f'<tbody>{rows}</tbody></table>', unsafe_allow_html=True)


def _track_card(col, code, t, cls):
    last = f'Last: {t["last_activity"]["code"]} — {t["last_activity"]["title"]}' if t["last_activity"] else "Not started yet"
    with col:
        st.markdown(
            f'<div class="tcard {cls}"><span class="md">{t["mode"]}</span>'
            f'<div class="tt">{t["name"]}</div>'
            f'<div class="bar"><i style="width:{t["completion_pct"]}%"></i></div>'
            f'<div class="meta"><b>{t["completed"]}</b> of {t["activities_available"]} activities · {t["completion_pct"]}%</div>'
            f'<div class="meta">{t["attempted"]} attempted · best {t["best_points"]}/{t["max_points"]} pts'
            f'{" · avg " + str(t["average_score"]) if t["average_score"] is not None else ""}</div>'
            f'<div class="meta" style="opacity:.8">{last}</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("Continue →", type="primary", key=f"open_{code}"):
            st.session_state["view"] = "track"
            st.session_state["track"] = code
            st.rerun()


def render_track(track):
    styling.top_bar("Better Repairs Programme · PRINCE2 practice", _who_html())
    if st.button("← Dashboard", key="t_back"):
        st.session_state["view"] = "dashboard"
        st.rerun()
    styling.fictional_notice()
    name = "PRINCE2 Foundation" if track == "FOUNDATION" else "PRINCE2 Practitioner"
    st.markdown(f"# {name}")
    mode = "Guided Practice" if track == "FOUNDATION" else "Applied Judgement"
    st.caption(f"{mode} — open an activity to begin. Your progress saves automatically.")

    rows = P.activities_with_status(st.session_state["learner"]["id"])[track]
    for a in rows:
        ico = {"COMPLETED": '<span class="stico done">✓</span>', "IN_PROGRESS": '<span class="stico prog">•</span>'}.get(
            a["status"], '<span class="stico open"></span>')
        sc = ""
        if a["status"] == "COMPLETED" and a["score"] is not None:
            scol = "var(--good)" if a["score"] == a["max_score"] else ("var(--amber)" if a["score"] >= 1 else "var(--bad)")
            sc = f'<span class="sc" style="color:{scol}">{a["score"]}/{a["max_score"]}</span>'
        _type_labels = {"H5P": "H5P", "H5P_LINK": "H5P link", "EXTERNAL_QUIZ": "Quiz",
                        "EMBED": "Embed", "VIDEO": "Video", "DOCUMENT": "Document", "LINK": "Link"}
        _tl = _type_labels.get(a.get("activity_type"))
        badge = f'<span class="badge">{_tl}</span>' if _tl else ""
        statusword = {"COMPLETED": "Completed", "IN_PROGRESS": "In progress",
                      "ACCESSED": "Opened"}.get(a["status"], "Not started")
        if not a["available"]:
            statusword += " · in build"
        row, btn = st.columns([0.82, 0.18])
        with row:
            st.markdown(
                f'<div class="arow">{ico}<span class="code">{a["code"]}</span>'
                f'<span class="t"><b>{a["title"]}</b><br><span style="font-size:12px;color:var(--ink-2)">{statusword}</span></span>'
                f'{badge} {sc}</div>', unsafe_allow_html=True)
        with btn:
            if a["available"]:
                if st.button("Open", key=f"act_{track}_{a['code']}"):
                    st.session_state["view"] = "activity"
                    st.session_state["act_code"] = a["code"]
                    st.session_state["track"] = track
                    st.rerun()
            else:
                st.button("Open", key=f"act_{track}_{a['code']}", disabled=True)


def render_activity():
    code = st.session_state["act_code"]
    track = st.session_state["track"]
    styling.top_bar("Better Repairs Programme · PRINCE2 practice", _who_html())
    if st.button("← Back", key="a_back"):
        st.session_state["view"] = "track"
        st.rerun()
    styling.fictional_notice()

    d = P.activity_detail(st.session_state["learner"]["id"], code, track)
    if not d:
        st.error("Activity not found.")
        return
    a, best = d["activity"], d["best"]
    atype = a.get("activity_type") or a.get("kind") or "NATIVE"

    # External activity types (links/embeds/videos/documents/H5P links) are handled by the launcher.
    if atype not in ("NATIVE", "H5P"):
        _render_external_detail(a, d.get("external"), track)
        return

    lvlcls = "lv-f" if track == "FOUNDATION" else "lv-p"
    name = "PRINCE2 Foundation" if track == "FOUNDATION" else "PRINCE2 Practitioner"
    st.markdown(f'<span class="levelchip {lvlcls}">{name}</span>', unsafe_allow_html=True)
    st.markdown(f"# {a['code']} — {a['title']}")
    st.markdown(f'<p class="doc-b">{a["description"] or ""}</p>', unsafe_allow_html=True)
    st.caption(f"Estimated time: {a['est_minutes'] or '10–12'} min · {'H5P activity' if a['kind']=='H5P' else 'Decision Lab mission'}")

    if best and best["completed"]:
        scol = "var(--good)" if best["score"] == best["max_score"] else ("var(--amber)" if best["score"] >= 1 else "var(--bad)")
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="kpi"><div class="l">Practice score</div><div class="v" style="color:{scol}">{best["score"]}/{best["max_score"]}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="kpi"><div class="l">Attempts</div><div class="v">{best["attempt_number"]}</div></div>', unsafe_allow_html=True)
        oc = "Aligned" if best["first_time_aligned"] else ("Repaired" if best["repaired"] else "Completed")
        c3.markdown(f'<div class="kpi"><div class="l">Outcome</div><div class="v" style="font-size:16px">{oc}</div></div>', unsafe_allow_html=True)
        label = "Replay"
    elif best and best["status"] == "IN_PROGRESS":
        st.info(f"In progress — attempt #{best['attempt_number']}.")
        label = "Continue"
    else:
        label = "Start"

    if not a["available"]:
        st.warning("This activity is registered but not yet built. I12 and I14 are the playable pilot activities.")
        return

    if st.button(label + " →", type="primary", key="play"):
        if atype == "H5P":
            st.session_state["view"] = "h5p"
            st.rerun()
        else:
            mission_player.start(code, track)
            st.session_state["view"] = "mission"
            st.rerun()


def _render_external_detail(a, ext, track):
    lvlcls = "lv-f" if track == "FOUNDATION" else "lv-p"
    name = "PRINCE2 Foundation" if track == "FOUNDATION" else "PRINCE2 Practitioner"
    st.markdown(f'<span class="levelchip {lvlcls}">{name}</span>', unsafe_allow_html=True)
    st.markdown(f"# {a['code']} — {a['title']}")
    if a.get("description"):
        st.markdown(f'<p class="doc-b">{a["description"]}</p>', unsafe_allow_html=True)
    _type_labels = {"H5P_LINK": "H5P link", "EXTERNAL_QUIZ": "External quiz", "EMBED": "Embedded activity",
                    "VIDEO": "Video", "DOCUMENT": "Document", "LINK": "External link"}
    st.caption(f"{_type_labels.get(a.get('activity_type'), 'Activity')}"
               + (f" · {a['provider']}" if a.get("provider") else ""))
    if ext and ext.get("last_access_at"):
        st.info(f"You last opened this on {ext['last_access_at']:%Y-%m-%d %H:%M} "
                f"· launches: {ext.get('launch_count') or 0}")
    if not a["available"]:
        st.warning("This activity is not published yet.")
        return
    if st.button("Open activity →", type="primary", key="open_external"):
        st.session_state["view"] = "launch"
        st.rerun()
