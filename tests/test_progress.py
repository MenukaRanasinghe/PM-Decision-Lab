from auth.learner_identity import upsert_learner
from services import progress_service as P


def _mk(sub):
    return upsert_learner({"issuer": "dev://local", "external_learner_id": sub,
                           "display_name": sub, "email": f"{sub}@x"})


def test_full_foundation_red_then_repair():
    a = _mk("P-A")
    st = P.start_attempt(a["id"], "I12", "FOUNDATION")
    aid = st["attempt_id"]
    P.record_event(a["id"], aid, "I12", "FOUNDATION", "decide", "C")
    P.record_event(a["id"], aid, "I12", "FOUNDATION", "repair", "A")
    P.record_event(a["id"], aid, "I12", "FOUNDATION", "triage", "5/5")
    res = P.complete_attempt(a["id"], aid, "I12", "FOUNDATION")
    at = res["attempt"]
    assert at["score"] == 1 and at["repaired"] and at["red_line_hit"]
    assert at["feedback_tags"] == ["authority-level"]


def test_practitioner_aligned_and_totals():
    a = _mk("P-B")
    st = P.start_attempt(a["id"], "I12", "PRACTITIONER")
    aid = st["attempt_id"]
    P.record_event(a["id"], aid, "I12", "PRACTITIONER", "evidence", "4/4")
    r = P.record_event(a["id"], aid, "I12", "PRACTITIONER", "classify", "request-for-change")
    assert r["correct"] is True
    P.record_event(a["id"], aid, "I12", "PRACTITIONER", "decide", "C")
    res = P.complete_attempt(a["id"], aid, "I12", "PRACTITIONER")
    assert res["attempt"]["score"] == 2 and res["attempt"]["first_time_aligned"]


def test_learner_isolation():
    a = _mk("P-ISO-A")
    b = _mk("P-ISO-B")
    st = P.start_attempt(a["id"], "I14", "FOUNDATION")
    P.record_event(a["id"], st["attempt_id"], "I14", "FOUNDATION", "decide", "A")
    P.complete_attempt(a["id"], st["attempt_id"], "I14", "FOUNDATION")
    tp_b = P.track_progress(b["id"])
    assert tp_b["FOUNDATION"]["completed"] == 0
    tp_a = P.track_progress(a["id"])
    assert tp_a["FOUNDATION"]["completed"] >= 1


def test_resume_in_progress_not_completed():
    a = _mk("P-RES")
    st = P.start_attempt(a["id"], "I14", "PRACTITIONER")
    P.record_event(a["id"], st["attempt_id"], "I14", "PRACTITIONER", "evidence", "4/4")
    # reopen without completing -> same attempt resumed
    st2 = P.start_attempt(a["id"], "I14", "PRACTITIONER")
    assert st2["resumed"] is True and st2["attempt_id"] == st["attempt_id"]
    det = P.activity_detail(a["id"], "I14", "PRACTITIONER")
    assert det["best"]["status"] == "IN_PROGRESS"


def test_echo_integrated_after_source_completed():
    a = _mk("P-ECHO")
    # complete I12 (source of the I14 echo)
    st = P.start_attempt(a["id"], "I12", "FOUNDATION")
    P.record_event(a["id"], st["attempt_id"], "I12", "FOUNDATION", "decide", "A")
    P.complete_attempt(a["id"], st["attempt_id"], "I12", "FOUNDATION")
    st2 = P.start_attempt(a["id"], "I14", "FOUNDATION")
    assert st2["echo"] and st2["echo"]["from"] == "I12" and st2["echo"]["integrated"] is True
