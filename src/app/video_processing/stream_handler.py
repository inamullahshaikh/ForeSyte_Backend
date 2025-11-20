"""
Video Stream Handler - UC-07: Process Exam Footage (Live/Recorded)
Handles both live CCTV feeds and uploaded exam recordings
"""

import cv2
import os
from datetime import datetime
from typing import Optional, Dict, Any
import asyncio
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoStreamHandler:
    """
    Handles video stream processing for both live and recorded footage.
    FR-31: Process both live CCTV feeds and uploaded recordings
    """
    
    def __init__(self, upload_dir: str = "uploads/videos", frame_dir: str = "uploads/frames"):
        # Use absolute paths to avoid OpenCV path resolution issues
        self.upload_dir = Path(upload_dir).resolve()
        self.frame_dir = Path(frame_dir).resolve()
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.frame_dir.mkdir(parents=True, exist_ok=True)
        
    def validate_video_input(self, source: str, stream_type: str) -> Dict[str, Any]:
        """
        Step 2 of UC-07: Validates video input and prepares it for analysis
        
        Args:
            source: Video file path or CCTV stream URL
            stream_type: 'live' or 'recorded'
            
        Returns:
            Dict with validation status and video properties
        """
        try:
            logger.info(f"[validate_video_input] Validating: {source}")
            logger.info(f"[validate_video_input] File exists: {os.path.exists(source)}")
            logger.info(f"[validate_video_input] Absolute path: {os.path.abspath(source)}")
            logger.info(f"[validate_video_input] Current working directory: {os.getcwd()}")
            
            cap = cv2.VideoCapture(source)
            
            if not cap.isOpened():
                error_msg = f"Unable to open video source: {source}"
                logger.error(f"[validate_video_input] {error_msg}")
                logger.error(f"[validate_video_input] Tried absolute: {os.path.abspath(source)}")
                return {
                    "valid": False,
                    "error": error_msg,
                    "source": source,
                    "absolute_path": os.path.abspath(source),
                    "file_exists": os.path.exists(source)
                }
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            logger.info(f"[validate_video_input] Success! FPS={fps}, Frames={frame_count}, Size={width}x{height}")
            
            cap.release()
            
            duration = frame_count / fps if fps > 0 and stream_type == 'recorded' else 0
            
            return {
                "valid": True,
                "fps": fps,
                "frame_count": frame_count if stream_type == 'recorded' else -1,
                "width": width,
                "height": height,
                "duration": duration,
                "stream_type": stream_type
            }
            
        except Exception as e:
            logger.error(f"[validate_video_input] Exception for {source}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "valid": False,
                "error": str(e),
                "source": source
            }
    
    def extract_frames(self, video_source: str, frame_rate: int = 1, 
                      job_id: str = None) -> list:
        """
        Extracts frames from video for analysis.
        Used in Step 3 of UC-07: Process video frames
        
        Args:
            video_source: Path to video file or stream URL
            frame_rate: Extract 1 frame per N frames (default: 1 = every frame)
            job_id: Processing job identifier
            
        Returns:
            List of extracted frame information
        """
        frames_info = []
        
        # Log video source for debugging
        logger.info(f"Attempting to open video: {video_source}")
        logger.info(f"Video source exists: {os.path.exists(video_source)}")
        logger.info(f"Current working directory: {os.getcwd()}")
        
        cap = cv2.VideoCapture(video_source)
        
        if not cap.isOpened():
            logger.error(f"Cannot open video source: {video_source}")
            logger.error(f"Tried absolute path: {os.path.abspath(video_source)}")
            return frames_info
        
        frame_number = 0
        extracted_count = 0
        
        try:
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                # Extract frame based on frame_rate
                if frame_number % frame_rate == 0:
                    timestamp = datetime.utcnow()
                    frame_filename = f"frame_{job_id}_{frame_number}_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
                    frame_path = self.frame_dir / frame_filename
                    
                    # Save frame
                    cv2.imwrite(str(frame_path), frame)
                    
                    frames_info.append({
                        "frame_number": frame_number,
                        "timestamp": timestamp,
                        "frame_path": str(frame_path),
                        "extracted": True
                    })
                    
                    extracted_count += 1
                    
                    if extracted_count % 100 == 0:
                        logger.info(f"Extracted {extracted_count} frames from job {job_id}")
                
                frame_number += 1
                
        except Exception as e:
            logger.error(f"Error extracting frames: {str(e)}")
        finally:
            cap.release()
            
        logger.info(f"Total frames extracted: {extracted_count} from {frame_number} total frames")
        return frames_info
    
    async def process_live_stream(self, stream_url: str, duration_seconds: int = 3600,
                                  callback=None) -> Dict[str, Any]:
        """
        Process live CCTV stream in real-time.
        Step 1 & 3 of UC-07: Connect to live CCTV and process in real-time
        
        Args:
            stream_url: CCTV camera stream URL (RTSP, HTTP, etc.)
            duration_seconds: How long to monitor (default: 1 hour)
            callback: Async function to call with each frame
            
        Returns:
            Processing statistics
        """
        cap = cv2.VideoCapture(stream_url)
        
        if not cap.isOpened():
            return {
                "success": False,
                "error": "Cannot connect to live stream",
                "stream_url": stream_url
            }
        
        start_time = datetime.utcnow()
        frame_count = 0
        processed_count = 0
        
        try:
            while (datetime.utcnow() - start_time).seconds < duration_seconds:
                ret, frame = cap.read()
                
                if not ret:
                    logger.warning("Failed to read frame from live stream")
                    await asyncio.sleep(0.1)
                    continue
                
                frame_count += 1
                
                # Process every Nth frame to optimize performance
                if frame_count % 30 == 0:  # Process 1 frame per second at 30fps
                    if callback:
                        await callback(frame, frame_count, datetime.utcnow())
                    processed_count += 1
                
                # Small delay to prevent overwhelming the system
                await asyncio.sleep(0.001)
                
        except Exception as e:
            logger.error(f"Error processing live stream: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "frames_captured": frame_count,
                "frames_processed": processed_count
            }
        finally:
            cap.release()
        
        return {
            "success": True,
            "frames_captured": frame_count,
            "frames_processed": processed_count,
            "duration": (datetime.utcnow() - start_time).seconds
        }
    
    def process_recorded_video(self, video_path: str, job_id: str,
                              progress_callback=None) -> Dict[str, Any]:
        """
        Process uploaded exam recording in batch mode.
        Step 1 & 3 of UC-07: Process uploaded recordings in batch
        
        Args:
            video_path: Path to uploaded video file
            job_id: Processing job identifier
            progress_callback: Function to update progress
            
        Returns:
            Processing results
        """
        logger.info(f"[process_recorded_video] Starting validation for: {video_path}")
        logger.info(f"[process_recorded_video] File exists: {os.path.exists(video_path)}")
        logger.info(f"[process_recorded_video] Absolute path: {os.path.abspath(video_path)}")
        
        validation = self.validate_video_input(video_path, 'recorded')
        
        logger.info(f"[process_recorded_video] Validation result: {validation}")
        
        if not validation['valid']:
            logger.error(f"[process_recorded_video] Validation failed: {validation.get('error')}")
            return {
                "success": False,
                "error": validation.get('error', 'Invalid video'),
                "video_path": video_path
            }
        
        total_frames = validation['frame_count']
        fps = validation['fps']
        
        logger.info(f"Processing recorded video: {video_path}")
        logger.info(f"Total frames: {total_frames}, FPS: {fps}")
        
        # Extract frames (every 30 frames = ~1 per second for 30fps video)
        frame_extraction_rate = max(1, int(fps))
        frames = self.extract_frames(video_path, frame_extraction_rate, job_id)
        
        # Update progress if callback provided
        if progress_callback:
            progress_callback(len(frames), total_frames)
        
        return {
            "success": True,
            "total_frames": total_frames,
            "extracted_frames": len(frames),
            "fps": fps,
            "duration": validation['duration'],
            "frames_info": frames
        }
    
    def save_uploaded_video(self, file_content: bytes, filename: str, 
                           exam_id: str, room_id: str) -> str:
        """
        Save uploaded video file with organized structure.
        
        Args:
            file_content: Video file bytes
            filename: Original filename
            exam_id: Exam identifier
            room_id: Room identifier
            
        Returns:
            Path to saved video file
        """
        # Create organized directory structure
        exam_dir = self.upload_dir / exam_id / room_id
        exam_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        file_extension = Path(filename).suffix
        new_filename = f"exam_footage_{timestamp}{file_extension}"
        
        file_path = exam_dir / new_filename
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Return absolute path to avoid OpenCV path resolution issues
        absolute_path = str(file_path.resolve())
        logger.info(f"Saved video to: {absolute_path}")
        return absolute_path
    
    def get_stream_info(self, source: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a video stream or file.
        
        Args:
            source: Video source (file path or stream URL)
            
        Returns:
            Dictionary with stream information or None
        """
        cap = cv2.VideoCapture(source)
        
        if not cap.isOpened():
            return None
        
        info = {
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "codec": int(cap.get(cv2.CAP_PROP_FOURCC))
        }
        
        cap.release()
        return info

