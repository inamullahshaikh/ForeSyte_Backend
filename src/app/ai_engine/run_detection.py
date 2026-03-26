"""
Exam Cheating Detection System
===============================
Multi-stage pipeline:
  1. CCTV image enhancement (CLAHE + unsharp mask + gamma)
  2. Person detection with tiled + full-frame fusion and NMS
  3. Per-student classification with configurable thresholds
  4. Annotated output image + detailed console report

Requirements:
  pip install ultralytics opencv-python-headless numpy torch
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env from ai_engine directory
_AI_ENGINE_DIR = Path(__file__).resolve().parent
load_dotenv(_AI_ENGINE_DIR / ".env")


def _resolve_model_path(path: str) -> str:
    """Resolve model path: if relative, resolve against ai_engine directory."""
    p = Path(path)
    if not p.is_absolute():
        p = _AI_ENGINE_DIR / path
    return str(p.resolve())


import cv2
import numpy as np
import torch
from ultralytics import YOLO

# ──────────────────────────────────────────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class Config:
    # I/O
    image_path: str = "D314_frame_28m44s.jpg"
    output_dir: str = "output"
    output_filename: str = "final_detection.jpg"

    # Models (paths from env, resolved relative to ai_engine dir if not absolute)
    person_model_path: str = field(default_factory=lambda: _resolve_model_path(os.getenv("PERSON_MODEL_PATH", "yolov8l.pt")))
    cheating_model_path: str = field(default_factory=lambda: _resolve_model_path(os.getenv("CHEATING_MODEL_PATH", "besta.pt")))

    # Detection thresholds
    person_conf: float = 0.40       # Person detector confidence floor
    nms_iou: float = 0.35           # NMS IoU threshold (lower = more aggressive merge)
    dedup_iou: float = 0.70         # IoU above which two boxes are considered duplicate
    standing_aspect_ratio: float = 2.2  # h/w ratio → person is standing, not seated

    # Classification
    cheat_run_conf: float = 0.01    # Keep low — we gather all raw scores manually
    min_crop_size: int = 200        # Upscale crops smaller than this (px)
    crop_pad_ratio: float = 0.15    # Context padding as fraction of bbox side
    margin_over_normal: float = 0.08  # Suspicious score must beat Normal by this much

    # Annotation
    cheating_box_thickness: int = 3
    normal_box_thickness: int = 2
    font_scale: float = 0.55
    font_thickness: int = 2
    banner_font_scale: float = 0.70

    # Class definitions
    cheating_classes: list = field(default_factory=lambda: [
        "Bend Over The Desk",
        "Hand Under Table",
        "Look Around",
        "Normal",
        "Stand Up",
        "Wave",
        "phone",
    ])

    # Per-class minimum confidence to flag as suspicious.
    # Tuned to reduce false positives while keeping recall high.
    class_flag_thresholds: dict = field(default_factory=lambda: {
        "phone":              0.12,
        "Hand Under Table":   0.20,
        "Bend Over The Desk": 0.12,
        "Stand Up":           0.55,   # Very noisy — leaning looks like standing
        "Wave":               0.15,
        "Look Around":        0.18,
        "Normal":             0.00,   # Not used for flagging
    })

    @property
    def suspicious_classes(self) -> list[str]:
        return [c for c in self.cheating_classes if c != "Normal"]

    @property
    def output_path(self) -> Path:
        return Path(self.output_dir) / self.output_filename


# ──────────────────────────────────────────────────────────────────────────────
# DATA CLASSES
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class Detection:
    bbox: tuple[int, int, int, int]
    person_conf: float

@dataclass
class ClassificationResult:
    bbox: tuple[int, int, int, int]
    label: str
    confidence: float
    all_scores: dict[str, float]
    student_index: int = 0

    @property
    def is_suspicious(self) -> bool:
        return self.label != "Normal"


# ──────────────────────────────────────────────────────────────────────────────
# IMAGE ENHANCEMENT
# ──────────────────────────────────────────────────────────────────────────────
def enhance_cctv_image(img: np.ndarray) -> np.ndarray:
    """
    Perceptual enhancement for blurry/low-contrast CCTV footage.
    Pipeline: CLAHE on L channel → unsharp mask → gamma lift.
    """
    # CLAHE in LAB space (only lightness channel to avoid colour shifts)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    enhanced = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)

    # Unsharp mask — boosts high-frequency edge detail
    blurred = cv2.GaussianBlur(enhanced, (0, 0), sigmaX=2.0)
    enhanced = cv2.addWeighted(enhanced, 1.4, blurred, -0.4, 0)

    # Mild gamma lift to reveal shadow detail
    gamma = 1.15
    lut = np.clip(
        ((np.arange(256) / 255.0) ** (1.0 / gamma)) * 255, 0, 255
    ).astype(np.uint8)
    return cv2.LUT(enhanced, lut)


# ──────────────────────────────────────────────────────────────────────────────
# NON-MAXIMUM SUPPRESSION (pure PyTorch — no torchvision dependency)
# ──────────────────────────────────────────────────────────────────────────────
def nms_torch(
    boxes: torch.Tensor,
    scores: torch.Tensor,
    iou_threshold: float,
) -> list[int]:
    """Greedy NMS. Returns indices of kept boxes sorted by descending score."""
    x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    areas = (x2 - x1).clamp(min=0) * (y2 - y1).clamp(min=0)
    order = scores.argsort(descending=True)
    keep: list[int] = []

    while order.numel() > 0:
        i = order[0].item()
        keep.append(i)
        if order.numel() == 1:
            break
        rest = order[1:]

        inter_w = (torch.min(x2[i], x2[rest]) - torch.max(x1[i], x1[rest])).clamp(min=0)
        inter_h = (torch.min(y2[i], y2[rest]) - torch.max(y1[i], y1[rest])).clamp(min=0)
        inter   = inter_w * inter_h
        union   = areas[i] + areas[rest] - inter
        iou     = inter / union.clamp(min=1e-6)

        order = rest[iou <= iou_threshold]

    return keep


def iou_pair(b1: tuple, b2: tuple) -> float:
    """IoU between two (x1,y1,x2,y2) tuples."""
    ix1, iy1 = max(b1[0], b2[0]), max(b1[1], b2[1])
    ix2, iy2 = min(b1[2], b2[2]), min(b1[3], b2[3])
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    a1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
    a2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
    denom = a1 + a2 - inter
    return inter / denom if denom > 0 else 0.0


# ──────────────────────────────────────────────────────────────────────────────
# PERSON DETECTION — tiled + full-frame fusion
# ──────────────────────────────────────────────────────────────────────────────
def detect_persons(
    model: YOLO,
    img: np.ndarray,
    cfg: Config,
) -> list[Detection]:
    """
    Runs two complementary passes to handle both large and small persons:
      - Full-frame at high resolution (detects context-rich large persons)
      - 2×2 overlapping tiles (catches small/far persons missed at full scale)
    All boxes are merged with NMS then deduplicated.
    """
    h, w = img.shape[:2]
    all_boxes: list[list[int]] = []
    all_confs: list[float] = []

    # ── Full-frame pass ──────────────────────────────────────────────────────
    for result in model(img, conf=cfg.person_conf, classes=[0], imgsz=1280):
        for box in result.boxes:
            all_boxes.append(list(map(int, box.xyxy[0])))
            all_confs.append(float(box.conf[0]))

    # ── 2×2 Tiled pass ──────────────────────────────────────────────────────
    tile_h, tile_w = h // 2, w // 2
    overlap = 0.20
    step_h = int(tile_h * (1 - overlap))
    step_w = int(tile_w * (1 - overlap))

    for y0 in range(0, h - tile_h + 1, step_h):
        for x0 in range(0, w - tile_w + 1, step_w):
            tile = img[y0:y0 + tile_h, x0:x0 + tile_w]
            tile_resized = cv2.resize(tile, (640, 640))

            for result in model(tile_resized, conf=cfg.person_conf, classes=[0], imgsz=640):
                for box in result.boxes:
                    bx1, by1, bx2, by2 = box.xyxy[0].cpu().numpy()
                    sx, sy = tile_w / 640.0, tile_h / 640.0

                    ox1 = max(0, int(bx1 * sx + x0))
                    oy1 = max(0, int(by1 * sy + y0))
                    ox2 = min(w, int(bx2 * sx + x0))
                    oy2 = min(h, int(by2 * sy + y0))

                    all_boxes.append([ox1, oy1, ox2, oy2])
                    all_confs.append(float(box.conf[0]))

    if not all_boxes:
        return []

    boxes_t = torch.tensor(all_boxes, dtype=torch.float32)
    confs_t = torch.tensor(all_confs, dtype=torch.float32)
    keep_idx = nms_torch(boxes_t, confs_t, cfg.nms_iou)

    raw = [
        Detection(
            bbox=tuple(boxes_t[i].int().tolist()),
            person_conf=round(confs_t[i].item(), 3),
        )
        for i in keep_idx
    ]

    # ── Deduplication (tiled + full-frame can produce near-identical boxes) ──
    deduped: list[Detection] = []
    for det in raw:
        if all(iou_pair(det.bbox, d.bbox) <= cfg.dedup_iou for d in deduped):
            deduped.append(det)

    return deduped


# ──────────────────────────────────────────────────────────────────────────────
# SEATED FILTER
# ──────────────────────────────────────────────────────────────────────────────
def filter_seated(detections: list[Detection], cfg: Config) -> tuple[list[Detection], int]:
    """
    Removes tall/narrow bounding boxes that correspond to standing persons
    (teachers, proctors) rather than seated students.
    Returns (seated_list, skipped_count).
    """
    seated, skipped = [], 0
    for det in detections:
        x1, y1, x2, y2 = det.bbox
        bw = max(1, x2 - x1)
        bh = y2 - y1
        aspect = bh / bw
        if aspect > cfg.standing_aspect_ratio:
            log.debug("SKIP standing person @ %s  aspect=%.2f", det.bbox, aspect)
            skipped += 1
        else:
            seated.append(det)
    return seated, skipped


# ──────────────────────────────────────────────────────────────────────────────
# CLASSIFICATION
# ──────────────────────────────────────────────────────────────────────────────
def classify_person(
    model: YOLO,
    full_image: np.ndarray,
    bbox: tuple[int, int, int, int],
    cfg: Config,
) -> tuple[str, float, dict[str, float]]:
    """
    Crops the person with contextual padding, upscales tiny crops, enhances,
    and runs the cheating classifier.

    Decision logic
    ──────────────
    1. Collect the highest score per class across all detections in the crop.
    2. A suspicious class only qualifies if:
         score ≥ per-class threshold  AND  score ≥ Normal + margin
    3. If no class qualifies → "Normal".
    4. If multiple qualify → pick the one with the highest score.
    """
    h, w = full_image.shape[:2]
    x1, y1, x2, y2 = bbox
    bw, bh = x2 - x1, y2 - y1

    # Contextual padding so the model can see desk/hands/surroundings
    pad_x = int(bw * cfg.crop_pad_ratio)
    pad_y = int(bh * cfg.crop_pad_ratio)
    cx1, cy1 = max(0, x1 - pad_x), max(0, y1 - pad_y)
    cx2, cy2 = min(w, x2 + pad_x), min(h, y2 + pad_y)

    crop = full_image[cy1:cy2, cx1:cx2]
    if crop.size == 0:
        return "Normal", 0.0, {c: 0.0 for c in cfg.cheating_classes}

    # Upscale very small crops — below min_crop_size the model misses detail
    ch, cw = crop.shape[:2]
    if min(ch, cw) < cfg.min_crop_size:
        scale = cfg.min_crop_size / min(ch, cw)
        new_w, new_h = int(cw * scale), int(ch * scale)
        crop = cv2.resize(crop, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

    crop = enhance_cctv_image(crop)

    # Run classifier at very low conf to gather raw logits for all classes
    results = model(crop, conf=cfg.cheat_run_conf, imgsz=640)

    all_scores: dict[str, float] = {c: 0.0 for c in cfg.cheating_classes}
    for result in results:
        for box in result.boxes:
            cls_id   = int(box.cls[0])
            score    = float(box.conf[0])
            cls_name = cfg.cheating_classes[cls_id]
            if score > all_scores[cls_name]:
                all_scores[cls_name] = round(score, 3)

    normal_score = all_scores["Normal"]

    # Evaluate every suspicious class independently
    qualifying: list[tuple[str, float]] = []
    for cls in cfg.suspicious_classes:
        score     = all_scores[cls]
        threshold = cfg.class_flag_thresholds.get(cls, 0.25)
        if score >= threshold and score >= normal_score + cfg.margin_over_normal:
            qualifying.append((cls, score))

    if not qualifying:
        # Return the highest-scoring class name for transparency, even if Normal
        best = max(all_scores, key=all_scores.get)
        return "Normal", round(all_scores[best], 3), all_scores

    best_label, best_conf = max(qualifying, key=lambda x: x[1])
    return best_label, round(best_conf, 3), all_scores


# ──────────────────────────────────────────────────────────────────────────────
# DRAWING UTILITIES
# ──────────────────────────────────────────────────────────────────────────────
def draw_label(
    img: np.ndarray,
    text: str,
    pos: tuple[int, int],
    color: tuple[int, int, int],
    font_scale: float = 0.55,
    thickness: int = 2,
) -> None:
    """Draws a filled-background text label so it's readable on any background."""
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    x, y = pos
    cv2.rectangle(img, (x, y - th - 4), (x + tw + 8, y + baseline + 2), (20, 20, 20), cv2.FILLED)
    cv2.putText(img, text, (x + 4, y), font, font_scale, color, thickness, cv2.LINE_AA)


