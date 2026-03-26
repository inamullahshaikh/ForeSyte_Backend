"""
Adapter to integrate run_detection with video processing.
Converts ClassificationResult to the behavior format expected by VideoProcessor.
"""

from __future__ import annotations

import logging
from typing import Any

import cv2
import numpy as np

from .run_detection import Config, run_on_image

log = logging.getLogger(__name__)


# Severity mapping for cheating behaviors (label -> severity)
LABEL_SEVERITY = {
    "phone": "high",
    "Hand Under Table": "high",
    "Bend Over The Desk": "medium",
    "Stand Up": "high",
    "Wave": "medium",
    "Look Around": "medium",
    "Normal": "low",
}


def process_frame(
    frame: np.ndarray,
    frame_number: int,
    timestamp,
    seat_mapping: dict | None = None,
    cfg: Config | None = None,
    return_annotated: bool = False,
) -> dict[str, Any]:
    """
    Process a single frame through the cheating detection pipeline.
    (seat_mapping kept for API compatibility; mapping done in processor via SeatMapper)
    Returns the format expected by VideoProcessor: student_behaviors, invigilator_behaviors.

    Args:
        frame: BGR image (numpy array from cv2)
        frame_number: Frame index in video
        timestamp: datetime of the frame
        seat_mapping: Optional bbox -> seat_id mapping (for future use)
        cfg: Optional Config override
        return_annotated: If True, include 'annotated_frame' in result for evidence saving

    Returns:
        dict with keys: student_behaviors, invigilator_behaviors, and optionally annotated_frame
    """
    results, annotated = run_on_image(frame, cfg=cfg, save_output=False)

    student_behaviors = []
    for r in results:
        # Only report suspicious behaviors
        if not r.is_suspicious:
            continue

        severity = LABEL_SEVERITY.get(r.label, "medium")
        student_behaviors.append({
            "behavior_type": r.label,
            "severity": severity,
            "confidence": float(r.confidence),
            "details": f"bbox={r.bbox}, student_index={r.student_index}",
            "bbox": r.bbox,
            "student_index": r.student_index,
        })

    # AI engine focuses on students; no invigilator detection for now
    invigilator_behaviors = []

    out = {
        "student_behaviors": student_behaviors,
        "invigilator_behaviors": invigilator_behaviors,
    }
    if return_annotated and (student_behaviors or invigilator_behaviors):
        out["annotated_frame"] = annotated
    return out


def map_detection_to_seat(behavior: dict, seat_mapping: dict | None) -> str | None:
    """
    Map a detection (bbox) to a seat_id using seat_mapping.
    For use when seat mapping is available (e.g. from seating plan overlay).

    Args:
        behavior: Behavior dict with 'bbox' key
        seat_mapping: Mapping from bbox or region to seat_id (format TBD)

    Returns:
        seat_id (UUID string) or None if no mapping
    """
    if not seat_mapping:
        return None
    # Future: implement bbox center -> polygon containment lookup
    bbox = behavior.get("bbox")
    if not bbox:
        return None
    # Placeholder: seat_mapping could be dict of (cx,cy) or bbox_hash -> seat_id
    return seat_mapping.get(tuple(bbox))
