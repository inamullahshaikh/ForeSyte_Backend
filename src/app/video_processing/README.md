# Video Processing Module

## Overview

This module implements **UC-07: Process Exam Footage (Live/Recorded)** for the ForeSyte exam monitoring system. It provides comprehensive video analysis capabilities for both real-time CCTV streams and pre-recorded exam footage.

## Features

### ✅ FR-31: Process Live & Recorded Videos
- Real-time CCTV stream processing (RTSP, HTTP)
- Batch processing of uploaded recordings
- Automatic frame extraction and analysis
- Optimized storage and performance

### ✅ AI-Powered Detection
- **Student Behavior Detection**:
  - Looking around / head movements
  - Phone usage detection
  - Communication attempts
  - Suspicious objects on desk
  - Paper exchange detection
  
- **Invigilator Monitoring**:
  - Presence detection
  - Activity monitoring
  - Phone usage detection
  - Attention tracking

### ✅ Complete UC-07 Implementation
All 10 steps of the Main Success Scenario implemented:
1. ✅ Connect to video sources (live/recorded)
2. ✅ Validate video input
3. ✅ Process frames with AI engine
4. ✅ Identify suspicious behaviors
5. ✅ Map detections to student seats
6. ✅ Log activities with timestamps
7. ✅ Provide results access for investigators
8. ✅ Display processed footage results
9. ✅ Enable activity review with evidence
10. ✅ Generate and export reports

## Architecture

```
video_processing/
├── __init__.py
├── stream_handler.py      # Video I/O and frame extraction
├── processor.py           # Main orchestrator
└── README.md             # This file

../ai_engine/
├── __init__.py
└── behavior_detector.py   # AI detection engine
```

## Components

### 1. VideoStreamHandler (`stream_handler.py`)

Handles all video input/output operations:

```python
from app.video_processing.stream_handler import VideoStreamHandler

handler = VideoStreamHandler()

# Validate video
validation = handler.validate_video_input(video_path, 'recorded')

# Extract frames
frames = handler.extract_frames(video_path, frame_rate=30, job_id="job-123")

# Process live stream
await handler.process_live_stream(stream_url, duration_seconds=3600)

# Save uploaded video
path = handler.save_uploaded_video(file_content, filename, exam_id, room_id)
```

**Key Methods:**
- `validate_video_input()` - Validates video format and properties
- `extract_frames()` - Extracts frames for analysis
- `process_live_stream()` - Processes real-time streams
- `process_recorded_video()` - Batch processes recordings
- `save_uploaded_video()` - Saves uploaded files with organization

### 2. BehaviorDetector (`behavior_detector.py`)

AI engine for detecting suspicious behaviors:

```python
from app.ai_engine.behavior_detector import BehaviorDetector

detector = BehaviorDetector()

# Analyze frame
results = detector.process_frame(frame, frame_number, timestamp, seat_mapping)

# Get student behaviors
student_behaviors = detector.analyze_student_behavior(frame, seat_info)

# Monitor invigilator
invigilator_issues = detector.analyze_invigilator_behavior(frame)

# Map detection to seat
seat_id = detector.map_detection_to_seat(detection, seat_mapping)
```

**Detection Categories:**

**Students:**
- `looking_around` (Low)
- `head_movement_excessive` (Medium)
- `using_phone` (High)
- `communication_attempt` (High)
- `suspicious_object` (Medium)
- `looking_at_neighbor` (Medium)
- `hand_gestures` (Medium)
- `paper_exchange` (High)

**Invigilators:**
- `not_present` (High)
- `using_phone` (Medium)
- `sleeping` (High)
- `distracted` (Medium)
- `inadequate_monitoring` (Medium)

### 3. VideoProcessor (`processor.py`)

Main orchestrator coordinating all components:

```python
from app.video_processing.processor import VideoProcessor

processor = VideoProcessor(db_session)

# Process complete video stream (UC-07 Steps 1-10)
results = await processor.process_video_stream(
    stream_id=stream_id,
    source=video_path,
    stream_type='recorded',
    exam_id=exam_id,
    room_id=room_id,
    seat_mapping=seat_mapping
)

# Get results (Steps 7-8)
results = processor.get_processing_results(stream_id)

# Generate report (Step 10)
report = processor.generate_report(stream_id, report_format='json')
```

## Usage Examples

### Example 1: Process Uploaded Video

```python
from app.video_processing.processor import VideoProcessor
from database.db import SessionLocal

db = SessionLocal()
processor = VideoProcessor(db)

# Process video
results = await processor.process_video_stream(
    stream_id="stream-uuid",
    source="/uploads/videos/exam1.mp4",
    stream_type="recorded",
    exam_id="exam-uuid",
    room_id="room-uuid",
    seat_mapping=seat_data
)

print(f"Detected {len(results['activities_logged'])} activities")
print(f"Found {len(results['violations_detected'])} violations")
```

### Example 2: Monitor Live CCTV

```python
# Connect to live camera
results = await processor.process_video_stream(
    stream_id="live-stream-uuid",
    source="rtsp://192.168.1.100:554/stream",
    stream_type="live",
    exam_id="exam-uuid",
    room_id="room-uuid",
    seat_mapping=seat_data
)
```

