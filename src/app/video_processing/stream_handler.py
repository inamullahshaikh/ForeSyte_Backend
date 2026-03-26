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
import json
import numpy as np

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
        
        # Path to seating plan directory
        self.seating_plan_dir = Path(__file__).parent.parent / "seating_plan"
        self.csfyp_dir = self.seating_plan_dir / "CSFYP"
        
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
    
    def get_seat_map_for_room(self, room_id: Optional[str], frame_width: int, frame_height: int, db_session=None) -> Optional[Dict[str, list]]:
        """
        Load and scale seat map for a room. Used for bbox-to-student mapping.
        Returns dict of seat_map_key -> polygon points, or None.
        """
        if not room_id or not db_session:
            return None
        try:
            from database.models import Room
            from uuid import UUID
            
            room = db_session.query(Room).filter(Room.room_id == UUID(room_id)).first()
            if not room:
                return None
            room_no = f"{room.block}-{room.room_number}" if room.block else room.room_number
            seat_map_path = self._get_room_paths(room_no)
            if seat_map_path:
                return self._load_seat_map(seat_map_path, frame_width, frame_height)
        except Exception as e:
            logger.error(f"Error loading seat map for room: {e}")
        return None

    def _get_room_paths(self, room_no: str):
        """
        Get room-specific seat_map.json path based on room number.
        Helper function similar to upload_plan.py get_room_paths.
        
        Args:
            room_no: Room number like "A-104", "A104", "B-127", "C-301", "C-311", "D-314"
        
        Returns:
            seat_map_path or None if not found
        """
        # Normalize room number (handle both "A-104" and "A104" formats)
        room_no_upper = room_no.upper().replace('-', '').replace(' ', '')
        room_block = room_no_upper[0] if room_no_upper and room_no_upper[0].isalpha() else None
        room_num = room_no_upper[1:] if len(room_no_upper) > 1 else None
        
        if not room_block or not room_num:
            return None
        
        # Determine which CSFYP folder to use
        if room_block == 'A':
            room_folder = self.csfyp_dir / "A104-25112025"
        elif room_block == 'B':
            room_folder = self.csfyp_dir / "B127-25112025"
        elif room_block == 'C':
            if room_num == '311':
                room_folder = self.csfyp_dir / "C311-25112025"
            else:
                room_folder = self.csfyp_dir / "C301-25112025"
        elif room_block == 'D':
            room_folder = self.csfyp_dir / "D314-25112025"
        else:
            return None
        
        # Find seat_map.json
        seat_map_path = room_folder / "seat_map.json"
        if not seat_map_path.exists():
            logger.warning(f"Seat map not found at {seat_map_path}")
            return None
        
        return seat_map_path
    
    def _load_seat_map(self, seat_map_path: Path, frame_width: int, frame_height: int):
        """
        Load seat map JSON and scale coordinates to match frame dimensions.
        
        Args:
            seat_map_path: Path to seat_map.json file
            frame_width: Width of the video frame
            frame_height: Height of the video frame
        
        Returns:
            Dictionary of seat_id -> scaled polygon points, or None if error
        """
        try:
            with open(seat_map_path, 'r', encoding='utf-8') as f:
                seat_map_data = json.load(f)
            
            seats = seat_map_data.get('seats', {})
            meta = seat_map_data.get('_meta', {})
            base_w = meta.get('base_w', frame_width)
            base_h = meta.get('base_h', frame_height)
            
            # Calculate scaling factors
            scale_x = frame_width / base_w if base_w > 0 else 1.0
            scale_y = frame_height / base_h if base_h > 0 else 1.0
            
            # Scale all seat polygons
            scaled_seats = {}
            for seat_id, polygon in seats.items():
                if polygon and len(polygon) >= 3:
                    scaled_polygon = [
                        [int(point[0] * scale_x), int(point[1] * scale_y)]
                        for point in polygon if len(point) >= 2
                    ]
                    if len(scaled_polygon) >= 3:
                        scaled_seats[seat_id] = scaled_polygon
            
            logger.info(f"Loaded {len(scaled_seats)} seats from seat map, scaled from {base_w}x{base_h} to {frame_width}x{frame_height}")
            return scaled_seats
            
        except Exception as e:
            logger.error(f"Error loading seat map: {str(e)}")
            return None
    
    def _draw_seat_boxes(self, frame, seat_map: Dict[str, list]):
        """
        Draw green bounding boxes (polygons) on frame for each seat.
        
        Args:
            frame: OpenCV frame (numpy array)
            seat_map: Dictionary of seat_id -> polygon points
        """
        if not seat_map:
            return
        
        for seat_id, polygon in seat_map.items():
            if len(polygon) < 3:
                continue
            
            # Convert to numpy array for OpenCV
            pts = np.array(polygon, np.int32)
            
            # Draw green polygon outline
            cv2.polylines(frame, [pts], True, (0, 255, 0), 2)
    
    def extract_frames(self, video_source: str, frame_rate: int = 1, 
                      job_id: str = None, progress_callback=None, 
                      room_id: Optional[str] = None, db_session=None) -> list:
        """
        Extracts frames from video for analysis.
        Used in Step 3 of UC-07: Process video frames
        
        Args:
            video_source: Path to video file or stream URL
            frame_rate: Extract 1 frame per N frames (default: 1 = every frame)
            job_id: Processing job identifier
            progress_callback: Callback function for progress updates
            room_id: Room UUID to get seating plan (optional)
            db_session: Database session to query room info (optional)
            
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
        
        # Get video dimensions for seat map scaling
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Load seat map if room_id is provided
        seat_map = None
        if room_id and db_session:
            try:
                from database.models import Room
                from uuid import UUID
                
                room = db_session.query(Room).filter(Room.room_id == UUID(room_id)).first()
                if room:
                    # Construct room number from block and room_number
                    room_no = f"{room.block}-{room.room_number}" if room.block else room.room_number
                    logger.info(f"Loading seat map for room: {room_no}")
                    
                    seat_map_path = self._get_room_paths(room_no)
                    if seat_map_path:
                        seat_map = self._load_seat_map(seat_map_path, frame_width, frame_height)
                        if seat_map:
                            logger.info(f"Successfully loaded seat map with {len(seat_map)} seats")
                        else:
                            logger.warning("Failed to load seat map data")
                    else:
                        logger.warning(f"Seat map file not found for room {room_no}")
                else:
                    logger.warning(f"Room not found in database for room_id: {room_id}")
            except Exception as e:
                logger.error(f"Error loading seat map: {str(e)}")
                import traceback
                traceback.print_exc()
        
        frame_number = 0
        extracted_count = 0
        
        # Get total frame count for progress tracking
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # Calculate expected number of extracted frames
        expected_extracted_frames = (total_frames // frame_rate) + (1 if total_frames % frame_rate > 0 else 0)
        logger.info(f"Video has {total_frames} total frames, extracting every {frame_rate} frames (expected: ~{expected_extracted_frames} frames)")
        
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
                    
                    # Draw seat bounding boxes if seat map is available
                    if seat_map:
                        frame_copy = frame.copy()
                        self._draw_seat_boxes(frame_copy, seat_map)
                        # Save annotated frame
                        cv2.imwrite(str(frame_path), frame_copy)
                    else:
                        # Save frame without annotations
                        cv2.imwrite(str(frame_path), frame)
                    
                    frames_info.append({
                        "frame_number": frame_number,
                        "timestamp": timestamp,
                        "frame_path": str(frame_path),
                        "extracted": True,
                        "annotated": seat_map is not None
                    })
                    
                    extracted_count += 1
                    
                    # Call progress callback if provided (every frame or at milestones)
                    if progress_callback:
                        try:
                            # Use expected extracted frames for progress, not total video frames
                            progress_callback(extracted_count, expected_extracted_frames)
                        except Exception as e:
                            logger.warning(f"Progress callback error: {e}")
                    
                    if extracted_count % 100 == 0:
                        logger.info(f"Extracted {extracted_count} frames from job {job_id} (out of ~{total_frames // frame_rate} expected)")
                
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
                              progress_callback=None, room_id: Optional[str] = None,
                              db_session=None) -> Dict[str, Any]:
        """
        Process uploaded exam recording in batch mode.
        Step 1 & 3 of UC-07: Process uploaded recordings in batch
        
        Args:
            video_path: Path to uploaded video file
            job_id: Processing job identifier
            progress_callback: Function to update progress (called during extraction)
            room_id: Room UUID to get seating plan (optional)
            db_session: Database session to query room info (optional)
            
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
        
        # Extract 1 frame per second: take every Nth frame where N = fps
        frame_extraction_rate = max(1, int(fps))
        
        # Calculate expected extracted frames
        expected_extracted = (total_frames // frame_extraction_rate) + (1 if total_frames % frame_extraction_rate > 0 else 0)
        
        # Notify callback of expected extracted frames before extraction starts
        if progress_callback:
            try:
                progress_callback(0, expected_extracted)
            except Exception as e:
                logger.warning(f"Progress callback error at start: {e}")
        
        frames = self.extract_frames(video_path, frame_extraction_rate, job_id, progress_callback, 
                                    room_id=room_id, db_session=db_session)
        
        # Final progress update
        if progress_callback:
            try:
                progress_callback(len(frames), expected_extracted)
            except Exception as e:
                logger.warning(f"Progress callback error at end: {e}")
        
        # Load seat map for bbox-to-student mapping (same dimensions as video frames)
        frame_width = validation.get('width', 1920)
        frame_height = validation.get('height', 1080)
        seat_map = self.get_seat_map_for_room(room_id, frame_width, frame_height, db_session)
        
        return {
            "success": True,
            "total_frames": total_frames,
            "extracted_frames": len(frames),
            "fps": fps,
            "duration": validation['duration'],
            "frames_info": frames,
            "seat_map": seat_map,
            "frame_width": frame_width,
            "frame_height": frame_height,
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

