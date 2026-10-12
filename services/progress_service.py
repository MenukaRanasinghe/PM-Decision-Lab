"""Core progress engine: attempts, decision events, scoring rollups, dashboards, practice record.
Port of the Node routes/missions.js + services/progress.js + h5pPlay.js logic. All scoring is
server-side; the UI only sends option keys. Every read/write is scoped to one learner.
"""
from datetime import datetime

from database.connection import session_scope
from database.models import (
    MissionAttempt, DecisionEvent, LearnerProgress, Learner, Activity, H5PVersion, ActivityProgress,
)
from content.registry import (
    MISSIONS, MISSION_IDS, TRACK_CODES, TRACKS, episode_of, echo_for, can_access_track,
)
from content.scoring import resolve_event, roll_up

# Activity types tracked via MissionAttempt (rich, server-side). Everything else uses
# ActivityProgress (launch/access + verified-only scores).
_NATIVE_TYPES = ("NATIVE", "H5P")


# ── native mission play ───────────────────────────────────────────────────────
def start_attempt(learner_id, mission_id, level):
    with session_scope() as s:
        attempt = (
            s.query(MissionAttempt)
            .filter_by(learner_id=learner_id, mission_id=mission_id, level=level, completed=False)
            .order_by(MissionAttempt.attempt_number.desc())
            .first()
        )
        resumed = attempt is not None
        if attempt is None:
            latest = (
                s.query(MissionAttempt)
                .filter_by(learner_id=learner_id, mission_id=mission_id, level=level)
                .order_by(MissionAttempt.attempt_number.desc())
                .first()
            )
            attempt = MissionAttempt(
                learner_id=learner_id, mission_id=mission_id, level=level,
                attempt_number=(latest.attempt_number if latest else 0) + 1,
                max_score=MISSIONS.get(mission_id, {}).get("max_score", 2),
                status="IN_PROGRESS",
            )
            s.add(attempt)
            s.flush()
        else:
            attempt.last_accessed_at = datetime.utcnow()
        return {
            "attempt_id": attempt.id,
            "attempt_number": attempt.attempt_number,
            "resumed": resumed,
            "echo": _load_echo(s, learner_id, mission_id),
        }


def _load_echo(s, learner_id, mission_id):
    echo = echo_for(mission_id)
    if not echo:
        return None
    src = (
        s.query(MissionAttempt)
        .filter_by(learner_id=learner_id, mission_id=echo["from"], completed=True)
        .order_by(MissionAttempt.score.desc())
        .first()
    )
    return {
        "from": echo["from"], "text": echo["text"],
        "route_code": src.route_code if src else None,
        "integrated": bool(src),
    }


def _refresh_attempt(s, attempt, mission_id):
    events = (
        s.query(DecisionEvent)
        .filter_by(attempt_id=attempt.id)
        .order_by(DecisionEvent.created_at.asc())
        .all()
    )
    roll = roll_up(mission_id, events)
    first_decide = next((e for e in events if e.step == "decide"), None)
    attempt.score = roll["score"]
    attempt.max_score = roll["max_score"]
    attempt.first_time_aligned = roll["first_time_aligned"]
    attempt.repaired = roll["repaired"]
    attempt.red_line_hit = roll["red_line_hit"]
    attempt.route_code = roll["route_code"]
    attempt.feedback_tags = list(roll["feedback_tags"])
    attempt.first_attempt_score = first_decide.score_change if first_decide else None
    attempt.repaired_score = roll["score"] if roll["repaired"] else None
    attempt.last_accessed_at = datetime.utcnow()
    return roll


