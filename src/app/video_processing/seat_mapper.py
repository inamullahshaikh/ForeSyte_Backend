"""
Maps detection bounding boxes to students using seating plan from DB and seat_map.json.
Flow: DB seating plan (Room, Seats, Students) -> seat_map.json by block (A,B,C,D) -> bbox point-in-polygon.
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from app.seating_plan.seat_mapping import (
    get_max_column_from_seats,
    seat_number_to_seat_map_key,
)

logger = logging.getLogger(__name__)


def _point_in_polygon(px: float, py: float, polygon: list) -> bool:
    """Ray-casting: point inside polygon iff ray crosses boundary odd times."""
    n = len(polygon)
    if n < 3:
        return False
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i][0], polygon[i][1]
        xj, yj = polygon[j][0], polygon[j][1]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


class SeatMapper:
    """
    Maps bbox (from AI detection) to student_id.
    1. Load seating plan from DB (Room, Seats, Students for exam/room)
    2. Map each Seat.seat_number to seat_map.json key using block-specific column mapping
    3. For each detection bbox: point-in-polygon -> seat_map_key -> student_id
    """

    def __init__(
        self,
        seat_map: dict,
        room_id: str,
        exam_id: str,
        db_session,
        room_no: str = "",
    ):
        """
        Args:
            seat_map: dict of seat_map_key (e.g. seat_c1r1) -> polygon [[x,y], ...]
            room_id: Room UUID
            exam_id: Exam UUID
            db_session: SQLAlchemy session
            room_no: Room number e.g. "D-314" (for block mapping A,B,C,D)
        """
        self.seat_map = seat_map or {}
        self.room_id = room_id
        self.exam_id = exam_id
        self.db_session = db_session
        self.room_no = room_no or ""
        self._seat_key_to_student: dict[str, tuple[str, str]] = {}
        self._build_lookup_from_db()

    def _build_lookup_from_db(self) -> None:
        """
        Build seat_map_key -> (seat_id, student_id) from DB seating plan.
        Uses the same mapping logic as seating plan upload (C1R1 -> seat_c1r1 via column mapping).
        """
        if not self.db_session or not self.seat_map:
            return
        try:
            from database.models import Seat

            seats = (
                self.db_session.query(Seat)
                .filter(Seat.room_id == UUID(self.room_id))
                .all()
            )

            seat_numbers = [s.seat_number for s in seats if s.seat_number]
            max_col = get_max_column_from_seats(seat_numbers)

            for seat in seats:
                if not seat.student_id:
                    continue
                seat_map_key = seat_number_to_seat_map_key(
                    seat.seat_number, self.room_no, max_col
                )
                if seat_map_key and seat_map_key in self.seat_map:
                    self._seat_key_to_student[seat_map_key] = (
                        str(seat.seat_id),
                        str(seat.student_id),
                    )

            logger.info(
                "SeatMapper: mapped %d/%d seats to students for room %s (from DB seating plan)",
                len(self._seat_key_to_student),
                len(seats),
                self.room_id,
            )
        except Exception as e:
            logger.warning("Failed to build seat lookup from DB: %s", e)

    def get_student_for_bbox(self, bbox: tuple[int, int, int, int]) -> Optional[tuple[str, str]]:
        """
        Map bbox (x1,y1,x2,y2) to (seat_id, student_id) via point-in-polygon.
        Returns (seat_id, student_id) or None.
        """
        if not self.seat_map or not self._seat_key_to_student:
            return None
        x1, y1, x2, y2 = bbox
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0

        for seat_map_key, polygon in self.seat_map.items():
            if _point_in_polygon(cx, cy, polygon):
                result = self._seat_key_to_student.get(seat_map_key)
                if result:
                    return result
                break
        return None
