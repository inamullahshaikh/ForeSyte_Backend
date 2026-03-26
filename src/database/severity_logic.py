"""
Severity logic: frequency-based severity levels per activity type.

Severity increases with how often the same action is done (per student, per exam).
Each activity type has its own thresholds: different actions escalate at different rates.

Frame-run logic: track consecutive same-label frames per student. One violation per run;
sustained labels (e.g. look around) require min consecutive frames; instant labels (e.g. phone) count from 1 frame.
"""

from typing import Dict, List, Tuple, Optional, Any
from uuid import UUID
from datetime import datetime, timedelta
from dataclasses import dataclass

# Severity levels (string for StudentActivity, int 1-4 for Violation)
SEVERITY_LEVELS = ("low", "medium", "high", "critical")
SEVERITY_TO_INT = {"low": 1, "medium": 2, "high": 3, "critical": 4}
INT_TO_SEVERITY = {1: "low", 2: "medium", 3: "high", 4: "critical"}


def _normalize_activity_type(activity_type: str) -> str:
    """Map various activity type names to a canonical key for config lookup."""
    if not activity_type or not isinstance(activity_type, str):
        return "unknown"
    # Strip any trailing time (e.g. ":20:00" or ":11:20:00") that may be stored with the type
    s = activity_type.strip()
    if ":" in s:
        parts = s.rsplit(":", 2)
        if len(parts) == 3 and all(p.strip().isdigit() for p in parts[-2:]):
            s = parts[0].strip()
    s = s.lower()
    # Serious / academic dishonesty: high from first occurrence
    if "cheat" in s or "academic dishonesty" in s:
        return "cheating_attempt"
    if "phone" in s or "device" in s or "mobile" in s or "cell" in s:
        return "phone_device"
    # Unauthorized materials (book, paper, notes): medium→high→critical by frequency
    if "unauthorized" in s and "material" in s or "book" in s or "paper" in s or ("material" in s and "use" in s):
        return "unauthorized_materials"
    # Communication / talking
    if "communication" in s or "talking" in s or "talk" in s or "neighbor" in s:
        return "talking_communication"
    # Looking around / looking away
    if "look" in s and ("around" in s or "away" in s) or "look around" in s or "looking away" in s:
        return "looking_around"
    # Audio detected: medium (could be discussion or noise)
    if "audio" in s and "detect" in s or s == "audio detected":
        return "audio_detected"
    # Multiple faces: high (impersonation risk)
    if "multiple" in s and "face" in s:
        return "multiple_faces"
    # Suspicious movement / movement
    if "suspicious" in s or "movement" in s:
        return "suspicious_movement"
    if "bend" in s or "desk" in s:
        return "bend_over_desk"
    if "hand under" in s or "hand under table" in s:
        return "hand_under_table"
    if "stand" in s or "stand up" in s:
        return "stand_up"
    if "wave" in s:
        return "wave"
    if "normal" in s or "no violation" in s:
        return "normal"
    return "unknown"


# Per-activity-type config: (min_count, severity) means "at least min_count occurrences -> this severity"
# Practical rule: serious violations start high; distraction/suspicion escalate with frequency.
ACTIVITY_SEVERITY_CONFIG: Dict[str, List[Tuple[int, str]]] = {
    "cheating_attempt": [(1, "high"), (2, "critical")],
    "phone_device": [(1, "high"), (2, "critical")],
    "multiple_faces": [(1, "high"), (2, "critical")],
    "unauthorized_materials": [(1, "medium"), (2, "high"), (3, "critical")],
    "audio_detected": [(1, "medium"), (3, "high"), (5, "critical")],
    "suspicious_movement": [(1, "low"), (3, "medium"), (6, "high"), (10, "critical")],
    "talking_communication": [(1, "low"), (3, "medium"), (6, "high"), (10, "critical")],
    "looking_around": [(1, "low"), (4, "medium"), (8, "high"), (15, "critical")],
    "bend_over_desk": [(1, "low"), (3, "medium"), (6, "high"), (10, "critical")],
    "hand_under_table": [(1, "medium"), (3, "high"), (5, "critical")],
    "stand_up": [(1, "low"), (2, "medium"), (4, "high"), (6, "critical")],
    "wave": [(1, "low"), (3, "medium"), (6, "high"), (10, "critical")],
    "unknown": [(1, "low"), (4, "medium"), (8, "high"), (12, "critical")],
    "normal": [(1, "low")],
}

# Frame-run logic: min consecutive frames for a run to count as a violation (1 = instant; 2+ = sustained).
# Severity for qualifying runs is then based on run length (frequency) via ACTIVITY_SEVERITY_CONFIG.
MIN_FRAMES_TO_COUNT: Dict[str, int] = {
    "cheating_attempt": 1,
    "phone_device": 1,
    "multiple_faces": 1,
    "unauthorized_materials": 1,
    "hand_under_table": 3,     # violation from 3rd frame
    "stand_up": 1,             # violation on first frame captured
    "looking_around": 5,       # violation from 5th frame (ignore brief glances)
    "bend_over_desk": 3,
    "wave": 3,
    "talking_communication": 2,
    "suspicious_movement": 2,
    "audio_detected": 2,
    "unknown": 1,
    "normal": 999,             # never count normal as violation
}