def record_event(learner_id, attempt_id, mission_id, level, step, selected_option):
    with session_scope() as s:
        attempt = s.query(MissionAttempt).filter_by(id=attempt_id).one_or_none()
        if not attempt or attempt.learner_id != learner_id:
            raise PermissionError("attempt_not_found")
        if attempt.mission_id != mission_id or attempt.level != level:
            raise ValueError("attempt_mismatch")
        if attempt.completed:
            raise ValueError("attempt_completed")

        outcome = resolve_event(mission_id, level, step, selected_option)
        route = f"{mission_id}-{str(selected_option).split(':')[0]}" if step == "decide" else None
        s.add(DecisionEvent(
            learner_id=learner_id, attempt_id=attempt.id, mission_id=mission_id, level=level,
            step=step, selected_option=str(selected_option),
            score_change=outcome["score_change"], red_line=outcome["red_line"],
            is_correct=outcome["is_correct"], feedback_tag=outcome["feedback_tag"], route_code=route,
        ))
        s.flush()
        roll = _refresh_attempt(s, attempt, mission_id)
        return {
            "score_change": outcome["score_change"], "feedback_tag": outcome["feedback_tag"],
            "red_line": outcome["red_line"], "correct": outcome["is_correct"],
            "attempt": {"id": attempt.id, **roll},
        }


def complete_attempt(learner_id, attempt_id, mission_id, level):
    with session_scope() as s:
        attempt = s.query(MissionAttempt).filter_by(id=attempt_id).one_or_none()
        if not attempt or attempt.learner_id != learner_id:
            raise PermissionError("attempt_not_found")
        if attempt.mission_id != mission_id or attempt.level != level:
            raise ValueError("attempt_mismatch")
        roll = _refresh_attempt(s, attempt, mission_id)
        attempt.completed = True
        attempt.status = "COMPLETED"
        attempt.percentage = round(roll["score"] / roll["max_score"] * 100) if roll["max_score"] else None
        attempt.completed_at = attempt.completed_at or datetime.utcnow()
        out = {
            "id": attempt.id, "mission_id": mission_id, "level": level,
            "attempt_number": attempt.attempt_number, **roll,
        }
    totals = recompute_progress(learner_id)
    return {"attempt": out, "totals": totals}


# ── rollup ────────────────────────────────────────────────────────────────────
def _best_by_activity(s, learner_id):
    rows = (
        s.query(MissionAttempt)
        .filter_by(learner_id=learner_id)
        .order_by(MissionAttempt.score.desc(), MissionAttempt.completed.desc(), MissionAttempt.last_accessed_at.desc())
        .all()
    )
    best = {}
    for r in rows:
        k = f"{r.mission_id}:{r.level}"
        if k not in best:
            best[k] = r
    return best


def recompute_progress(learner_id):
    with session_scope() as s:
        best = _best_by_activity(s, learner_id)
        attempted = completed = points = first = repaired = red = 0
        for code in MISSION_IDS:
            f = best.get(f"{code}:FOUNDATION")
            p = best.get(f"{code}:PRACTITIONER")
            cands = [x for x in (f, p) if x]
            if not cands:
                continue
            attempted += 1
            top = sorted(cands, key=lambda a: (a.score, int(a.completed)), reverse=True)[0]
            points += top.score
            if top.first_time_aligned:
                first += 1
            if top.repaired:
                repaired += 1
            if any(c.red_line_hit for c in cands):
                red += 1
            if any(c.completed for c in cands):
                completed += 1
        current_mission = None
        for code in MISSION_IDS:
            f = best.get(f"{code}:FOUNDATION")
            p = best.get(f"{code}:PRACTITIONER")
            if not (f and f.completed and p and p.completed):
                current_mission = code
                break
        data = dict(
            completed_missions=completed, attempted_missions=attempted, total_points=points,
            first_time_aligned=first, repaired_count=repaired, red_line_hits=red,
            current_mission=current_mission, current_episode=(episode_of(current_mission) if current_mission else "E"),
        )
        prog = s.query(LearnerProgress).filter_by(learner_id=learner_id).one_or_none()
        if prog is None:
            prog = LearnerProgress(learner_id=learner_id)
            s.add(prog)
        for k, v in data.items():
            setattr(prog, k, v)
        return data


# ── dashboards ────────────────────────────────────────────────────────────────
def _status_of(a):
    if a is None:
        return "NOT_STARTED"
    return a.status or ("COMPLETED" if a.completed else "IN_PROGRESS")


