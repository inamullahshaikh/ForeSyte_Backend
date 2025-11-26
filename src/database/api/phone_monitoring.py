"""
Phone Camera Live Monitoring API
Handles live monitoring using phone camera feeds
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel
from uuid import UUID, uuid4
from datetime import datetime
from pathlib import Path
import logging
import os
import glob

from database.db import get_db
from database.auth import get_current_user
from app.live_phone_feeds.phone_processor import PhoneFeedProcessor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/phone-monitoring", tags=["Phone Monitoring"])

# Global state to track active monitoring sessions
active_monitoring: Dict[str, PhoneFeedProcessor] = {}

# -------------------------
# Request/Response Schemas
# -------------------------

class StartMonitoringRequest(BaseModel):
    stream_url: str
    exam_id: Optional[str] = None
    room_id: Optional[str] = None
    duration_seconds: int = 3600
    process_every_n_frames: int = 30

class StartMonitoringResponse(BaseModel):
    session_id: str
    status: str
    message: str
    stream_url: str

class MonitoringStatusResponse(BaseModel):
    session_id: str
    status: str
    is_active: bool
    frames_captured: int
    started_at: Optional[str] = None
    stream_url: Optional[str] = None

# -------------------------
# API Endpoints
# -------------------------

@router.post("/start", response_model=StartMonitoringResponse)
async def start_phone_monitoring(
    request: StartMonitoringRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Start live monitoring using phone camera feed.
    Only one active monitoring session at a time.
    """
    if current_user.get("user_type") not in ["admin", "investigator", "invigilator"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if there's already an active monitoring session
    if active_monitoring:
        # Stop existing session
        for session_id, processor in list(active_monitoring.items()):
            processor.stop_processing()
        active_monitoring.clear()
    
    # Generate new session ID
    session_id = str(uuid4())
    
    # Create processor
    processor = PhoneFeedProcessor(db_session=db, enable_ai=False, save_frames=True)
    
    # Start processing in background
    stream_id = f"phone-{session_id}"
    exam_id = request.exam_id or "default-exam"
    room_id = request.room_id or "default-room"
    
    # Store processor in active monitoring
    active_monitoring[session_id] = processor
    
    # Start processing as background task
    background_tasks.add_task(
        start_monitoring_task,
        processor=processor,
        session_id=session_id,
        stream_url=request.stream_url,
        stream_id=stream_id,
        exam_id=exam_id,
        room_id=room_id,
        duration_seconds=request.duration_seconds,
        process_every_n_frames=request.process_every_n_frames
    )
    
    return StartMonitoringResponse(
        session_id=session_id,
        status="started",
        message="Phone monitoring started successfully",
        stream_url=request.stream_url
    )


async def start_monitoring_task(
    processor: PhoneFeedProcessor,
    session_id: str,
    stream_url: str,
    stream_id: str,
    exam_id: str,
    room_id: str,
    duration_seconds: int,
    process_every_n_frames: int
):
    """Background task to start phone feed processing"""
    try:
        logger.info(f"Starting phone monitoring task: {session_id}")
        results = await processor.start_phone_feed_processing(
            stream_url=stream_url,
            stream_id=stream_id,
            exam_id=exam_id,
            room_id=room_id,
            duration_seconds=duration_seconds,
            process_every_n_frames=process_every_n_frames
        )
        
        if not results.get("success"):
            logger.error(f"Phone monitoring failed: {results.get('error')}")
            # Remove from active monitoring if failed
            if session_id in active_monitoring:
                del active_monitoring[session_id]
    except Exception as e:
        logger.error(f"Error in phone monitoring task: {e}", exc_info=True)
        if session_id in active_monitoring:
            del active_monitoring[session_id]
    finally:
        # Remove from active monitoring when done
        if session_id in active_monitoring:
            del active_monitoring[session_id]


@router.post("/stop/{session_id}")
async def stop_phone_monitoring(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Stop active phone monitoring session.
    """
    if current_user.get("user_type") not in ["admin", "investigator", "invigilator"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if session_id not in active_monitoring:
        raise HTTPException(status_code=404, detail="Monitoring session not found")
    
    processor = active_monitoring[session_id]
    processor.stop_processing()
    del active_monitoring[session_id]
    
    return {"status": "stopped", "message": "Monitoring stopped successfully"}


@router.get("/status/{session_id}", response_model=MonitoringStatusResponse)
async def get_monitoring_status(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get status of active monitoring session.
    """
    if current_user.get("user_type") not in ["admin", "investigator", "invigilator"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if session_id not in active_monitoring:
        return MonitoringStatusResponse(
            session_id=session_id,
            status="not_found",
            is_active=False,
            frames_captured=0
        )
    
    processor = active_monitoring[session_id]
    stream_id = f"phone-{session_id}"
    
    # Get real-time frame count if available
    live_frame_count = processor.live_frame_count.get(stream_id, 0)
    live_stream_url = processor.live_stream_url.get(stream_id)
    
    # Fallback: Count frames from directory if live count is 0
    if live_frame_count == 0:
        try:
            frame_dir = Path(processor.frame_dir)
            pattern = f"phone_{stream_id}_*.jpg"
            frame_files = list(frame_dir.glob(pattern))
            if frame_files:
                live_frame_count = len(frame_files)
        except Exception as e:
            logger.debug(f"Error counting frames from directory: {e}")
    
    # Try to get from saved results (if processing completed)
    results = processor.get_processing_results(stream_id)
    
    # Use live count if available, otherwise use results
    frames_captured = live_frame_count if live_frame_count > 0 else (results.get("frames_captured", 0) if results else 0)
    stream_url = live_stream_url or (results.get("stream_url") if results else None)
    
    return MonitoringStatusResponse(
        session_id=session_id,
        status="active" if processor.is_processing else "stopped",
        is_active=processor.is_processing,
        frames_captured=frames_captured,
        started_at=results.get("started_at") if results else None,
        stream_url=stream_url
    )


@router.get("/active")
async def get_active_monitoring(
    current_user: dict = Depends(get_current_user)
):
    """
    Get all active monitoring sessions (should be only one).
    """
    if current_user.get("user_type") not in ["admin", "investigator", "invigilator"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    active_sessions = []
    for session_id, processor in active_monitoring.items():
        stream_id = f"phone-{session_id}"
        
        # Get real-time frame count
        live_frame_count = processor.live_frame_count.get(stream_id, 0)
        live_stream_url = processor.live_stream_url.get(stream_id)
        
        # Try to get from saved results (if processing completed)
        results = processor.get_processing_results(stream_id)
        
        # Use live count if available, otherwise use results
        frames_captured = live_frame_count if live_frame_count > 0 else (results.get("frames_captured", 0) if results else 0)
        stream_url = live_stream_url or (results.get("stream_url") if results else None)
        
        active_sessions.append({
            "session_id": session_id,
            "status": "active" if processor.is_processing else "stopped",
            "is_active": processor.is_processing,
            "frames_captured": frames_captured,
            "stream_url": stream_url
        })
    
    return {"active_sessions": active_sessions, "count": len(active_sessions)}


@router.get("/latest-frame/{session_id}")
async def get_latest_frame(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get the latest saved frame from active monitoring session.
    Returns the most recent frame as JPEG image.
    """
    if current_user.get("user_type") not in ["admin", "investigator", "invigilator"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if session_id not in active_monitoring:
        raise HTTPException(status_code=404, detail="Monitoring session not found")
    
    processor = active_monitoring[session_id]
    stream_id = f"phone-{session_id}"
    
    # Get the latest frame from saved frames
    frame_dir = Path(processor.frame_dir)
    
    if not frame_dir.exists():
        raise HTTPException(status_code=404, detail=f"Frame directory not found: {frame_dir}")
    
    # Search for frames with this stream_id - pattern matches saved frame format
    # Saved frames: phone_phone-{session_id}_{frame_num}_{timestamp}.jpg
    pattern = f"phone_{stream_id}_*.jpg"
    frame_files = list(frame_dir.glob(pattern))
    
    if not frame_files:
        # Try alternative pattern in case format is slightly different
        alt_pattern = f"*{stream_id}*.jpg"
        frame_files = list(frame_dir.glob(alt_pattern))
    
    if not frame_files:
        # Try to find any frames with phone_ prefix as last resort
        all_phone_frames = list(frame_dir.glob("phone_*.jpg"))
        if all_phone_frames:
            # Get the most recent one (might be from a different session but better than nothing)
            latest_frame = max(all_phone_frames, key=os.path.getmtime)
            logger.info(f"Using fallback frame: {latest_frame} for session {session_id}")
            return FileResponse(
                path=str(latest_frame),
                media_type="image/jpeg",
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                    "Access-Control-Allow-Origin": "*"
                }
            )
        
        # Return 404 but with helpful message
        logger.debug(f"No frames found for session {session_id} in {frame_dir} with pattern {pattern}")
        raise HTTPException(
            status_code=404, 
            detail=f"No frames found yet. Frames are being captured. Please wait a moment."
        )
    
    # Get the most recent frame (by modification time)
    latest_frame = max(frame_files, key=os.path.getmtime)
    
    if not latest_frame.exists():
        raise HTTPException(status_code=404, detail="Latest frame file not found")
    
    logger.debug(f"Serving latest frame: {latest_frame} for session {session_id}")
    
    return FileResponse(
        path=str(latest_frame),
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Access-Control-Allow-Origin": "*"
        }
    )

