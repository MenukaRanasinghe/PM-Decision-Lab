"""Authoritative answer keys + attempt rollup. Port of keys.js + scoring.js.

Scoring is server-side only: the UI sends an option key; this module decides score, tag,
red-line and correctness. Each mission is out of 2 (2 aligned, 1 repaired, 0 unresolved);
a correct repair lifts a 0 to at most 1; practice steps never change the /2.
"""
from content.registry import MISSIONS

KEYS = {
    "I12": {
        "FOUNDATION": {
            "decide": {
                "A": {"score": 2},
                "B": {"score": 0, "tag": "authority-level", "repairable": True},
                "C": {"score": 0, "tag": "authority-level", "red": True, "repairable": True},
            },
            "repair": {"A": {"correct": True}, "B": {"correct": False}, "C": {"correct": False}},
            "triage": {"practice": True},
        },
        "PRACTITIONER": {
            "evidence": {"practice": True},
            "classify": {
                "request-for-change": {"correct": True},
                "off-specification": {"correct": False},
                "problem-concern": {"correct": False},
                "business-opportunity": {"correct": False},
                "external-event": {"correct": False},
            },
            "decide": {
                "A": {"score": 0, "tag": "authority-level", "red": True, "repairable": True},
                "B": {"score": 0, "tag": "issue-vs-exception", "repairable": True},
                "C": {"score": 2},
                "D": {"score": 0, "tag": "impact-scope", "repairable": True},
            },
            "repair": {"A": {"correct": True}, "B": {"correct": False}, "C": {"correct": False}},
        },
    },
    "I14": {
        "FOUNDATION": {
            "decide": {
                "A": {"score": 2},
                "B": {"score": 0, "tag": "tolerance", "red": True, "repairable": True},
                "C": {"score": 0, "tag": "stage-boundary", "repairable": True},
            },
            "repair": {"A": {"correct": True}, "B": {"correct": False}, "C": {"correct": False}},
            "order": {"practice": True},
        },
        "PRACTITIONER": {
            "evidence": {"practice": True},
            "classify": {
                "exception": {"correct": True},
                "routine-issue": {"correct": False},
                "risk": {"correct": False},
            },
            "decide": {
                "A": {"score": 2},
                "B": {"score": 0, "tag": "tolerance", "red": True, "repairable": True},
                "C": {"score": 0, "tag": "issue-vs-exception", "repairable": True},
                "D": {"score": 0, "tag": "stage-boundary", "repairable": True},
            },
            "repair": {"A": {"correct": True}, "B": {"correct": False}, "C": {"correct": False}},
        },
    },
}

PLAYABLE = set(KEYS.keys())


def option_key(mission_id, level, step, option):
    step_key = KEYS.get(mission_id, {}).get(level, {}).get(step)
    if step_key is None:
        return None
    if step_key.get("practice"):
        return {"practice": True}
    return step_key.get(option)


def resolve_event(mission_id, level, step, selected_option):
    """Resolve one event's authoritative outcome. Returns a dict the caller persists."""
    base = str(selected_option).split(":")[0]
    key = option_key(mission_id, level, step, base)
    out = {"score_change": 0, "feedback_tag": None, "red_line": False, "is_correct": None}
    if key is None:
        return out
    if key.get("practice"):
        return out
    if isinstance(key.get("score"), int):
        out["score_change"] = key["score"]
    if isinstance(key.get("correct"), bool):
        out["is_correct"] = key["correct"]
    out["feedback_tag"] = key.get("tag")
    out["red_line"] = bool(key.get("red"))
    return out


def roll_up(mission_id, events):
    """Derive the /2 result from an attempt's events. `events` is a list of objects/dicts with
    .step, .score_change, .red_line, .is_correct, .feedback_tag, .route_code (or dict keys)."""
    max_score = MISSIONS.get(mission_id, {}).get("max_score", 2)

    def g(e, name):
        return getattr(e, name) if not isinstance(e, dict) else e.get(name)

    decide = None
    repair = None
    for e in events:
        if g(e, "step") == "decide":
            decide = e
        if g(e, "step") == "repair":
            repair = e

    score = 0
    first_time_aligned = False
    repaired = False
    red_line_hit = False
    route_code = None
    tags = []

    if decide is not None:
        sc = g(decide, "score_change") or 0
        score = max(0, min(sc, max_score))
        route_code = g(decide, "route_code") or f"{mission_id}-{g(decide, 'selected_option')}"
        if g(decide, "feedback_tag"):
            tags.append(g(decide, "feedback_tag"))
        if sc >= max_score:
            first_time_aligned = True
        if g(decide, "red_line"):
            red_line_hit = True

    if repair is not None and (decide is None or (g(decide, "score_change") or 0) < max_score):
        repaired = True
        if g(repair, "is_correct"):
            score = max(score, 1)

    for e in events:
        t = g(e, "feedback_tag")
        if t and t not in tags:
            tags.append(t)

    return {
        "score": score,
        "max_score": max_score,
        "first_time_aligned": first_time_aligned,
        "repaired": repaired,
        "red_line_hit": red_line_hit,
        "route_code": route_code,
        "feedback_tags": tags,
    }