def track_progress(learner_id):
    with session_scope() as s:
        best = _best_by_activity(s, learner_id)
        out = {}
        for code in TRACK_CODES:
            acts = s.query(Activity).filter_by(track=code).all()
            attempted = completed = points = max_points = score_sum = scored = 0
            last = None
            for act in acts:
                a = best.get(f"{act.code}:{code}")
                if a:
                    attempted += 1
                    if a.completed:
                        completed += 1
                        points += a.score
                        max_points += a.max_score
                        score_sum += a.score
                        scored += 1
                    if last is None or a.last_accessed_at > last["at"]:
                        last = {"code": act.code, "title": act.title, "at": a.last_accessed_at}
            avail = sum(1 for x in acts if x.available)
            out[code] = {
                "code": code, "name": TRACKS[code]["name"], "mode": TRACKS[code]["mode"],
                "activities_total": len(acts), "activities_available": avail,
                "attempted": attempted, "completed": completed,
                "completion_pct": round(completed / avail * 100) if avail else 0,
                "best_points": points, "max_points": max_points,
                "average_score": round(score_sum / scored, 2) if scored else None,
                "last_activity": ({"code": last["code"], "title": last["title"]} if last else None),
            }
        return out


def activities_with_status(learner_id):
    with session_scope() as s:
        best = _best_by_activity(s, learner_id)
        ext = {p.activity_id: p for p in s.query(ActivityProgress).filter_by(learner_id=learner_id).all()}
        out = {}
        for code in TRACK_CODES:
            acts = s.query(Activity).filter_by(track=code).order_by(Activity.order_index).all()
            rows = []
            for act in acts:
                atype = act.activity_type or act.kind or "NATIVE"
                row = {
                    "id": act.id, "code": act.code, "title": act.title, "description": act.description,
                    "est_minutes": act.est_minutes, "kind": act.kind, "activity_type": atype,
                    "available": act.available, "status_lifecycle": act.status,
                    "url": act.url, "embed_url": act.embed_url, "open_mode": act.open_mode,
                    "instructions": act.instructions, "category": act.category, "provider": act.provider,
                    "pass_mark": act.pass_mark, "due_date": act.due_date,
                    # tracking fields (filled per type below)
                    "status": "NOT_STARTED", "score": None, "max_score": None, "percentage": None,
                    "attempts": 0, "first_time_aligned": False, "repaired": False,
                    "score_verified": None, "last_accessed_at": None,
                }
                if atype in _NATIVE_TYPES:
                    a = best.get(f"{act.code}:{code}")
                    row.update(
                        status=_status_of(a),
                        score=a.score if a else None, max_score=a.max_score if a else None,
                        percentage=a.percentage if a else None,
                        attempts=a.attempt_number if a else 0,
                        first_time_aligned=a.first_time_aligned if a else False,
                        repaired=a.repaired if a else False,
                        score_verified=True if a else None,
                        last_accessed_at=a.last_accessed_at if a else None,
                    )
                else:
                    p = ext.get(act.id)
                    if p:
                        row.update(
                            status=p.completion_status or "NOT_STARTED",
                            score=p.best_score, max_score=p.best_max_score,
                            percentage=p.progress_pct, attempts=p.attempt_count,
                            score_verified=bool(p.score_verified),
                            last_accessed_at=p.last_access_at,
                        )
                rows.append(row)
            out[code] = rows
        return out


def recently_opened(learner_id, limit=8):
    """Most-recently touched activities across native/H5P attempts AND external progress."""
    with session_scope() as s:
        acts = {(a.code, a.track): a for a in s.query(Activity).all()}
        items = {}
        for a in (s.query(MissionAttempt).filter_by(learner_id=learner_id)
                  .order_by(MissionAttempt.last_accessed_at.desc()).limit(40).all()):
            key = (a.mission_id, a.level)
            act = acts.get(key)
            cur = items.get(key)
            if cur is None or (a.last_accessed_at and a.last_accessed_at > cur["last_accessed_at"]):
                items[key] = {
                    "code": a.mission_id, "track": a.level,
                    "title": act.title if act else a.mission_id,
                    "activity_type": (act.activity_type if act else "NATIVE"),
                    "status": a.status or ("COMPLETED" if a.completed else "IN_PROGRESS"),
                    "score": a.score, "max_score": a.max_score, "score_verified": True,
                    "last_accessed_at": a.last_accessed_at,
                }
        for p in (s.query(ActivityProgress).filter_by(learner_id=learner_id)
                  .order_by(ActivityProgress.last_access_at.desc()).limit(40).all()):
            key = (p.code, p.track)
            act = acts.get(key)
            cur = items.get(key)
            ts = p.last_access_at
            if cur is None or (ts and cur["last_accessed_at"] and ts > cur["last_accessed_at"]):
                items[key] = {
                    "code": p.code, "track": p.track,
                    "title": act.title if act else p.code,
                    "activity_type": (act.activity_type if act else "LINK"),
                    "status": p.completion_status, "score": p.best_score, "max_score": p.best_max_score,
                    "score_verified": bool(p.score_verified), "last_accessed_at": ts,
                }
        ordered = sorted(items.values(), key=lambda r: (r["last_accessed_at"] or datetime.min), reverse=True)
        return ordered[:limit]


