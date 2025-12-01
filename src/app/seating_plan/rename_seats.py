#!/usr/bin/env python3
"""
Script to rename seat IDs from seat_1, seat_2, ... to seat_c1r1, seat_c1r2, ...
Pattern: Every 6 seats = 1 column (c1r1-6, c2r1-6, etc.)
"""

import json
from pathlib import Path

def rename_seats(input_file: Path, output_file: Path = None):
    """Rename seat IDs from sequential to column-row format"""
    
    # Load the JSON file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    seats = data.get('seats', {})
    new_seats = {}
    
    # Sort seat keys to process in order
    sorted_keys = sorted(seats.keys(), key=lambda x: int(x.split('_')[1]) if x.split('_')[1].isdigit() else 0)
    
    column = 1
    row = 1
    
    for old_seat_id in sorted_keys:
        # Create new seat ID
        new_seat_id = f"seat_c{column}r{row}"
        new_seats[new_seat_id] = seats[old_seat_id]
        
        print(f"Renamed: {old_seat_id} → {new_seat_id}")
        
        # Move to next row
        row += 1
        
        # After 6 rows, move to next column
        if row > 6:
            row = 1
            column += 1
    
    # Update the data
    data['seats'] = new_seats
    
    # Save to output file
    if output_file is None:
        output_file = input_file
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✓ Renamed {len(new_seats)} seats")
    print(f"✓ Saved to {output_file}")
    
    return data

if __name__ == "__main__":
    script_dir = Path(__file__).parent
    input_file = script_dir / "seat_map_new.json"
    output_file = script_dir / "seat_map_new.json"  # Overwrite same file
    
    rename_seats(input_file, output_file)

