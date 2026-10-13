"""Kestrelford Repairs Decision Lab — Streamlit entry point.

Run locally:  streamlit run app.py

Identity: resolved from a signed session token in the URL (?s=), which is set after a validated
LMS launch (?launch=<signed token>) or a dev login. A raw query parameter is never trusted as
identity — only a signed, short-lived token. Progress always lives in the database, so a refresh
(which re-reads ?s=) restores the learner's state.
"""
import streamlit as st

st.set_page_config(page_title="Kestrelford Decision Lab", page_icon="🧭", layout="wide")

from config import config
from database.init_db import init_db
from components import styling
from auth.tokens import verify_session, issue_session, verify_launch_token
from auth.learner_identity import upsert_learner, consume_nonce, get_learner
from auth.dev_login import SAMPLE_LEARNERS
from auth import email_identity
from learner import portal, mission_player, practice_record, h5p_player, activity_launcher
from admin import panel as admin_panel

# one-time DB init per process
if not st.session_state.get("_db_ready"):
    init_db()
    st.session_state["_db_ready"] = True

styling.inject()


def _login_learner(learner):
    st.session_state["learner"] = learner
    token = issue_session(learner["id"])
    st.session_state["session_token"] = token
    try:
        st.query_params.clear()
        st.query_params["s"] = token
    except Exception:
        pass


def resolve_identity():
    if st.session_state.get("learner"):
        return
    qp = st.query_params

    launch = qp.get("launch")
    if launch:
        claims = verify_launch_token(launch)
        if claims and consume_nonce(claims["jti"], claims.get("issuer") or ""):
            learner = upsert_learner(claims)
            _login_learner(learner)
            if claims.get("mission"):
                st.session_state["deeplink"] = claims["mission"]
            st.rerun()
        else:
            st.session_state["launch_error"] = "That launch link was invalid or has expired. Please relaunch from your LMS."
            try:
                del st.query_params["launch"]
            except Exception:
                pass
        return

    dev = qp.get("dev")
    if dev and config.DEV_MODE:
        sample = next((s for s in SAMPLE_LEARNERS if s["external_learner_id"] == dev), None)
        if sample:
            _login_learner(upsert_learner(sample))
            st.rerun()
        return

    s = qp.get("s")
    if s:
        lid = verify_session(s)
        if lid:
            learner = get_learner(lid)
            if learner:
                st.session_state["learner"] = learner
                st.session_state["session_token"] = s
                return


def learner_nav():
    cols = st.columns([0.16, 0.16, 0.16, 0.2, 0.32])
    if cols[0].button("Dashboard", key="nav_dash"):
        st.session_state["view"] = "dashboard"; st.rerun()
    if cols[1].button("Foundation", key="nav_f"):
        st.session_state.update(view="track", track="FOUNDATION"); st.rerun()
    if cols[2].button("Practitioner", key="nav_p"):
        st.session_state.update(view="track", track="PRACTITIONER"); st.rerun()
    if cols[3].button("Practice Record", key="nav_pr"):
        st.session_state["view"] = "record"; st.rerun()
    if cols[4].button("Admin Login", key="nav_admin"):
        st.session_state["view"] = "admin"; st.rerun()


def render_gate():
    styling.top_bar("Better Repairs Programme · PRINCE2 practice")
    styling.fictional_notice()
    st.markdown("## Open from your LMS")
    st.write("The Decision Lab signs you in automatically through your learning platform. "
             "There is no separate learner login.")
    if st.session_state.get("launch_error"):
        st.error(st.session_state["launch_error"])

    if config.ALLOW_EMAIL_IDENTITY:
        _email_fallback_form()

    if config.DEV_MODE:
        st.markdown("---")
        st.info("Development mode — launch as a sample learner (this simulates an LMS launch).")
        labels = {f'{s["display_name"]} ({s["email"]})': s for s in SAMPLE_LEARNERS}
        choice = st.selectbox("Sample learner", list(labels.keys()))
        if st.button("Launch as this learner", type="primary"):
            _login_learner(upsert_learner(labels[choice]))
            st.rerun()

    st.markdown("---")
    if st.button("Admin Login", key="gate_admin"):
        st.session_state["view"] = "admin"; st.rerun()


def _email_fallback_form():
    """First-visit email entry used ONLY when the LMS did not provide a verified identity.
    The email is self-declared and clearly marked unverified; identity is then carried by the
    signed session token, never by an editable field."""
    st.markdown("---")
    st.markdown("### Continue with your email")
    st.caption("If you weren't automatically signed in by your learning platform, enter your email "
               "so we can save and restore your progress.")
    st.warning("This email is **self-declared and unverified** — it simply lets you keep your own "
               "progress on this device. It is not a secure proof of identity.")
    with st.form("email_identity"):
        email = st.text_input("Your email address")
        submit = st.form_submit_button("Continue", type="primary")
    if submit:
        try:
            if config.REQUIRE_EMAIL_VERIFICATION:
                code = email_identity.send_login_code(email)
                st.session_state["pending_email"] = email_identity.normalize_email(email)
                msg = "We've sent you a one-time code. Enter it below to continue."
                if code:  # DEV only: surface the code so you can test without a mail provider
                    msg += f"  (dev code: {code})"
                st.info(msg)
            else:
                learner = email_identity.claim_identity(email, verified=False)
                _login_learner(learner)
                st.rerun()
        except ValueError as e:
            st.error(str(e))

    if config.REQUIRE_EMAIL_VERIFICATION and st.session_state.get("pending_email"):
        with st.form("email_verify"):
            code_in = st.text_input("One-time code")
            verify = st.form_submit_button("Verify & continue", type="primary")
        if verify:
            pe = st.session_state["pending_email"]
            if email_identity.verify_login_code(pe, code_in):
                learner = email_identity.claim_identity(pe, verified=True)
                st.session_state.pop("pending_email", None)
                _login_learner(learner)
                st.rerun()
            else:
                st.error("That code is invalid or has expired. Please try again.")


def main():
    view = st.session_state.get("view", "dashboard")

    # Admin area is reachable regardless of learner identity.
    if view in ("admin",):
        if admin_panel.is_admin():
            admin_panel.render_panel()
        else:
            admin_panel.render_login()
        return

    resolve_identity()

    if not st.session_state.get("learner"):
        render_gate()
        return

    # handle a deep-linked mission once
    if st.session_state.get("deeplink"):
        code = st.session_state.pop("deeplink")
        st.session_state.update(view="activity", act_code=code, track="FOUNDATION")
        view = "activity"

    if view == "mission":
        mission_player.render()
        return
    if view == "h5p":
        h5p_player.render()
        return
    if view == "launch":
        activity_launcher.render()
        return

    learner_nav()
    if view == "track":
        portal.render_track(st.session_state.get("track", "FOUNDATION"))
    elif view == "activity":
        portal.render_activity()
    elif view == "record":
        practice_record.render()
    else:
        portal.render_dashboard()


main()