@dataclass
class LabelRun:
    """One contiguous run of the same label for a student (frame sequence)."""
    start_ts: Any
    end_ts: Any
    label_raw: str
    normalized_key: str
    frame_count: int
    first_detection: Dict[str, Any]


def get_runs_from_detections(detections: List[Dict[str, Any]]) -> List[LabelRun]:
    """
    Group detections into consecutive same-label runs (by timestamp).
    When the label changes (including to/from 'normal'), a new run starts.
    Detections must be sorted by timestamp; we sort if not.
    """
    if not detections:
        return []
    sorted_d = sorted(detections, key=lambda x: (x.get("timestamp") or x.get("frame_number", 0)))
    runs: List[LabelRun] = []
    current: List[Dict] = []
    current_key: Optional[str] = None

    for d in sorted_d:
        raw = (d.get("behavior_type") or d.get("activity_type") or "").strip() or "unknown"
        key = _normalize_activity_type(raw)
        if key != current_key:
            if current and current_key and current_key != "normal":
                runs.append(LabelRun(
                    start_ts=current[0].get("timestamp"),
                    end_ts=current[-1].get("timestamp"),
                    label_raw=current[0].get("behavior_type") or current[0].get("activity_type") or raw,
                    normalized_key=current_key,
                    frame_count=len(current),
                    first_detection=current[0],
                ))
            current = [d]
            current_key = key
        else:
            current.append(d)

    if current and current_key and current_key != "normal":
        runs.append(LabelRun(
            start_ts=current[0].get("timestamp"),
            end_ts=current[-1].get("timestamp"),
            label_raw=current[0].get("behavior_type") or current[0].get("activity_type") or "unknown",
            normalized_key=current_key,
            frame_count=len(current),
            first_detection=current[0],
        ))
    return runs


def filter_qualifying_runs(runs: List[LabelRun]) -> List[LabelRun]:
    """Keep only runs that meet the min consecutive frames for that label (one violation per run, no redundant)."""
    return [
        r for r in runs
        if r.frame_count >= MIN_FRAMES_TO_COUNT.get(r.normalized_key, 1)
    ]


def compute_severity_from_count(count: int, activity_type: str) -> str:
    """
    Get severity for a given occurrence count of an action type.
    count: total number of times this action has been recorded (including the current one).
    activity_type: raw activity type string (e.g. "Looking at Phone", "Cheating Attempt").
    Returns: "low" | "medium" | "high" | "critical"
    """
    if count < 1:
        count = 1
    key = _normalize_activity_type(activity_type)
    thresholds = ACTIVITY_SEVERITY_CONFIG.get(key, ACTIVITY_SEVERITY_CONFIG["unknown"])
    # thresholds are (min_count, severity) sorted by min_count ascending
    severity = "low"
    for min_count, sev in thresholds:
        if count >= min_count:
            severity = sev
    return severity


def count_same_activity_in_exam(
    student_id: UUID,
    exam_id: UUID,
    activity_type: str,
    db: Any,
    time_window_minutes: Optional[int] = None,
    exclude_activity_id: Optional[UUID] = None,
) -> int:
    """
    Count how many activities of the same type (for the same student, same exam) exist.
    Optionally within the last time_window_minutes, and optionally excluding one activity_id.
    """
    from database.models import StudentActivity

    q = db.query(StudentActivity).filter(
        StudentActivity.student_id == student_id,
        StudentActivity.exam_id == exam_id,
        StudentActivity.activity_type == activity_type,
    )
    if time_window_minutes is not None:
        since = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        q = q.filter(StudentActivity.timestamp >= since)
    if exclude_activity_id is not None:
        q = q.filter(StudentActivity.activity_id != exclude_activity_id)
    return q.count()


def compute_severity(
    student_id: UUID,
    exam_id: UUID,
    activity_type: str,
    db: Any,
    time_window_minutes: Optional[int] = None,
    exclude_activity_id: Optional[UUID] = None,
) -> str:
    """
    Compute severity for a new activity of the given type, based on how often
    this student has already done this action in this exam (frequency-based).
    """
    count = count_same_activity_in_exam(
        student_id, exam_id, activity_type, db,
        time_window_minutes=time_window_minutes,
        exclude_activity_id=exclude_activity_id,
    )
    # This new activity will be the (count + 1)-th occurrence
    return compute_severity_from_count(count + 1, activity_type)


def severity_to_int(severity: str) -> int:
    """Map severity string to integer 1–4 for Violation model."""
    if isinstance(severity, int) and 1 <= severity <= 4:
        return severity
    return SEVERITY_TO_INT.get((severity or "").lower(), 1)


def severity_from_int(severity_int: int) -> str:
    """Map integer 1–4 to severity string."""
    return INT_TO_SEVERITY.get(severity_int, "low")
