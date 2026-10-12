"""The native mission player — reproduces the branching Decision Lab flow in Streamlit.

Streamlit reruns the script on every interaction, so all per-attempt state lives in
st.session_state['mp'] and every graded decision is persisted to the database immediately
(so a rerun or refresh never loses it). Each decision is recorded exactly once: the record
call happens inside the button-click branch, which only runs on the click's rerun.
"""
import streamlit as st

from content.missions import get_mission
from content.registry import TASK_BY_ID, TAGS, REGISTER
from services import progress_service as P


def _mp():
    return st.session_state.setdefault("mp", {})


def start(code, level):
    """Initialise (or resume) an attempt and reset the player substate."""
    started = P.start_attempt(st.session_state["learner"]["id"], code, level)
    st.session_state["mp"] = {
        "code": code, "level": level,
        "attempt_id": started["attempt_id"],
        "echo": started["echo"],
        "i": 0,                 # current step index
        "needs_repair": False,
        "consequence": None,    # {"code","tone","title","html","continue","score","max","aligned","red"}
        "repair": None,         # {"ok","title","html"}
        "classify": None,       # {"ok","text"}
        "evidence": None,       # {"picked","need"}
        "triage": None,         # {"ok","total","rows"}
        "order": None,          # {"ok","total"}
        "final": None,          # completed attempt dict
    }


def _steps():
    m = _mp()
    return get_mission(m["code"])[m["level"]]["steps"]


def _advance():
    m = _mp()
    nxt = m["i"] + 1
    steps = _steps()
    if nxt < len(steps) and steps[nxt]["type"] == "repair" and not m["needs_repair"]:
        nxt += 1
    m["i"] = nxt
    # reset per-step scratch for the step we are entering
    m["consequence"] = m["repair"] = m["classify"] = None


def _progress_bar():
    m = _mp()
    steps = _steps()
    chips = []
    for idx, s in enumerate(steps):
        cls = "stp cur" if idx == m["i"] else ("stp ok" if idx < m["i"] else "stp")
        chips.append(f'<span class="{cls}">{s["label"]}</span>')
    st.markdown(f'<div class="steps">{"".join(chips)}</div>', unsafe_allow_html=True)


def _docs_html(docs):
    out = []
    for d in docs or []:
        head = d["head"]["label"]
        if d.get("kind") == "email":
            rows = "".join(f'<div class="row"><b>{a}:</b> {b}</div>' for a, b in d.get("rows", []))
            body = f'{rows}<div class="subject">{d["subject"]}</div><div>{d["body"]}</div>'
        else:
            body = d["html"]
        out.append(f'<div class="doc"><div class="doc-h">{head}</div><div class="doc-b">{body}</div></div>')
    return "".join(out)


def render():
    m = _mp()
    code, level = m["code"], m["level"]
    mission = get_mission(code)
    lvlcls = "lv-f" if level == "FOUNDATION" else "lv-p"
    lvlname = "Foundation" if level == "FOUNDATION" else "Practitioner"

    top1, top2 = st.columns([0.8, 0.2])
    with top1:
        st.markdown(f'<span class="levelchip {lvlcls}">{lvlname}</span>  &nbsp; '
                    f'<b style="font-family:Inter">{code} — {mission["title"]}</b>', unsafe_allow_html=True)
    with top2:
        if st.button("✕ Close", key="mp_close"):
            st.session_state["view"] = "activity"
            st.rerun()

    steps = _steps()
    if m["i"] >= len(steps):
        return _render_record()

    _progress_bar()
    step = steps[m["i"]]
    t = step["type"]
    if t in ("brief", "evidence"):
        _render_brief(step)
    elif t == "evidenceSelect":
        _render_evidence_select(step)
    elif t == "classify":
        _render_classify(step)
    elif t == "decide":
        _render_decide(step)
    elif t == "repair":
        _render_repair(step)
    elif t == "triage":
        _render_triage(step)
    elif t == "order":
        _render_order(step)
    elif t == "method":
        _render_method(step)


