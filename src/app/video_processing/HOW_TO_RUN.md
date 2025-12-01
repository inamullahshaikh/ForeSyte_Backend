# How to Run Video Processing Module

This guide explains all the ways to run the video processing files in the `video_processing/` folder.

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Method 1: Via FastAPI Server (Recommended)](#method-1-via-fastapi-server-recommended)
3. [Method 2: Direct Python Usage](#method-2-direct-python-usage)
4. [Method 3: Using the Test Script](#method-3-using-the-test-script)
5. [Troubleshooting](#troubleshooting)

---

## Prerequisites

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Required Packages**
   - `opencv-python` - Video processing
   - `fastapi` - API framework
   - `uvicorn` - ASGI server
   - `python-multipart` - File uploads

3. **Directory Structure**
   Ensure these directories exist (they'll be created automatically):
   - `uploads/videos/` - For uploaded videos
   - `uploads/frames/` - For extracted frames
   - `uploads/reports/` - For generated reports

---

## Method 1: Via FastAPI Server (Recommended)

This is the **production way** to use the video processing module. It provides REST API endpoints.

### Step 1: Start the FastAPI Server

```bash
# Navigate to src directory
cd src

# Start the server
uvicorn main:app --reload

# Or with specific host/port
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start at `http://localhost:8000`

### Step 2: Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Step 3: Use the API Endpoints

#### Upload a Video File

```bash
curl -X POST "http://localhost:8000/api/video-streams/upload" \
  -F "video_file=@path/to/your/video.mp4" \
  -F "exam_id=your-exam-uuid" \
  -F "room_id=your-room-uuid"
```

#### Check Processing Status

```bash
curl "http://localhost:8000/api/video-streams/{stream_id}/status"
```

#### Get Processing Results

```bash
curl "http://localhost:8000/api/video-streams/{stream_id}/results"
```

#### List All Streams

```bash
curl "http://localhost:8000/api/video-streams/all"
```

### Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/video-streams/upload` | POST | Upload video file |
| `/api/video-streams/{stream_id}/status` | GET | Get processing status |
| `/api/video-streams/{stream_id}/results` | GET | Get processing results |
| `/api/video-streams/exam/{exam_id}/streams` | GET | List streams for exam |
| `/api/video-streams/room/{room_id}/streams` | GET | List streams for room |
| `/api/video-streams/all` | GET | List all streams |
| `/api/video-streams/{stream_id}` | DELETE | Delete stream |

---

## Method 2: Direct Python Usage

You can import and use the classes directly in your Python scripts.

### Example 1: Process a Recorded Video

```python
import asyncio
from app.video_processing.processor import VideoProcessor
from database.db import SessionLocal  # Optional: if using database

async def process_video():
    # Initialize processor (without database)
    processor = VideoProcessor(db_session=None, enable_ai=False)
    
    # Process video
    results = await processor.process_video_stream(
        stream_id="test-stream-123",
        source="path/to/your/video.mp4",
        stream_type="recorded",
        exam_id="exam-uuid",
        room_id="room-uuid",
        seat_mapping={}  # Optional seat mapping
    )
    
    print(f"Success: {results.get('success')}")
    print(f"Activities: {len(results.get('activities_logged', []))}")
    print(f"Violations: {len(results.get('violations_detected', []))}")
    
    # Get results later
    stored_results = processor.get_processing_results("test-stream-123")
    
    # Generate report
    report = processor.generate_report("test-stream-123", report_format='json')
    print(f"Report saved to: {report['report_path']}")

# Run
asyncio.run(process_video())
```

### Example 2: Process Live Stream

```python
import asyncio
from app.video_processing.processor import VideoProcessor

async def process_live_stream():
    processor = VideoProcessor(db_session=None, enable_ai=False)
    
    results = await processor.process_video_stream(
        stream_id="live-stream-123",
        source="rtsp://192.168.1.100:554/stream",  # RTSP URL
        stream_type="live",
        exam_id="exam-uuid",
        room_id="room-uuid",
        seat_mapping={}
    )
    
    print(f"Processing completed: {results.get('success')}")

asyncio.run(process_live_stream())
```

### Example 3: Use Stream Handler Directly

```python
from app.video_processing.stream_handler import VideoStreamHandler

# Initialize handler
handler = VideoStreamHandler()

# Validate video
validation = handler.validate_video_input("path/to/video.mp4", "recorded")
print(f"Valid: {validation['valid']}")
print(f"FPS: {validation['fps']}")
print(f"Duration: {validation['duration']} seconds")

# Extract frames
frames = handler.extract_frames(
    video_source="path/to/video.mp4",
    frame_rate=30,  # Extract 1 frame per 30 frames
    job_id="job-123"
)

print(f"Extracted {len(frames)} frames")
for frame_info in frames[:5]:  # Show first 5
    print(f"Frame {frame_info['frame_number']}: {frame_info['frame_path']}")
```

### Example 4: Save Uploaded Video

```python
from app.video_processing.stream_handler import VideoStreamHandler

handler = VideoStreamHandler()

# Read video file
with open("path/to/video.mp4", "rb") as f:
    file_content = f.read()

# Save with organization
video_path = handler.save_uploaded_video(
    file_content=file_content,
    filename="exam_recording.mp4",
    exam_id="exam-uuid",
    room_id="room-uuid"
)

print(f"Video saved to: {video_path}")
```

---

## Method 3: Using the Test Script

A comprehensive test script is available at the root: `test.py`

### Step 1: Update Configuration

Edit `test.py` and update:
```python
VIDEO_FILE_PATH = "path/to/your/test/video.mp4"  # Update this!
```

### Step 2: Start the Server

In one terminal:
```bash
cd src
uvicorn main:app --reload
```

### Step 3: Run the Test

In another terminal:
```bash
python test.py
```

The test script will:
1. ✅ Check if video file exists
2. ✅ Verify API is running
3. ✅ Upload video file
4. ✅ Monitor processing status
5. ✅ Get processing results
6. ✅ Verify extracted frames
7. ✅ List all streams
8. ✅ Check API documentation

---

## File Structure

```
video_processing/
├── __init__.py          # Module initialization
├── processor.py         # Main orchestrator (VideoProcessor class)
├── stream_handler.py    # Video I/O handler (VideoStreamHandler class)
├── README.md            # Complete documentation
└── HOW_TO_RUN.md        # This file
```

---

## Key Classes

### 1. `VideoProcessor`
**Location**: `processor.py`

Main orchestrator that coordinates video processing, AI detection, and database logging.

**Key Methods**:
- `process_video_stream()` - Process complete video (async)
- `get_processing_results()` - Retrieve results
- `generate_report()` - Generate JSON/PDF report

### 2. `VideoStreamHandler`
**Location**: `stream_handler.py`

Handles all video input/output operations.

**Key Methods**:
- `validate_video_input()` - Validate video format
- `extract_frames()` - Extract frames from video
- `process_live_stream()` - Process live CCTV stream (async)
- `process_recorded_video()` - Process uploaded video
- `save_uploaded_video()` - Save uploaded file

---

## Configuration Options

### Enable AI Detection

By default, AI detection is **disabled** (`enable_ai=False`). To enable:

```python
processor = VideoProcessor(db_session=db, enable_ai=True)
```

**Note**: Requires `behavior_detector.py` from `app/ai_engine/`

### Frame Extraction Rate

Control how many frames to extract per second:

```python
# In stream_handler.py, modify:
frame_extraction_rate = max(1, int(fps))  # Default: 1 frame per second
```

### Storage Directories

Change where files are stored:

```python
handler = VideoStreamHandler(
    upload_dir="custom/videos",  # Uploaded videos
    frame_dir="custom/frames"     # Extracted frames
)
```

---

## Troubleshooting

### Issue: "Cannot open video source"

**Solution**:
1. Check file path is absolute or relative to current working directory
2. Verify video format is supported (MP4, AVI, MOV, MKV, WEBM)
3. Check file permissions
4. Ensure OpenCV can read the video codec

### Issue: "Database connection error"

**Solution**:
- The module works **without database** by default
- Set `USE_DATABASE=false` in `.env` or environment
- Or provide `db_session=None` when initializing

### Issue: "Module not found"

**Solution**:
```bash
# Make sure you're in the correct directory
cd src

# Or add to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: "Upload directory not found"

**Solution**:
The directories are created automatically, but you can create manually:
```bash
mkdir -p uploads/videos uploads/frames uploads/reports
```

### Issue: "Processing takes too long"

**Solution**:
- Reduce frame extraction rate (extract fewer frames)
- Process shorter video segments
- Use lower resolution videos for testing
- Disable AI detection for faster processing

---

## Quick Start Example

**Simplest way to test**:

```python
# test_quick.py
import asyncio
from app.video_processing.processor import VideoProcessor

async def quick_test():
    processor = VideoProcessor(enable_ai=False)
    
    results = await processor.process_video_stream(
        stream_id="test-1",
        source="path/to/test/video.mp4",
        stream_type="recorded",
        exam_id="test-exam",
        room_id="test-room",
        seat_mapping={}
    )
    
    print(f"✅ Success: {results.get('success')}")
    print(f"📊 Frames: {results.get('total_frames_processed', 0)}")
    print(f"🎯 Activities: {len(results.get('activities_logged', []))}")

asyncio.run(quick_test())
```

Run:
```bash
cd src
python test_quick.py
```

---

## Next Steps

1. **For Production**: Use Method 1 (FastAPI Server)
2. **For Development**: Use Method 2 (Direct Python)
3. **For Testing**: Use Method 3 (Test Script)

For more details, see `README.md` in the same directory.

---

**Need Help?**
- Check `README.md` for complete documentation
- Review API docs at `/docs` when server is running
- Check backend logs for detailed error messages

