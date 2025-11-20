"""
Complete Test Script for Video Streams API
Tests ALL functionalities of the video processing system
"""

import requests
import time
import os
import json
from datetime import datetime
from uuid import uuid4

# ==========================================
# CONFIGURATION
# ==========================================

BASE_URL = "http://localhost:8000"

# Path to your Cheat video (update if needed)
VIDEO_FILE_PATH = "Cheat-1.mp4"  # Update this path!

# Test UUIDs (will be generated)
TEST_EXAM_ID = str(uuid4())
TEST_ROOM_ID = str(uuid4())

# Test configuration
CHECK_INTERVAL = 2  # seconds
MAX_WAIT_TIME = 180  # 3 minutes max

# ==========================================
# COLORS FOR OUTPUT
# ==========================================

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def print_header(title):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(f"{Colors.BOLD}{Colors.HEADER}  {title}{Colors.ENDC}")
    print("="*80)


def print_success(message):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")


def print_error(message):
    """Print error message"""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")


def print_warning(message):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")


def print_info(message):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ️  {message}{Colors.ENDC}")


def print_json(data, indent=2):
    """Print formatted JSON"""
    print(json.dumps(data, indent=indent))


# ==========================================
# TEST FUNCTIONS
# ==========================================

def test_00_check_video_file():
    """Test 0: Check if video file exists"""
    print_header("TEST 0: Check Video File")
    
    if not os.path.exists(VIDEO_FILE_PATH):
        print_error(f"Video file not found: {VIDEO_FILE_PATH}")
        print_info("Please update VIDEO_FILE_PATH in this script")
        return False
    
    file_size = os.path.getsize(VIDEO_FILE_PATH)
    file_size_mb = file_size / (1024 * 1024)
    
    print_success("Video file found!")
    print(f"   Path: {VIDEO_FILE_PATH}")
    print(f"   Size: {file_size_mb:.2f} MB")
    
    if file_size_mb > 500:
        print_warning("File is larger than 500MB (may take longer to upload)")
    
    return True


def test_01_api_health():
    """Test 1: Check if API is running"""
    print_header("TEST 1: API Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        
        if response.status_code == 200:
            print_success("API is running!")
            print(f"   URL: {BASE_URL}")
            print(f"   Response: {response.json()}")
            return True
        else:
            print_error(f"API returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to API at {BASE_URL}")
        print_info("Start backend: cd src && uvicorn main:app --reload")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_02_upload_video():
    """Test 2: Upload video file"""
    print_header("TEST 2: Upload Video")
    
    print_info(f"Uploading: {VIDEO_FILE_PATH}")
    print_info(f"Exam ID: {TEST_EXAM_ID}")
    print_info(f"Room ID: {TEST_ROOM_ID}")
    print_info("⏳ Uploading... (this may take a moment)\n")
    
    try:
        with open(VIDEO_FILE_PATH, 'rb') as video_file:
            files = {'video_file': video_file}
            data = {
                'exam_id': TEST_EXAM_ID,
                'room_id': TEST_ROOM_ID
            }
            
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/api/video-streams/upload",
                files=files,
                data=data,
                timeout=300
            )
            upload_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print_success("Upload successful!")
                print(f"   Stream ID: {result['data']['stream_id']}")
                print(f"   Status: {result['data']['status']}")
                print(f"   Type: {result['data']['stream_type']}")
                print(f"   File Size: {result['data'].get('file_size', 0) / (1024*1024):.2f} MB")
                print(f"   Upload Time: {upload_time:.2f} seconds")
                print(f"   Source Path: {result['data']['source_url']}")
                return result['data']['stream_id']
            else:
                print_error("Upload failed!")
                print_json(result)
                return None
        else:
            print_error(f"Upload failed with status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Upload error: {e}")
        return None


