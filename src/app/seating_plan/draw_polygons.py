#!/usr/bin/env python3
"""
Interactive polygon drawing tool for seat map annotation.
Click on the CCTV frame image to draw polygons around seats.
"""

import cv2
import numpy as np
import json
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Optional


class PolygonDrawer:
    """Interactive polygon drawing tool using OpenCV"""
    
    def __init__(self, image_path: Path, output_path: Optional[Path] = None):
        self.image_path = image_path
        self.output_path = output_path or image_path.parent / "seat_map_new.json"
        
        # Load image
        self.original_image = cv2.imread(str(image_path))
        if self.original_image is None:
            raise FileNotFoundError(f"Could not load image: {image_path}")
        
        self.display_image = self.original_image.copy()
        self.height, self.width = self.original_image.shape[:2]
        
        # Polygon drawing state
        self.current_polygon: List[Tuple[int, int]] = []
        self.completed_polygons: Dict[str, List[List[int]]] = {}
        self.current_seat_id = ""
        self.drawing = False
        self.seat_counter = 1  # Auto-incrementing seat ID counter
        
        # Window setup
        self.window_name = "Polygon Drawer - Click to add points, 'c' to complete, 's' to save, 'q' to quit"
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        
        # Instructions
        self.show_instructions()
    
    def show_instructions(self):
        """Display instructions in console"""
        print("\n" + "="*70)
        print("POLYGON DRAWING TOOL")
        print("="*70)
        print("\nControls:")
        print("  • LEFT CLICK: Add point to current polygon")
        print("  • 'c' or ENTER: Complete current polygon (auto-assigns seat_1, seat_2, ...)")
        print("  • 'u': Undo last point in current polygon")
        print("  • 'r': Reset current polygon")
        print("  • 'd': Delete last completed polygon")
        print("  • 's': Save all polygons to JSON file")
        print("  • 'q' or ESC: Quit (will prompt to save)")
        print("  • 'l': List all completed polygons")
        print("\nNote: Seat IDs are auto-assigned. Edit JSON later to rename them.")
        print("="*70)
    
    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse events"""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.current_polygon.append((x, y))
            self.drawing = True
            self.update_display()
            print(f"Point added: ({x}, {y}) - Total points: {len(self.current_polygon)}")
        
        elif event == cv2.EVENT_MOUSEMOVE and self.drawing:
            # Show preview line while moving mouse
            self.update_display(preview_point=(x, y))
    
    def update_display(self, preview_point: Optional[Tuple[int, int]] = None):
        """Update the display image with all polygons"""
        self.display_image = self.original_image.copy()
        
        # Draw all completed polygons
        for seat_id, polygon in self.completed_polygons.items():
            pts = np.array(polygon, np.int32)
            cv2.polylines(self.display_image, [pts], True, (0, 255, 0), 2)
            
            # Draw seat ID label
            if len(polygon) > 0:
                center = self.get_polygon_center(polygon)
                cv2.putText(self.display_image, seat_id, 
                          (center[0] - 30, center[1]), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Draw current polygon
        if len(self.current_polygon) > 0:
            # Draw points
            for i, point in enumerate(self.current_polygon):
                cv2.circle(self.display_image, point, 5, (0, 0, 255), -1)
                if i > 0:
                    cv2.line(self.display_image, self.current_polygon[i-1], point, (0, 0, 255), 2)
            
            # Draw preview line to mouse cursor
            if preview_point and len(self.current_polygon) > 0:
                cv2.line(self.display_image, self.current_polygon[-1], preview_point, (255, 0, 0), 1, cv2.LINE_AA)
            
            # Draw closing line if more than 2 points
            if len(self.current_polygon) >= 3:
                cv2.line(self.display_image, self.current_polygon[-1], self.current_polygon[0], (255, 0, 0), 1, cv2.LINE_AA)
        
        # Show current seat ID
        if self.current_seat_id:
            cv2.putText(self.display_image, f"Current: {self.current_seat_id}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Show status
        status_text = f"Points: {len(self.current_polygon)} | Completed: {len(self.completed_polygons)}"
        cv2.putText(self.display_image, status_text, 
                   (10, self.height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        cv2.imshow(self.window_name, self.display_image)
    
    def get_polygon_center(self, polygon: List[List[int]]) -> Tuple[int, int]:
        """Calculate center point of polygon"""
        if not polygon:
            return (0, 0)
        x_coords = [p[0] for p in polygon]
        y_coords = [p[1] for p in polygon]
        return (int(sum(x_coords) / len(x_coords)), int(sum(y_coords) / len(y_coords)))
    
    def complete_polygon(self):
        """Complete current polygon and save it"""
        if len(self.current_polygon) < 3:
            print("⚠ Warning: Polygon must have at least 3 points!")
            return
        
        # Auto-generate seat ID (sequential: 1, 2, 3, ...)
        seat_id = f"seat_{self.seat_counter}"
        self.seat_counter += 1
        
        # Convert to list of lists format
        polygon_list = [[int(p[0]), int(p[1])] for p in self.current_polygon]
        
        # Close the polygon (add first point at end if not already there)
        if polygon_list[0] != polygon_list[-1]:
            polygon_list.append(polygon_list[0])
        
        # Save polygon
        self.completed_polygons[seat_id] = polygon_list
        
        print(f"✓ Completed polygon {seat_id} with {len(polygon_list)} points")
        
        # Reset for next polygon
        self.current_polygon = []
        self.current_seat_id = ""
        self.drawing = False
        self.update_display()
    
    def undo_last_point(self):
        """Remove last point from current polygon"""
        if self.current_polygon:
            removed = self.current_polygon.pop()
            print(f"Removed point: {removed}")
            self.update_display()
        else:
            print("No points to undo")
    
    def reset_current_polygon(self):
        """Reset current polygon"""
        if self.current_polygon:
            self.current_polygon = []
            self.current_seat_id = ""
            self.drawing = False
            self.update_display()
            print("Current polygon reset")
        else:
            print("No polygon to reset")
    
    def delete_last_polygon(self):
        """Delete the last completed polygon"""
        if self.completed_polygons:
            last_seat = list(self.completed_polygons.keys())[-1]
            del self.completed_polygons[last_seat]
            print(f"Deleted polygon: {last_seat}")
            self.update_display()
        else:
            print("No polygons to delete")
    
    def list_polygons(self):
        """List all completed polygons"""
        if not self.completed_polygons:
            print("\nNo completed polygons yet.")
            return
        
        print("\n" + "="*70)
        print("Completed Polygons:")
        print("="*70)
        for seat_id, polygon in self.completed_polygons.items():
            print(f"  {seat_id}: {len(polygon)} points")
        print("="*70)
    
    def save_to_json(self):
        """Save all polygons to JSON file"""
        if not self.completed_polygons:
            print("⚠ No polygons to save!")
            return False
        
        # Create seat map structure
        seat_map = {
            "_meta": {
                "base_w": self.width,
                "base_h": self.height
            },
            "seats": self.completed_polygons
        }
        
        # Save to file
        try:
            with open(self.output_path, 'w', encoding='utf-8') as f:
                json.dump(seat_map, f, indent=2)
            
            print(f"\n✓ Saved {len(self.completed_polygons)} polygons to {self.output_path}")
            return True
        except Exception as e:
            print(f"✗ Error saving file: {e}")
            return False
    
    def run(self):
        """Main loop"""
        self.update_display()
        
        print("\nReady! Start clicking on the image to draw polygons.")
        print("Seat IDs will be auto-assigned sequentially (seat_1, seat_2, seat_3, ...)")
        print("You can edit the JSON file later to rename them.\n")
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q') or key == 27:  # 'q' or ESC
                if self.completed_polygons:
                    save = input("\nSave polygons before quitting? (y/n): ").strip().lower()
                    if save == 'y':
                        self.save_to_json()
                break
            
            elif key == ord('c') or key == 13:  # 'c' or ENTER
                self.complete_polygon()
            
            elif key == ord('u'):  # Undo last point
                self.undo_last_point()
            
            elif key == ord('r'):  # Reset current polygon
                self.reset_current_polygon()
            
            elif key == ord('d'):  # Delete last polygon
                self.delete_last_polygon()
            
            elif key == ord('s'):  # Save
                self.save_to_json()
            
            elif key == ord('l'):  # List polygons
                self.list_polygons()
        
        cv2.destroyAllWindows()


def main():
    """Main function"""
    script_dir = Path(__file__).parent
    default_image = script_dir / "cctv_frame.jpg"
    
    print("="*70)
    print("Seat Map Polygon Drawing Tool")
    print("="*70)
    
    # Get image path
    image_path = input(f"\nEnter CCTV frame image path (default: {default_image}): ").strip()
    if not image_path:
        image_path = default_image
    else:
        image_path = Path(image_path)
    
    if not image_path.exists():
        print(f"Error: Image file not found: {image_path}")
        sys.exit(1)
    
    # Get output path
    output_path = input("\nEnter output JSON file path (default: seat_map_new.json): ").strip()
    if not output_path:
        output_path = script_dir / "seat_map_new.json"
    else:
        output_path = Path(output_path)
    
    try:
        drawer = PolygonDrawer(image_path, output_path)
        drawer.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


