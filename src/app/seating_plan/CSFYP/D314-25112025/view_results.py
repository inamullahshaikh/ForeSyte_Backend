"""
Quick viewer for detection results
"""

import cv2
from pathlib import Path
import json

def view_detection_results(model_name="best"):
    """
    Display the detection results for a specific model
    
    Args:
        model_name: Name of model (best, last, or yolov8n)
    """
    script_dir = Path(__file__).parent
    detection_dir = script_dir / "processed" / "cheating_detection" / model_name
    
    # Find the most recent detection image
    images = list(detection_dir.glob("D314_frame_*_cheating_detection_*.jpg"))
    reports = list(detection_dir.glob("D314_frame_*_report_*.json"))
    
    if not images:
        print(f"No detection results found for model: {model_name}")
        print(f"Looked in: {detection_dir}")
        return
    
    # Get the most recent files
    image_path = sorted(images)[-1]
    report_path = sorted(reports)[-1]
    
    print(f"Loading detection results for {model_name} model...")
    print(f"Image: {image_path.name}")
    print(f"Report: {report_path.name}")
    
    # Load and display the report
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    print("\n" + "="*80)
    print(f"DETECTION SUMMARY - {model_name.upper()} MODEL")
    print("="*80)
    print(f"Timestamp: {report['timestamp']}")
    print(f"\nSummary:")
    for key, value in report['summary'].items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    print(f"\nSeverity Breakdown:")
    for severity, count in report['severity_breakdown'].items():
        print(f"  {severity.upper()}: {count}")
    
    print(f"\nBehavior Counts:")
    for behavior, count in sorted(report['behavior_counts'].items(), 
                                  key=lambda x: x[1], reverse=True):
        print(f"  {behavior.replace('_', ' ').title()}: {count}")
    
    if report.get('seat_violations'):
        print(f"\nSeat Violations:")
        for seat, violations in sorted(report['seat_violations'].items()):
            print(f"  {seat}:")
            for v in violations:
                print(f"    - {v['behavior'].replace('_', ' ').title()} "
                     f"[{v['severity'].upper()}] (conf: {v['confidence']:.2%})")
    
    print("="*80)
    
    # Load and display the image
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"Error: Could not load image from {image_path}")
        return
    
    # Resize if too large for display
    height, width = image.shape[:2]
    max_width = 1280
    if width > max_width:
        scale = max_width / width
        new_width = max_width
        new_height = int(height * scale)
        image = cv2.resize(image, (new_width, new_height))
    
    # Display the image
    window_name = f"Cheating Detection Results - {model_name.upper()} Model"
    cv2.imshow(window_name, image)
    
    print(f"\nDisplaying annotated image...")
    print("Press any key to close the window")
    
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def view_all_models():
    """Display results from all models one by one"""
    models = ["best", "last", "yolov8n"]
    
    for model in models:
        print(f"\n{'='*80}")
        print(f"Viewing results for {model.upper()} model")
        print(f"{'='*80}\n")
        
        try:
            view_detection_results(model)
            print(f"\n{model.upper()} model viewing complete.")
            input("Press Enter to continue to next model...")
        except Exception as e:
            print(f"Error viewing {model}: {e}")
            continue


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        model_name = sys.argv[1].lower()
        if model_name == "--all":
            view_all_models()
        elif model_name in ["best", "last", "yolov8n"]:
            view_detection_results(model_name)
        else:
            print(f"Unknown model: {model_name}")
            print("Available models: best, last, yolov8n")
            print("Or use --all to view all models")
    else:
        # Default: show best model
        view_detection_results("best")