def draw_results(
    image: np.ndarray,
    results: list[ClassificationResult],
    cfg: Config,
) -> np.ndarray:
    """Annotates the image with bounding boxes, labels, and a summary banner."""
    out = image.copy()
    cheating_count = sum(1 for r in results if r.is_suspicious)

    for res in results:
        x1, y1, x2, y2 = res.bbox
        color     = (0, 60, 255) if res.is_suspicious else (0, 210, 0)
        thickness = cfg.cheating_box_thickness if res.is_suspicious else cfg.normal_box_thickness

        cv2.rectangle(out, (x1, y1), (x2, y2), color, thickness)

        label_text = f"#{res.student_index} {res.label} ({res.confidence:.2f})"
        draw_label(out, label_text, (x1, max(18, y1 - 18)), color,
                   cfg.font_scale, cfg.font_thickness)

    # Top-left summary banner
    banner = f"Students: {len(results)}  |  Suspicious: {cheating_count}"
    draw_label(out, banner, (10, 30), (255, 255, 255),
               cfg.banner_font_scale, cfg.font_thickness)

    return out


# ──────────────────────────────────────────────────────────────────────────────
# CONSOLE REPORT
# ──────────────────────────────────────────────────────────────────────────────
def print_report(results: list[ClassificationResult], cfg: Config) -> None:
    cheating_count = sum(1 for r in results if r.is_suspicious)
    sep = "═" * 62

    print(f"\n{sep}")
    print("  EXAM CHEATING DETECTION — FULL REPORT")
    print(sep)

    for res in results:
        flag = "  ⚠  SUSPICIOUS" if res.is_suspicious else ""
        print(f"\n  Student #{res.student_index}  bbox={res.bbox}{flag}")
        print(f"  {'─' * 48}")

        sorted_scores = sorted(
            [(k, res.all_scores.get(k, 0.0)) for k in cfg.cheating_classes],
            key=lambda x: (-x[1], x[0]),
        )
        for cls_name, score in sorted_scores:
            marker = " ◄ FLAGGED" if cls_name == res.label and res.is_suspicious else ""
            bar    = "█" * int(score * 30)
            print(f"    {cls_name:<24} {score:.3f}  {bar}{marker}")

    print(f"\n{sep}")
    print(f"  Total detected : {len(results)}")
    print(f"  Suspicious     : {cheating_count}")
    print(f"  Clean          : {len(results) - cheating_count}")
    print(sep + "\n")


