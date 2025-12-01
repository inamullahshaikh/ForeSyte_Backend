#!/usr/bin/env python3
"""
Interactive script to update polygon coordinates in seat_map.json
Creates a new JSON file with updated polygon values.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def load_seat_map(file_path: Path) -> Dict:
    """Load seat map from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found!")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path}: {e}")
        sys.exit(1)


def save_seat_map(data: Dict, file_path: Path):
    """Save seat map to JSON file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"\n✓ Saved to {file_path}")


def display_seat_info(seat_id: str, polygon: List[List[int]]):
    """Display information about a seat"""
    print(f"\n  Seat ID: {seat_id}")
    print(f"  Points: {len(polygon)}")
    print(f"  Coordinates:")
    for i, point in enumerate(polygon):
        print(f"    Point {i+1}: [{point[0]}, {point[1]}]")


def list_all_seats(seat_map: Dict):
    """List all seats in the map"""
    seats = seat_map.get('seats', {})
    if not seats:
        print("No seats found in the map!")
        return
    
    print(f"\n{'='*60}")
    print(f"Found {len(seats)} seats:")
    print(f"{'='*60}")
    
    for seat_id in sorted(seats.keys()):
        polygon = seats[seat_id]
        print(f"  {seat_id}: {len(polygon)} points")
    
    print(f"{'='*60}")


def edit_polygon_interactive(seat_id: str, current_polygon: List[List[int]]) -> List[List[int]]:
    """Interactively edit polygon coordinates"""
    print(f"\n{'='*60}")
    print(f"Editing: {seat_id}")
    print(f"{'='*60}")
    print("\nCurrent polygon:")
    for i, point in enumerate(current_polygon):
        print(f"  Point {i+1}: [{point[0]}, {point[1]}]")
    
    print("\nOptions:")
    print("  1. Replace entire polygon")
    print("  2. Edit individual points")
    print("  3. Add new point")
    print("  4. Remove point")
    print("  5. Keep current polygon")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == '5':
        return current_polygon
    
    if choice == '1':
        return replace_entire_polygon()
    elif choice == '2':
        return edit_individual_points(current_polygon)
    elif choice == '3':
        return add_point(current_polygon)
    elif choice == '4':
        return remove_point(current_polygon)
    else:
        print("Invalid choice. Keeping current polygon.")
        return current_polygon


def replace_entire_polygon() -> List[List[int]]:
    """Replace entire polygon with new coordinates"""
    print("\nEnter new polygon coordinates.")
    print("Format: x1,y1 x2,y2 x3,y3 ... (space-separated)")
    print("Example: 100,200 300,400 500,600")
    
    coords_input = input("Coordinates: ").strip()
    
    try:
        points = []
        for coord_pair in coords_input.split():
            x, y = map(int, coord_pair.split(','))
            points.append([x, y])
        
        if len(points) < 3:
            print("Error: Polygon must have at least 3 points!")
            return []
        
        print(f"\nNew polygon with {len(points)} points:")
        for i, point in enumerate(points):
            print(f"  Point {i+1}: [{point[0]}, {point[1]}]")
        
        confirm = input("\nConfirm? (y/n): ").strip().lower()
        if confirm == 'y':
            return points
        else:
            return []
    except ValueError as e:
        print(f"Error parsing coordinates: {e}")
        return []


def edit_individual_points(polygon: List[List[int]]) -> List[List[int]]:
    """Edit individual points in the polygon"""
    new_polygon = polygon.copy()
    
    while True:
        print("\nCurrent polygon:")
        for i, point in enumerate(new_polygon):
            print(f"  {i+1}. [{point[0]}, {point[1]}]")
        
        point_num = input("\nEnter point number to edit (or 'done' to finish): ").strip()
        
        if point_num.lower() == 'done':
            break
        
        try:
            idx = int(point_num) - 1
            if 0 <= idx < len(new_polygon):
                print(f"\nEditing point {idx + 1}: [{new_polygon[idx][0]}, {new_polygon[idx][1]}]")
                new_coords = input("Enter new coordinates (x,y): ").strip()
                x, y = map(int, new_coords.split(','))
                new_polygon[idx] = [x, y]
                print(f"Updated to: [{x}, {y}]")
            else:
                print("Invalid point number!")
        except (ValueError, IndexError) as e:
            print(f"Error: {e}")
    
    return new_polygon


def add_point(polygon: List[List[int]]) -> List[List[int]]:
    """Add a new point to the polygon"""
    print("\nCurrent polygon:")
    for i, point in enumerate(polygon):
        print(f"  {i+1}. [{point[0]}, {point[1]}]")
    
    try:
        new_coords = input("\nEnter new point coordinates (x,y): ").strip()
        x, y = map(int, new_coords.split(','))
        new_point = [x, y]
        
        position = input("Insert at position (1-based, or 'end'): ").strip()
        
        if position.lower() == 'end':
            polygon.append(new_point)
        else:
            idx = int(position) - 1
            if 0 <= idx <= len(polygon):
                polygon.insert(idx, new_point)
            else:
                print("Invalid position. Adding at end.")
                polygon.append(new_point)
        
        return polygon
    except ValueError as e:
        print(f"Error: {e}")
        return polygon


def remove_point(polygon: List[List[int]]) -> List[List[int]]:
    """Remove a point from the polygon"""
    if len(polygon) <= 3:
        print("Error: Cannot remove point. Polygon must have at least 3 points!")
        return polygon
    
    print("\nCurrent polygon:")
    for i, point in enumerate(polygon):
        print(f"  {i+1}. [{point[0]}, {point[1]}]")
    
    try:
        point_num = input("\nEnter point number to remove: ").strip()
        idx = int(point_num) - 1
        
        if 0 <= idx < len(polygon):
            removed = polygon.pop(idx)
            print(f"Removed point: [{removed[0]}, {removed[1]}]")
        else:
            print("Invalid point number!")
    except ValueError as e:
        print(f"Error: {e}")
    
    return polygon


def batch_edit_from_file(seat_map: Dict, input_file: Path) -> Dict:
    """Load polygon updates from a JSON file"""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            updates = json.load(f)
        
        seats = seat_map.get('seats', {})
        
        if 'seats' in updates:
            # Full seat map format
            for seat_id, polygon in updates['seats'].items():
                if seat_id in seats:
                    seats[seat_id] = polygon
                    print(f"✓ Updated {seat_id}")
                else:
                    print(f"⚠ Warning: {seat_id} not found in original map")
        else:
            # Just seat updates format
            for seat_id, polygon in updates.items():
                if seat_id in seats:
                    seats[seat_id] = polygon
                    print(f"✓ Updated {seat_id}")
                else:
                    print(f"⚠ Warning: {seat_id} not found in original map")
        
        seat_map['seats'] = seats
        return seat_map
    except Exception as e:
        print(f"Error loading updates from file: {e}")
        return seat_map


def main():
    """Main function"""
    script_dir = Path(__file__).parent
    default_input = script_dir / "seat_map.json"
    
    print("="*60)
    print("Seat Map Polygon Editor")
    print("="*60)
    
    # Get input file
    input_file = input(f"\nEnter input JSON file path (default: {default_input}): ").strip()
    if not input_file:
        input_file = default_input
    else:
        input_file = Path(input_file)
    
    # Load seat map
    print(f"\nLoading {input_file}...")
    seat_map = load_seat_map(input_file)
    
    # Display metadata
    meta = seat_map.get('_meta', {})
    if meta:
        print(f"\nMetadata:")
        print(f"  Base width: {meta.get('base_w', 'N/A')}")
        print(f"  Base height: {meta.get('base_h', 'N/A')}")
    
    # List all seats
    list_all_seats(seat_map)
    
    # Choose editing mode
    print("\n" + "="*60)
    print("Editing Mode:")
    print("  1. Interactive (edit seats one by one)")
    print("  2. Batch from file (load updates from JSON file)")
    print("  3. View only (no editing)")
    print("="*60)
    
    mode = input("\nEnter mode (1-3): ").strip()
    
    if mode == '1':
        # Interactive editing
        seats = seat_map.get('seats', {})
        seats_to_edit = input("\nEnter seat IDs to edit (comma-separated, or 'all'): ").strip()
        
        if seats_to_edit.lower() == 'all':
            seat_ids = list(seats.keys())
        else:
            seat_ids = [s.strip() for s in seats_to_edit.split(',')]
        
        for seat_id in seat_ids:
            if seat_id in seats:
                new_polygon = edit_polygon_interactive(seat_id, seats[seat_id])
                if new_polygon:
                    seats[seat_id] = new_polygon
            else:
                print(f"⚠ Warning: {seat_id} not found!")
    
    elif mode == '2':
        # Batch edit from file
        update_file = input("\nEnter path to JSON file with updates: ").strip()
        if update_file:
            seat_map = batch_edit_from_file(seat_map, Path(update_file))
    
    elif mode == '3':
        # View only
        seat_id = input("\nEnter seat ID to view (or 'all'): ").strip()
        seats = seat_map.get('seats', {})
        
        if seat_id.lower() == 'all':
            for sid, poly in seats.items():
                display_seat_info(sid, poly)
        elif seat_id in seats:
            display_seat_info(seat_id, seats[seat_id])
        else:
            print(f"Seat {seat_id} not found!")
        
        print("\nView-only mode. No changes saved.")
        return
    
    else:
        print("Invalid mode. Exiting.")
        return
    
    # Save to new file
    output_file = input("\nEnter output file path (default: seat_map_new.json): ").strip()
    if not output_file:
        output_file = script_dir / "seat_map_new.json"
    else:
        output_file = Path(output_file)
    
    save_seat_map(seat_map, output_file)
    
    print("\n" + "="*60)
    print("Done!")
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

