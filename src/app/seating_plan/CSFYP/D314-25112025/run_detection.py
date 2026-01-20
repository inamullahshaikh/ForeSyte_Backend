"""
Quick runner script for cheating detection
"""

from detect_cheating import CheatingDetector
from pathlib import Path

def run_all_models():
    """Run detection with all available models and compare results"""
    script_dir = Path(__file__).parent
    # Navigate to foresyte root and find models directory
    models_dir = script_dir.parent.parent.parent.parent.parent.parent / "models"
    image_path = script_dir / "D314_frame_28m44s.jpg"
    seat_map_path = script_dir / "seat_map.json"
    
    # Model paths
    models = [
        ("best.pt", models_dir / "best.pt"),
        ("last.pt", models_dir / "last.pt"),
        ("yolov8n.pt", models_dir / "yolov8n.pt")
    ]
    
    results_comparison = {}
    
    for model_name, model_path in models:
        if not model_path.exists():
            print(f"[SKIP] Model not found: {model_path}")
            continue
        
        print(f"\n{'='*80}")
        print(f"Testing with {model_name}")
        print(f"{'='*80}\n")
        
        output_dir = script_dir / "processed" / "cheating_detection" / model_name.replace('.pt', '')
        
        try:
            detector = CheatingDetector(model_path=str(model_path))
            results = detector.detect_cheating_behaviors(
                image_path=str(image_path),
                seat_map_path=str(seat_map_path),
                output_dir=str(output_dir)
            )
            
            detector.print_report_summary(results['report'])
            
            results_comparison[model_name] = {
                'total_detections': results['report']['summary']['total_detections'],
                'people_detected': results['report']['summary']['people_detected'],
                'risk_score': results['report']['summary']['risk_score'],
                'assessment': results['report']['summary']['assessment'],
                'output_image': results['annotated_image_path']
            }
            
        except Exception as e:
            print(f"[ERROR] Failed with {model_name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Print comparison
    if len(results_comparison) > 1:
        print(f"\n{'='*80}")
        print("MODEL COMPARISON")
        print(f"{'='*80}")
        for model_name, result in results_comparison.items():
            print(f"\n{model_name}:")
            print(f"  Total Detections: {result['total_detections']}")
            print(f"  People Detected: {result['people_detected']}")
            print(f"  Risk Score: {result['risk_score']}")
            print(f"  Assessment: {result['assessment']}")
            print(f"  Output: {result['output_image']}")
        print(f"{'='*80}\n")


def run_best_model_only():
    """Run detection with the best available model"""
    script_dir = Path(__file__).parent
    image_path = script_dir / "D314_frame_28m44s.jpg"
    seat_map_path = script_dir / "seat_map.json"
    output_dir = script_dir / "processed" / "cheating_detection"
    
    print("Running cheating detection with best available model...")
    
    detector = CheatingDetector()  # Auto-selects best model
    results = detector.detect_cheating_behaviors(
        image_path=str(image_path),
        seat_map_path=str(seat_map_path),
        output_dir=str(output_dir)
    )
    
    detector.print_report_summary(results['report'])
    
    print(f"\nResults saved to: {output_dir}")
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--compare":
        print("Running comparison with all available models...\n")
        run_all_models()
    else:
        print("Running with best available model...")
        print("(Use --compare flag to test all models)\n")
        run_best_model_only()

