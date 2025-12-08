import json
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

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
        (255, 99, 71, 128),  # Tomato
        (60, 179, 113, 128), # MediumSeaGreen
        (65, 105, 225, 128), # RoyalBlue
        (255, 165, 0, 128),  # Orange
        (138, 43, 226, 128), # BlueViolet
        (0, 191, 255, 128),  # DeepSkyBlue
        (255, 20, 147, 128), # DeepPink
        (0, 255, 127, 128),  # SpringGreen
        (255, 215, 0, 128),  # Gold
        (75, 0, 130, 128),   # Indigo
    ]
    
    # Try to load a font for labels
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        except IOError:
            font = ImageFont.load_default()
            print("Warning: Using default font.")
    
    outline_color = (0, 0, 0, 255)  # Black outline
    text_color = (0, 0, 0, 255)  # Black text
    text_bg_color = (255, 255, 255, 192)  # Semi-transparent white background for text
    
    draw = ImageDraw.Draw(img)
    
    # Draw each seat
    for idx, (seat_id, coordinates) in enumerate(seats.items()):
        if not coordinates or len(coordinates) < 3:
            continue
        
        # Convert coordinates to tuples
        points = [(int(coord[0]), int(coord[1])) for coord in coordinates if len(coord) >= 2]
        
        if len(points) < 3:
            continue
        
        # Get color for this seat (cycle through colors)
        fill_color = colors[idx % len(colors)]
        
        # Draw filled polygon with transparency
        draw.polygon(points, fill=fill_color, outline=outline_color)
        
        # Calculate center for label
        if points:
            center_x = sum(p[0] for p in points) / len(points)
            center_y = sum(p[1] for p in points) / len(points)
            
            # Get seat label (remove 'seat_' prefix)
            label = seat_id.replace('seat_', '')
            
            # Get text bounding box
            try:
                bbox = draw.textbbox((0, 0), label, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except AttributeError:
                # Fallback for older PIL versions
                text_width, text_height = draw.textsize(label, font=font)
            
            # Calculate text position to center it
            text_x = center_x - (text_width / 2)
            text_y = center_y - (text_height / 2)
            
            # Draw text background
            padding = 5
            draw.rectangle(
                (text_x - padding, text_y - padding, text_x + text_width + padding, text_y + text_height + padding),
                fill=text_bg_color
            )
            
            # Draw text
            draw.text((text_x, text_y), label, font=font, fill=text_color)
    
    # Convert back to RGB for JPEG format
    if img.mode == 'RGBA':
        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
        rgb_img.paste(img, mask=img.split()[3])  # Use alpha channel as mask
        img = rgb_img
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Save the annotated image
    img.save(output_path, quality=95)
    print(f"Saved annotated image: {output_path}")

if __name__ == "__main__":
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    
    seat_map_path = script_dir / "seat_map.json"
    image_path = script_dir / "D314-25112025.jpg"
    output_dir = script_dir / "processed"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "D314-25112025_annotated.jpg"
    
    if not seat_map_path.exists():
        print(f"Error: seat_map.json not found at {seat_map_path}")
        print("Please create a seat_map.json file with seat coordinates first.")
        exit(1)
    
    if not image_path.exists():
        print(f"Error: Image not found at {image_path}")
        exit(1)
    
    print(f"Processing D314...")
    print(f"  Seat map: {seat_map_path}")
    print(f"  Image: {image_path}")
    print(f"  Output: {output_path}")
    
    try:
        draw_seats_on_image(seat_map_path, image_path, output_path)
        print(f"[OK] Successfully processed D314")
    except Exception as e:
        print(f"[ERROR] Error processing D314: {str(e)}")
        import traceback
        traceback.print_exc()

