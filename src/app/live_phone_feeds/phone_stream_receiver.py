"""
Phone Stream Receiver
Receives live video feeds from phone apps via HTTP/RTSP
Supports multiple phone streaming apps and protocols
"""

import cv2
import asyncio
import logging
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from urllib.parse import urlparse
import requests
from threading import Thread
import time
import numpy as np
from PIL import Image
import io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PhoneStreamReceiver:
    """
    Receives and processes live video streams from phone apps.
    Supports various phone streaming apps and protocols.
    """
    
    def __init__(self):
        """Initialize phone stream receiver"""
        self.is_streaming = False
        self.current_stream = None
        self.frame_callback = None
        
    def connect_to_phone_stream(self, stream_url: str, timeout: int = 10) -> Dict[str, Any]:
        """
        Connect to phone video stream.
        
        Supported formats:
        - IP Webcam: http://phone_ip:8080/video
        - DroidCam: http://phone_ip:4747/video
        - RTSP: rtsp://phone_ip:8554/stream
        - MJPEG: http://phone_ip:8080/video.mjpeg
        
        Args:
            stream_url: URL of the phone stream
            timeout: Connection timeout in seconds (default: 10)
            
        Returns:
            Connection status and stream info
        """
        logger.info(f"Connecting to phone stream: {stream_url}")
        
        # First, test HTTP connectivity (for HTTP streams)
        parsed = urlparse(stream_url)
        if parsed.scheme == "http":
            # Test if server is reachable
            try:
                base_url = f"{parsed.scheme}://{parsed.netloc}"
                response = requests.get(base_url, timeout=5)
                logger.info(f"HTTP server is reachable: {base_url}")
            except requests.exceptions.RequestException as e:
                logger.warning(f"HTTP server test failed: {e}")
                return {
                    "success": False,
                    "error": f"Cannot reach phone server: {parsed.netloc}",
                    "error_details": str(e),
                    "suggestions": self._get_connection_suggestions(stream_url)
                }
        
        # Try alternative URLs for IP Webcam if main URL fails
        urls_to_try = [stream_url]
        if parsed.scheme == "http":
            base_path = parsed.path.rstrip('/')
            # Generate alternative URLs
            if base_path == "/video" or base_path == "":
                # Standard video path - try alternatives
                urls_to_try.extend([
                    f"http://{parsed.netloc}/video.mjpeg",
                    f"http://{parsed.netloc}/videofeed",
                    f"http://{parsed.netloc}/video"
                ])
            elif base_path == "/video.mjpeg":
                # Already MJPEG - try other formats
                urls_to_try.extend([
                    f"http://{parsed.netloc}/videofeed",
                    f"http://{parsed.netloc}/video"
                ])
            elif "/video" in base_path:
                # Has video in path - try MJPEG version
                if ".mjpeg" not in base_path:
                    urls_to_try.append(f"http://{parsed.netloc}{base_path}.mjpeg")
                urls_to_try.append(f"http://{parsed.netloc}/videofeed")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls_to_try:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        urls_to_try = unique_urls
        
        # Try each URL
        for test_url in urls_to_try:
            logger.info(f"Trying URL: {test_url}")
            
            try:
                # Configure OpenCV with timeout
                cap = cv2.VideoCapture(test_url)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer
                
                # Try to read a frame with timeout
                import time
                start_time = time.time()
                
                # Give it a few seconds to connect
                ret = False
                frame = None
                attempts = 0
                max_attempts = timeout * 10  # 10 attempts per second
                
                while not ret and attempts < max_attempts:
                    ret, frame = cap.read()
                    attempts += 1
                    if not ret:
                        time.sleep(0.1)
                
                if not ret or frame is None:
                    cap.release()
                    logger.warning(f"Could not read frame from: {test_url}")
                    
                    # Try alternative method: Direct HTTP request for MJPEG
                    if ".mjpeg" in test_url or "/videofeed" in test_url:
                        logger.info(f"Trying direct HTTP method for: {test_url}")
                        frame_data = self._try_direct_http_frame(test_url)
                        if frame_data:
                            # Success with direct HTTP
                            import numpy as np
                            from PIL import Image
                            import io
                            
                            try:
                                img = Image.open(io.BytesIO(frame_data))
                                frame = np.array(img)
                                height, width = frame.shape[:2]
                                
                                logger.info(f"✅ Successfully connected via HTTP: {test_url}")
                                return {
                                    "success": True,
                                    "stream_url": test_url,
                                    "original_url": stream_url,
                                    "width": width,
                                    "height": height,
                                    "fps": 30,  # Default for MJPEG
                                    "connected_at": datetime.utcnow().isoformat(),
                                    "method": "http_direct"
                                }
                            except Exception as e:
                                logger.warning(f"Failed to decode HTTP frame: {e}")
                    
                    continue
                
                # Success! Get stream properties
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                
                # If dimensions are 0, use frame dimensions
                if width == 0 or height == 0:
                    height, width = frame.shape[:2]
                
                cap.release()
                
                # If we used an alternative URL, note it
                working_url = test_url if test_url != stream_url else stream_url
                
                logger.info(f"✅ Successfully connected to: {working_url}")
                
                return {
                    "success": True,
                    "stream_url": working_url,
                    "original_url": stream_url,
                    "width": width,
                    "height": height,
                    "fps": fps if fps > 0 else 30,
                    "connected_at": datetime.utcnow().isoformat(),
                    "alternative_url_used": working_url != stream_url
                }
                
            except Exception as e:
                logger.warning(f"Error with {test_url}: {e}")
                if cap:
                    try:
                        cap.release()
                    except:
                        pass
                continue
        
        # All URLs failed
        return {
            "success": False,
            "error": f"Cannot connect to stream: {stream_url}",
            "error_code": "CONNECTION_FAILED",
            "tried_urls": urls_to_try,
            "suggestions": self._get_connection_suggestions(stream_url)
        }
    
    def _get_connection_suggestions(self, stream_url: str) -> list:
        """Get helpful suggestions for connection issues"""
        suggestions = []
        
        parsed = urlparse(stream_url)
        host = parsed.hostname
        
        if not host or host == "localhost":
            suggestions.append("❌ Use your phone's IP address instead of localhost")
            suggestions.append("   Find IP: Settings > WiFi > Network Details")
        
        if parsed.scheme == "http":
            suggestions.append("📱 Try alternative URL formats:")
            suggestions.append("   - http://phone_ip:8080/video.mjpeg (MJPEG format)")
            suggestions.append("   - http://phone_ip:8080/videofeed")
            suggestions.append("   - http://phone_ip:8080/video (standard)")
        
        suggestions.append("🔍 Troubleshooting steps:")
        suggestions.append("   1. Ensure phone and computer are on SAME WiFi network")
        suggestions.append("   2. Test in web browser: Open URL in Chrome/Firefox")
        suggestions.append("   3. Check phone app is running and server is started")
        suggestions.append("   4. Try pinging phone: ping " + (host or "phone_ip"))
        suggestions.append("   5. Check firewall: Temporarily disable to test")
        suggestions.append("   6. Restart phone app and try again")
        
        if "8080" in stream_url:
            suggestions.append("📲 For IP Webcam:")
            suggestions.append("   - Open IP Webcam app")
            suggestions.append("   - Tap 'Start server'")
            suggestions.append("   - Note the IP address shown")
            suggestions.append("   - Try: http://phone_ip:8080/video.mjpeg")
        
        if "4747" in stream_url:
            suggestions.append("📲 For DroidCam:")
            suggestions.append("   - Open DroidCam app")
            suggestions.append("   - Tap 'Start'")
            suggestions.append("   - Use IP shown in app")
        
        return suggestions
    
    async def process_phone_stream(
        self, 
        stream_url: str,
        duration_seconds: int = 3600,
        frame_callback: Optional[Callable] = None,
        process_every_n_frames: int = 30,
        use_http_fallback: bool = True
    ) -> Dict[str, Any]:
        """
        Process live stream from phone in real-time.
        
        Args:
            stream_url: Phone stream URL
            duration_seconds: How long to process (default: 1 hour)
            frame_callback: Async function(frame, frame_num, timestamp) called for each processed frame
            process_every_n_frames: Process 1 frame every N frames (default: 30 = ~1fps at 30fps)
            use_http_fallback: Use HTTP direct method if OpenCV fails (default: True)
            
        Returns:
            Processing statistics
        """
        logger.info(f"Starting phone stream processing: {stream_url}")
        
        self.is_streaming = True
        self.frame_callback = frame_callback
        
        # Try OpenCV first
        cap = cv2.VideoCapture(stream_url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        use_http_method = False
        
        if not cap.isOpened():
            # Try HTTP direct method for MJPEG streams
            if use_http_fallback and (".mjpeg" in stream_url or "/videofeed" in stream_url or "/video" in stream_url):
                logger.info("OpenCV cannot open stream, trying HTTP direct method...")
                use_http_method = True
            else:
                self.is_streaming = False
                return {
                    "success": False,
                    "error": "Cannot open phone stream",
                    "stream_url": stream_url,
                    "suggestions": ["Try MJPEG format: /video.mjpeg", "Try /videofeed", "Check app is running"]
                }
        else:
            # Test if we can read a frame
            ret, test_frame = cap.read()
            if not ret or test_frame is None:
                # OpenCV opened but can't read frames - try HTTP method
                if use_http_fallback and (".mjpeg" in stream_url or "/videofeed" in stream_url or "/video" in stream_url):
                    logger.info("OpenCV cannot read frames, trying HTTP direct method...")
                    use_http_method = True
                    cap.release()
                else:
                    cap.release()
                    self.is_streaming = False
                    return {
                        "success": False,
                        "error": "Cannot read frames from phone stream",
                        "stream_url": stream_url,
                        "suggestions": ["Try MJPEG format: /video.mjpeg", "Try /videofeed", "Check app is running"]
                    }
            else:
                # OpenCV works, reset capture for processing
                cap.release()
                cap = cv2.VideoCapture(stream_url)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        start_time = datetime.utcnow()
        frame_count = 0
        processed_count = 0
        errors = 0
        
        try:
            if use_http_method:
                # Use HTTP direct method for MJPEG
                result = await self._process_http_stream(
                    stream_url, duration_seconds, frame_callback, 
                    process_every_n_frames, start_time
                )
                frame_count = result.get('frames_captured', 0)
                processed_count = result.get('frames_processed', 0)
            else:
                # Use OpenCV method
                while self.is_streaming and (datetime.utcnow() - start_time).seconds < duration_seconds:
                    ret, frame = cap.read()
                    
                    if not ret:
                        errors += 1
                        if errors > 10:
                            logger.warning("Too many read errors, stopping stream")
                            break
                        await asyncio.sleep(0.1)
                        continue
                    
                    errors = 0  # Reset error count on success
                    frame_count += 1
                    
                    # Always call callback for frame saving, but track processed separately
                    if frame_callback:
                        try:
                            await frame_callback(frame, frame_count, datetime.utcnow())
                            # Only count as processed if it's every Nth frame
                            if frame_count % process_every_n_frames == 0:
                                processed_count += 1
                        except Exception as e:
                            logger.error(f"Frame callback error: {e}")
                    else:
                        # If no callback, still track processed frames
                        if frame_count % process_every_n_frames == 0:
                            processed_count += 1
                    
                    # Small delay to prevent overwhelming
                    await asyncio.sleep(0.001)
                
        except KeyboardInterrupt:
            logger.info("Stream processing interrupted by user")
        except Exception as e:
            logger.error(f"Error processing stream: {e}")
            return {
                "success": False,
                "error": str(e),
                "frames_captured": frame_count,
                "frames_processed": processed_count
            }
        finally:
            if not use_http_method:
                cap.release()
            self.is_streaming = False
            logger.info(f"Stream processing stopped. Frames: {frame_count}, Processed: {processed_count}")
        
        return {
            "success": True,
            "frames_captured": frame_count,
            "frames_processed": processed_count,
            "duration_seconds": (datetime.utcnow() - start_time).seconds,
            "stream_url": stream_url,
            "method": "http_direct" if use_http_method else "opencv"
        }
    
    async def _process_http_stream(
        self, stream_url: str, duration_seconds: int,
        frame_callback: Optional[Callable], process_every_n_frames: int,
        start_time: datetime
    ) -> Dict[str, int]:
        """Process MJPEG stream using direct HTTP requests"""
        logger.info(f"Using HTTP direct method for stream: {stream_url}")
        
        frame_count = 0
        processed_count = 0
        
        try:
            # Try the stream URL
            response = requests.get(stream_url, stream=True, timeout=10)
            if response.status_code != 200:
                # If /videofeed works but /video.mjpeg doesn't, try /videofeed
                if "/video.mjpeg" in stream_url:
                    alt_url = stream_url.replace("/video.mjpeg", "/videofeed")
                    logger.info(f"Trying alternative URL: {alt_url}")
                    response = requests.get(alt_url, stream=True, timeout=10)
                    if response.status_code != 200:
                        raise Exception(f"HTTP request failed: {response.status_code} (tried {stream_url} and {alt_url})")
                else:
                    raise Exception(f"HTTP request failed: {response.status_code}")
            
            # MJPEG stream: frames are separated by boundary markers
            boundary = None
            content_type = response.headers.get('Content-Type', '')
            if 'boundary=' in content_type:
                boundary = content_type.split('boundary=')[1].strip()
            
            buffer = b''
            
            while self.is_streaming and (datetime.utcnow() - start_time).seconds < duration_seconds:
                try:
                    chunk = response.raw.read(8192)
                    if not chunk:
                        await asyncio.sleep(0.1)
                        continue
                    
                    buffer += chunk
                    
                    # Try to find JPEG frame markers
                    start_marker = buffer.find(b'\xff\xd8')  # JPEG start
                    end_marker = buffer.find(b'\xff\xd9')    # JPEG end
                    
                    if start_marker != -1 and end_marker != -1 and end_marker > start_marker:
                        # Extract frame
                        frame_data = buffer[start_marker:end_marker + 2]
                        buffer = buffer[end_marker + 2:]
                        
                        # Decode frame
                        try:
                            img = Image.open(io.BytesIO(frame_data))
                            frame = np.array(img)
                            
                            frame_count += 1
                            
                            # Always call callback for frame saving, but track processed separately
                            if frame_callback:
                                try:
                                    await frame_callback(frame, frame_count, datetime.utcnow())
                                    # Only count as processed if it's every Nth frame
                                    if frame_count % process_every_n_frames == 0:
                                        processed_count += 1
                                except Exception as e:
                                    logger.error(f"Frame callback error: {e}")
                            else:
                                # If no callback, still track processed frames
                                if frame_count % process_every_n_frames == 0:
                                    processed_count += 1
                            
                            await asyncio.sleep(0.001)
                            
                        except Exception as e:
                            logger.debug(f"Failed to decode frame: {e}")
                            continue
                    
                    # Prevent buffer from growing too large
                    if len(buffer) > 1024 * 1024:  # 1MB
                        buffer = buffer[-512 * 1024:]  # Keep last 512KB
                        
                except Exception as e:
                    logger.warning(f"Error reading chunk: {e}")
                    await asyncio.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"HTTP stream error: {e}")
            raise
        finally:
            return {
                'frames_captured': frame_count,
                'frames_processed': processed_count
            }
    
    def stop_stream(self):
        """Stop the current stream"""
        self.is_streaming = False
        logger.info("Stream stop requested")
    
    def _try_direct_http_frame(self, stream_url: str) -> Optional[bytes]:
        """
        Try to fetch a single frame directly via HTTP (for MJPEG streams).
        
        Args:
            stream_url: Stream URL
            
        Returns:
            Frame data as bytes or None
        """
        try:
            response = requests.get(stream_url, stream=True, timeout=5)
            if response.status_code == 200:
                # Read first chunk (should contain a frame)
                chunk = next(response.iter_content(chunk_size=1024*1024), None)
                if chunk:
                    return chunk
        except Exception as e:
            logger.debug(f"Direct HTTP method failed: {e}")
        return None
    
    def get_stream_info(self, stream_url: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a phone stream without processing.
        
        Args:
            stream_url: Stream URL
            
        Returns:
            Stream information or None
        """
        cap = cv2.VideoCapture(stream_url)
        
        if not cap.isOpened():
            return None
        
        info = {
            "stream_url": stream_url,
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "codec": int(cap.get(cv2.CAP_PROP_FOURCC)),
            "is_connected": True
        }
        
        cap.release()
        return info


class PhoneStreamHelper:
    """
    Helper class for common phone streaming app configurations
    """
    
    @staticmethod
    def get_ip_webcam_url(phone_ip: str, port: int = 8080, quality: str = "mjpeg") -> str:
        """
        Get IP Webcam stream URL.
        
        Args:
            phone_ip: Phone's IP address
            port: Port number (default: 8080)
            quality: 'video', 'mjpeg', or 'videofeed' (default: 'mjpeg' - most reliable)
            
        Returns:
            Stream URL
        """
        if quality == "mjpeg":
            return f"http://{phone_ip}:{port}/video.mjpeg"
        elif quality == "videofeed":
            return f"http://{phone_ip}:{port}/videofeed"
        return f"http://{phone_ip}:{port}/video"
    
    @staticmethod
    def get_all_ip_webcam_urls(phone_ip: str, port: int = 8080) -> list:
        """
        Get all common IP Webcam URL formats to try.
        
        Args:
            phone_ip: Phone's IP address
            port: Port number (default: 8080)
            
        Returns:
            List of URLs to try
        """
        return [
            f"http://{phone_ip}:{port}/video.mjpeg",  # Most reliable
            f"http://{phone_ip}:{port}/videofeed",
            f"http://{phone_ip}:{port}/video",
        ]
    
    @staticmethod
    def get_droidcam_url(phone_ip: str, port: int = 4747) -> str:
        """
        Get DroidCam stream URL.
        
        Args:
            phone_ip: Phone's IP address
            port: Port number (default: 4747)
            
        Returns:
            Stream URL
        """
        return f"http://{phone_ip}:{port}/video"
    
    @staticmethod
    def get_rtsp_url(phone_ip: str, port: int = 8554, path: str = "stream") -> str:
        """
        Get RTSP stream URL.
        
        Args:
            phone_ip: Phone's IP address
            port: Port number (default: 8554)
            path: Stream path (default: 'stream')
            
        Returns:
            RTSP URL
        """
        return f"rtsp://{phone_ip}:{port}/{path}"
    
    @staticmethod
    def test_connection(stream_url: str) -> Dict[str, Any]:
        """
        Test if phone stream is accessible.
        
        Args:
            stream_url: Stream URL to test
            
        Returns:
            Test results
        """
        logger.info(f"Testing connection to: {stream_url}")
        
        receiver = PhoneStreamReceiver()
        result = receiver.connect_to_phone_stream(stream_url)
        
        if result.get("success"):
            logger.info("✅ Connection successful!")
            logger.info(f"   Resolution: {result['width']}x{result['height']}")
            logger.info(f"   FPS: {result.get('fps', 'unknown')}")
        else:
            logger.error("❌ Connection failed!")
            logger.error(f"   Error: {result.get('error')}")
            if result.get('suggestions'):
                logger.info("   Suggestions:")
                for suggestion in result['suggestions']:
                    logger.info(f"     - {suggestion}")
        
        return result

