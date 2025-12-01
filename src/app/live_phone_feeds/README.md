# Live Phone Feed Processing

This module processes live video feeds from mobile phones for exam monitoring.

## 📱 Features

- **Multiple Phone App Support**: Works with IP Webcam, DroidCam, and custom RTSP/HTTP streams
- **Real-time Processing**: Processes live video feeds in real-time
- **Frame Extraction**: Extracts and analyzes frames from phone streams
- **Integration**: Uses existing VideoProcessor for analysis
- **Easy Setup**: Simple configuration for common phone streaming apps

## 🚀 Quick Start

### Step 1: Install Phone Streaming App

Choose one of these apps:

#### Option A: IP Webcam (Recommended)

1. Install **IP Webcam** from Google Play Store
2. Open the app and tap "Start server"
3. Note your phone's IP address (shown in app)
4. Default port: `8080`

#### Option B: DroidCam

1. Install **DroidCam** from Google Play Store
2. Open the app and start server
3. Note your phone's IP address
4. Default port: `4747`

### Step 2: Find Your Phone's IP Address

**Android:**

- Settings → WiFi → Tap on connected network → View IP address

**iPhone:**

- Settings → WiFi → Tap (i) icon next to network → View IP address

### Step 3: Test Connection

```bash
cd src/app/live_phone_feeds
python test_phone_feed.py
```

The script will:

1. Ask for your phone's IP address
2. Test the connection
3. Process the feed for a specified duration

### Step 4: Process Feed

```python
import asyncio
from app.live_phone_feeds.phone_processor import PhoneFeedProcessor

async def process():
    processor = PhoneFeedProcessor(enable_ai=False)

    results = await processor.start_phone_feed_processing(
        stream_url="http://192.168.1.100:8080/video",  # Your phone's URL
        stream_id="phone-feed-001",
        exam_id="exam-uuid",
        room_id="room-uuid",
        duration_seconds=3600  # 1 hour
    )

    print(f"Frames captured: {results['frames_captured']}")

asyncio.run(process())
```

## 📋 Usage Examples

### Example 1: Test Connection Only

```python
from app.live_phone_feeds.phone_stream_receiver import PhoneStreamReceiver, PhoneStreamHelper

# Get stream URL for IP Webcam
phone_ip = "192.168.1.100"
stream_url = PhoneStreamHelper.get_ip_webcam_url(phone_ip, port=8080)

# Test connection
receiver = PhoneStreamReceiver()
result = receiver.connect_to_phone_stream(stream_url)

if result['success']:
    print(f"✅ Connected! Resolution: {result['width']}x{result['height']}")
else:
    print(f"❌ Failed: {result['error']}")
```

### Example 2: Process Feed with Callback

```python
import asyncio
from app.live_phone_feeds.phone_stream_receiver import PhoneStreamReceiver

async def process_frame(frame, frame_num, timestamp):
    """Custom frame processing"""
    print(f"Processing frame {frame_num} at {timestamp}")
    # Add your custom processing here

async def main():
    receiver = PhoneStreamReceiver()

    stream_url = "http://192.168.1.100:8080/video"

    await receiver.process_phone_stream(
        stream_url=stream_url,
        duration_seconds=60,
        frame_callback=process_frame,
        process_every_n_frames=30  # Process 1 frame per second
    )

asyncio.run(main())
```

### Example 3: Full Processing with Report

```python
import asyncio
from app.live_phone_feeds.phone_processor import PhoneFeedProcessor

async def main():
    processor = PhoneFeedProcessor(enable_ai=False)

    results = await processor.start_phone_feed_processing(
        stream_url="http://192.168.1.100:8080/video",
        stream_id="exam-monitoring-001",
        exam_id="exam-123",
        room_id="room-456",
        seat_mapping={},
        duration_seconds=7200  # 2 hours
    )

    # Get results
    stored_results = processor.get_processing_results("exam-monitoring-001")

    # Generate report
    report = processor.generate_report("exam-monitoring-001", report_format='json')
    print(f"Report: {report['report_path']}")

asyncio.run(main())
```

## 🔧 Configuration

### Supported Stream URLs

#### IP Webcam

```
http://phone_ip:8080/video          # Standard video
http://phone_ip:8080/video.mjpeg    # MJPEG stream
```

#### DroidCam

```
http://phone_ip:4747/video
```

#### RTSP (if supported by app)

