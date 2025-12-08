#!/usr/bin/env python3
"""
Batch Seat Map Drawing Tool
Processes all block images in CSFYP folder and allows drawing seat polygons for each.
Creates seat_map.json files for each block.
"""

import cv2
import numpy as np
import json
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from draw_polygons import PolygonDrawer


class BatchSeatMapDrawer:
    """Batch processor for drawing seat maps on multiple block images"""
    
    def __init__(self, csfyp_dir: Path):
        """
        Initialize batch drawer.
        
        Args:
            csfyp_dir: Path to CSFYP directory containing block folders
        """
        self.csfyp_dir = Path(csfyp_dir)
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
        
    def find_all_images(self) -> List[Tuple[str, Path]]:
        """
        Find all images in CSFYP subdirectories.
        
        Returns:
            List of tuples: (block_name, image_path)
        """
        images = []
        
        if not self.csfyp_dir.exists():
            print(f"Error: CSFYP directory not found: {self.csfyp_dir}")
            return images
        
        for block_folder in sorted(self.csfyp_dir.iterdir()):
            if block_folder.is_dir():
                for file in sorted(block_folder.iterdir()):
                    if file.suffix.lower() in self.image_extensions:
                        images.append((block_folder.name, file))
        
        return images
    
    def get_seat_map_path(self, block_name: str, image_path: Path) -> Path:
        """
        Get the path for seat_map.json for a block.
        
        Args:
            block_name: Name of the block folder
            image_path: Path to the image file
            
        Returns:
            Path to seat_map.json file
        """
        # Save in the same folder as the image
        return image_path.parent / "seat_map.json"
    
    def check_existing_seat_map(self, seat_map_path: Path) -> bool:
        """
        Check if seat_map.json already exists and ask user if they want to overwrite.
        
        Args:
            seat_map_path: Path to seat_map.json
            
        Returns:
            True if should proceed, False if should skip
        """
        if not seat_map_path.exists():
            return True
        
        print(f"\n⚠ Seat map already exists: {seat_map_path}")
        response = input("  [O]verwrite, [S]kip, or [L]oad existing? (o/s/l): ").strip().lower()
        
        if response == 's':
            return False
        elif response == 'l':
            return True  # Will load in PolygonDrawer
        else:  # 'o' or default
            return True
    
    def process_image(self, block_name: str, image_path: Path, 
                     seat_map_path: Path, load_existing: bool = True) -> bool:
        """
        Process a single image and draw seat map.
        
        Args:
            block_name: Name of the block folder
            image_path: Path to the image file
            seat_map_path: Path to save seat_map.json
            load_existing: Whether to load existing seat_map if it exists
            
        Returns:
            True if completed successfully, False if skipped/cancelled
        """
        print("\n" + "="*70)
        print(f"Processing: {block_name}")
        print(f"Image: {image_path.name}")
        print(f"Output: {seat_map_path}")
        print("="*70)
        
        # Check if seat map exists and load it
        existing_polygons = {}
        if load_existing and seat_map_path.exists():
            try:
                with open(seat_map_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    existing_polygons = data.get('seats', {})
                print(f"✓ Loaded {len(existing_polygons)} existing polygons")
            except Exception as e:
                print(f"⚠ Warning: Could not load existing seat_map: {e}")
        
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
                print(f"✓ Resumed from seat_{drawer.seat_counter}")
            
            # Run interactive drawing
            print("\nStarting interactive polygon drawing...")
            print("Draw polygons around each seat, then save and quit.")
            drawer.run()
            
            # Check if polygons were saved
            if seat_map_path.exists():
                with open(seat_map_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    seat_count = len(data.get('seats', {}))
                print(f"\n✓ Successfully saved {seat_count} seats to {seat_map_path}")
                return True
            else:
                print("\n⚠ No seat map was saved. Did you press 's' to save?")
                return False
                
        except KeyboardInterrupt:
            print("\n\n⚠ Interrupted by user. Progress may be lost if not saved.")
            return False
        except Exception as e:
            print(f"\n✗ Error processing image: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def process_all(self, start_from: Optional[str] = None, 
                   skip_existing: bool = False):
        """
        Process all images in batch.
        
        Args:
            start_from: Block name to start from (resume from this block)
            skip_existing: If True, skip blocks that already have seat_map.json
        """
        images = self.find_all_images()
        
        if not images:
            print(f"No images found in {self.csfyp_dir}")
            return
        
        print("\n" + "="*70)
        print("BATCH SEAT MAP DRAWING TOOL")
        print("="*70)
        print(f"\nFound {len(images)} image(s) in {len(set(img[0] for img in images))} block(s):")
        for block_name, img_path in images:
            print(f"  • {block_name}: {img_path.name}")
        
        print("\n" + "="*70)
        print("Instructions:")
        print("  - For each image, you'll draw polygons around seats")
        print("  - Click points to form a polygon, press 'c' to complete")
        print("  - Press 's' to save, 'q' to quit and move to next image")
        print("  - Existing seat maps will be loaded if available")
        print("="*70)
        
        input("\nPress ENTER to start...")
        
        start_processing = start_from is None
        processed = 0
        skipped = 0
        
        for block_name, image_path in images:
            # Check if we should start from this block
            if not start_processing:
                if block_name == start_from:
                    start_processing = True
                else:
                    continue
            
            seat_map_path = self.get_seat_map_path(block_name, image_path)
            
            # Skip if exists and skip_existing is True
            if skip_existing and seat_map_path.exists():
                print(f"\n⏭ Skipping {block_name} (seat_map.json already exists)")
                skipped += 1
                continue
            
            # Check existing and ask user
            if not self.check_existing_seat_map(seat_map_path):
                skipped += 1
                continue
            
            # Process image
            success = self.process_image(block_name, image_path, seat_map_path)
            
            if success:
                processed += 1
            else:
                # Ask if user wants to continue
                response = input("\nContinue to next image? (y/n): ").strip().lower()
                if response != 'y':
                    print("\nStopped by user.")
                    break
        
        # Summary
        print("\n" + "="*70)
        print("BATCH PROCESSING COMPLETE")
        print("="*70)
        print(f"  Processed: {processed}")
        print(f"  Skipped: {skipped}")
        print(f"  Total: {len(images)}")
        print("="*70)


def main():
    """Main function"""
    script_dir = Path(__file__).parent
    csfyp_dir = script_dir / "CSFYP"
    
    # Check if CSFYP directory exists
    if not csfyp_dir.exists():
        print(f"Error: CSFYP directory not found at: {csfyp_dir}")
        print("Please ensure the CSFYP folder exists with block subdirectories.")
        sys.exit(1)
    
    # Parse command line arguments
    start_from = None
    skip_existing = False
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--skip-existing':
            skip_existing = True
        elif sys.argv[1].startswith('--start-from='):
            start_from = sys.argv[1].split('=', 1)[1]
        else:
            start_from = sys.argv[1]
    
    if len(sys.argv) > 2:
        if sys.argv[2] == '--skip-existing':
            skip_existing = True
    
    # Create batch drawer and process
    drawer = BatchSeatMapDrawer(csfyp_dir)
    
    try:
        drawer.process_all(start_from=start_from, skip_existing=skip_existing)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

