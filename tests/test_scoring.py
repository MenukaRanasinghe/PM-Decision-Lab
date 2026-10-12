from content.scoring import resolve_event, roll_up


def ev(step, opt, sc, red=False, correct=None, tag=None):
    return {"step": step, "selected_option": opt, "score_change": sc, "red_line": red,
            "is_correct": correct, "feedback_tag": tag, "route_code": f"I12-{opt}" if step == "decide" else None}


def test_resolve_aligned():
    r = resolve_event("I12", "FOUNDATION", "decide", "A")
    assert r["score_change"] == 2 and not r["red_line"] and r["feedback_tag"] is None


def test_resolve_red_line():
    r = resolve_event("I12", "FOUNDATION", "decide", "C")
    assert r["score_change"] == 0 and r["red_line"] and r["feedback_tag"] == "authority-level"


def test_practice_step_scores_zero():
    r = resolve_event("I12", "FOUNDATION", "triage", "4/5")
    assert r["score_change"] == 0 and r["is_correct"] is None


def test_rollup_aligned_first_time():
    r = roll_up("I12", [ev("decide", "A", 2)])
    assert r["score"] == 2 and r["first_time_aligned"] and not r["repaired"]


def test_rollup_red_then_repair():
    r = roll_up("I12", [ev("decide", "C", 0, red=True, tag="authority-level"), ev("repair", "A", 0, correct=True)])
    assert r["score"] == 1 and r["repaired"] and r["red_line_hit"]
    assert r["feedback_tags"] == ["authority-level"]


def test_rollup_failed_repair_stays_zero():
    r = roll_up("I12", [ev("decide", "C", 0, red=True), ev("repair", "B", 0, correct=False)])
    assert r["score"] == 0 and r["repaired"]


def test_i14_tolerance_red_line():
    r = resolve_event("I14", "FOUNDATION", "decide", "B")
    assert r["red_line"] and r["feedback_tag"] == "tolerance"
