#!/usr/bin/env python3
"""
Visualize Seat Maps
Draws seat polygons from seat_map.json files on their corresponding images.
Useful for reviewing and verifying seat maps.
"""

import cv2
import numpy as np
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional


def load_seat_map(seat_map_path: Path) -> Dict:
    """
    Load seat map from JSON file.
    
    Args:
        seat_map_path: Path to seat_map.json
        
    Returns:
        Dictionary with seat polygons
    """
    try:
        with open(seat_map_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('seats', {})
    except Exception as e:
        print(f"Error loading seat_map: {e}")
        return {}


def draw_seat_map_on_image(image_path: Path, seat_map_path: Path, 
                           output_path: Optional[Path] = None,
                           show_labels: bool = True,
                           color: tuple = (0, 255, 0),
                           thickness: int = 2) -> np.ndarray:
    """
    Draw seat map polygons on an image.
    
    Args:
        image_path: Path to the image file
        seat_map_path: Path to seat_map.json
        output_path: Path to save annotated image (optional)
        show_labels: Whether to show seat ID labels
        color: BGR color for polygons (default: green)
        thickness: Line thickness
        
    Returns:
        Annotated image as numpy array
    """
    # Load image
    image = cv2.imread(str(image_path))
    if image is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")
    
    # Load seat map
    seats = load_seat_map(seat_map_path)
    
    if not seats:
        print(f"Warning: No seats found in {seat_map_path}")
        return image
    
    # Draw polygons
    for seat_id, polygon_points in seats.items():
        if not polygon_points:
            continue
        
        # Convert to numpy array
        pts = np.array(polygon_points, np.int32)
        
        # Draw polygon
        cv2.polylines(image, [pts], True, color, thickness)
        
        # Draw label
        if show_labels:
            # Calculate center
            M = cv2.moments(pts)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
            else:
                cx, cy = polygon_points[0]
            
            # Draw text background
            (text_width, text_height), baseline = cv2.getTextSize(
                seat_id, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1
            )
            cv2.rectangle(
                image,
                (cx - text_width // 2 - 2, cy - text_height - baseline - 2),
                (cx + text_width // 2 + 2, cy + baseline + 2),
                color,
                -1
            )
            
            # Draw text
            cv2.putText(
                image,
                seat_id,
                (cx - text_width // 2, cy),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (255, 255, 255),
                1
            )
    
    # Save if output path provided
    if output_path:
        cv2.imwrite(str(output_path), image)
        print(f"✓ Saved annotated image: {output_path}")
    
    return image


def visualize_all_blocks(csfyp_dir: Path, output_dir: Optional[Path] = None):
    """
    Visualize seat maps for all blocks in CSFYP folder.
    
    Args:
        csfyp_dir: Path to CSFYP directory
        output_dir: Directory to save visualized images (default: CSFYP/visualized)
    """
    if not csfyp_dir.exists():
        print(f"Error: Directory not found: {csfyp_dir}")
        return
    
    # Setup output directory
    if output_dir is None:
        output_dir = csfyp_dir / "visualized"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all images and their seat maps
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
    processed = 0
    skipped = 0
    
    print("\n" + "="*70)
    print("VISUALIZING SEAT MAPS")
    print("="*70 + "\n")
    
    for block_folder in sorted(csfyp_dir.iterdir()):
        if not block_folder.is_dir():
            continue
        
        block_name = block_folder.name
        seat_map_path = block_folder / "seat_map.json"
        
        # Find images in this block
        images = [f for f in sorted(block_folder.iterdir()) 
                 if f.suffix.lower() in image_extensions]
        
        if not images:
            continue
        
        print(f"Processing block: {block_name}")
        
        # Check if seat map exists
        if not seat_map_path.exists():
            print(f"  ⚠ No seat_map.json found, skipping")
            skipped += len(images)
            continue
        
        # Process each image
        for image_path in images:
            try:
                output_filename = f"{block_name}_{image_path.stem}_visualized{image_path.suffix}"
                output_path = output_dir / output_filename
                
                draw_seat_map_on_image(image_path, seat_map_path, output_path)
                print(f"  ✓ {image_path.name}")
                processed += 1
            except Exception as e:
                print(f"  ✗ Error processing {image_path.name}: {e}")
                skipped += 1
    
    # Summary
    print("\n" + "="*70)
    print(f"Visualization complete!")
    print(f"  Processed: {processed}")
    print(f"  Skipped: {skipped}")
    print(f"  Output directory: {output_dir}")
    print("="*70)


def main():
    """Main function"""
    script_dir = Path(__file__).parent
    csfyp_dir = script_dir / "CSFYP"
    
    if len(sys.argv) > 1:
        # Process specific image
        image_path = Path(sys.argv[1])
        seat_map_path = image_path.parent / "seat_map.json"
        
        if not image_path.exists():
            print(f"Error: Image not found: {image_path}")
            sys.exit(1)
        
        if not seat_map_path.exists():
            print(f"Error: seat_map.json not found: {seat_map_path}")
            sys.exit(1)
        
        output_path = image_path.parent / f"{image_path.stem}_visualized{image_path.suffix}"
        draw_seat_map_on_image(image_path, seat_map_path, output_path)
        print(f"\n✓ Visualization saved to: {output_path}")
    else:
        # Process all blocks
        if not csfyp_dir.exists():
            print(f"Error: CSFYP directory not found at: {csfyp_dir}")
            sys.exit(1)
        
        visualize_all_blocks(csfyp_dir)


if __name__ == "__main__":
    main()