def _render_brief(step):
    m = _mp()
    st.markdown(f'<div class="eyebrow">{step.get("eyebrow","")}</div>', unsafe_allow_html=True)
    st.markdown(f"## {step['title']}")
    if m["i"] == 0 and m.get("echo"):
        st.markdown(f'<div class="echo">⚡ <b>Earlier decision echo — {m["echo"]["from"]}.</b> {m["echo"]["text"]}</div>', unsafe_allow_html=True)
    if step.get("body"):
        st.markdown(f'<p>{step["body"]}</p>', unsafe_allow_html=True)
    if step.get("docs"):
        st.markdown(_docs_html(step["docs"]), unsafe_allow_html=True)
    if st.button(step.get("cta", "Continue") + " →", type="primary", key=f"c{m['i']}"):
        _advance()
        st.rerun()


def _render_method(step):
    m = _mp()
    st.markdown(f'<div class="eyebrow">{step.get("eyebrow","Method debrief")}</div>', unsafe_allow_html=True)
    st.markdown(f"## {step['title']}")
    panels = "".join(f"<p>{p}</p>" for p in step.get("panels", []))
    st.markdown(f'<div class="panel method">{panels}</div>', unsafe_allow_html=True)
    if step.get("missed"):
        st.markdown(f'<div class="doc"><div class="doc-h">Missed evidence to revisit</div><div class="doc-b">{step["missed"]}</div></div>', unsafe_allow_html=True)
    if st.button(step.get("cta", "See your record") + " →", type="primary", key=f"m{m['i']}"):
        _advance()
        st.rerun()


def _render_decide(step):
    m = _mp()
    st.markdown(f'<div class="eyebrow">{step.get("eyebrow","Decision")}</div>', unsafe_allow_html=True)
    st.markdown(f"## {step['title']}")
    if step.get("body"):
        st.markdown(f'<p class="doc-b">{step["body"]}</p>', unsafe_allow_html=True)

    if m["consequence"] is None:
        for o in step["options"]:
            if st.button(f"**{o['code']}** — {o['text']}", key=f"d{m['i']}{o['code']}"):
                r = P.record_event(st.session_state["learner"]["id"], m["attempt_id"], m["code"], m["level"], "decide", o["code"])
                cons = step["consequence"][o["code"]]
                aligned = r["attempt"]["score"] >= r["attempt"]["max_score"]
                m["needs_repair"] = not aligned
                m["consequence"] = {**cons, "code": o["code"], "score": r["attempt"]["score"],
                                    "max": r["attempt"]["max_score"], "aligned": aligned, "red": r["red_line"]}
                st.rerun()
    else:
        c = m["consequence"]
        flag = "s2" if c["aligned"] else ("s0" if c["tone"] == "bad" else "s1")
        flagtxt = "2 points · method-aligned" if c["aligned"] else ("0 · red-line" if c["tone"] == "bad" else "repair needed")
        st.markdown(f'<div class="panel {c["tone"]}"><span class="scoreflag {flag}">● {flagtxt}</span>'
                    f'<h4>{c["title"]}</h4><p>{c["html"]}</p></div>', unsafe_allow_html=True)
        if m["needs_repair"]:
            label = "Complete the mandatory repair →" if c["tone"] == "bad" else "Repair this decision →"
            if st.button(label, type="primary", key=f"dn{m['i']}"):
                _advance()
                st.rerun()
        else:
            if st.button(c.get("continue", "Continue") + " →", type="primary", key=f"dn{m['i']}"):
                _advance()
                st.rerun()


def _render_repair(step):
    m = _mp()
    st.markdown(f'<div class="eyebrow">{step.get("eyebrow","Repair")}</div>', unsafe_allow_html=True)
    st.markdown(f"## {step['title']}")
    if step.get("body"):
        st.markdown(f'<p class="doc-b">{step["body"]}</p>', unsafe_allow_html=True)
    if m["repair"] is None:
        for o in step["options"]:
            if st.button(f"**{o['code']}** — {o['text']}", key=f"r{m['i']}{o['code']}"):
                r = P.record_event(st.session_state["learner"]["id"], m["attempt_id"], m["code"], m["level"], "repair", o["code"])
                ok = bool(r["correct"])
                fb = step["feedback"]["ok"] if ok else step["feedback"]["bad"]
                m["repair"] = {"ok": ok, **fb}
                st.rerun()
    else:
        c = m["repair"]
        flag = "s1" if c["ok"] else "s0"
        flagtxt = "1 point · repaired" if c["ok"] else "0 · unresolved"
        tone = "good" if c["ok"] else "bad"
        st.markdown(f'<div class="panel {tone}"><span class="scoreflag {flag}">● {flagtxt}</span>'
                    f'<h4>{c["title"]}</h4><p>{c["html"]}</p></div>', unsafe_allow_html=True)
        if st.button(step.get("continue", "Continue") + " →", type="primary", key=f"rn{m['i']}"):
            _advance()
            st.rerun()


