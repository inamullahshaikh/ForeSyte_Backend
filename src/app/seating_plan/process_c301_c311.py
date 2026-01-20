#!/usr/bin/env python3
"""
Draw Seat Maps for C301 and C311
Interactive polygon drawing tool for rooms C301-25112025 and C311-25112025
"""

import sys
from pathlib import Path
from typing import Optional
from draw_polygons import PolygonDrawer


def process_room(room_folder: Path, load_existing: bool = True):
    """
    Process a single room folder - opens interactive polygon drawing tool.
    
    Args:
        room_folder: Path to room folder (e.g., C301-25112025)
        load_existing: Whether to load existing seat_map.json if it exists
    """
    room_name = room_folder.name
    print(f"\n{'='*70}")
    print(f"Processing Room: {room_name}")
    print(f"{'='*70}")
    
    # Find image file
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
    images = [f for f in room_folder.iterdir() 
             if f.suffix.lower() in image_extensions]
    
    if not images:
        print(f"  ⚠ No image files found in {room_folder}")
        return False
    
    # Use the first image found
    image_path = images[0]
    print(f"  Image: {image_path.name}")
    
    # Seat map path
    seat_map_path = room_folder / "seat_map.json"
    print(f"  Output: {seat_map_path}")
    
    # Check if seat map exists
    existing_polygons = {}
    if load_existing and seat_map_path.exists():
        try:
            import json
            with open(seat_map_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                existing_polygons = data.get('seats', {})
            print(f"  ✓ Loaded {len(existing_polygons)} existing polygons")
        except Exception as e:
            print(f"  ⚠ Warning: Could not load existing seat_map: {e}")
    
    try:
        # Create polygon drawer
        drawer = PolygonDrawer(image_path, seat_map_path)
        
        # Load existing polygons if any
        if existing_polygons:
            drawer.completed_polygons = existing_polygons
            # Update seat counter to continue from existing
            if existing_polygons:
                max_seat_num = 0
                for seat_id in existing_polygons.keys():
                    try:
                        num = int(seat_id.split('_')[-1])
                        max_seat_num = max(max_seat_num, num)
                    except:
                        pass
                drawer.seat_counter = max_seat_num + 1
            drawer.update_display()
            print(f"  ✓ Resumed from seat_{drawer.seat_counter}")
        
        # Run interactive drawing
        print("\n  Starting interactive polygon drawing...")
        print("  Draw polygons around each seat, then press 's' to save and 'q' to quit.")
        drawer.run()
        
        # Check if polygons were saved
        if seat_map_path.exists():
            import json
            with open(seat_map_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                seat_count = len(data.get('seats', {}))
            print(f"\n  ✓ Successfully saved {seat_count} seats to {seat_map_path}")
            return True
        else:
            print("\n  ⚠ No seat map was saved. Did you press 's' to save?")
            return False
            
    except KeyboardInterrupt:
        print("\n\n  ⚠ Interrupted by user. Progress may be lost if not saved.")
        return False
    except Exception as e:
        print(f"\n  ✗ Error processing image: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    script_dir = Path(__file__).parent
    csfyp_dir = script_dir / "CSFYP"
    
    if not csfyp_dir.exists():
        print(f"Error: CSFYP directory not found at: {csfyp_dir}")
        sys.exit(1)
    
    # Process C301 and C311
    rooms_to_process = [
        "C301-25112025",
    ]
    
    print("\n" + "="*70)
    print("DRAWING SEAT MAPS: C301 and C311")
    print("="*70)
    print("\nYou will draw polygons interactively for each room.")
    print("Controls:")
    print("  • LEFT CLICK: Add point to current polygon")
    print("  • 'c' or ENTER: Complete current polygon")
    print("  • 'u': Undo last point")
    print("  • 'r': Reset current polygon")
    print("  • 'd': Delete last completed polygon")
    print("  • 's': Save all polygons to JSON file")
    print("  • 'q' or ESC: Quit (will prompt to save)")
    print("="*70)
    
    processed = 0
    skipped = 0
    
    for room_name in rooms_to_process:
        room_folder = csfyp_dir / room_name
        if not room_folder.exists():
            print(f"\n⚠ Room folder not found: {room_folder}")
            skipped += 1
            continue
        
        try:
            success = process_room(room_folder)
            if success:
                processed += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"\n✗ Error processing {room_name}: {e}")
            skipped += 1
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*70)
    print("PROCESSING COMPLETE")
    print(f"  Processed: {processed}")
    print(f"  Skipped: {skipped}")
    print("="*70)


if __name__ == "__main__":
    main()

