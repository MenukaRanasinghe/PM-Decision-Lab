"""Learner practice record view with PDF download."""
import streamlit as st

from services import progress_service as P
from services.pdf_service import practice_record_pdf
from components import styling


def render():
    styling.top_bar("Better Repairs Programme · PRINCE2 practice",
                    f'Learner: <b>{st.session_state["learner"].get("display_name") or "—"}</b>')
    if st.button("← Dashboard", key="pr_back"):
        st.session_state["view"] = "dashboard"
        st.rerun()
    styling.fictional_notice()

    r = P.practice_record(st.session_state["learner"]["id"])
    st.markdown(f"# {r['title']}")
    st.caption(f'{r["learner"]["name"]} · {r["learner"]["email"] or ""} · generated {r["generated_at"]:%Y-%m-%d %H:%M}')

    c1, c2 = st.columns(2)
    for col, code in zip((c1, c2), ("FOUNDATION", "PRACTITIONER")):
        t = r["tracks"][code]
        avg = t["average_score"] if t["average_score"] is not None else "—"
        col.markdown(
            f'<div class="kpi" style="text-align:left;padding:16px"><div class="l">{t["name"]}</div>'
            f'<div style="margin-top:8px;font-size:13px">Completed <b>{t["completed"]}</b>/{t["attempted"] or 0} · '
            f'Score <b>{t["total_practice_score"]}/{t["max_practice_score"]}</b> · Avg <b>{avg}</b> · '
            f'{t["completion_pct"]}%</div></div>', unsafe_allow_html=True)

    st.markdown("### Recent decisions")
    rows = "".join(
        f'<tr><td><b>{x["activity"]}</b> {x["title"]}</td><td>{"Foundation" if x["track"]=="FOUNDATION" else "Practitioner"}</td>'
        f'<td>{x["score"]}</td><td>{x["tag"] or "—"}</td><td>{x["completed_at"]:%Y-%m-%d}</td></tr>'
        for x in r["recent"]) or '<tr><td colspan="5">No completed activities yet.</td></tr>'
    st.markdown(f'<table class="simple"><thead><tr><th>Activity</th><th>Track</th><th>Score</th>'
                f'<th>Feedback tag</th><th>Completed</th></tr></thead><tbody>{rows}</tbody></table>', unsafe_allow_html=True)

    pdf = practice_record_pdf(r)
    st.download_button("Download Practice Record (PDF)", data=pdf,
                       file_name="kestrelford-practice-record.pdf", mime="application/pdf", type="primary")

    st.markdown('<p class="disclaim">Fictional Project Practice Record — not a certificate, professional qualification, '
                'assessed portfolio, exam result, or verified professional evidence.</p>', unsafe_allow_html=True)