# ──────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ──────────────────────────────────────────────────────────────────────────────
def run_on_image(
    image: np.ndarray,
    cfg: Optional[Config] = None,
    save_output: bool = False,
    output_path: Optional[Path] = None,
) -> tuple[list[ClassificationResult], np.ndarray]:
    """
    Run detection pipeline on an in-memory image.
    Returns (list of ClassificationResult, annotated image as numpy array).
    """
    cfg = cfg or Config()
    if save_output:
        Path(cfg.output_dir).mkdir(parents=True, exist_ok=True)

    h, w = image.shape[:2]
    log.info("Processing image (%dx%d)", w, h)

    # ── Enhance for detection ────────────────────────────────────────────────
    enhanced = enhance_cctv_image(image)

    # ── Load models ──────────────────────────────────────────────────────────
    log.info("Loading models …")
    person_model   = YOLO(cfg.person_model_path)
    cheating_model = YOLO(cfg.cheating_model_path)

    # ── Stage 1: Person detection ────────────────────────────────────────────
    t0 = time.perf_counter()
    log.info("Detecting persons …")
    persons = detect_persons(person_model, enhanced, cfg)
    log.info("Raw detections after NMS: %d  (%.2fs)", len(persons), time.perf_counter() - t0)

    seated, skipped = filter_seated(persons, cfg)
    log.info("Seated: %d  |  Standing (skipped): %d", len(seated), skipped)

    if not seated:
        log.warning("No seated persons detected — check thresholds or image.")
        annotated = draw_results(image, [], cfg)
        return [], annotated

    # ── Stage 2: Classify each student ──────────────────────────────────────
    log.info("Classifying %d students …", len(seated))
    t1 = time.perf_counter()
    results: list[ClassificationResult] = []

    for idx, det in enumerate(seated, start=1):
        label, conf, all_scores = classify_person(
            cheating_model, enhanced, det.bbox, cfg
        )
        results.append(ClassificationResult(
            bbox=det.bbox,
            label=label,
            confidence=conf,
            all_scores=all_scores,
            student_index=idx,
        ))
        status = "⚠ " + label if label != "Normal" else "✓  Normal"
        log.info("  #%02d  %s  (%.3f)", idx, status, conf)

    log.info("Classification done in %.2fs", time.perf_counter() - t1)

    # ── Stage 3: Annotate & optionally save ──────────────────────────────────
    annotated = draw_results(image, results, cfg)
    if save_output:
        out_path = output_path or cfg.output_path
        cv2.imwrite(str(out_path), annotated)
        log.info("Output saved: %s", out_path)

    # ── Stage 4: Report (console only when running as script) ─────────────────
    if save_output:
        print_report(results, cfg)

    return results, annotated


def run(cfg: Optional[Config] = None) -> list[ClassificationResult]:
    """Run detection from a file path (original CLI behavior)."""
    cfg = cfg or Config()
    Path(cfg.output_dir).mkdir(parents=True, exist_ok=True)

    image = cv2.imread(cfg.image_path)
    if image is None:
        log.error("Could not load image: %s", cfg.image_path)
        return []

    results, _ = run_on_image(
        image,
        cfg=cfg,
        save_output=True,
        output_path=cfg.output_path,
    )
    return results


# ──────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run()