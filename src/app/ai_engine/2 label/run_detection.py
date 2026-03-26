from ultralytics import YOLO
import cv2
import numpy as np
import os
import torch

# -----------------------------
# CONFIG
# -----------------------------
IMAGE_PATH = "D314_frame_28m44s.jpg"

PERSON_MODEL = YOLO("yolov8l.pt")     # COCO person detector
CHEATING_MODEL = YOLO("best.pt")      # binary cheating model

OUTPUT_PATH = "output/final_detection.jpg"
os.makedirs("output", exist_ok=True)

# Binary class names (IMPORTANT: order must match training)
CHEATING_CLASSES = ["cheating", "not_cheating"]
CHEATING_CLASS_ID = 0
NOT_CHEATING_CLASS_ID = 1

# -----------------------------
# THRESHOLDS
# -----------------------------
PERSON_CONF = 0.40
NMS_IOU = 0.35

CHEATING_CONF = 0.1        # cheating must reach this
CONF_MARGIN = 0.15          # cheating must beat not_cheating by this

STANDING_ASPECT_RATIO = 2.2


# -----------------------------
# CCTV IMAGE ENHANCEMENT
# -----------------------------
def enhance_cctv_image(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)

    lab = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    blurred = cv2.GaussianBlur(enhanced, (0, 0), 2.0)
    enhanced = cv2.addWeighted(enhanced, 1.4, blurred, -0.4, 0)

    gamma = 1.15
    lut = np.clip(
        ((np.arange(256) / 255.0) ** (1.0 / gamma)) * 255,
        0, 255
    ).astype(np.uint8)

    return cv2.LUT(enhanced, lut)


# -----------------------------
# PURE PYTORCH NMS
# -----------------------------
def nms(boxes, scores, iou_threshold):
    x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    areas = (x2 - x1) * (y2 - y1)
    order = scores.argsort(descending=True)
    keep = []

    while order.numel() > 0:
        i = order[0].item()
        keep.append(i)
        if order.numel() == 1:
            break

        order = order[1:]
        xx1 = torch.max(x1[i], x1[order])
        yy1 = torch.max(y1[i], y1[order])
        xx2 = torch.min(x2[i], x2[order])
        yy2 = torch.min(y2[i], y2[order])

        inter = (xx2 - xx1).clamp(min=0) * (yy2 - yy1).clamp(min=0)
        iou = inter / (areas[i] + areas[order] - inter)

        order = order[iou <= iou_threshold]

    return keep


# -----------------------------
# PERSON DETECTION (FULL + TILED)
# -----------------------------
def detect_persons(model, img, conf=PERSON_CONF):
    h, w = img.shape[:2]
    all_boxes, all_confs = [], []

    # Full frame
    for r in model(img, conf=conf, classes=[0], imgsz=1280):
        for box in r.boxes:
            all_boxes.append(list(map(int, box.xyxy[0])))
            all_confs.append(float(box.conf[0]))

    # 2x2 tiled
    tile_h, tile_w = h // 2, w // 2
    overlap = 0.20
    step_h, step_w = int(tile_h * (1 - overlap)), int(tile_w * (1 - overlap))

    for y0 in range(0, h - tile_h + 1, step_h):
        for x0 in range(0, w - tile_w + 1, step_w):
            tile = img[y0:y0 + tile_h, x0:x0 + tile_w]
            tile_up = cv2.resize(tile, (640, 640))

            for r in model(tile_up, conf=conf, classes=[0], imgsz=640):
                for box in r.boxes:
                    bx1, by1, bx2, by2 = box.xyxy[0].cpu().numpy()
                    sx, sy = tile_w / 640, tile_h / 640

                    all_boxes.append([
                        int(bx1 * sx + x0),
                        int(by1 * sy + y0),
                        int(bx2 * sx + x0),
                        int(by2 * sy + y0)
                    ])
                    all_confs.append(float(box.conf[0]))

    if not all_boxes:
        return []

    boxes_t = torch.tensor(all_boxes, dtype=torch.float32)
    confs_t = torch.tensor(all_confs, dtype=torch.float32)
    keep = nms(boxes_t, confs_t, NMS_IOU)

    return [{"bbox": tuple(boxes_t[i].int().tolist())} for i in keep]


# -----------------------------
# BINARY CHEATING CLASSIFIER
# -----------------------------
def classify_person(model, full_image, bbox):
    h, w = full_image.shape[:2]
    x1, y1, x2, y2 = bbox
    bw, bh = x2 - x1, y2 - y1

    pad_x, pad_y = int(bw * 0.15), int(bh * 0.15)
    cx1, cy1 = max(0, x1 - pad_x), max(0, y1 - pad_y)
    cx2, cy2 = min(w, x2 + pad_x), min(h, y2 + pad_y)

    crop = full_image[cy1:cy2, cx1:cx2]
    if crop.size == 0:
        return "not_cheating", 0.0, {"cheating": 0.0, "not_cheating": 0.0}

    if min(crop.shape[:2]) < 200:
        scale = 200 / min(crop.shape[:2])
        crop = cv2.resize(
            crop,
            (int(crop.shape[1] * scale), int(crop.shape[0] * scale)),
            interpolation=cv2.INTER_LANCZOS4
        )

    crop = enhance_cctv_image(crop)

    results = model(crop, conf=0.01, imgsz=640)

    scores = {"cheating": 0.0, "not_cheating": 0.0}
    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            scores[CHEATING_CLASSES[cls_id]] = max(
                scores[CHEATING_CLASSES[cls_id]],
                round(conf, 3)
            )

    if scores["cheating"] >= CHEATING_CONF and \
       scores["cheating"] >= scores["not_cheating"] + CONF_MARGIN:
        return "cheating", round(scores["cheating"], 2), scores

    return "not_cheating", round(scores["cheating"], 2), scores


# -----------------------------
# DRAW LABEL
# -----------------------------
def draw_label(img, text, pos, color):
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
    x, y = pos
    cv2.rectangle(img, (x, y - th - 4), (x + tw + 6, y + 2), (0, 0, 0), -1)
    cv2.putText(img, text, (x + 3, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)


# -----------------------------
# MAIN
# -----------------------------
def main():
    image = cv2.imread(IMAGE_PATH)
    if image is None:
        print("[ERROR] Image not found")
        return

    enhanced = enhance_cctv_image(image)

    print("[INFO] Detecting persons...")
    persons = detect_persons(PERSON_MODEL, enhanced)

    seated = []
    for p in persons:
        x1, y1, x2, y2 = p["bbox"]
        aspect = (y2 - y1) / max(1, (x2 - x1))
        if aspect <= STANDING_ASPECT_RATIO:
            seated.append(p)

    print(f"[INFO] Seated students: {len(seated)}")

    output = image.copy()
    cheating_count = 0

    for i, p in enumerate(seated, 1):
        label, conf, scores = classify_person(
            CHEATING_MODEL, enhanced, p["bbox"]
        )

        is_cheating = label == "cheating"
        if is_cheating:
            cheating_count += 1

        color = (0, 0, 255) if is_cheating else (0, 220, 0)
        x1, y1, x2, y2 = p["bbox"]

        cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
        draw_label(output, f"#{i} {label} ({conf})", (x1, y1 - 8), color)

    draw_label(
        output,
        f"Students: {len(seated)} | Cheating: {cheating_count}",
        (10, 30),
        (255, 255, 255)
    )

    cv2.imwrite(OUTPUT_PATH, output)
    print(f"[INFO] Output saved → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