def _render_classify(step):
    m = _mp()
    st.markdown(f'<div class="eyebrow">{step.get("eyebrow","Classify")}</div>', unsafe_allow_html=True)
    st.markdown(f"## {step['title']}")
    if m["classify"] is None:
        for o in step["options"]:
            if st.button(o["label"], key=f"cl{m['i']}{o['key']}"):
                r = P.record_event(st.session_state["learner"]["id"], m["attempt_id"], m["code"], m["level"], "classify", o["key"])
                ok = bool(r["correct"])
                m["classify"] = {"ok": ok, "text": step["feedback"]["ok"] if ok else step["feedback"]["bad"]}
                st.rerun()
    else:
        c = m["classify"]
        st.markdown(f'<div class="panel {"good" if c["ok"] else "warn"}"><p>{c["text"]}</p></div>', unsafe_allow_html=True)
        if st.button(step.get("continue", "Continue") + " →", type="primary", key=f"cln{m['i']}"):
            _advance()
            st.rerun()


def _render_evidence_select(step):
    m = _mp()
    st.markdown(f'<div class="eyebrow">{step.get("eyebrow","Evidence selection")}</div>', unsafe_allow_html=True)
    st.markdown(f"## {step['title']}")
    st.markdown(f'<p class="doc-b">{step.get("body","")}</p>', unsafe_allow_html=True)
    graded = m["evidence"] is not None
    picks = []
    for idx, it in enumerate(step["items"]):
        checked = st.checkbox(f"**{it['t']}** — {it['d']}", key=f"ev{m['i']}{idx}", disabled=graded)
        picks.append(checked)
        if graded:
            if it["good"]:
                st.markdown('<span style="color:var(--good);font-size:12px">✓ needed</span>', unsafe_allow_html=True)
            elif checked:
                st.markdown('<span style="color:var(--bad);font-size:12px">✗ not decisive</span>', unsafe_allow_html=True)
    if not graded:
        if st.button("Check selection", type="primary", key=f"evg{m['i']}"):
            picked_good = sum(1 for i, it in enumerate(step["items"]) if it["good"] and picks[i])
            P.record_event(st.session_state["learner"]["id"], m["attempt_id"], m["code"], m["level"], "evidence", f"{picked_good}/{step['need']}")
            m["evidence"] = {"picked": picked_good, "need": step["need"]}
            st.rerun()
    else:
        st.caption(f"You identified {m['evidence']['picked']} of {m['evidence']['need']} decisive items.")
        if st.button(step.get("continue", "Continue") + " →", type="primary", key=f"evn{m['i']}"):
            _advance()
            st.rerun()


def _render_triage(step):
    m = _mp()
    st.markdown(f'<div class="eyebrow">{step.get("eyebrow","Supporting task")}</div>', unsafe_allow_html=True)
    st.markdown(f"## {step['title']}")
    st.markdown(f'<p class="doc-b">{step.get("body","")}</p>', unsafe_allow_html=True)
    graded = m["triage"] is not None
    choices = []
    for idx, c in enumerate(step["cases"]):
        sel = st.selectbox(f"{idx+1}. {c['case']}", ["— choose —"] + step["types"], key=f"tr{m['i']}{idx}", disabled=graded)
        choices.append(sel)
        if graded:
            right = choices[idx] == c["ans"]
            st.markdown(f'<span style="color:var(--{"good" if right else "bad"});font-size:12px">'
                        f'{"✓ " + c["fb"] if right else "✗ Correct: " + c["ans"] + " — " + c["fb"]}</span>', unsafe_allow_html=True)
    if not graded:
        if st.button("Grade triage", type="primary", key=f"trg{m['i']}"):
            ok = sum(1 for i, c in enumerate(step["cases"]) if choices[i] == c["ans"])
            P.record_event(st.session_state["learner"]["id"], m["attempt_id"], m["code"], m["level"], "triage", f"{ok}/{len(step['cases'])}")
            m["triage"] = {"ok": ok, "total": len(step["cases"])}
            st.rerun()
    else:
        st.caption(f"Triage {m['triage']['ok']}/{m['triage']['total']}")
        if st.button(step.get("continue", "Continue") + " →", type="primary", key=f"trn{m['i']}"):
            _advance()
            st.rerun()


