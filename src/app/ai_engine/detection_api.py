"""
API router for exam cheating detection.
Exposes the detection pipeline as a REST endpoint.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.ai_engine.run_detection import Config, run_on_image

log = logging.getLogger(__name__)

router = APIRouter(prefix="/detection", tags=["AI Detection"])

# Output directory for annotated images (served under /uploads)
DETECTION_OUTPUT_DIR = Path("uploads/detection")
DETECTION_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------
# Response Schemas
# -------------------------
class StudentDetection(BaseModel):
    student_index: int
    bbox: tuple[int, int, int, int]
    label: str
    confidence: float
    is_suspicious: bool
    all_scores: dict[str, float]


class DetectionResponse(BaseModel):
    total_students: int
    suspicious_count: int
    students: list[StudentDetection]
    annotated_image_url: str | None
    processing_time_seconds: float


# -------------------------
# Detection Endpoint
# -------------------------
@router.post("/run", response_model=DetectionResponse)
async def run_detection(
    image: UploadFile = File(..., description="CCTV/exam room image (JPG, PNG)"),
):
    """
    Run exam cheating detection on an uploaded image.
    Detects persons, classifies behavior, and returns detections with an annotated image.
    """
    # Validate content type
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an image (JPG, PNG, etc.).",
        )

    try:
        content = await image.read()
    except Exception as e:
        log.error("Failed to read uploaded file: %s", e)
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}") from e

    # Decode image
    arr = np.frombuffer(content, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(
            status_code=400,
            detail="Could not decode image. Please ensure the file is a valid image.",
        )

    import time
    t0 = time.perf_counter()

    try:
        cfg = Config()
        results, annotated = run_on_image(
            img,
            cfg=cfg,
            save_output=False,
        )
    except Exception as e:
        log.exception("Detection pipeline failed")
        raise HTTPException(
            status_code=500,
            detail=f"Detection failed: {str(e)}",
        ) from e

    elapsed = time.perf_counter() - t0

    # Save annotated image and build URL
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    suffix = Path(image.filename or "image").suffix or ".jpg"
    if suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
        suffix = ".jpg"
    out_filename = f"detection_{timestamp}_{uuid.uuid4().hex[:8]}{suffix}"
    out_path = DETECTION_OUTPUT_DIR / out_filename
    cv2.imwrite(str(out_path), annotated)
    annotated_url = f"/uploads/detection/{out_filename}"

    # Build response
    student_detections = [
        StudentDetection(
            student_index=r.student_index,
            bbox=r.bbox,
            label=r.label,
            confidence=r.confidence,
            is_suspicious=r.is_suspicious,
            all_scores=r.all_scores,
        )
        for r in results
    ]

    return DetectionResponse(
        total_students=len(results),
        suspicious_count=sum(1 for r in results if r.is_suspicious),
        students=student_detections,
        annotated_image_url=annotated_url,
        processing_time_seconds=round(elapsed, 2),
    )