```
rtsp://phone_ip:8554/stream
```

### Frame Processing Rate

Control how many frames to process:

```python
# Process 1 frame per second (at 30fps)
process_every_n_frames=30

# Process 1 frame per 2 seconds (at 30fps)
process_every_n_frames=60

# Process every frame (may be slow)
process_every_n_frames=1
```

## 🏗️ Architecture

```
live_phone_feeds/
├── __init__.py
├── phone_stream_receiver.py    # Receives streams from phone
├── phone_processor.py          # Processes feeds with VideoProcessor
├── test_phone_feed.py          # Test script
└── README.md                   # This file
```

### Components

1. **PhoneStreamReceiver**: Handles connection and frame capture from phone
2. **PhoneFeedProcessor**: Integrates with VideoProcessor for analysis
3. **PhoneStreamHelper**: Helper functions for common app configurations

## 🔌 Integration with FastAPI

Add to your FastAPI app:

```python
from fastapi import APIRouter
from app.live_phone_feeds.phone_processor import PhoneFeedProcessor

router = APIRouter(prefix="/api/phone-feeds", tags=["phone-feeds"])

@router.post("/start")
async def start_phone_feed(stream_url: str, exam_id: str, room_id: str):
    processor = PhoneFeedProcessor(enable_ai=False)

    results = await processor.start_phone_feed_processing(
        stream_url=stream_url,
        stream_id=f"phone-{uuid4()}",
        exam_id=exam_id,
        room_id=room_id,
        duration_seconds=3600
    )

    return results
```

## 🐛 Troubleshooting

### Cannot Connect to Phone

1. **Check WiFi Connection**

   - Phone and computer must be on same WiFi network
   - Try pinging phone IP: `ping 192.168.1.100`

2. **Check Firewall**

   - Disable firewall temporarily to test
   - Allow port in firewall settings

3. **Test in Browser**

   - Open stream URL in web browser first
   - If browser works, Python should work too

4. **Check App Settings**
   - Ensure streaming app is running
   - Check app permissions (camera, network)
   - Try restarting the app

### Stream Drops Frequently

1. **Reduce Frame Rate**

   ```python
   process_every_n_frames=60  # Process fewer frames
   ```

2. **Check Network Quality**

   - Move closer to WiFi router
   - Reduce other network usage

3. **Lower Video Quality**
   - In phone app, reduce video resolution
   - Use lower quality setting

### High CPU Usage

1. **Increase Frame Skip**

   ```python
   process_every_n_frames=60  # Process 1 frame per 2 seconds
   ```

2. **Disable AI Processing**

   ```python
   processor = PhoneFeedProcessor(enable_ai=False)
   ```

3. **Reduce Resolution**
   - Lower video quality in phone app

## 📱 Phone App Setup Guides

### IP Webcam Setup

1. Install IP Webcam from Play Store
2. Open app → Settings → Video preferences
3. Set resolution (recommended: 1280x720)
4. Tap "Start server"
5. Note IP address shown (e.g., `192.168.1.100:8080`)
6. Use URL: `http://192.168.1.100:8080/video`

### DroidCam Setup

1. Install DroidCam from Play Store
2. Open app → Start
3. Note IP address shown
4. Use URL: `http://phone_ip:4747/video`

## 🔒 Security Notes

- **Local Network Only**: These streams are on local network
- **No Authentication**: Most apps don't require authentication
- **Production**: For production, use VPN or secure tunnel
- **HTTPS**: Consider using HTTPS if app supports it

## 📊 Performance

Expected performance:

- **Frame Rate**: 1-2 frames per second (processable)
- **Latency**: 1-3 seconds
- **CPU Usage**: 10-30% (depending on resolution)
- **Memory**: ~200-500MB

## 🎯 Next Steps

1. **Enable AI Detection**: Set `enable_ai=True` for behavior analysis
2. **Add Database Logging**: Pass `db_session` to processor
3. **Create API Endpoints**: Integrate with FastAPI
4. **Add Authentication**: Secure phone feed endpoints
5. **Multi-Phone Support**: Process multiple phone feeds simultaneously

## 📚 Related Documentation

- `../video_processing/README.md` - Video processing module
- `../video_processing/HOW_TO_RUN.md` - How to run video processing

---

**Module Version**: 1.0.0  
**Last Updated**: November 2025  
**Status**: ✅ Ready for Testing