def _render_order(step):
    m = _mp()
    st.markdown(f'<div class="eyebrow">{step.get("eyebrow","Supporting task")}</div>', unsafe_allow_html=True)
    st.markdown(f"## {step['title']}")
    st.markdown(f'<p class="doc-b">{step.get("body","")}</p>', unsafe_allow_html=True)
    graded = m["order"] is not None
    n = len(step["items"])
    positions = []
    for idx, item in enumerate(step["items"]):
        pos = st.selectbox(item, list(range(1, n + 1)), index=idx, key=f"or{m['i']}{idx}", disabled=graded)
        positions.append(pos)
    if not graded:
        if st.button("Grade sequence", type="primary", key=f"org{m['i']}"):
            # correct order = the natural order of items (0..n-1 => positions 1..n)
            correct = sum(1 for idx in range(n) if positions[idx] == idx + 1)
            P.record_event(st.session_state["learner"]["id"], m["attempt_id"], m["code"], m["level"], "order", f"{correct}/{n}")
            m["order"] = {"ok": correct, "total": n}
            st.rerun()
    else:
        st.caption(f"Sequence {m['order']['ok']}/{m['order']['total']} in the right place. Correct order: " +
                   " → ".join(f"{i+1}. {step['items'][i]}" for i in range(n)))
        if st.button(step.get("continue", "Continue") + " →", type="primary", key=f"orn{m['i']}"):
            _advance()
            st.rerun()


def _render_record():
    m = _mp()
    if m["final"] is None:
        res = P.complete_attempt(st.session_state["learner"]["id"], m["attempt_id"], m["code"], m["level"])
        m["final"] = res["attempt"]
    a = m["final"]
    mission = get_mission(m["code"])
    sc = a["score"]
    color = "var(--good)" if sc == 2 else ("var(--warn)" if sc == 1 else "var(--bad)")
    outcome = "Aligned first time" if (sc == 2 and a["first_time_aligned"]) else ("Repaired" if a["repaired"] else "Unresolved")
    tag = (a["feedback_tags"] or [None])[0]

    st.markdown(f"## {m['code']} — complete")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="kpi"><div class="l">Practice score</div><div class="v" style="color:{color}">{sc}/{a["max_score"]}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi"><div class="l">Outcome</div><div class="v" style="font-size:16px">{outcome}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi"><div class="l">Route</div><div class="v" style="font-size:16px">{a["route_code"] or "—"}</div></div>', unsafe_allow_html=True)

    if tag:
        st.markdown(f'<div class="panel warn" style="margin-top:12px"><h4>Misconception tag</h4>'
                    f'<p><code>{tag}</code> — {TAGS.get(tag,"")}. Review {mission["method_ref"]}.</p></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="panel good" style="margin-top:12px"><p>No misconception tag — clean run on the method rule.</p></div>', unsafe_allow_html=True)

    st.markdown("**Recommended next**")
    cols = st.columns(len(mission.get("related", [])) or 1)
    for i, rel in enumerate(mission.get("related", [])):
        label = next((r["task"] for r in REGISTER if r["id"] == rel["id"]), rel["id"])
        with cols[i]:
            st.caption(f"{rel['id']} — {rel['why']}")

    st.markdown('<p class="disclaim">Fictional Project Practice Record — an automatically generated record of practice in a '
                'fictional simulation. Not a certificate, qualification, assessed portfolio, exam result or verified professional evidence.</p>',
                unsafe_allow_html=True)

    b1, b2 = st.columns(2)
    if b1.button("Replay mission", key="replay"):
        start(m["code"], m["level"])
        st.rerun()
    if b2.button("Back to the hub →", type="primary", key="tohub"):
        st.session_state["view"] = "dashboard"
        st.rerun()
