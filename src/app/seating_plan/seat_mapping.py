"""
Shared seat mapping utilities for seating plan and video processing.
Maps seating plan seat numbers (C1R1, Chair1) to seat_map.json keys (seat_c1r1)
using block-specific column mapping for A, B, C, D blocks.
"""

from __future__ import annotations

import re
from typing import Optional


def get_column_mapping(room_no: str, max_col: int) -> dict[int, int]:
    """Column mapping from seating plan col -> seat_map col for blocks A,B,C,D."""
    room_no_upper = room_no.upper().replace("-", "").replace(" ", "")
    room_block = room_no_upper[0] if room_no_upper and room_no_upper[0].isalpha() else None
    room_num = room_no_upper[1:] if len(room_no_upper) > 1 else None

    if not room_block or not room_num:
        return {i: i for i in range(1, max_col + 1)}

    if room_block == "A":
        if max_col == 5:
            return {1: 1, 2: 3, 3: 5, 4: 7, 5: 9}
        return {1: 1, 2: 3, 3: 4, 4: 7, 5: 8, 6: 10}
    elif room_block == "B":
        if max_col == 4:
            return {1: 1, 2: 3, 3: 5, 4: 7}
        return {i: i for i in range(1, max_col + 1)}
    elif room_block == "C":
        if room_num == "311":
            if max_col == 4:
                return {1: 1, 2: 3, 3: 6, 4: 8}
        else:
            if max_col == 6:
                return {1: 1, 2: 3, 3: 5, 4: 6, 5: 8, 6: 10}
            elif max_col == 5:
                return {1: 1, 2: 4, 3: 6, 4: 8, 5: 10}
        return {i: i for i in range(1, max_col + 1)}
    elif room_block == "D":
        if max_col == 6:
            return {1: 1, 2: 3, 3: 5, 4: 6, 5: 8, 6: 10}
        elif max_col == 5:
            return {1: 1, 2: 4, 3: 6, 4: 8, 5: 10}
        return {i: i for i in range(1, max_col + 1)}

    return {i: i for i in range(1, max_col + 1)}


def seat_number_to_seat_map_key(seat_no: str, room_no: str, max_col: int) -> Optional[str]:
    """
    Map seat number from DB (C1R1, Chair1) to seat_map.json key (seat_c1r1).
    Uses block-specific column mapping for A, B, C, D blocks.
    """
    seat_no = (seat_no or "").upper().strip()
    if not seat_no:
        return None

    # C1R1, C2R3 format
    match = re.search(r"C(\d+)R(\d+)", seat_no)
    if match:
        input_col = int(match.group(1))
        row = int(match.group(2))
        col_mapping = get_column_mapping(room_no, max_col)
        mapped_col = col_mapping.get(input_col)
        if not mapped_col:
            return None
        return f"seat_c{mapped_col}r{row}"

    # Chair1, Chair2 format - treat as column 1, row N (Chair N = first column, row N)
    match = re.search(r"CHAIR(\d+)", seat_no)
    if match:
        row = int(match.group(1))
        col_mapping = get_column_mapping(room_no, max_col)
        mapped_col = col_mapping.get(1, 1)
        return f"seat_c{mapped_col}r{row}"

    return None


def get_max_column_from_seats(seat_numbers: list[str]) -> int:
    """Extract max column from seat numbers (C1R1, C2R3, Chair1, etc.)."""
    max_col = 0
    for sn in seat_numbers or []:
        m = re.search(r"C(\d+)", (sn or "").upper())
        if m:
            max_col = max(max_col, int(m.group(1)))
        # Chair format - assume at least 1 column
        if re.search(r"CHAIR", (sn or "").upper()):
            max_col = max(max_col, 1)
    return max_col or 10