def activity_detail(learner_id, code, track):
    with session_scope() as s:
        act = s.query(Activity).filter_by(code=code, track=track).one_or_none()
        if not act:
            return None
        attempts = (
            s.query(MissionAttempt)
            .filter_by(learner_id=learner_id, mission_id=code, level=track)
            .order_by(MissionAttempt.attempt_number.asc())
            .all()
        )
        best = None
        if attempts:
            best = sorted(attempts, key=lambda a: (a.score, int(a.completed)), reverse=True)[0]
        h5p = None
        if act.kind == "H5P":
            v = (
                s.query(H5PVersion)
                .filter_by(activity_id=act.id, status="PUBLISHED")
                .order_by(H5PVersion.version.desc())
                .first()
            )
            if v:
                h5p = {"version_id": v.id, "title": v.title}
        ext = None
        if (act.activity_type or act.kind) not in _NATIVE_TYPES:
            p = s.query(ActivityProgress).filter_by(learner_id=learner_id, activity_id=act.id).one_or_none()
            if p:
                ext = {
                    "completion_status": p.completion_status, "launch_count": p.launch_count,
                    "view_count": p.view_count, "attempt_count": p.attempt_count,
                    "best_score": p.best_score, "best_max_score": p.best_max_score,
                    "progress_pct": p.progress_pct, "passed": p.passed,
                    "score_verified": bool(p.score_verified),
                    "first_access_at": p.first_access_at, "last_access_at": p.last_access_at,
                    "completed_at": p.completed_at,
                }
        return {
            "activity": {"id": act.id, "code": act.code, "title": act.title, "description": act.description,
                         "est_minutes": act.est_minutes, "kind": act.kind,
                         "activity_type": act.activity_type or act.kind, "track": track,
                         "available": act.available, "url": act.url, "embed_url": act.embed_url,
                         "open_mode": act.open_mode, "provider": act.provider,
                         "instructions": act.instructions, "category": act.category,
                         "pass_mark": act.pass_mark, "max_points": act.max_points, "due_date": act.due_date},
            "external": ext,
            "best": (None if not best else {
                "score": best.score, "max_score": best.max_score, "percentage": best.percentage,
                "status": _status_of(best), "completed": best.completed,
                "first_time_aligned": best.first_time_aligned, "repaired": best.repaired,
                "red_line_hit": best.red_line_hit, "attempt_number": best.attempt_number,
                "route_code": best.route_code, "feedback_tags": best.feedback_tags or [],
            }),
            "attempts": [{"attempt_number": a.attempt_number, "score": a.score, "max_score": a.max_score,
                          "status": _status_of(a), "completed": a.completed} for a in attempts],
            "h5p": h5p,
        }