def test_03_monitor_processing(stream_id):
    """Test 3: Monitor video processing status"""
    print_header("TEST 3: Monitor Processing Status")
    
    print_info(f"Monitoring stream: {stream_id}")
    print_info(f"Check interval: {CHECK_INTERVAL} seconds")
    print_info(f"Max wait time: {MAX_WAIT_TIME} seconds\n")
    
    start_time = time.time()
    last_status = None
    last_progress = -1
    
    while (time.time() - start_time) < MAX_WAIT_TIME:
        try:
            response = requests.get(
                f"{BASE_URL}/api/video-streams/{stream_id}/status",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    data = result['data']
                    status = data.get('status', 'unknown')
                    progress = data.get('progress', 0)
                    processed = data.get('processed_frames', 0)
                    total = data.get('total_frames', 0)
                    
                    # Print status changes
                    if status != last_status:
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        print(f"\n[{timestamp}] Status: {status.upper()}")
                        last_status = status
                    
                    # Show progress updates
                    if status == 'processing' and progress > last_progress:
                        print(f"           Progress: {progress:.1f}% | Frames: {processed}/{total if total else '?'}", end='\r')
                        last_progress = progress
                    
                    # Check completion
                    if status == 'completed':
                        print(f"\n")
                        print_success("Processing completed!")
                        print(f"   Total frames: {processed}")
                        print(f"   Time taken: {time.time() - start_time:.1f} seconds")
                        print(f"   Activities detected: {data.get('detected_activities', 0)}")
                        print(f"   Violations detected: {data.get('detected_violations', 0)}")
                        return True, data
                        
                    elif status == 'failed':
                        print(f"\n")
                        print_error("Processing failed!")
                        error_msg = data.get('error_message', 'Unknown error')
                        print(f"   Error: {error_msg}")
                        return False, data
                else:
                    print_error("API returned unsuccessful response")
                    return False, None
                    
            elif response.status_code == 404:
                print_warning("Processing job not created yet, waiting...")
            else:
                print_warning(f"Status check returned: {response.status_code}")
            
            time.sleep(CHECK_INTERVAL)
            
        except Exception as e:
            print_error(f"Error checking status: {e}")
            time.sleep(CHECK_INTERVAL)
    
    print(f"\n")
    print_warning(f"Timeout reached ({MAX_WAIT_TIME} seconds)")
    print_info("Processing may still be running - check backend logs")
    return False, None


def test_04_get_results(stream_id):
    """Test 4: Get processing results"""
    print_header("TEST 4: Get Processing Results")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/video-streams/{stream_id}/results",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                data = result['data']
                
                print_success("Results retrieved!")
                
                # Processing Summary
                print(f"\n📊 {Colors.BOLD}Processing Summary:{Colors.ENDC}")
                summary = data.get('processing_summary', {})
                print(f"   Started: {summary.get('started_at', 'N/A')}")
                print(f"   Completed: {summary.get('completed_at', 'N/A')}")
                print(f"   Total Frames: {summary.get('total_frames', 0)}")
                print(f"   Stream Type: {summary.get('stream_type', 'N/A')}")
                
                # Activities Summary
                print(f"\n🎯 {Colors.BOLD}Activities Summary:{Colors.ENDC}")
                activities = data.get('activities_summary', {})
                print(f"   Total Activities: {activities.get('total_activities', 0)}")
                print(f"   Student Activities: {activities.get('student_activities', 0)}")
                print(f"   Invigilator Issues: {activities.get('invigilator_issues', 0)}")
                
                # Violations Summary
                print(f"\n⚠️  {Colors.BOLD}Violations Summary:{Colors.ENDC}")
                violations = data.get('violations_summary', {})
                print(f"   Total Violations: {violations.get('total_violations', 0)}")
                print(f"   High Severity: {violations.get('high_severity', 0)}")
                print(f"   Pending Review: {violations.get('pending_review', 0)}")
                
                # Frame Analysis
                frames = data.get('frame_analysis', [])
                print(f"\n🖼️  {Colors.BOLD}Frame Analysis:{Colors.ENDC}")
                print(f"   Frames Extracted: {len(frames)}")
                if len(frames) > 0:
                    print(f"   First Frame: #{frames[0].get('frame_number', 'N/A')}")
                    print(f"   Last Frame: #{frames[-1].get('frame_number', 'N/A')}")
                
                # Sample Activities (if any)
                activity_list = data.get('activities', [])
                if len(activity_list) > 0:
                    print(f"\n📋 {Colors.BOLD}Sample Activities (first 3):{Colors.ENDC}")
                    for i, activity in enumerate(activity_list[:3], 1):
                        print(f"   {i}. {activity.get('behavior_type', 'N/A')}")
                        print(f"      Severity: {activity.get('severity', 'N/A')}")
                        print(f"      Confidence: {activity.get('confidence', 0):.2%}")
                        print(f"      Time: {activity.get('timestamp', 'N/A')}")
                
                return data
            else:
                print_error("Failed to get results")
                print_json(result)
                return None
        else:
            print_error(f"Request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Error: {e}")
        return None


def test_05_verify_files(results):
    """Test 5: Verify extracted frame files exist"""
    print_header("TEST 5: Verify Extracted Files")
    
    if not results:
        print_warning("No results to verify")
        return False
    
    frames = results.get('frame_analysis', [])
    
    if len(frames) == 0:
        print_warning("No frames were extracted")
        return False
    
    print_info(f"Checking {len(frames)} extracted frames...\n")
    
    # Check video file
    source_url = results.get('processing_summary', {}).get('source_url')
    if source_url:
        video_path = os.path.join('src', source_url)
        if os.path.exists(video_path):
            print_success(f"Video file exists: {source_url}")
        else:
            print_warning(f"Video file not found: {video_path}")
    
    # Check sample frames
    found_count = 0
    not_found_count = 0
    
    for i, frame in enumerate(frames[:5], 1):  # Check first 5 frames
        frame_path = frame.get('frame_path', '')
        full_path = os.path.join('src', frame_path)
        
        print(f"\n   Frame {i}:")
        print(f"   - Number: #{frame.get('frame_number', 'N/A')}")
        print(f"   - Path: {frame_path}")
        
        if os.path.exists(full_path):
            file_size = os.path.getsize(full_path)
            print_success(f"     File exists ({file_size / 1024:.1f} KB)")
            found_count += 1
        else:
            print_error(f"     File not found!")
            not_found_count += 1
    
    if len(frames) > 5:
        print(f"\n   ... and {len(frames) - 5} more frames")
    
    print(f"\n{Colors.BOLD}Summary:{Colors.ENDC}")
    print(f"   Total frames: {len(frames)}")
    print(f"   Checked: {found_count + not_found_count}")
    print(f"   Found: {found_count}")
    print(f"   Not found: {not_found_count}")
    
    return found_count > 0


def test_06_list_all_streams():
    """Test 6: List all video streams"""
    print_header("TEST 6: List All Streams")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/video-streams/all",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                data = result['data']
                streams = data.get('streams', [])
                count = data.get('count', 0)
                
                print_success(f"Found {count} stream(s)")
                
                if count > 0:
                    print(f"\n{Colors.BOLD}Streams:{Colors.ENDC}")
                    for i, stream in enumerate(streams[:5], 1):
                        print(f"\n   Stream {i}:")
                        print(f"   - ID: {stream.get('stream_id', 'N/A')}")
                        print(f"   - Status: {stream.get('status', 'N/A')}")
                        print(f"   - Type: {stream.get('stream_type', 'N/A')}")
                        print(f"   - Created: {stream.get('created_at', 'N/A')}")
                    
                    if count > 5:
                        print(f"\n   ... and {count - 5} more streams")
                else:
                    print_info("No streams found")
                
                return True
            else:
                print_warning("API returned unsuccessful response")
                print_json(result)
                return False
        else:
            print_error(f"Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_07_list_exam_streams():
    """Test 7: List streams for specific exam"""
    print_header("TEST 7: List Streams for Exam")
    
    print_info(f"Exam ID: {TEST_EXAM_ID}")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/video-streams/exam/{TEST_EXAM_ID}/streams",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                data = result['data']
                count = data.get('count', 0)
                streams = data.get('streams', [])
                
                print_success(f"Found {count} stream(s) for this exam")
                
                if count > 0:
                    for i, stream in enumerate(streams, 1):
                        print(f"\n   Stream {i}:")
                        print(f"   - ID: {stream.get('stream_id', 'N/A')}")
                        print(f"   - Room ID: {stream.get('room_id', 'N/A')}")
                        print(f"   - Status: {stream.get('status', 'N/A')}")
                
                return True
            else:
                print_warning("No streams found for this exam")
                return True
        else:
            print_error(f"Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_08_list_room_streams():
    """Test 8: List streams for specific room"""
    print_header("TEST 8: List Streams for Room")
    
    print_info(f"Room ID: {TEST_ROOM_ID}")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/video-streams/room/{TEST_ROOM_ID}/streams",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                data = result['data']
                count = data.get('count', 0)
                streams = data.get('streams', [])
                
                print_success(f"Found {count} stream(s) for this room")
                
                if count > 0:
                    for i, stream in enumerate(streams, 1):
                        print(f"\n   Stream {i}:")
                        print(f"   - ID: {stream.get('stream_id', 'N/A')}")
                        print(f"   - Exam ID: {stream.get('exam_id', 'N/A')}")
                        print(f"   - Status: {stream.get('status', 'N/A')}")
                
                return True
            else:
                print_warning("No streams found for this room")
                return True
        else:
            print_error(f"Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_09_api_documentation():
    """Test 9: Check API documentation is accessible"""
    print_header("TEST 9: API Documentation")
    
    try:
        # Check Swagger UI
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print_success("Swagger UI accessible")
            print(f"   URL: {BASE_URL}/docs")
        else:
            print_warning(f"Swagger UI returned: {response.status_code}")
        
        # Check ReDoc
        response = requests.get(f"{BASE_URL}/redoc", timeout=5)
        if response.status_code == 200:
            print_success("ReDoc accessible")
            print(f"   URL: {BASE_URL}/redoc")
        else:
            print_warning(f"ReDoc returned: {response.status_code}")
        
        return True
        
    except Exception as e:
        print_error(f"Error: {e}")
        return False


# ==========================================
# MAIN TEST RUNNER
# ==========================================

def run_all_tests():
    """Run all tests in sequence"""
    
    print("\n")
    print("="*80)
    print(f"{Colors.BOLD}{Colors.HEADER}ForeSyte - Complete Video Streams Test Suite{Colors.ENDC}")
    print("="*80)
    print(f"\n{Colors.BOLD}Configuration:{Colors.ENDC}")
    print(f"  API URL: {BASE_URL}")
    print(f"  Video File: {VIDEO_FILE_PATH}")
    print(f"  Exam ID: {TEST_EXAM_ID}")
    print(f"  Room ID: {TEST_ROOM_ID}")
    
    # Track results
    results = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'stream_id': None,
        'processing_results': None
    }
    
    # Test 0: Check video file
    results['total'] += 1
    if test_00_check_video_file():
        results['passed'] += 1
    else:
        results['failed'] += 1
        print_error("\nCannot continue without video file!")
        return results
    
    # Test 1: API health
    results['total'] += 1
    if test_01_api_health():
        results['passed'] += 1
    else:
        results['failed'] += 1
        print_error("\nCannot continue without API connection!")
        return results
    
    # Test 2: Upload video
    results['total'] += 1
    stream_id = test_02_upload_video()
    if stream_id:
        results['passed'] += 1
        results['stream_id'] = stream_id
    else:
        results['failed'] += 1
        print_error("\nCannot continue without successful upload!")
        return results
    
    # Test 3: Monitor processing
    results['total'] += 1
    success, job_info = test_03_monitor_processing(stream_id)
    if success:
        results['passed'] += 1
    else:
        results['failed'] += 1
        print_warning("\nProcessing incomplete, but continuing with other tests...")
    
    # Test 4: Get results
    results['total'] += 1
    processing_results = test_04_get_results(stream_id)
    if processing_results:
        results['passed'] += 1
        results['processing_results'] = processing_results
    else:
        results['failed'] += 1
        print_warning("\nCouldn't get results, but continuing...")
    
    # Test 5: Verify files
    results['total'] += 1
    if test_05_verify_files(processing_results):
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Test 6: List all streams
    results['total'] += 1
    if test_06_list_all_streams():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Test 7: List exam streams
    results['total'] += 1
    if test_07_list_exam_streams():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Test 8: List room streams
    results['total'] += 1
    if test_08_list_room_streams():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Test 9: API documentation
    results['total'] += 1
    if test_09_api_documentation():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    return results


def print_final_summary(results):
    """Print final test summary"""
    print_header("TEST SUMMARY")
    
    print(f"\n{Colors.BOLD}Results:{Colors.ENDC}")
    print(f"   Total Tests: {results['total']}")
    print(f"   {Colors.OKGREEN}Passed: {results['passed']}{Colors.ENDC}")
    print(f"   {Colors.FAIL}Failed: {results['failed']}{Colors.ENDC}")
    
    success_rate = (results['passed'] / results['total'] * 100) if results['total'] > 0 else 0
    print(f"   Success Rate: {success_rate:.1f}%")
    
    if results['stream_id']:
        print(f"\n{Colors.BOLD}Stream Information:{Colors.ENDC}")
        print(f"   Stream ID: {results['stream_id']}")
        print(f"   View in browser: {BASE_URL}/docs")
        print(f"   Status API: {BASE_URL}/api/video-streams/{results['stream_id']}/status")
        print(f"   Results API: {BASE_URL}/api/video-streams/{results['stream_id']}/results")
    
    if results['processing_results']:
        frames = len(results['processing_results'].get('frame_analysis', []))
        activities = results['processing_results'].get('activities_summary', {}).get('total_activities', 0)
        violations = results['processing_results'].get('violations_summary', {}).get('total_violations', 0)
        
        print(f"\n{Colors.BOLD}Processing Results:{Colors.ENDC}")
        print(f"   Frames Extracted: {frames}")
        print(f"   Activities Detected: {activities}")
        print(f"   Violations Detected: {violations}")
    
    print(f"\n{Colors.BOLD}Next Steps:{Colors.ENDC}")
    if results['failed'] == 0:
        print_success("All tests passed! ✨")
        print(f"   1. Check extracted frames in: src/uploads/frames/")
        print(f"   2. View API docs: {BASE_URL}/docs")
        print(f"   3. Ready for frontend integration!")
    else:
        print_warning("Some tests failed.")
        print(f"   1. Check backend logs for errors")
        print(f"   2. Verify backend is running properly")
        print(f"   3. Check file permissions on uploads/ directory")
    
    print("\n" + "="*80 + "\n")


# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == "__main__":
    try:
        # Run all tests
        results = run_all_tests()
        
        # Print summary
        print_final_summary(results)
        
        # Exit code
        exit(0 if results['failed'] == 0 else 1)
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}⚠️  Tests interrupted by user{Colors.ENDC}")
        exit(1)
    except Exception as e:
        print(f"\n\n{Colors.FAIL}❌ Unexpected error: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        exit(1)

