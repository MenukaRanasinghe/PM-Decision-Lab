"""I12 — Executive requests an AI chatbot. Content port of I12.js (both levels).
Option codes match content/scoring.py KEYS['I12']. Content only; scoring is authoritative server-side.
"""

ISSUE_TYPES = [
    "Problem / concern",
    "Business opportunity",
    "Request for change",
    "Off-specification",
    "Event external to the project",
]

MISSION = {
    "id": "I12",
    "title": "Executive requests an AI chatbot",
    "est_minutes": "10–12",
    "method_ref": "Foundation M11 — Issues & Change",
    "FOUNDATION": {
        "steps": [
            {
                "type": "brief", "label": "Brief",
                "eyebrow": "Episode C · Deliver within authority",
                "title": "The Executive wants an AI chatbot — now",
                "body": "You are the <b>Project Manager</b>. Stage 2 is authorised and the approved baseline does not include an AI chatbot. This should take 10–12 minutes.",
                "docs": [
                    {"kind": "email", "head": {"label": "Email · priority"},
                     "rows": [["From", "D. Castellan, Executive (Senior Responsible Owner)"], ["To", "You — Project Manager, Better Repairs Programme"]],
                     "subject": "Add an AI chatbot while the portal is being built",
                     "body": "“The supplier is already in the code for the resident portal. Let’s get them to bolt on an AI chatbot for repair queries while they’re at it — residents will love it and it’ll save the call centre. I’ll square it with finance. Can you get them moving this week?”"},
                    {"head": {"label": "Stage status"},
                     "html": "Stage 2 (Build the resident service) is <b>authorised and in progress</b>. The approved baseline covers “Report and track a repair” only. A chatbot is not in scope."},
                ],
                "cta": "Inspect the evidence",
            },
            {
                "type": "evidence", "label": "Evidence", "eyebrow": "Evidence",
                "title": "What the controls say",
                "body": "A Foundation brief highlights what you need. Notice the authority limits before you decide.",
                "docs": [
                    {"head": {"label": "Issue Management Approach — extract"},
                     "html": "Any proposed change to an approved baseline is a <b>request for change</b>. It must be <b>captured and assessed for impact</b>, then routed to the delegated <b>Change Authority</b> within its agreed limits."},
                    {"head": {"label": "Impact surface"},
                     "html": "A chatbot could affect <b>cost, schedule, privacy &amp; security, accessibility acceptance, support load</b> and the expected <b>benefits</b>. None of this is yet assessed."},
                    {"head": {"label": "Tolerance card"},
                     "html": "Change budget remaining: <b>partly committed</b> · Delegated Change Authority: <b>exists, with a stated limit</b> · Impact analysis done? <b>No</b>"},
                ],
                "cta": "Make the decision",
            },
            {
                "type": "decide", "label": "Decide", "eyebrow": "Decision",
                "title": "What should the Project Manager do next?",
                "options": [
                    {"code": "A", "text": "Record it as a request for change, assess its impacts, and submit it to the decision authority defined in the Issue Management Approach."},
                    {"code": "B", "text": "Ask the supplier for a quick estimate and decide after checking whether it fits the stage budget."},
                    {"code": "C", "text": "Start the chatbot work because the Executive is the business authority and asked directly."},
                ],
                "consequence": {
                    "A": {"tone": "good", "title": "Consequence",
                          "html": "You log the request, kick off a proportionate impact assessment and route it to the Change Authority. The baseline stays protected, the Board keeps control, and the Executive gets a decision they can defend.",
                          "continue": "Continue to issue triage"},
                    "B": {"tone": "warn", "title": "Consequence",
                          "html": "Analysis starts, but a supplier estimate is not an impact assessment and “fits the budget” is not the authority test. You’ve skipped the change route and the delegated decision-maker. The issue is half-handled."},
                    "C": {"tone": "bad", "title": "Red-line consequence",
                          "html": "This choice commits unapproved work before impact and decision authority are confirmed. The team begins building, the baseline and acceptance criteria become unreliable, and stage control weakens. That is a red-line error — complete the repair before continuing."},
                },
            },
            {
                "type": "repair", "label": "Repair", "eyebrow": "Repair · new surface data",
                "title": "A fresh request lands",
                "body": "Different request, same rule. The Executive now asks you to <b>add SMS notifications</b> to the portal “since we’re changing things anyway.” Apply the correct route.",
                "options": [
                    {"code": "A", "text": "Record it as a request for change, assess impacts, and route it to the Change Authority within its limits."},
                    {"code": "B", "text": "Add it to the supplier’s current sprint — it’s only a small notification feature."},
                    {"code": "C", "text": "Approve it yourself to save the Board’s time."},
                ],
                "feedback": {
                    "ok": {"title": "Repaired", "html": "Correct. Any change to an approved baseline — large or small — is captured, assessed and routed by delegated authority. You’ve shown you can apply the rule, not just recall it."},
                    "bad": {"title": "Still off-method", "html": "Size doesn’t change the route. A baseline change needs capture, impact assessment and the delegated decision-maker. Revisit the Issue Management Approach before the next mission."},
                },
                "continue": "Continue to issue triage",
            },
            {
                "type": "triage", "label": "Triage", "eyebrow": "Supporting task",
                "title": "Classify the five issue types",
                "body": "Every PRINCE2 issue is one of five types. Tag each micro-case, then grade.",
                "types": ISSUE_TYPES,
                "cases": [
                    {"case": "Residents report that the repair-status wording is confusing.", "ans": "Problem / concern", "fb": "A concern requiring capture and analysis."},
                    {"case": "A new grant could fund multilingual notifications.", "ans": "Business opportunity", "fb": "An opportunity that may improve value."},
                    {"case": "The Executive asks for an AI chatbot.", "ans": "Request for change", "fb": "A proposed change to an approved baseline."},
                    {"case": "The supplier says the agreed page-load target cannot be met.", "ans": "Off-specification", "fb": "A product forecast not to meet its specification."},
                    {"case": "New national cyber guidance is issued during delivery.", "ans": "Event external to the project", "fb": "An external event with project impact."},
                ],
                "continue": "See the method debrief",
            },
            {
                "type": "method", "label": "Method", "eyebrow": "Method debrief",
                "title": "Why this is a request for change",
                "panels": [
                    "The chatbot proposes a change to an approved baseline, so it is a <b>request for change</b> — one of the five PRINCE2 issue types. The Project Manager <b>records and assesses</b> the issue, considers impacts across the whole project, and <b>routes the decision</b> according to delegated authority and tolerances.",
                    "Being the Executive makes someone the business authority on the Project Board — it does <b>not</b> make impact analysis optional, and it does not turn a sponsor’s email into approved work. Update the Issue Register and report through the agreed route.",
                ],
                "missed": "Issue Management Approach extract — the line delegating change decisions to the <b>Change Authority</b> within set limits.",
                "cta": "See your record",
            },
        ],
    },
    "PRACTITIONER": {
        "steps": [
            {
                "type": "brief", "label": "Brief",
                "eyebrow": "Episode C · Deliver within authority · Applied judgement",
                "title": "A sponsor request, and a pile of mixed evidence",
                "body": "Same canonical case: Stage 2 is authorised, no chatbot in the baseline, the Executive wants it added. This time nothing is highlighted. Read the pack, decide what matters, then act.",
                "docs": [
                    {"kind": "email", "head": {"label": "Email"}, "rows": [["From", "D. Castellan, Executive"]],
                     "subject": "AI chatbot — let’s do it now",
                     "body": "“Supplier’s already building the portal. Add an AI repair chatbot while they’re in there. I own the Business Case, so treat this as approved — just get it moving.”"},
                ],
                "cta": "Open the evidence pack",
            },
            {
                "type": "evidenceSelect", "label": "Select evidence", "eyebrow": "Step 1 · Evidence selection",
                "title": "Which evidence do you need before deciding?",
                "body": "Pick the four items that actually bear on the change decision. One or two are plausible distractors.",
                "need": 4,
                "items": [
                    {"t": "Issue Management Approach — delegated Change Authority limit", "d": "Change decisions above a set value escalate to the Board.", "good": True},
                    {"t": "Accessibility acceptance criterion for the resident service", "d": "A conversational UI creates new WCAG obligations.", "good": True},
                    {"t": "Data-protection note on conversational logging", "d": "Chatbot transcripts may capture personal data.", "good": True},
                    {"t": "Remaining stage tolerance", "d": "How much room exists before escalation is forced.", "good": True},
                    {"t": "Supplier’s framework day-rate card", "d": "Standard commercial rates — background only.", "good": False},
                    {"t": "Resident satisfaction survey from last year", "d": "Interesting context, not decisive for this change.", "good": False},
                ],
                "continue": "Classify the issue",
            },
            {
                "type": "classify", "label": "Classify", "eyebrow": "Step 2 · Classify",
                "title": "What type of issue is this?",
                "options": [
                    {"key": "problem-concern", "label": "Problem / concern"},
                    {"key": "business-opportunity", "label": "Business opportunity"},
                    {"key": "request-for-change", "label": "Request for change"},
                    {"key": "off-specification", "label": "Off-specification"},
                    {"key": "external-event", "label": "Event external to the project"},
                ],
                "feedback": {
                    "ok": "Correct — it proposes a change to an approved baseline, so it is a request for change, not an off-specification or a mere concern.",
                    "bad": "Not quite. It proposes adding something new to an approved baseline — that is a <b>request for change</b>. Off-specification is a product forecast to miss spec; a concern wouldn’t alter the baseline.",
                },
                "continue": "Choose the action",
            },
            {
                "type": "decide", "label": "Decide", "eyebrow": "Step 3 · Action",
                "title": "Choose the next action",
                "body": "Four plausible routes. Only one protects the baseline and respects delegated authority.",
                "options": [
                    {"code": "A", "text": "Accept because the Executive owns the Business Case, then document the change retrospectively."},
                    {"code": "B", "text": "Reject because any post-authorisation change must wait until the next stage."},
                    {"code": "C", "text": "Record and assess the request, then decide or escalate using the defined Change Authority and relevant tolerance."},
                    {"code": "D", "text": "Ask the supplier only for cost and schedule impact, then use remaining stage tolerance to decide."},
                ],
                "consequence": {
                    "A": {"tone": "bad", "title": "Consequence", "html": "Red-line: this confuses business accountability with change authority and process. The request is treated as approved before any impact is known, and “documenting it later” cannot restore the control you have already given up."},
                    "B": {"tone": "warn", "title": "Consequence", "html": "Over-control: this ignores the delegated in-stage decision route that exists for exactly this. A legitimate change is blocked for no methodological reason, and the sponsor is given no real answer."},
                    "C": {"tone": "good", "title": "Consequence", "html": "The request is logged and impact-assessed; the Change Authority decides within tolerance. Control holds, impacts across cost, quality, risk and benefits are visible, and the sponsor still gets a timely answer.", "continue": "Method debrief"},
                    "D": {"tone": "warn", "title": "Consequence", "html": "Incomplete: a cost-and-schedule estimate hides the quality, privacy, accessibility and benefit impacts that make this decision real. Tolerance alone is not the authority test."},
                },
            },
            {
                "type": "repair", "label": "Repair", "eyebrow": "Repair · transfer task",
                "title": "A different change, a different limit",
                "body": "New request: add <b>predictive appointment scheduling</b> to the portal. It carries a <b>different delegated limit</b> and a <b>different quality impact</b> (it touches the appointment-booking acceptance criteria). What is the correct route?",
                "options": [
                    {"code": "A", "text": "Capture and assess the request, then decide or escalate via the Change Authority using the limit and tolerance that apply to this change."},
                    {"code": "B", "text": "Treat it like the chatbot and reuse that decision — same project, same answer."},
                    {"code": "C", "text": "Push it to the next stage boundary so it doesn’t disturb the current plan."},
                ],
                "feedback": {
                    "ok": {"title": "Repaired", "html": "Right. The rule transfers: each change is assessed on its own impacts and routed by the limit that applies to it — you can’t recycle a previous decision or park a change to dodge the route."},
                    "bad": {"title": "Still off-method", "html": "Each change stands on its own impacts and authority limit. Reusing a prior decision or deferring to the boundary both skip the assessment this change needs."},
                },
                "continue": "Method debrief",
            },
            {
                "type": "method", "label": "Method", "eyebrow": "Debrief",
                "title": "Business accountability is not change authority",
                "panels": [
                    "The Executive owns the Business Case, but that is accountability for <b>why</b> the project runs — not a licence to approve changes to an approved baseline outside the agreed route. A request for change is captured, assessed across cost, schedule, quality, risk, benefits and accessibility, then <b>decided or escalated</b> through the delegated Change Authority against the relevant tolerance.",
                    "Rejecting outright (B) over-controls and wastes a legitimate in-stage route; a cost-only estimate (D) hides the quality, privacy and benefit impacts that make this decision real.",
                ],
                "cta": "See your record",
            },
        ],
    },
    "related": [
        {"id": "I14", "why": "Your I12 change route feeds the forecast exception here."},
        {"id": "I13", "why": "Off-specification vs request for change — the sibling decision."},
        {"id": "I11", "why": "Authorise a Work Package: where delegated authority begins."},
    ],
}
