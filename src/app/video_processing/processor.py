"""
Video Processing Orchestrator - Complete UC-07 Implementation
Coordinates video processing, AI detection, and database logging
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from collections import defaultdict
import json
import asyncio
import logging
from pathlib import Path

import cv2

from .stream_handler import VideoStreamHandler
from database.severity_logic import (
    get_runs_from_detections,
    filter_qualifying_runs,
    compute_severity_from_count,
    severity_to_int,
)

logging.basicConfig(level=logging.INFO)


def _evidence_path_to_url(file_path: Optional[str]) -> Optional[str]:
    """Convert filesystem path to frontend-accessible URL (/uploads/...)."""
    if not file_path:
        return None
    path = str(file_path).replace("\\", "/")
    if "uploads" in path:
        idx = path.find("uploads")
        return "/" + path[idx:]
    return path
logger = logging.getLogger(__name__)


class VideoProcessor:
    """
    Main orchestrator for UC-07: Process Exam Footage (Live/Recorded)
    Coordinates all steps from video input to final report generation
    """
    
    def __init__(self, db_session=None, enable_ai=False):
        """
        Initialize video processor with all components.
        
        Args:
            db_session: Database session for logging activities
            enable_ai: Enable AI detection (default: False for testing input)
        """
        self.stream_handler = VideoStreamHandler()
        self.enable_ai = enable_ai
        if enable_ai:
            try:
                from app.ai_engine.detection_adapter import process_frame, map_detection_to_seat
                self.process_frame = process_frame
                self.map_detection_to_seat = map_detection_to_seat
                self.behavior_detector = True  # Flag that AI is available
            except ImportError as e:
                logger.warning("AI engine module not found. AI detection disabled. %s", e)
                self.enable_ai = False
                self.process_frame = None
                self.map_detection_to_seat = None
                self.behavior_detector = None
        else:
            self.process_frame = None
            self.map_detection_to_seat = None
            self.behavior_detector = None
        self.db_session = db_session
        self.processing_results = {}
        self.progress_callback = None  # Callback to update progress during processing
        
    def set_progress_callback(self, callback):
        """Set callback function to update progress during frame extraction"""
        self.progress_callback = callback
        
    async def process_video_stream(self, stream_id: str, source: str, 
                                   stream_type: str, exam_id: str,
                                   room_id: str, seat_mapping: Dict = None) -> Dict[str, Any]:
        """
        Complete UC-07 Main Success Scenario (Steps 1-10)
        
        Args:
            stream_id: Video stream identifier
            source: Video source (file path or stream URL)
            stream_type: 'live' or 'recorded'
            exam_id: Exam identifier
            room_id: Room identifier  
            seat_mapping: Seat position mapping
            
        Returns:
            Complete processing results
        """
        logger.info(f"Starting video processing for stream {stream_id}")
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Connect to video source
            # Step 2: Validate video input
            validation = self.stream_handler.validate_video_input(source, stream_type)
            
            if not validation['valid']:
                return {
                    "success": False,
                    "error": validation.get('error', 'Invalid video source'),
                    "stream_id": stream_id
                }
            
            logger.info(f"Video validated: {validation}")
            
            # Initialize results
            results = {
                "stream_id": stream_id,
                "exam_id": exam_id,
                "room_id": room_id,
                "stream_type": stream_type,
                "started_at": start_time.isoformat(),
                "validation": validation,
                "activities_logged": [],
                "violations_detected": [],
                "frame_analysis": []
            }
            
            # Step 3-6: Process video based on type
            if stream_type == 'live':
                processing_result = await self._process_live_footage(
                    stream_id, source, exam_id, room_id, seat_mapping
                )
            else:  # recorded
                processing_result = await self._process_recorded_footage(
                    stream_id, source, exam_id, room_id, seat_mapping
                )
            
            results.update(processing_result)
            
            # Step 7-10: Results accessible through reports API
            results['completed_at'] = datetime.utcnow().isoformat()
            results['success'] = True
            
            # Store results
            self.processing_results[stream_id] = results
            
            logger.info(f"Processing completed for stream {stream_id}")
            logger.info(f"Total activities: {len(results['activities_logged'])}")
            logger.info(f"Total violations: {len(results['violations_detected'])}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing stream {stream_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "stream_id": stream_id,
                "completed_at": datetime.utcnow().isoformat()
            }
    
    async def _process_live_footage(self, stream_id: str, stream_url: str,
                                   exam_id: str, room_id: str,
                                   seat_mapping: Dict = None) -> Dict[str, Any]:
        """
        Process live CCTV footage (real-time processing).
        Steps 3-6 of UC-07 for live streams.
        
        Args:
            stream_id: Stream identifier
            stream_url: CCTV stream URL
            exam_id: Exam identifier
            room_id: Room identifier
            seat_mapping: Seat position mapping
            
        Returns:
            Processing results
        """
        logger.info(f"Processing live stream: {stream_url}")

        activities = []
        violations = []
        frame_count = 0
        detections_by_student_live: Dict[str, List[Dict]] = defaultdict(list)

        async def frame_callback(frame, frame_num, timestamp):
            """Process each frame: collect detections per student for run-based logic."""
            nonlocal frame_count

            if self.enable_ai and self.process_frame:
                analysis = self.process_frame(
                    frame, frame_num, timestamp, seat_mapping
                )
                student_behaviors = analysis.get('student_behaviors', [])
                invigilator_behaviors = analysis.get('invigilator_behaviors', [])
            else:
                logger.info(f"Frame {frame_num} captured (AI detection disabled)")
                student_behaviors = []
                invigilator_behaviors = []

            for behavior in student_behaviors:
                seat_id = self.map_detection_to_seat(behavior, seat_mapping) if (self.enable_ai and self.map_detection_to_seat) else None
                student_id = (behavior.get('student_id') or (seat_id if isinstance(seat_id, str) else None))
                detection = {
                    "timestamp": timestamp.isoformat(),
                    "frame_number": frame_num,
                    "behavior_type": behavior['behavior_type'],
                    "severity": behavior['severity'],
                    "confidence": behavior['confidence'],
                    "seat_id": seat_id,
                    "student_id": str(student_id) if student_id else None,
                    "details": behavior.get('details', ''),
                    "actor_type": "student",
                }
                key = str(student_id) if student_id else "unidentified"
                detections_by_student_live[key].append(detection)

            for behavior in invigilator_behaviors:
                activity = {
                    "timestamp": timestamp.isoformat(),
                    "frame_number": frame_num,
                    "behavior_type": behavior['behavior_type'],
                    "severity": behavior['severity'],
                    "confidence": behavior['confidence'],
                    "details": behavior.get('details', ''),
                    "actor_type": "invigilator",
                }
                activities.append(activity)
                if self.db_session:
                    await self._log_invigilator_activity_to_db(activity, room_id)

            frame_count += 1
            if frame_count % 100 == 0:
                logger.info(f"Processed {frame_count} frames")

        stream_result = await self.stream_handler.process_live_stream(
            stream_url, duration_seconds=3600, callback=frame_callback
        )

        # Run-based logic: one activity + one violation per qualifying run per student
        for student_key, det_list in detections_by_student_live.items():
            runs = get_runs_from_detections(det_list)
            qualifying = filter_qualifying_runs(runs)
            for run in qualifying:
                fd = run.first_detection
                severity_str = compute_severity_from_count(run.frame_count, run.label_raw)
                activity = {
                    "timestamp": fd.get("timestamp"),
                    "frame_number": fd.get("frame_number"),
                    "behavior_type": run.label_raw,
                    "severity": severity_str,
                    "confidence": fd.get("confidence"),
                    "seat_id": fd.get("seat_id"),
                    "student_id": fd.get("student_id") if student_key != "unidentified" else None,
                    "details": fd.get("details", "") or f"({run.frame_count} consecutive frames)",
                    "actor_type": "student",
                }
                activities.append(activity)
                violations.append({
                    "activity": activity,
                    "violation_type": run.label_raw,
                    "severity_level": severity_to_int(severity_str),
                    "status": "pending",
                    "timestamp": fd.get("timestamp"),
                })
                if self.db_session:
                    await self._log_activity_and_violation(
                        activity, exam_id, room_id,
                        create_violation=True,
                    )

        return {
            "stream_result": stream_result,
            "activities_logged": activities,
            "violations_detected": violations,
            "total_frames_processed": frame_count,
            "total_frames_in_video": frame_count
        }
    
    async def _process_recorded_footage(self, stream_id: str, video_path: str,
                                       exam_id: str, room_id: str,
                                       seat_mapping: Dict = None) -> Dict[str, Any]:
        """
        Process recorded exam footage (batch processing).
        Steps 3-6 of UC-07 for recorded videos.
        
        Args:
            stream_id: Stream identifier
            video_path: Path to recorded video file
            exam_id: Exam identifier
            room_id: Room identifier
            seat_mapping: Seat position mapping
            
        Returns:
            Processing results
        """
        logger.info(f"Processing recorded video: {video_path}")

        # Collect detections per student (frame sequence) for run-based violation logic
        detections_by_student: Dict[str, List[Dict]] = defaultdict(list)
        activities = []
        violations = []
        frame_analyses = []
        
        # Extract and process frames
        def progress_callback(processed, total):
            progress = (processed / total * 100) if total > 0 else 0
            logger.info(f"Progress: {progress:.1f}% ({processed}/{total} frames)")
            # Call external progress callback if set (for database updates)
            if self.progress_callback:
                try:
                    self.progress_callback(processed, total)
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")
        
        # Step 3: Process video frames in batch mode
        # Pass progress_callback, room_id, and db_session to stream_handler which will call it during frame extraction
        extraction_result = self.stream_handler.process_recorded_video(
            video_path, stream_id, progress_callback, 
            room_id=room_id, db_session=self.db_session
        )
        
        if not extraction_result['success']:
            return {
                "success": False,
                "error": extraction_result.get('error', 'Failed to extract frames')
            }
        
        frames_info = extraction_result['frames_info']
        total_frames_in_video = extraction_result.get('total_frames', len(frames_info))
        logger.info(f"Extracted {len(frames_info)} frames for analysis (out of {total_frames_in_video} total frames in video)")
        
        # Build seat mapper for bbox -> student resolution (seating plan coordinates)
        seat_mapper = None
        if extraction_result.get('seat_map') and self.db_session:
            from uuid import UUID
            from app.video_processing.seat_mapper import SeatMapper
            from database.models import Room

            room = self.db_session.query(Room).filter(Room.room_id == UUID(room_id)).first()
            room_no = f"{room.block}-{room.room_number}" if room and room.block else (room.room_number if room else "")
            seat_mapper = SeatMapper(
                extraction_result['seat_map'],
                room_id,
                exam_id,
                self.db_session,
                room_no=room_no,
            )
            logger.info("Seat mapper initialized for student identification")
        
        # Step 4: AI engine processes each frame
        for idx, frame_info in enumerate(frames_info):
            frame_path = frame_info['frame_path']
            frame_number = frame_info['frame_number']
            timestamp = frame_info['timestamp']
            
            if self.enable_ai and self.process_frame:
                # Load frame
                import cv2
                frame = cv2.imread(frame_path)
                
                if frame is None:
                    logger.warning(f"Failed to load frame: {frame_path}")
                    continue
                
                # Analyze frame with cheating detection (request annotated for evidence)
                analysis = self.process_frame(
                    frame, frame_number, timestamp, return_annotated=True
                )
                
                # Default: use local path as evidence URL
                evidence_url_preferred = _evidence_path_to_url(frame_path)
                # Save annotated frame when suspicious activity detected (evidence)
                if analysis.get("annotated_frame") is not None:
                    ann_path = str(Path(frame_path).with_suffix("")) + "_detection.jpg"
                    cv2.imwrite(ann_path, analysis["annotated_frame"])
                    frame_path = ann_path  # Use annotated frame as evidence
                    # Upload to Backblaze B2 when configured (preserves evidence in cloud)
                    try:
                        from app.storage.b2_storage import upload_evidence_frame
                        b2_url = upload_evidence_frame(ann_path)
                        evidence_url_preferred = b2_url if b2_url else _evidence_path_to_url(ann_path)
                    except Exception as e:
                        logger.debug("B2 upload skipped or failed: %s", e)
                        evidence_url_preferred = _evidence_path_to_url(ann_path)
                
                frame_analyses.append({
                    "frame_number": frame_number,
                    "timestamp": timestamp.isoformat(),
                    "detections": len(analysis['student_behaviors']) + len(analysis['invigilator_behaviors'])
                })
                
                # Step 5 & 6: Process detections, map to seats, and log
                student_behaviors = analysis.get('student_behaviors', [])
                invigilator_behaviors = analysis.get('invigilator_behaviors', [])
            else:
                # Skip AI detection - just log frame extraction
                frame_analyses.append({
                    "frame_number": frame_number,
                    "timestamp": timestamp.isoformat(),
                    "frame_path": frame_path,
                    "detections": 0
                })
                student_behaviors = []
                invigilator_behaviors = []
                logger.info(f"Frame {frame_number} extracted (AI disabled)")
            
            # Process student behaviors: collect per student for frame-run logic (one violation per run)
            for behavior in student_behaviors:
                seat_id = None
                student_id = None
                if seat_mapper and behavior.get('bbox'):
                    result = seat_mapper.get_student_for_bbox(behavior['bbox'])
                    if result:
                        seat_id, student_id = result

                detection = {
                    "timestamp": timestamp.isoformat(),
                    "frame_number": frame_number,
                    "behavior_type": behavior['behavior_type'],
                    "severity": behavior['severity'],
                    "confidence": behavior['confidence'],
                    "seat_id": seat_id,
                    "student_id": str(student_id) if student_id else None,
                    "details": behavior.get('details', ''),
                    "evidence_path": frame_path,
                    "evidence_url": evidence_url_preferred,
                    "actor_type": "student",
                }
                key = str(student_id) if student_id else "unidentified"
                detections_by_student[key].append(detection)
            
            # Process invigilator behaviors
            for behavior in invigilator_behaviors:
                activity = {
                    "timestamp": timestamp.isoformat(),
                    "frame_number": frame_number,
                    "behavior_type": behavior['behavior_type'],
                    "severity": behavior['severity'],
                    "confidence": behavior['confidence'],
                    "details": behavior.get('details', ''),
                    "evidence_path": frame_path,
                    "actor_type": "invigilator"
                }
                activities.append(activity)
                
                if self.db_session:
                    await self._log_invigilator_activity_to_db(activity, room_id)
            
            # Progress logging
            if (idx + 1) % 10 == 0:
                logger.info(f"Analyzed {idx + 1}/{len(frames_info)} frames")

        # Run-based logic: one activity + one violation per qualifying run per student (no redundant per-frame)
        for student_key, det_list in detections_by_student.items():
            runs = get_runs_from_detections(det_list)
            qualifying = filter_qualifying_runs(runs)
            for run in qualifying:
                fd = run.first_detection
                severity_str = compute_severity_from_count(run.frame_count, run.label_raw)
                activity = {
                    "timestamp": fd.get("timestamp"),
                    "frame_number": fd.get("frame_number"),
                    "behavior_type": run.label_raw,
                    "severity": severity_str,
                    "confidence": fd.get("confidence"),
                    "seat_id": fd.get("seat_id"),
                    "student_id": fd.get("student_id") if student_key != "unidentified" else None,
                    "details": fd.get("details", "") or f"({run.frame_count} consecutive frames)",
                    "evidence_path": fd.get("evidence_path"),
                    "evidence_url": fd.get("evidence_url"),
                    "actor_type": "student",
                }
                activities.append(activity)
                violations.append({
                    "activity": activity,
                    "violation_type": run.label_raw,
                    "severity_level": severity_to_int(severity_str),
                    "status": "pending",
                    "evidence_url": fd.get("evidence_url") or fd.get("evidence_path"),
                    "timestamp": fd.get("timestamp"),
                })
                if self.db_session:
                    await self._log_activity_and_violation(
                        activity, exam_id, room_id,
                        create_violation=True,
                    )

        return {
            "success": True,
            "activities_logged": activities,
            "violations_detected": violations,
            "frame_analysis": frame_analyses,
            "total_frames_analyzed": len(frames_info),
            "total_frames_processed": len(frames_info),
            "total_frames_in_video": extraction_result.get('total_frames', len(frames_info)),
            "extraction_result": extraction_result
        }
    
    def _get_or_create_unidentified_student(self):
        """Get or create a placeholder student for unmapped detections."""
        from database.models import Student

        UNIDENTIFIED_EMAIL = "unidentified-ai-detection@foresyte.system"
        student = self.db_session.query(Student).filter(
            Student.email == UNIDENTIFIED_EMAIL
        ).first()
        if not student:
            student = Student(
                name="Unidentified (AI Detection)",
                email=UNIDENTIFIED_EMAIL,
                roll_number="UNIDENTIFIED-AI",
            )
            self.db_session.add(student)
            self.db_session.commit()
            self.db_session.refresh(student)
            logger.info("Created Unidentified placeholder student for unmapped detections")
        return str(student.student_id)

    async def _log_activity_and_violation(
        self, activity: Dict, exam_id: str, room_id: str, create_violation: bool = False
    ):
        """
        Step 6 of UC-07: Store StudentActivity and optionally Violation in database.
        Uses student_id from seat mapping when available; otherwise uses Unidentified placeholder.
        """
        if not self.db_session:
            return
        student_id = activity.get("student_id")
        if not student_id:
            student_id = self._get_or_create_unidentified_student()
            logger.debug(
                "No seat mapping for %s - saving as Unidentified",
                activity.get("behavior_type")
            )
        try:
            from uuid import UUID
            from database.models import StudentActivity, Violation

            ts = activity.get("timestamp")
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00")) if "T" in ts else datetime.fromisoformat(ts)
            else:
                ts = ts or datetime.utcnow()

            raw = activity.get("evidence_url") or activity.get("evidence_path")
            if raw and (str(raw).startswith("http://") or str(raw).startswith("https://")):
                evidence_url = raw  # Already a full URL (e.g. B2)
            else:
                evidence_url = _evidence_path_to_url(raw)
            student_activity = StudentActivity(
                student_id=UUID(student_id),
                exam_id=UUID(exam_id),
                activity_type=activity.get("behavior_type"),
                severity=activity.get("severity"),
                confidence=activity.get("confidence"),
                evidence_url=evidence_url,
                timestamp=ts,
            )
            self.db_session.add(student_activity)
            self.db_session.commit()
            self.db_session.refresh(student_activity)
            logger.info(
                "Logged activity to DB: %s for student %s",
                activity["behavior_type"],
                student_id
            )

            if create_violation:
                violation = Violation(
                    activity_id=student_activity.activity_id,
                    violation_type=activity.get("behavior_type"),
                    timestamp=ts,
                    severity=3,
                    status="pending",
                    evidence_url=evidence_url,
                )
                self.db_session.add(violation)
                self.db_session.commit()
                logger.info("Created violation for %s (student %s)", activity["behavior_type"], student_id)
        except Exception as e:
            logger.warning("Failed to log activity/violation to DB: %s", e)
            if self.db_session:
                self.db_session.rollback()
    
    async def _log_invigilator_activity_to_db(self, activity: Dict, room_id: str):
        """
        Log invigilator activity to database.
        
        Args:
            activity: Activity data
            room_id: Room identifier
        """
        logger.debug(f"Logging invigilator activity to DB: {activity['behavior_type']}")
        pass
    
    def get_processing_results(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """
        Steps 7-8 of UC-07: Retrieve processed footage results for investigator.
        
        Args:
            stream_id: Stream identifier
            
        Returns:
            Processing results or None
        """
        return self.processing_results.get(stream_id)
    
    def generate_report(self, stream_id: str, report_format: str = 'json') -> Dict[str, Any]:
        """
        Steps 9-10 of UC-07: Generate final report for investigator.
        
        Args:
            stream_id: Stream identifier
            report_format: Output format (json, pdf, csv)
            
        Returns:
            Report data
        """
        results = self.get_processing_results(stream_id)
        
        if not results:
            return {
                "success": False,
                "error": f"No results found for stream {stream_id}"
            }
        
        # Compile comprehensive report
        report = {
            "report_id": f"report_{stream_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "stream_id": stream_id,
            "exam_id": results.get('exam_id'),
            "room_id": results.get('room_id'),
            "generated_at": datetime.utcnow().isoformat(),
            "processing_summary": {
                "started_at": results.get('started_at'),
                "completed_at": results.get('completed_at'),
                "stream_type": results.get('stream_type'),
                "total_frames": results.get('total_frames_processed', 0)
            },
            "activities_summary": {
                "total_activities": len(results.get('activities_logged', [])),
                "student_activities": len([a for a in results.get('activities_logged', []) 
                                          if a.get('actor_type') == 'student']),
                "invigilator_issues": len([a for a in results.get('activities_logged', []) 
                                          if a.get('actor_type') == 'invigilator'])
            },
            "violations_summary": {
                "total_violations": len(results.get('violations_detected', [])),
                "high_severity": len([v for v in results.get('violations_detected', []) 
                                     if v.get('severity_level', 0) >= 3]),
                "pending_review": len([v for v in results.get('violations_detected', []) 
                                      if v.get('status') == 'pending'])
            },
            "detailed_activities": results.get('activities_logged', []),
            "violations": results.get('violations_detected', []),
            "format": report_format
        }
        
        # Save report based on format
        if report_format == 'json':
            report_path = self._save_json_report(report)
            report['report_path'] = report_path
        
        return report
    
    def _save_json_report(self, report: Dict) -> str:
        """
        Save report as JSON file.
        
        Args:
            report: Report data
            
        Returns:
            Path to saved report
        """
        reports_dir = Path("uploads/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        report_filename = f"{report['report_id']}.json"
        report_path = reports_dir / report_filename
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to: {report_path}")
        return str(report_path)