def practice_record(learner_id):
    with session_scope() as s:
        learner = s.query(Learner).filter_by(id=learner_id).one_or_none()
        best = _best_by_activity(s, learner_id)
        tracks = {}
        for code in TRACK_CODES:
            acts = s.query(Activity).filter_by(track=code).all()
            attempted = completed = total = max_sum = score_sum = scored = 0
            for act in acts:
                a = best.get(f"{act.code}:{code}")
                if a:
                    attempted += 1
                    if a.completed:
                        completed += 1
                        total += a.score
                        max_sum += a.max_score
                        score_sum += a.score
                        scored += 1
            avail = sum(1 for x in acts if x.available)
            tracks[code] = {
                "name": TRACKS[code]["name"], "attempted": attempted, "completed": completed,
                "total_practice_score": total, "max_practice_score": max_sum,
                "average_score": round(score_sum / scored, 2) if scored else None,
                "completion_pct": round(completed / avail * 100) if avail else 0,
            }
        completed_rows = (
            s.query(MissionAttempt)
            .filter_by(learner_id=learner_id, completed=True)
            .order_by(MissionAttempt.completed_at.desc())
            .limit(12)
            .all()
        )
        recent = [{
            "activity": a.mission_id, "title": MISSIONS.get(a.mission_id, {}).get("title", a.mission_id),
            "track": a.level, "score": f"{a.score}/{a.max_score}",
            "tag": (a.feedback_tags or [None])[0] if a.feedback_tags else None,
            "completed_at": a.completed_at,
        } for a in completed_rows]
        return {
            "title": "Fictional Project Practice Record",
            "learner": {"name": (learner.display_name or learner.email) if learner else "Learner",
                        "email": learner.email if learner else None},
            "generated_at": datetime.utcnow(),
            "tracks": tracks, "recent": recent,
        }


# ── H5P attempts ──────────────────────────────────────────────────────────────
def h5p_start(learner_id, code, level):
    with session_scope() as s:
        act = s.query(Activity).filter_by(code=code, track=level).one_or_none()
        if not act or act.kind != "H5P":
            raise ValueError("not_h5p_activity")
        version = (
            s.query(H5PVersion).filter_by(activity_id=act.id, status="PUBLISHED")
            .order_by(H5PVersion.version.desc()).first()
        )
        if not version:
            raise ValueError("no_published_version")
        attempt = (
            s.query(MissionAttempt)
            .filter_by(learner_id=learner_id, mission_id=code, level=level, completed=False, h5p_version_id=version.id)
            .order_by(MissionAttempt.attempt_number.desc()).first()
        )
        if not attempt:
            latest = (
                s.query(MissionAttempt).filter_by(learner_id=learner_id, mission_id=code, level=level)
                .order_by(MissionAttempt.attempt_number.desc()).first()
            )
            attempt = MissionAttempt(
                learner_id=learner_id, mission_id=code, level=level,
                attempt_number=(latest.attempt_number if latest else 0) + 1,
                max_score=0, status="IN_PROGRESS", h5p_version_id=version.id,
            )
            s.add(attempt)
            s.flush()
        return {"attempt_id": attempt.id, "version_id": version.id}


def h5p_event(learner_id, attempt_id, mission_id, level, normalized):
    with session_scope() as s:
        attempt = s.query(MissionAttempt).filter_by(id=attempt_id).one_or_none()
        if not attempt or attempt.learner_id != learner_id:
            raise PermissionError("attempt_not_found")
        n = normalized
        if n["kind"] == "answered":
            s.add(DecisionEvent(
                learner_id=learner_id, attempt_id=attempt.id, mission_id=mission_id, level=level,
                step="h5p", selected_option=(n.get("response") or "answered")[:80],
                score_change=n.get("raw") or 0, is_correct=n.get("correct"),
            ))
        if n.get("raw") is not None and n.get("max") is not None:
            attempt.score = int(n["raw"])
            attempt.max_score = int(n["max"])
            attempt.percentage = round(n["raw"] / n["max"] * 100) if n["max"] else (round(n["scaled"] * 100) if n.get("scaled") is not None else None)
        elif n.get("scaled") is not None:
            attempt.percentage = round(n["scaled"] * 100)
        completed = False
        if n["kind"] == "completed":
            attempt.completed = True
            attempt.status = "COMPLETED"
            attempt.completed_at = attempt.completed_at or datetime.utcnow()
            completed = True
        attempt.last_accessed_at = datetime.utcnow()
        attempt.resume_state = {"last_verb": n.get("verb"), "percentage": attempt.percentage}
    if completed:
        recompute_progress(learner_id)
    return {"completed": completed, "percentage": normalized.get("scaled")}
