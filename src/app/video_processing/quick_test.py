"""
Quick Test Script for Video Processing Module
Simple script to test video processing without API server
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.video_processing.processor import VideoProcessor
from app.video_processing.stream_handler import VideoStreamHandler


async def test_video_processing(video_path: str):
    """
    Test video processing with a video file
    
    Args:
        video_path: Path to video file to process
    """
    print("=" * 60)
    print("Video Processing Quick Test")
    print("=" * 60)
    print(f"\n📹 Video: {video_path}")
    
    # Check if file exists
    if not Path(video_path).exists():
        print(f"❌ Error: Video file not found: {video_path}")
        print("\nPlease provide a valid video file path.")
        return
    
    # Step 1: Validate video
    print("\n[1/4] Validating video...")
    handler = VideoStreamHandler()
    validation = handler.validate_video_input(video_path, "recorded")
    
    if not validation['valid']:
        print(f"❌ Validation failed: {validation.get('error')}")
        return
    
    print(f"✅ Video is valid!")
    print(f"   - FPS: {validation['fps']:.2f}")
    print(f"   - Resolution: {validation['width']}x{validation['height']}")
    print(f"   - Duration: {validation['duration']:.2f} seconds")
    print(f"   - Total frames: {validation['frame_count']}")
    
    # Step 2: Process video
    print("\n[2/4] Processing video...")
    processor = VideoProcessor(db_session=None, enable_ai=False)
    
    stream_id = "quick-test-001"
    exam_id = "test-exam-001"
    room_id = "test-room-001"
    
    print("   Processing frames (this may take a moment)...")
    results = await processor.process_video_stream(
        stream_id=stream_id,
        source=video_path,
        stream_type="recorded",
        exam_id=exam_id,
        room_id=room_id,
        seat_mapping={}
    )
    
    if not results.get('success'):
        print(f"❌ Processing failed: {results.get('error')}")
        return
    
    print("✅ Processing completed!")
    
    # Step 3: Show results
    print("\n[3/4] Processing Results:")
    print(f"   - Total frames processed: {results.get('total_frames_processed', 0)}")
    print(f"   - Activities logged: {len(results.get('activities_logged', []))}")
    print(f"   - Violations detected: {len(results.get('violations_detected', []))}")
    print(f"   - Frame analyses: {len(results.get('frame_analysis', []))}")
    
    # Show frame extraction info
    frame_analysis = results.get('frame_analysis', [])
    if frame_analysis:
        print(f"\n   Sample frames extracted:")
        for frame in frame_analysis[:3]:
            frame_path = frame.get('frame_path', 'N/A')
            frame_num = frame.get('frame_number', 'N/A')
            print(f"     - Frame #{frame_num}: {Path(frame_path).name if frame_path != 'N/A' else 'N/A'}")
    
    # Step 4: Generate report
    print("\n[4/4] Generating report...")
    report = processor.generate_report(stream_id, report_format='json')
    
    if report.get('success') is not False:
        print(f"✅ Report generated!")
        print(f"   - Report ID: {report.get('report_id')}")
        print(f"   - Report path: {report.get('report_path')}")
        print(f"   - Total activities: {report.get('activities_summary', {}).get('total_activities', 0)}")
        print(f"   - Total violations: {report.get('violations_summary', {}).get('total_violations', 0)}")
    else:
        print(f"⚠️  Report generation skipped: {report.get('error')}")
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ Test Completed Successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Check extracted frames in: uploads/frames/")
    print("  2. Check report in: uploads/reports/")
    print("  3. Use FastAPI server for production: uvicorn main:app --reload")
    print("\nFor more info, see: HOW_TO_RUN.md")


def main():
    """Main entry point"""
    print("\n" + "=" * 60)
    print("Video Processing Module - Quick Test")
    print("=" * 60)
    
    # Get video path from command line or use default
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        # Try common test video locations
        possible_paths = [
            "input.mp4",
            "test_video.mp4",
            "../test_video.mp4",
            "../../test_video.mp4",
            "Cheat-1.mp4",
            "../Cheat-1.mp4",
        ]
        
        video_path = None
        for path in possible_paths:
            if Path(path).exists():
                video_path = path
                break
        
        if not video_path:
            print("\n❌ No video file provided!")
            print("\nUsage:")
            print("  python quick_test.py <path_to_video>")
            print("\nExample:")
            print("  python quick_test.py ../test_video.mp4")
            print("  python quick_test.py C:/Videos/exam_recording.mp4")
            return
    
    # Run async test
    try:
        asyncio.run(test_video_processing(video_path))
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

