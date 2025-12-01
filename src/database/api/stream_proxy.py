"""
Stream Proxy for Phone Camera Feeds
Proxies MJPEG streams to avoid CORS issues in browsers
"""

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
import requests
import logging
from typing import Iterator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stream-proxy", tags=["Stream Proxy"])


@router.get("/mjpeg")
def proxy_mjpeg_stream(
    url: str = Query(..., description="Stream URL to proxy")
):
    """
    Proxy MJPEG stream from phone camera to avoid CORS issues.
    
    Usage:
        /stream-proxy/mjpeg?url=http://192.168.1.100:8080/video.mjpeg
    """
    def generate() -> Iterator[bytes]:
        try:
            logger.info(f"Proxying MJPEG stream from: {url}")
            # Stream the request with streaming enabled
            response = requests.get(url, stream=True, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0',
                'Accept': '*/*'
            })
            response.raise_for_status()
            
            # Get content type from source, or default to MJPEG
            content_type = response.headers.get('Content-Type', 'multipart/x-mixed-replace')
            
            logger.info(f"Stream connected successfully, Content-Type: {content_type}")
            
            # Stream chunks of data
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
                    
        except requests.exceptions.Timeout:
            logger.error(f"Timeout connecting to stream: {url}")
            error_msg = b"Stream Error: Connection timeout"
            yield error_msg
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error to stream {url}: {e}")
            error_msg = b"Stream Error: Cannot connect to camera"
            yield error_msg
        except requests.exceptions.RequestException as e:
            logger.error(f"Error proxying stream {url}: {e}")
            error_msg = f"Stream Error: {str(e)}".encode()
            yield error_msg
        except Exception as e:
            logger.error(f"Unexpected error proxying stream: {e}")
            error_msg = f"Stream Error: {str(e)}".encode()
            yield error_msg
    
    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=--BoundaryString",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

