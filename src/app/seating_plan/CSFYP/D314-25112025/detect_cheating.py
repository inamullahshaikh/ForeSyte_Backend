"""
Cheating Detection Script using YOLOv8 Models
Analyzes classroom footage for suspicious behaviors and activities
"""

import cv2
import json
import os
from pathlib import Path
from datetime import datetime
from ultralytics import YOLO
import numpy as np
from typing import Dict, List, Tuple, Any

class CheatingDetector:
    """
    Detects cheating behaviors in exam footage using YOLO models
    """
    
    def __init__(self, model_path: str = None):
        """
        Initialize the cheating detector
        
        Args:
            model_path: Path to the YOLO model. If None, tries to load best.pt, then last.pt, then yolov8n.pt
        """
        # Models are in the same directory as this script
        self.models_dir = Path(__file__).parent
        
        # Try to load the best available model
        if model_path and Path(model_path).exists():
            print(f"Loading specified model: {model_path}")
            self.model = YOLO(model_path)
            self.model_name = Path(model_path).stem
        else:
            # Try best.pt first (likely fine-tuned for cheating detection)
            model_candidates = [
                self.models_dir / "best.pt",
                self.models_dir / "last.pt", 
                self.models_dir / "yolov8n.pt"
            ]
            
            self.model = None
            for model_path in model_candidates:
                if model_path.exists():
                    print(f"Loading model: {model_path}")
                    self.model = YOLO(str(model_path))
                    self.model_name = model_path.stem
                    break
            
            if self.model is None:
                raise FileNotFoundError(
                    f"No YOLO models found in {self.models_dir}. "
                    f"Please ensure best.pt, last.pt, or yolov8n.pt exists."
                )
        
        print(f"Model loaded successfully: {self.model_name}")
        print(f"Model classes: {self.model.names}")
        
        # Define severity mapping based on model classes
        # Custom model classes: Bend Over The Desk, Hand Under Table, Look Around, Normal, Stand Up, Wave, phone
        self.behavior_severity = {
            'phone': 'high',
            'stand up': 'high',
            'bend over the desk': 'medium',
            'hand under table': 'high',
            'wave': 'medium',
            'look around': 'medium',
            'normal': 'low',
            # Generic COCO classes
            'cell phone': 'high',
            'mobile': 'high',
            'book': 'medium',
            'paper': 'medium',
            'bottle': 'low',
            'backpack': 'medium',
            'handbag': 'medium',
        }
        
        # Detection thresholds - Lowered for blurry images and better detection
        self.confidence_threshold = 0.15  # Lower threshold for more detections
        self.iou_threshold = 0.40         # Lower IOU for more overlapping detections
        
    def load_seat_map(self, seat_map_path: str) -> Dict:
        """Load seat map JSON with coordinates"""
        if not Path(seat_map_path).exists():
            print(f"Warning: Seat map not found at {seat_map_path}")
            return {"seats": {}}
        
        with open(seat_map_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def point_in_polygon(self, point: Tuple[float, float], polygon: List[List[float]]) -> bool:
        """Check if a point is inside a polygon using ray casting algorithm"""
        x, y = point
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def map_detection_to_seat(self, bbox: Tuple[int, int, int, int], 
                             seat_map: Dict) -> str:
        """
        Map a detection bounding box to a seat using seat coordinates
        
        Args:
            bbox: Bounding box (x1, y1, x2, y2)
            seat_map: Dictionary with seat coordinates
            
        Returns:
            Seat ID or "unknown"
        """
        x1, y1, x2, y2 = bbox
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        
        seats = seat_map.get('seats', {})
        
        for seat_id, coordinates in seats.items():
            if not coordinates or len(coordinates) < 3:
                continue
            
            # Convert to proper format
            polygon = [[float(coord[0]), float(coord[1])] for coord in coordinates]
            
            if self.point_in_polygon((center_x, center_y), polygon):
                return seat_id.replace('seat_', '')
        
        return "unknown"
    
    def enhance_image_for_detection(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image quality for better detection, especially for blurry images
        
        Args:
            image: Input image
            
        Returns:
            Enhanced image
        """
        # Apply sharpening filter for blurry images
        kernel = np.array([[-1,-1,-1],
                          [-1, 9,-1],
                          [-1,-1,-1]])
        sharpened = cv2.filter2D(image, -1, kernel)
        
        # Enhance contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
        lab = cv2.cvtColor(sharpened, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        # Denoise slightly to reduce artifacts
        enhanced = cv2.fastNlMeansDenoisingColored(enhanced, None, 10, 10, 7, 21)
        
        return enhanced
    
    def analyze_posture(self, person_bbox: Tuple[int, int, int, int], 
                       frame_height: int) -> Tuple[str, str]:
        """
        Analyze student posture based on bounding box characteristics
        
        Returns:
            (behavior_type, severity_level)
        """
        x1, y1, x2, y2 = person_bbox
        bbox_height = y2 - y1
        bbox_width = x2 - x1
        aspect_ratio = bbox_height / bbox_width if bbox_width > 0 else 0
        
        # Analyze vertical position (head position)
        head_position_ratio = y1 / frame_height
        
        behaviors = []
        
        # Bending down (head very low)
        if head_position_ratio > 0.6:
            behaviors.append(("bending_over_desk", "medium"))
        
        # Unusual aspect ratio (turned sideways, looking at neighbor)
        if aspect_ratio < 1.5:
            behaviors.append(("turned_sideways", "medium"))
        
        # Standing up (very tall bbox relative to frame)
        if bbox_height > frame_height * 0.7:
            behaviors.append(("standing_up", "high"))
        
        return behaviors if behaviors else [("normal_posture", "low")]
    
    def detect_cheating_behaviors(self, image_path: str, 
                                  seat_map_path: str = None,
                                  output_dir: str = None) -> Dict[str, Any]:
        """
        Main detection method - analyzes image for cheating behaviors
        
        Args:
            image_path: Path to the image to analyze
            seat_map_path: Path to seat map JSON (optional)
            output_dir: Directory to save annotated output (optional)
            
        Returns:
            Dictionary with detection results
        """
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        orig_image = image.copy()
        height, width = image.shape[:2]
        
        print(f"Analyzing image: {image_path}")
        print(f"Image size: {width}x{height}")
        
        # Enhance image for better detection (especially for blurry images)
        print("Enhancing image quality for detection...")
        enhanced_image = self.enhance_image_for_detection(image)
        print("Image enhancement complete")
        
        # Load seat map if provided
        seat_map = {}
        if seat_map_path and Path(seat_map_path).exists():
            seat_map = self.load_seat_map(seat_map_path)
            print(f"Loaded seat map with {len(seat_map.get('seats', {}))} seats")
        
        # Run YOLO detection on enhanced image
        print("Running YOLO detection...")
        results = self.model.predict(
            enhanced_image,  # Use enhanced image for detection
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            verbose=False
        )
        
        # Process detections
        detections = []
        people_count = 0
        suspicious_objects = []
        behavior_detections = []
        
        for result in results:
            boxes = result.boxes
            
            for box in boxes:
                # Get box coordinates
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = self.model.names[class_id]
                class_lower = class_name.lower()
                
                bbox = (int(x1), int(y1), int(x2), int(y2))
                
                # Map to seat
                seat_id = self.map_detection_to_seat(bbox, seat_map) if seat_map else "unknown"
                
                # Check if it's a behavior class from custom model
                if class_lower in self.behavior_severity:
                    severity = self.behavior_severity[class_lower]
                    
                    # Count as person if not 'normal'
                    if class_lower != 'normal':
                        people_count += 1
                        behavior_detections.append(class_name)
                    
                    detection = {
                        'type': 'behavior',
                        'class': class_name,
                        'confidence': confidence,
                        'bbox': bbox,
                        'seat_id': seat_id,
                        'behavior': class_lower.replace(' ', '_'),
                        'severity': severity,
                        'color': self._get_severity_color(severity)
                    }
                    detections.append(detection)
                
                # Standard person detection from COCO
                elif class_lower in ['person', 'student', 'people']:
                    people_count += 1
                    
                    # Analyze posture
                    posture_behaviors = self.analyze_posture(bbox, height)
                    
                    for behavior, severity in posture_behaviors:
                        detection = {
                            'type': 'person',
                            'class': class_name,
                            'confidence': confidence,
                            'bbox': bbox,
                            'seat_id': seat_id,
                            'behavior': behavior,
                            'severity': severity,
                            'color': self._get_severity_color(severity)
                        }
                        detections.append(detection)
                
                # Check for suspicious objects
                elif class_lower in self.behavior_severity:
                    severity = self.behavior_severity[class_lower]
                    
                    detection = {
                        'type': 'object',
                        'class': class_name,
                        'confidence': confidence,
                        'bbox': bbox,
                        'seat_id': seat_id,
                        'behavior': f'suspicious_object_{class_lower.replace(" ", "_")}',
                        'severity': severity,
                        'color': self._get_severity_color(severity)
                    }
                    detections.append(detection)
                    suspicious_objects.append(class_name)
        
        # Draw annotations
        annotated_image = self._draw_detections(orig_image, detections, seat_map)
        
        # Save annotated image
        if output_dir:
            output_path = self._save_annotated_image(annotated_image, image_path, output_dir)
        else:
            output_path = None
        
        # Generate report (include behavior_detections if it exists, else empty list)
        behavior_list = behavior_detections if 'behavior_detections' in locals() else []
        report = self._generate_report(detections, people_count, suspicious_objects, image_path, behavior_list)
        
        # Save report
        if output_dir:
            report_path = self._save_report(report, image_path, output_dir)
        else:
            report_path = None
        
        return {
            'detections': detections,
            'people_count': people_count,
            'suspicious_objects': suspicious_objects,
            'report': report,
            'annotated_image_path': output_path,
            'report_path': report_path
        }
    
    def _get_severity_color(self, severity: str) -> Tuple[int, int, int]:
        """Get BGR color for severity level"""
        colors = {
            'low': (0, 255, 0),      # Green
            'medium': (0, 165, 255),  # Orange
            'high': (0, 0, 255)       # Red
        }
        return colors.get(severity, (255, 255, 255))
    
    def _draw_detections(self, image: np.ndarray, detections: List[Dict], 
                        seat_map: Dict) -> np.ndarray:
        """Draw bounding boxes and labels on image"""
        annotated = image.copy()
        
        # Draw seat polygons first (semi-transparent)
        if seat_map and 'seats' in seat_map:
            overlay = annotated.copy()
            for seat_id, coordinates in seat_map['seats'].items():
                if coordinates and len(coordinates) >= 3:
                    points = np.array([[int(c[0]), int(c[1])] for c in coordinates], np.int32)
                    cv2.polylines(overlay, [points], True, (200, 200, 200), 2)
                    
                    # Draw seat label
                    center_x = int(sum(p[0] for p in coordinates) / len(coordinates))
                    center_y = int(sum(p[1] for p in coordinates) / len(coordinates))
                    label = seat_id.replace('seat_', '')
                    cv2.putText(overlay, label, (center_x - 20, center_y), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 2)
            
            # Blend overlay
            cv2.addWeighted(overlay, 0.3, annotated, 0.7, 0, annotated)
        
        # Draw detections
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            color = det['color']
            
            # Draw bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            # Prepare label
            label = f"{det['class']} {det['confidence']:.2f}"
            if det['seat_id'] != 'unknown':
                label += f" | Seat: {det['seat_id']}"
            if det['behavior'] != 'normal_posture':
                label += f" | {det['behavior'].replace('_', ' ').title()}"
            
            # Draw label background
            (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, y1 - label_h - 10), (x1 + label_w, y1), color, -1)
            
            # Draw label text
            cv2.putText(annotated, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Add summary info
        summary = f"Detections: {len(detections)} | Model: {self.model_name}"
        cv2.putText(annotated, summary, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        return annotated
    
    def _save_annotated_image(self, image: np.ndarray, original_path: str, 
                             output_dir: str) -> str:
        """Save annotated image"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        original_name = Path(original_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"{original_name}_cheating_detection_{timestamp}.jpg"
        
        cv2.imwrite(str(output_path), image)
        print(f"Saved annotated image: {output_path}")
        
        return str(output_path)
    
    def _generate_report(self, detections: List[Dict], people_count: int,
                        suspicious_objects: List[str], image_path: str,
                        behavior_detections: List[str] = None) -> Dict:
        """Generate detection report"""
        # Count by severity
        severity_counts = {'low': 0, 'medium': 0, 'high': 0}
        behavior_counts = {}
        seat_violations = {}
        
        for det in detections:
            severity = det['severity']
            severity_counts[severity] += 1
            
            behavior = det['behavior']
            behavior_counts[behavior] = behavior_counts.get(behavior, 0) + 1
            
            seat_id = det['seat_id']
            if seat_id != 'unknown':
                if seat_id not in seat_violations:
                    seat_violations[seat_id] = []
                seat_violations[seat_id].append({
                    'behavior': behavior,
                    'severity': severity,
                    'confidence': det['confidence']
                })
        
        # Calculate risk score
        risk_score = (
            severity_counts['low'] * 1 +
            severity_counts['medium'] * 3 +
            severity_counts['high'] * 5
        )
        
        # Determine overall assessment
        if risk_score == 0:
            assessment = "No suspicious activity detected"
        elif risk_score < 5:
            assessment = "Low risk - Minor issues detected"
        elif risk_score < 15:
            assessment = "Medium risk - Multiple suspicious behaviors"
        else:
            assessment = "High risk - Serious violations detected"
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'image_analyzed': image_path,
            'model_used': self.model_name,
            'summary': {
                'total_detections': len(detections),
                'people_detected': people_count,
                'suspicious_objects': len(suspicious_objects),
                'behaviors_detected': len(behavior_detections) if behavior_detections else 0,
                'risk_score': risk_score,
                'assessment': assessment
            },
            'severity_breakdown': severity_counts,
            'behavior_counts': behavior_counts,
            'behavior_detections': behavior_detections if behavior_detections else [],
            'seat_violations': seat_violations,
            'all_detections': detections
        }
        
        return report
    
    def _save_report(self, report: Dict, original_path: str, output_dir: str) -> str:
        """Save report as JSON"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        original_name = Path(original_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"{original_name}_report_{timestamp}.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"Saved report: {report_path}")
        
        return str(report_path)
    
    def print_report_summary(self, report: Dict):
        """Print a formatted summary of the detection report"""
        print("\n" + "="*80)
        print("CHEATING DETECTION REPORT")
        print("="*80)
        print(f"Timestamp: {report['timestamp']}")
        print(f"Image: {Path(report['image_analyzed']).name}")
        print(f"Model: {report['model_used']}")
        print("-"*80)
        print("SUMMARY:")
        summary = report['summary']
        print(f"  Total Detections: {summary['total_detections']}")
        print(f"  People Detected: {summary['people_detected']}")
        print(f"  Suspicious Objects: {summary['suspicious_objects']}")
        print(f"  Risk Score: {summary['risk_score']}")
        print(f"  Assessment: {summary['assessment']}")
        print("-"*80)
        print("SEVERITY BREAKDOWN:")
        for severity, count in report['severity_breakdown'].items():
            print(f"  {severity.upper()}: {count}")
        print("-"*80)
        print("BEHAVIOR COUNTS:")
        for behavior, count in sorted(report['behavior_counts'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {behavior.replace('_', ' ').title()}: {count}")
        
        if report['seat_violations']:
            print("-"*80)
            print("SEAT-SPECIFIC VIOLATIONS:")
            for seat_id, violations in sorted(report['seat_violations'].items()):
                print(f"  Seat {seat_id}:")
                for v in violations:
                    print(f"    - {v['behavior'].replace('_', ' ').title()} "
                          f"[{v['severity'].upper()}] (conf: {v['confidence']:.2f})")
        
        print("="*80 + "\n")


def main():
    """Main execution function"""
    # Setup paths
    script_dir = Path(__file__).parent
    image_path = script_dir / "D314_frame_28m44s.jpg"
    seat_map_path = script_dir / "seat_map.json"
    output_dir = script_dir / "processed" / "cheating_detection"
    
    # Verify image exists
    if not image_path.exists():
        print(f"Error: Image not found at {image_path}")
        return
    
    # Initialize detector
    try:
        detector = CheatingDetector()
    except Exception as e:
        print(f"Error initializing detector: {e}")
        return
    
    # Run detection
    print("\nStarting cheating detection analysis...")
    try:
        results = detector.detect_cheating_behaviors(
            image_path=str(image_path),
            seat_map_path=str(seat_map_path) if seat_map_path.exists() else None,
            output_dir=str(output_dir)
        )
        
        # Print report summary
        detector.print_report_summary(results['report'])
        
        print(f"\nAnalysis complete!")
        print(f"Annotated image saved to: {results['annotated_image_path']}")
        print(f"Full report saved to: {results['report_path']}")
        
    except Exception as e:
        print(f"Error during detection: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

