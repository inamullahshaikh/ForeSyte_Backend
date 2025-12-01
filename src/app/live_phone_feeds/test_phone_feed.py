"""
Test Script for Phone Feed Processing
Tests live video feed from phone
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.live_phone_feeds.phone_stream_receiver import PhoneStreamReceiver, PhoneStreamHelper
from app.live_phone_feeds.phone_processor import PhoneFeedProcessor


async def test_phone_connection(stream_url: str):
    """Test connection to phone stream"""
    print("=" * 60)
    print("Phone Stream Connection Test")
    print("=" * 60)
    print(f"\n📱 Testing connection to: {stream_url}\n")
    
    receiver = PhoneStreamReceiver()
    result = receiver.connect_to_phone_stream(stream_url)
    
    if result.get("success"):
        print("✅ Connection successful!")
        print(f"   Resolution: {result['width']}x{result['height']}")
        print(f"   FPS: {result.get('fps', 'unknown')}")
        print(f"   Connected at: {result.get('connected_at')}")
        return True
    else:
        print("❌ Connection failed!")
        print(f"   Error: {result.get('error')}")
        
        suggestions = result.get('suggestions', [])
        if suggestions:
            print("\n💡 Suggestions:")
            for suggestion in suggestions:
                print(f"   - {suggestion}")
        
        return False


async def test_phone_feed_processing(
    stream_url: str,
    duration_seconds: int = 30,
    exam_id: str = "test-exam-phone",
    room_id: str = "test-room-phone"
):
    """Test processing phone feed"""
    print("\n" + "=" * 60)
    print("Phone Feed Processing Test")
    print("=" * 60)
    print(f"\n📹 Stream URL: {stream_url}")
    print(f"⏱️  Duration: {duration_seconds} seconds")
    print(f"📊 Exam ID: {exam_id}")
    print(f"🏠 Room ID: {room_id}\n")
    
    # Initialize processor
    processor = PhoneFeedProcessor(db_session=None, enable_ai=False)
    
    stream_id = "phone-feed-test-001"
    
    print("🚀 Starting processing...")
    print("   (Press Ctrl+C to stop early)\n")
    
    try:
        results = await processor.start_phone_feed_processing(
            stream_url=stream_url,
            stream_id=stream_id,
            exam_id=exam_id,
            room_id=room_id,
            seat_mapping={},
            duration_seconds=duration_seconds,
            process_every_n_frames=30  # Process ~1 frame per second
        )
        
        if results.get("success"):
            print("\n✅ Processing completed!")
            print(f"   - Frames captured: {results.get('frames_captured', 0)}")
            print(f"   - Frames processed: {results.get('frames_processed', 0)}")
            print(f"   - Frames saved: {results.get('frames_saved', 0)}")
            print(f"   - Duration: {results.get('duration_seconds', 0)} seconds")
            print(f"   - Activities: {len(results.get('activities_logged', []))}")
            print(f"   - Violations: {len(results.get('violations_detected', []))}")
            
            if results.get('frame_directory'):
                print(f"\n📁 Frames saved to: {results.get('frame_directory')}")
                saved_frames = results.get('saved_frames', [])
                if saved_frames:
                    print(f"   Sample frames:")
                    for frame in saved_frames[:3]:
                        print(f"     - Frame #{frame.get('frame_number')}: {frame.get('frame_path', 'N/A')}")
            
            # Generate report
            print("\n📄 Generating report...")
            report = processor.generate_report(stream_id, report_format='json')
            if report.get('report_path'):
                print(f"   ✅ Report saved: {report['report_path']}")
        else:
            print(f"\n❌ Processing failed: {results.get('error')}")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Processing interrupted by user")
        processor.stop_processing()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point"""
    print("\n" + "=" * 60)
    print("Phone Feed Processing - Test Script")
    print("=" * 60)
    
    # Get stream URL from command line or use default
    if len(sys.argv) > 1:
        stream_url = sys.argv[1]
    else:
        # Interactive mode
        print("\n📱 Phone Stream Configuration")
        print("-" * 60)
        
        phone_ip = input("\nEnter your phone's IP address: ").strip()
        if not phone_ip:
            print("❌ IP address required!")
            return
        
        print("\nSelect streaming app:")
        print("  1. IP Webcam (default)")
        print("  2. DroidCam")
        print("  3. Custom URL")
        
        choice = input("\nChoice (1-3): ").strip() or "1"
        
        if choice == "1":
            port = input("Port (default 8080): ").strip() or "8080"
            # Use MJPEG format (more reliable)
            stream_url = PhoneStreamHelper.get_ip_webcam_url(phone_ip, int(port), quality="mjpeg")
        elif choice == "2":
            port = input("Port (default 4747): ").strip() or "4747"
            stream_url = PhoneStreamHelper.get_droidcam_url(phone_ip, int(port))
        else:
            stream_url = input("Enter full stream URL: ").strip()
            if not stream_url:
                print("❌ Stream URL required!")
                return
    
    # Test connection first
    print("\n" + "=" * 60)
    print("Step 1: Testing Connection")
    print("=" * 60)
    
    connection_ok = asyncio.run(test_phone_connection(stream_url))
    
    if not connection_ok:
        print("\n❌ Cannot proceed without connection!")
        print("\nTroubleshooting:")
        print("  1. Ensure phone and computer are on same WiFi")
        print("  2. Check phone streaming app is running")
        print("  3. Try accessing URL in web browser")
        print("  4. Check firewall settings")
        return
    
    # Ask for processing duration
    print("\n" + "=" * 60)
    duration_input = input("\nProcessing duration in seconds (default 30): ").strip()
    duration = int(duration_input) if duration_input else 30
    
    # Process feed
    print("\n" + "=" * 60)
    print("Step 2: Processing Feed")
    print("=" * 60)
    
    asyncio.run(test_phone_feed_processing(stream_url, duration_seconds=duration))
    
    print("\n" + "=" * 60)
    print("✅ Test Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Check processing results")
    print("  2. Enable AI detection for behavior analysis")
    print("  3. Integrate with FastAPI for production use")
    print("\nFor more info, see README.md")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

