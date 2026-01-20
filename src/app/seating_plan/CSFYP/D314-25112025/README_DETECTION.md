# Cheating Detection for D314 Classroom

This directory contains scripts for detecting cheating behaviors in exam footage using YOLOv8 models.

## Files

- `D314_frame_28m44s.jpg` - Extracted frame from exam video at 28:44
- `D314.mp4` - Full exam video
- `seat_map.json` - Seat coordinates for the classroom
- `extract_frame.py` - Script to extract frames from video
- `detect_cheating.py` - Main cheating detection module
- `run_detection.py` - Quick runner script

## Available Models

The system will automatically use the best available model from the `models` directory:

1. **best.pt** - Fine-tuned model (highest priority)
2. **last.pt** - Last checkpoint from training
3. **yolov8n.pt** - Base YOLOv8 nano model

## Setup

Install required dependencies:

```bash
pip install ultralytics opencv-python numpy
```

## Usage

### Quick Detection (Best Model)

Run detection with the best available model:

```bash
cd D314-25112025
python run_detection.py
```

### Compare All Models

Test all available models and compare results:

```bash
python run_detection.py --compare
```

### Using the Detection Module Directly

```python
from detect_cheating import CheatingDetector
from pathlib import Path

# Initialize detector
detector = CheatingDetector()

# Run detection
results = detector.detect_cheating_behaviors(
    image_path="D314_frame_28m44s.jpg",
    seat_map_path="seat_map.json",
    output_dir="processed/cheating_detection"
)

# Print report
detector.print_report_summary(results['report'])
```

### Use Specific Model

```python
detector = CheatingDetector(model_path="path/to/best.pt")
```

## Detection Capabilities

### Suspicious Objects Detected
- **High Risk**: Phone, cell phone, mobile
- **Medium Risk**: Book, paper, backpack, handbag
- **Low Risk**: Bottle

### Posture Analysis
- **Bending over desk** (Medium risk)
- **Turned sideways** (Medium risk - looking at neighbor)
- **Standing up** (High risk)

### Output

The script generates:

1. **Annotated Image** - Visual representation with:
   - Bounding boxes around detections
   - Seat polygons overlay
   - Labels with confidence scores
   - Seat mappings
   - Behavior classifications

2. **JSON Report** containing:
   - Total detections count
   - People detected
   - Suspicious objects found
   - Risk score calculation
   - Seat-specific violations
   - Severity breakdown (Low/Medium/High)
   - Detailed behavior counts

### Report Structure

```json
{
  "timestamp": "2025-01-15T12:34:56",
  "image_analyzed": "D314_frame_28m44s.jpg",
  "model_used": "best",
  "summary": {
    "total_detections": 45,
    "people_detected": 42,
    "suspicious_objects": 3,
    "risk_score": 15,
    "assessment": "Medium risk - Multiple suspicious behaviors"
  },
  "severity_breakdown": {
    "low": 5,
    "medium": 8,
    "high": 2
  },
  "behavior_counts": {
    "normal_posture": 35,
    "bending_over_desk": 5,
    "turned_sideways": 3,
    "suspicious_object_phone": 2
  },
  "seat_violations": {
    "c3r4": [
      {
        "behavior": "suspicious_object_phone",
        "severity": "high",
        "confidence": 0.87
      }
    ]
  }
}
```

## Risk Scoring

The system calculates a risk score based on:
- Low severity: 1 point each
- Medium severity: 3 points each
- High severity: 5 points each

**Assessment Categories:**
- 0 points: No suspicious activity
- 1-4 points: Low risk - Minor issues
- 5-14 points: Medium risk - Multiple suspicious behaviors
- 15+ points: High risk - Serious violations

## Seat Mapping

Detections are automatically mapped to specific seats using the polygon coordinates in `seat_map.json`. The system uses a ray-casting algorithm to determine which seat each detection belongs to based on the bounding box center point.

## Output Location

All outputs are saved to:
```
processed/cheating_detection/
├── D314_frame_28m44s_cheating_detection_TIMESTAMP.jpg
└── D314_frame_28m44s_report_TIMESTAMP.json
```

When comparing models, outputs are organized by model:
```
processed/cheating_detection/
├── best/
│   ├── D314_frame_28m44s_cheating_detection_TIMESTAMP.jpg
│   └── D314_frame_28m44s_report_TIMESTAMP.json
├── last/
└── yolov8n/
```

## Examples

### Example 1: Basic Detection
```bash
python run_detection.py
```

### Example 2: Compare Models
```bash
python run_detection.py --compare
```

### Example 3: Custom Script
```python
from detect_cheating import CheatingDetector

detector = CheatingDetector(model_path="../../../../../../models/best.pt")
results = detector.detect_cheating_behaviors(
    image_path="D314_frame_28m44s.jpg",
    seat_map_path="seat_map.json",
    output_dir="custom_output"
)

print(f"Risk Score: {results['report']['summary']['risk_score']}")
print(f"Assessment: {results['report']['summary']['assessment']}")
```

## Troubleshooting

### Model Not Found
If you see "No YOLO models found", ensure at least one model file exists in the `models` directory:
- `d:/foresyte/models/best.pt`
- `d:/foresyte/models/last.pt`
- `d:/foresyte/models/yolov8n.pt`

### Import Error
Install ultralytics:
```bash
pip install ultralytics
```

### Seat Mapping Issues
Verify `seat_map.json` exists and contains valid polygon coordinates. The script will still run without seat mapping but won't show seat-specific violations.

