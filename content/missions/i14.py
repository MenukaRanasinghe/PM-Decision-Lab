"""I14 — Forecast exceeds stage tolerance. Content port of I14.js (both levels).
Option codes match content/scoring.py KEYS['I14'].
"""

MISSION = {
    "id": "I14",
    "title": "Forecast exceeds stage tolerance",
    "est_minutes": "10–12",
    "method_ref": "Foundation M8/M10/M14 — Progress, Plans & Tolerances",
    "FOUNDATION": {
        "steps": [
            {
                "type": "brief", "label": "Brief", "eyebrow": "Episode D · Recover and decide",
                "title": "The stage will overrun what you are allowed to absorb",
                "body": "You are the <b>Project Manager</b> in Stage 2. The supplier has slipped and the change work agreed earlier has added effort. Your latest forecast now pushes the stage past its agreed tolerance.",
                "docs": [
                    {"head": {"label": "Checkpoint Report — trend"},
                     "html": "Three consecutive Checkpoint Reports show the migration task sliding: +1 week, then +2, now +4 weeks against plan. Cost forecast is tracking the same way."},
                    {"head": {"label": "Stage tolerance card"},
                     "html": "Time tolerance: <b>± 2 weeks</b> · Cost tolerance: <b>± £15,000</b> · Current forecast: <b>+4 weeks · +£28,000</b> · Within tolerance? <b>No — forecast breach</b>"},
                ],
                "cta": "Inspect the evidence",
            },
            {
                "type": "evidence", "label": "Evidence", "eyebrow": "Evidence",
                "title": "What your authority allows",
                "body": "A forecast to breach tolerance is the trigger for exception management. Read what you may and may not do.",
                "docs": [
                    {"head": {"label": "Controls extract — tolerance & escalation"},
                     "html": "Tolerance is the Project Manager’s delegated room to manage the stage <b>without</b> going back to the Board. A forecast to exceed it must be <b>escalated</b>: the Project Manager raises the issue and produces an <b>Exception Report</b>; the <b>Project Board</b> decides what happens next. The PM does not self-authorise more time or money."},
                    {"head": {"label": "What the Board can direct"},
                     "html": "The Board may ask for an <b>Exception Plan</b> to replace the rest of the stage, change the project, or stop it (premature close). The Board — not the Project Manager — chooses."},
                ],
                "cta": "Make the decision",
            },
            {
                "type": "decide", "label": "Decide", "eyebrow": "Decision",
                "title": "What should the Project Manager do?",
                "options": [
                    {"code": "A", "text": "Capture the forecast breach as an issue, produce an Exception Report setting out the situation, options and your recommendation, and escalate to the Project Board for a direction."},
                    {"code": "B", "text": "Approve the extra time and budget yourself and push on — you are nearly there."},
                    {"code": "C", "text": "Note it and raise it at the next stage boundary in the End Stage Report."},
                ],
                "consequence": {
                    "A": {"tone": "good", "title": "Consequence", "html": "You escalate honestly and early. The Board has real options and a recommendation, decides with full visibility, and can commission an Exception Plan if it wants the stage to continue on a new baseline. Control is preserved.", "continue": "Continue to the exception sequence"},
                    "B": {"tone": "bad", "title": "Red-line consequence", "html": "You have spent authority you do not hold. Approving beyond tolerance without the Board is a governance breach: the baseline is now fictional, the Board is blind to a decision that was theirs to make, and assurance is undermined. Complete the repair."},
                    "C": {"tone": "warn", "title": "Consequence", "html": "Waiting for the boundary is too late. A forecast breach needs escalation now, while the Board still has options. By the boundary the overspend is a fact, not a decision — you have turned a choice into a report."},
                },
            },
            {
                "type": "repair", "label": "Repair", "eyebrow": "Repair · new surface data",
                "title": "A time-only breach this time",
                "body": "Different numbers, same rule. Cost is fine, but the supplier now forecasts <b>+3 weeks</b> against a <b>± 1 week</b> time tolerance. What do you do?",
                "options": [
                    {"code": "A", "text": "Raise the forecast breach and produce an Exception Report for the Project Board to direct."},
                    {"code": "B", "text": "Quietly re-plan the remaining work to try to claw the time back before anyone notices."},
                    {"code": "C", "text": "Carry on and report the slippage at the stage boundary."},
                ],
                "feedback": {
                    "ok": {"title": "Repaired", "html": "Correct. Breaching <b>any</b> dimension of tolerance — time, cost, scope, quality, risk or benefit — triggers the same exception route: raise it, produce an Exception Report, let the Board direct."},
                    "bad": {"title": "Still off-method", "html": "Re-planning in secret or deferring to the boundary both keep a decision from the people who own it. A forecast tolerance breach is escalated through an Exception Report, not absorbed quietly."},
                },
                "continue": "Continue to the exception sequence",
            },
            {
                "type": "order", "label": "Sequence", "eyebrow": "Supporting task",
                "title": "Put the exception steps in order",
                "body": "Use the controls to order the exception sequence correctly, then grade.",
                "items": [
                    "Project Manager captures the forecast breach (raises an issue / Issue Report)",
                    "Project Manager produces an Exception Report",
                    "Project Board considers it and gives a direction",
                    "Project Manager produces an Exception Plan — only if the Board requests one",
                ],
                "continue": "See the method debrief",
            },
            {
                "type": "method", "label": "Method", "eyebrow": "Method debrief",
                "title": "Tolerance is a limit, not a target",
                "panels": [
                    "Tolerance is the <b>delegated authority</b> the Board gives the Project Manager to run the stage. A forecast to exceed it is an <b>exception</b>: the Project Manager escalates with an <b>Exception Report</b> (situation, options, recommendation) and the <b>Board decides</b> — approve an Exception Plan, change the project, or close it early.",
                    "Self-authorising (B) spends authority you do not have; waiting for the boundary (C) removes the Board’s options. Update the Issue Register, reflect any materialised risk in the Risk Register, and report through the Exception Report.",
                ],
                "missed": "Stage tolerance card — the line showing the forecast had already crossed the agreed limit.",
                "cta": "See your record",
            },
        ],
    },
    "PRACTITIONER": {
        "steps": [
            {
                "type": "brief", "label": "Brief", "eyebrow": "Episode D · Recover and decide · Applied judgement",
                "title": "The forecast has moved. Work out what it means.",
                "body": "Stage 2, mixed signals. Some of the slippage traces back to a change you handled earlier; some to a risk that has now materialised. Decide what the evidence shows before you act.",
                "docs": [
                    {"head": {"label": "Programme note"},
                     "html": "The migration is late and the appointment-booking build absorbed more effort than planned. Finance has flagged the stage cost forecast as “trending over”. No formal escalation has been made yet."},
                ],
                "cta": "Open the evidence pack",
            },
            {
                "type": "evidenceSelect", "label": "Select evidence", "eyebrow": "Step 1 · Evidence selection",
                "title": "Which evidence establishes the exception?",
                "body": "Pick the four items that show whether tolerance is forecast to breach and why. Two are distractors.",
                "need": 4,
                "items": [
                    {"t": "Checkpoint Report trend across the last three periods", "d": "Shows the slippage is sustained, not a blip.", "good": True},
                    {"t": "Stage Plan tolerance (time & cost)", "d": "The limit the forecast must be compared against.", "good": True},
                    {"t": "Risk Register entry for the data migration", "d": "A risk that has now occurred — feeds the forecast.", "good": True},
                    {"t": "Impact record from the I12 change decision", "d": "Part of the added effort traces to the change route.", "good": True},
                    {"t": "Supplier’s quarterly marketing deck", "d": "Promotional material — no bearing on tolerance.", "good": False},
                    {"t": "Team wellbeing pulse survey", "d": "Worth caring about, not evidence of the breach.", "good": False},
                ],
                "continue": "Classify the situation",
            },
            {
                "type": "classify", "label": "Classify", "eyebrow": "Step 2 · Classify",
                "title": "What are you actually dealing with?",
                "options": [
                    {"key": "routine-issue", "label": "A routine issue to log and manage within tolerance"},
                    {"key": "risk", "label": "A risk to record and watch"},
                    {"key": "exception", "label": "An exception — a forecast to breach stage tolerance"},
                ],
                "feedback": {
                    "ok": "Correct. The migration risk has occurred and the forecast now exceeds tolerance, so this is an exception situation — not something to absorb quietly or merely watch.",
                    "bad": "Re-read the forecast against the tolerance. The limit is forecast to be breached, which makes this an <b>exception</b>, not a routine issue or an open risk.",
                },
                "continue": "Choose the action",
            },
            {
                "type": "decide", "label": "Decide", "eyebrow": "Step 3 · Action",
                "title": "Choose the next action",
                "body": "Four plausible routes. Only one escalates correctly without over- or under-reacting.",
                "options": [
                    {"code": "A", "text": "Produce an Exception Report — situation, options and a recommendation — and escalate to the Project Board; prepare an Exception Plan only if the Board directs."},
                    {"code": "B", "text": "Re-baseline the stage plan yourself to recover the position and keep delivering."},
                    {"code": "C", "text": "Log it as a routine issue in the Issue Register and continue within current tolerance."},
                    {"code": "D", "text": "Fold it into the End Stage Report and raise it at the stage boundary."},
                ],
                "consequence": {
                    "A": {"tone": "good", "title": "Consequence", "html": "You give the Board a clear exception: what has happened, the realistic options, and your recommendation. They direct — most likely requesting an Exception Plan to re-baseline the rest of the stage. Authority stays where it belongs and delivery continues on honest numbers.", "continue": "Method debrief"},
                    "B": {"tone": "bad", "title": "Consequence", "html": "Red-line: re-baselining the plan yourself is exactly the authority a forecast breach removes from you. You would be setting a new tolerance the Board never agreed — a governance breach dressed up as recovery."},
                    "C": {"tone": "warn", "title": "Consequence", "html": "Under-reaction: a forecast tolerance breach is not a routine issue. Logging it and carrying on inside a tolerance you are about to exceed misreads the severity and delays the Board’s decision."},
                    "D": {"tone": "warn", "title": "Consequence", "html": "Too late: the stage boundary is where you report what happened, not where you escalate a live breach. Deferring removes the Board’s options while the overspend accrues."},
                },
            },
            {
                "type": "repair", "label": "Repair", "eyebrow": "Repair · transfer task",
                "title": "A benefit forecast slips instead",
                "body": "New surface: cost and time hold, but the forecast now shows a <b>key benefit</b> (first-time-fix rate) will fall short of its agreed benefit tolerance. What is the correct route?",
                "options": [
                    {"code": "A", "text": "Treat it as a forecast breach of benefit tolerance: raise it and produce an Exception Report for the Board to direct."},
                    {"code": "B", "text": "Adjust the target down to what looks achievable and keep going."},
                    {"code": "C", "text": "Leave it for the post-project benefits review — benefits are measured later anyway."},
                ],
                "feedback": {
                    "ok": {"title": "Repaired", "html": "Right. Benefit is a tolerance dimension like any other. A forecast to breach it is escalated through an Exception Report — you cannot quietly move the target or defer a live breach to the benefits review."},
                    "bad": {"title": "Still off-method", "html": "Lowering the target yourself re-baselines benefit without the Board; deferring to the benefits review ignores a breach you can see now. Benefit tolerance breaches escalate like any other."},
                },
                "continue": "Method debrief",
            },
            {
                "type": "method", "label": "Method", "eyebrow": "Debrief",
                "title": "Escalate the forecast, not the actual",
                "panels": [
                    "Exception management is triggered by a <b>forecast</b> to breach tolerance, not by waiting for the breach to happen. The Project Manager raises the issue and produces an <b>Exception Report</b>; the <b>Project Board</b> decides. Re-baselining (B) usurps that decision; a routine-issue log (C) under-reacts; the boundary (D) is too late.",
                    "Tolerance applies across six dimensions — time, cost, scope, quality, risk and benefit — and a forecast breach of any of them follows the same route. Update the Issue and Risk Registers and let the Exception Report carry the recommendation.",
                ],
                "cta": "See your record",
            },
        ],
    },
    "related": [
        {"id": "I15", "why": "The Board direction you get here sets the baseline at the stage boundary."},
        {"id": "I12", "why": "Part of this exception traces back to the change you routed in I12."},
        {"id": "I10", "why": "The migration risk that materialised was first assessed here."},
    ],
}
