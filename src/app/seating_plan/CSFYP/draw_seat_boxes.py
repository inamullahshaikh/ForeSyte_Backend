import json
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

def draw_seats_on_image(seat_map_path, image_path, output_path):
    """
    Draw seat polygons on an image based on seat_map.json coordinates.
    
    Args:
        seat_map_path: Path to seat_map.json file
        image_path: Path to the original image
        output_path: Path to save the annotated image
    """
    # Read seat map JSON
    with open(seat_map_path, 'r', encoding='utf-8') as f:
        seat_data = json.load(f)
    
    # Load image and convert to RGBA for transparency support
    img = Image.open(image_path).convert('RGBA')
    
    # Get seats
    seats = seat_data.get('seats', {})
    
    # Colors for different seats (cycling through colors)
    colors = [
        (255, 0, 0, 100),      # Red with transparency
        (0, 255, 0, 100),      # Green with transparency
        (0, 0, 255, 100),      # Blue with transparency
        (255, 255, 0, 100),    # Yellow with transparency
        (255, 0, 255, 100),    # Magenta with transparency
        (0, 255, 255, 100),    # Cyan with transparency
        (255, 128, 0, 100),    # Orange with transparency
        (128, 0, 255, 100),    # Purple with transparency
    ]
    
    # Try to load a font for labels
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except:
            font = ImageFont.load_default()
    
    # Draw each seat
    for idx, (seat_id, coordinates) in enumerate(seats.items()):
        if not coordinates or len(coordinates) < 3:
            continue
        
        # Convert coordinates to tuples
        points = [(int(coord[0]), int(coord[1])) for coord in coordinates if len(coord) >= 2]
        
        if len(points) < 3:
            continue
        
        # Get color for this seat (cycle through colors)
        color_rgba = colors[idx % len(colors)]
        color_rgb = color_rgba[:3]  # RGB without alpha
        
        # Create overlay for filled polygon
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # Draw filled polygon with transparency
        overlay_draw.polygon(points, fill=color_rgba)
        
        # Composite overlay onto image
        img = Image.alpha_composite(img, overlay)
        
        # Draw outline on the main image
        draw = ImageDraw.Draw(img)
        draw.polygon(points, outline=color_rgb, width=2)
        
        # Calculate center for label
        if points:
            center_x = sum(p[0] for p in points) // len(points)
            center_y = sum(p[1] for p in points) // len(points)
            
            # Draw seat label
            label = seat_id.replace('seat_', '')
            
            # Get text bounding box
            try:
                bbox = draw.textbbox((0, 0), label, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except AttributeError:
                # Fallback for older PIL versions
                text_width, text_height = draw.textsize(label, font=font)
            
            # Draw background for text
            padding = 3
            bg_x1 = center_x - text_width // 2 - padding
            bg_y1 = center_y - text_height // 2 - padding
            bg_x2 = center_x + text_width // 2 + padding
            bg_y2 = center_y + text_height // 2 + padding
            
            # Draw semi-transparent white background
            bg_overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
            bg_draw = ImageDraw.Draw(bg_overlay)
            bg_draw.rectangle([bg_x1, bg_y1, bg_x2, bg_y2], fill=(255, 255, 255, 220), outline=color_rgb, width=1)
            img = Image.alpha_composite(img, bg_overlay)
            
            # Draw text
            draw = ImageDraw.Draw(img)
            try:
                draw.text((center_x, center_y), label, fill=(0, 0, 0), font=font, anchor='mm')
            except:
                # Fallback for older PIL versions
                text_x = center_x - text_width // 2
                text_y = center_y - text_height // 2
                draw.text((text_x, text_y), label, fill=(0, 0, 0), font=font)
    
    # Convert back to RGB for JPEG format
    if img.mode == 'RGBA':
        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
        rgb_img.paste(img, mask=img.split()[3])  # Use alpha channel as mask
        img = rgb_img
    
    # Save the annotated image
    img.save(output_path, quality=95)
    print(f"Saved annotated image: {output_path}")

def process_all_seat_maps(base_dir):
    """
    Process all seat_map.json files in the CSFYP directory.
    
    Args:
        base_dir: Base directory containing the room folders
    """
    base_path = Path(base_dir)
    
    # Find all seat_map.json files
    seat_map_files = list(base_path.rglob('seat_map.json'))
    
    for seat_map_path in seat_map_files:
        room_dir = seat_map_path.parent
        room_name = room_dir.name
        
        print(f"\nProcessing {room_name}...")
        
        # Find corresponding image file (look for .jpg files)
        image_files = list(room_dir.glob('*.jpg'))
        
        if not image_files:
            print(f"  No image file found in {room_dir}")
            continue
        
        # Use the first .jpg file found
        image_path = image_files[0]
        
        # Create processed directory if it doesn't exist
        processed_dir = room_dir / 'processed'
        processed_dir.mkdir(exist_ok=True)
        
        # Generate output filename
        image_stem = image_path.stem
        output_filename = f"{room_name}_{image_stem}_annotated.jpg"
        output_path = processed_dir / output_filename
        
        print(f"  Image: {image_path.name}")
        print(f"  Output: {output_path}")
        
        try:
            draw_seats_on_image(seat_map_path, image_path, output_path)
            print(f"  [OK] Successfully processed {room_name}")
        except Exception as e:
            print(f"  [ERROR] Error processing {room_name}: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    process_all_seat_maps(script_dir)
