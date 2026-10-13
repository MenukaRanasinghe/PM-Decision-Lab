"""Mission register, episodes, tracks, consequence echoes and tags.
Port of the Node registry.js + tracks.js. Single source of truth for metadata.
"""

EPISODES = [
    {"id": "A", "title": "Make it a project", "range": ("I01", "I05")},
    {"id": "B", "title": "Establish control", "range": ("I06", "I10")},
    {"id": "C", "title": "Deliver within authority", "range": ("I11", "I13")},
    {"id": "D", "title": "Recover and decide", "range": ("I14", "I15")},
    {"id": "E", "title": "Close and show", "range": ("I16",)},
]

MISSIONS = {
    "I01": {"episode": "A", "title": "Mandate lacks measurable outcomes", "max_score": 2},
    "I02": {"episode": "A", "title": "A previous resident portal failed", "max_score": 2},
    "I03": {"episode": "A", "title": "Create the Project Board", "max_score": 2},
    "I04": {"episode": "A", "title": "Choose an investment option", "max_score": 2},
    "I05": {"episode": "A", "title": "Define the project product", "max_score": 2},
    "I06": {"episode": "B", "title": "Authorise initiation", "max_score": 2},
    "I07": {"episode": "B", "title": "Tailor the PID", "max_score": 2},
    "I08": {"episode": "B", "title": "Create the product-based plan", "max_score": 2},
    "I09": {"episode": "B", "title": "Set accessibility acceptance", "max_score": 2},
    "I10": {"episode": "B", "title": "Data-migration / interface risk", "max_score": 2},
    "I11": {"episode": "C", "title": "Authorise a Work Package", "max_score": 2},
    "I12": {"episode": "C", "title": "Executive requests an AI chatbot", "max_score": 2},
    "I13": {"episode": "C", "title": "A product will miss specification", "max_score": 2},
    "I14": {"episode": "D", "title": "Forecast exceeds stage tolerance", "max_score": 2},
    "I15": {"episode": "D", "title": "Approaching the stage boundary", "max_score": 2},
    "I16": {"episode": "E", "title": "Close and hand over", "max_score": 2},
}
MISSION_IDS = list(MISSIONS.keys())
TOTAL_MISSIONS = len(MISSION_IDS)
TOTAL_POINTS = sum(m["max_score"] for m in MISSIONS.values())  # 32

REGISTER = [
    {"id": "I01", "ep": "A", "task": "Identify missing evidence; decide project vs business-as-usual."},
    {"id": "I02", "ep": "A", "task": "Select useful lessons and co-creation actions."},
    {"id": "I03", "ep": "A", "task": "Match business, user and supplier interests; spot an assurance conflict."},
    {"id": "I04", "ep": "A", "task": "Compare do-nothing, minimum and ambitious options."},
    {"id": "I05", "ep": "A", "task": "Classify product / outcome / benefit; choose acceptance criteria."},
    {"id": "I06", "ep": "B", "task": "Select what the Board is authorising — and what it is not."},
    {"id": "I07", "ep": "B", "task": "Choose proportionate tailoring that retains purpose and control."},
    {"id": "I08", "ep": "B", "task": "Choose product flow, dependencies and Work Package boundary."},
    {"id": "I09", "ep": "B", "task": "Distinguish Project Product Description from Product Descriptions."},
    {"id": "I10", "ep": "B", "task": "Build cause–event–effect; distinguish risk and action owners."},
    {"id": "I11", "ep": "C", "task": "Sequence authorise, accept, execute, evaluate and notify completion."},
    {"id": "I12", "ep": "C", "task": "Classify and assess a request for change; apply decision authority."},
    {"id": "I13", "ep": "C", "task": "Classify off-specification; choose correction or concession route."},
    {"id": "I14", "ep": "D", "task": "Issue Report → Exception Report → Board direction → Plan if asked."},
    {"id": "I15", "ep": "D", "task": "Select updates; recommend continue / change / stop."},
    {"id": "I16", "ep": "E", "task": "Acceptance, handover, residuals, lessons and future benefits review."},
]
TASK_BY_ID = {r["id"]: r["task"] for r in REGISTER}

# ── Tracks (the two Level values with display metadata). NOT a table. ──────────
TRACKS = {
    "FOUNDATION": {"code": "FOUNDATION", "name": "PRINCE2 Foundation", "mode": "Guided Practice"},
    "PRACTITIONER": {"code": "PRACTITIONER", "name": "PRINCE2 Practitioner", "mode": "Applied Judgement"},
}
TRACK_CODES = list(TRACKS.keys())


def can_access_track(learner, track_code):
    """MVP: every authenticated learner may open both tracks. Swap this body for an LMS
    enrollment check later — nothing else changes."""
    return True


# ── Consequence echoes (the five guide-sanctioned links) ──────────────────────
ECHOES = {
    "I05": {"from": "I02", "text": "Because you captured the failed-portal lessons in I02, the product definition here must show how co-creation and accessibility were designed in from the start."},
    "I09": {"from": "I05", "text": "The acceptance criteria you set when defining the project product in I05 now drive what “accessible” must mean in the Product Descriptions."},
    "I12": {"from": "I09", "text": "The accessibility acceptance you locked in I09 is exactly what a bolt-on chatbot would put at risk — weigh that in the change impact."},
    "I14": {"from": "I12", "text": "The change you routed in I12 is part of why the stage forecast now moves. How you handled that request shapes the exception you face here."},
    "I15": {"from": "I14", "text": "The Board direction you obtained after the I14 exception sets the baseline you are now measuring against at the stage boundary."},
}

TAGS = {
    "authority-level": "Confuses seniority or accountability with decision authority",
    "impact-scope": "Assesses too narrow a set of impacts",
    "evidence-selection": "Decides before gathering the decisive evidence",
    "tolerance": "Acts outside the delegated tolerance / self-authorises",
    "risk-vs-issue": "Confuses a risk with an issue that has already occurred",
    "quality": "Overlooks quality or acceptance criteria",
    "acceptance": "Weak use of acceptance criteria",
    "change-control": "Does not follow change control",
    "planning": "Planning or dependency error",
    "issue-vs-exception": "Mishandles routine issue vs exception escalation",
    "stage-boundary": "Defers a decision the stage cannot wait for",
    "closure": "Incomplete closure or handover",
}

_DESCRIPTIONS = {
    "I12": "A sponsor wants an AI chatbot added mid-build. Classify the request for change and apply decision authority.",
    "I14": "Delay and change push the stage past tolerance. Escalate correctly through exception management.",
}

# Which missions have fully-authored native content (both levels)
PLAYABLE = {"I12", "I14"}


def episode_of(mission_id):
    return MISSIONS.get(mission_id, {}).get("episode")


def echo_for(mission_id):
    return ECHOES.get(mission_id)


def activity_catalog():
    """Rows to seed into the Activity table for BOTH tracks (python attribute keys)."""
    rows = []
    for code in MISSION_IDS:
        meta = MISSIONS[code]
        available = code in PLAYABLE
        for track in TRACK_CODES:
            rows.append({
                "code": code,
                "track": track,
                "title": meta["title"],
                "description": _DESCRIPTIONS.get(code, meta["title"]),
                "est_minutes": "10–12",
                "kind": "NATIVE",
                "available": available,
                "order_index": MISSION_IDS.index(code),
            })
    return rows