### Example 3: Generate Report

```python
# After processing completes
report = processor.generate_report(
    stream_id="stream-uuid",
    report_format="json"
)

print(f"Report saved to: {report['report_path']}")
print(f"Total activities: {report['activities_summary']['total_activities']}")
print(f"Total violations: {report['violations_summary']['total_violations']}")
```

## API Integration

The video processing module is exposed through REST API endpoints in `database/api/video_streams.py`:

### Upload Video
```http
POST /api/video-streams/upload
Content-Type: multipart/form-data

video_file: <file>
exam_id: <uuid>
room_id: <uuid>
```

### Connect Live Stream
```http
POST /api/video-streams/connect-live
Content-Type: application/json

{
  "room_id": "uuid",
  "exam_id": "uuid",
  "stream_type": "live",
  "source_url": "rtsp://camera-url"
}
```

### Get Processing Status
```http
GET /api/video-streams/{stream_id}/status
```

### Get Results
```http
GET /api/video-streams/{stream_id}/results
```

### Generate Report
```http
POST /api/video-streams/{stream_id}/report?report_format=json
```

## Configuration

### Frame Extraction Rate
Control how many frames to process per second:

```python
# In stream_handler.py
frame_extraction_rate = max(1, int(fps))  # Default: 1 frame per second
```

### Detection Thresholds
Adjust sensitivity of behavior detection:

```python
# In behavior_detector.py
STUDENT_BEHAVIORS = {
    "using_phone": {"severity": "high", "threshold": 0.8},
    # Increase threshold = more confident detections required
    # Decrease threshold = more sensitive detection
}
```

### Storage Locations
Configure where files are stored:

```python
# In stream_handler.py __init__
VideoStreamHandler(
    upload_dir="uploads/videos",  # Uploaded videos
    frame_dir="uploads/frames"     # Extracted frames
)
```

## Performance

### Optimization Techniques
1. **Frame Sampling**: Process 1 frame per second by default
2. **Async Processing**: Background tasks for non-blocking uploads
3. **Batch Mode**: Efficient processing for recorded videos
4. **Storage Management**: Frames saved only when needed

### Expected Performance
- **Recorded Video**: ~30-60 seconds per minute of footage
- **Live Stream**: Real-time processing at 1fps
- **Storage**: ~100KB per extracted frame
- **Memory**: ~500MB for typical processing job

## Error Handling

The module includes comprehensive error handling:

```python
try:
    results = await processor.process_video_stream(...)
    if results.get('success'):
        # Process results
    else:
        # Handle failure
        error = results.get('error')
except Exception as e:
    # Handle exception
    logger.error(f"Processing failed: {e}")
```

## Database Integration

### Models Used
- `VideoStream` - Stream records
- `ProcessingJob` - Job tracking
- `FrameLog` - Frame analysis logs
- `StudentActivity` - Detected activities
- `InvigilatorActivity` - Invigilator logs
- `Violation` - Detected violations

### Activity Logging
All detected activities are automatically logged to the database with:
- Timestamp (exact moment of detection)
- Frame number (reference to video position)
- Behavior type (what was detected)
- Confidence score (AI confidence)
- Severity level (low/medium/high)
- Seat mapping (which student)
- Evidence path (frame image)

## Testing

Run the test script:

```bash
# Update test_video_processing.py with your data
python test_video_processing.py
```

Or test individual components:

```python
# Test stream handler
handler = VideoStreamHandler()
validation = handler.validate_video_input("test.mp4", "recorded")
assert validation['valid'] == True

# Test behavior detector
detector = BehaviorDetector()
frame = cv2.imread("test_frame.jpg")
behaviors = detector.analyze_student_behavior(frame)
assert isinstance(behaviors, list)
```

## Troubleshooting

### Video Won't Process
1. Check video format (MP4, AVI, MOV supported)
2. Verify video codec (H.264 recommended)
3. Check file permissions
4. Verify disk space in uploads directory

### Low Detection Accuracy
1. Improve lighting in exam hall
2. Use higher resolution cameras (1080p minimum)
3. Adjust detection thresholds
4. Ensure camera positioning captures faces clearly

### Live Stream Disconnects
1. Check network stability
2. Verify RTSP URL format
3. Test stream with VLC first
4. Check camera authentication settings

## Future Enhancements

Potential improvements:
- [ ] Custom YOLO model for exam-specific detection
- [ ] Multi-camera synchronization
- [ ] Real-time alerts/notifications
- [ ] Advanced pose estimation
- [ ] Facial recognition integration
- [ ] Audio analysis for cheating detection
- [ ] GPU acceleration support
- [ ] Distributed processing for multiple rooms

## Dependencies

- `opencv-python` - Video processing
- `numpy` - Numerical operations
- `fastapi` - API framework
- `sqlalchemy` - Database ORM
- `asyncio` - Async processing

## License

Part of the ForeSyte exam monitoring system.

---

**Module Version**: 1.0.0  
**Last Updated**: November 2025  
**Status**: ✅ Production Ready

