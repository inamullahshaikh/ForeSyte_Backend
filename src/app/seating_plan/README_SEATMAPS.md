# Seat Map Drawing Tools

Tools for drawing and managing seat maps (polygons) for all block images in the CSFYP folder.

## Overview

This set of tools allows you to:
1. **Draw seat maps** interactively for all block images
2. **Visualize** existing seat maps on images
3. **Batch process** multiple blocks efficiently

## Files

- `draw_seatmaps_batch.py` - Batch tool for drawing seat maps on all block images
- `visualize_seatmaps.py` - Visualize existing seat maps on images
- `draw_polygons.py` - Original interactive polygon drawing tool (used by batch tool)

## Quick Start

### 1. Draw Seat Maps for All Blocks

```bash
# From the seating_plan directory
python draw_seatmaps_batch.py
```

This will:
- Find all images in CSFYP subdirectories (A104, B127, C301, C311, etc.)
- Open each image one by one for interactive polygon drawing
- Save `seat_map.json` in each block folder

### 2. Visualize Existing Seat Maps

```bash
# Visualize all seat maps
python visualize_seatmaps.py

# Visualize a specific image
python visualize_seatmaps.py "CSFYP/A104-25112025/image.jpg"
```

## Detailed Usage

### Batch Drawing Tool (`draw_seatmaps_batch.py`)

Process all block images and draw seat polygons:

```bash
# Basic usage - process all images
python draw_seatmaps_batch.py

# Resume from a specific block
python draw_seatmaps_batch.py --start-from=A104-25112025

# Skip blocks that already have seat_map.json
python draw_seatmaps_batch.py --skip-existing
```

**Interactive Controls:**
- **Left Click**: Add point to current polygon
- **'c' or ENTER**: Complete current polygon
- **'u'**: Undo last point
- **'r'**: Reset current polygon
- **'d'**: Delete last completed polygon
- **'s'**: Save all polygons to JSON
- **'q' or ESC**: Quit and move to next image
- **'l'**: List all completed polygons

**Workflow:**
1. Script opens first image
2. Click points around each seat to form polygons
3. Press 'c' to complete each polygon
4. Press 's' to save when done with image
5. Press 'q' to move to next image
6. Repeat for all blocks

### Visualization Tool (`visualize_seatmaps.py`)

Draw seat polygons from JSON files onto images:

```bash
# Visualize all blocks
python visualize_seatmaps.py

# Visualize specific image
python visualize_seatmaps.py "CSFYP/C301-25112025/C-Block 301 Class Room_243_20251125165959_20251125171000_39691319.jpg"
```

Output images are saved to `CSFYP/visualized/` folder.

## File Structure

After processing, your CSFYP folder will look like:

```
CSFYP/
├── A104-25112025/
│   ├── A-104 Class Room_244_20251125165000_20251125170959_39742414.jpg
│   ├── A-104.mp4
│   └── seat_map.json                    ← Created by draw_seatmaps_batch.py
├── B127-25112025/
│   ├── B-127 Class Room_244_20251125164000_20251125170000_39633362.jpg
│   ├── B127449-451.mp4
│   └── seat_map.json
├── C301-25112025/
│   ├── C-Block 301 Class Room_243_20251125165959_20251125171000_39691319.jpg
│   ├── C-Block 301 Class Room_243_20251125165959_20251125171000_39691319.mp4
│   └── seat_map.json
├── C311-25112025/
│   ├── C-311 Class Room_243_20251125170000_20251125171459_39815032.jpg
│   ├── C-311 Class Room_243_20251125170000_20251125171459_39815032.mp4
│   └── seat_map.json
└── visualized/                          ← Created by visualize_seatmaps.py
    ├── A104-25112025_..._visualized.jpg
    ├── B127-25112025_..._visualized.jpg
    └── ...
```

## Seat Map JSON Format

Each `seat_map.json` file follows this structure:

```json
{
  "_meta": {
    "base_w": 1920,
    "base_h": 1080
  },
  "seats": {
    "seat_c1r1": [
      [104, 566],
      [226, 534],
      [250, 782],
      [99, 819],
      [104, 566]
    ],
    "seat_c1r2": [
      [117, 404],
      [224, 388],
      [226, 533],
      [100, 566],
      [117, 404]
    ]
  }
}
```

- `_meta`: Image dimensions
- `seats`: Dictionary mapping seat IDs to polygon point arrays
- Each polygon is a list of [x, y] coordinates
- Polygons should be closed (first point = last point)

## Tips

1. **Naming Convention**: Seat IDs typically follow `seat_cXrY` format (column X, row Y)
2. **Polygon Points**: Use 4-6 points per seat for best accuracy
3. **Save Frequently**: Press 's' to save after completing each seat
4. **Resume Work**: If interrupted, existing seat_map.json will be loaded automatically
5. **Review**: Use visualization tool to verify seat maps before using in production

## Integration with Upload Plan

Once seat maps are created, they can be used with `upload_plan.py`:

1. Copy or rename the appropriate `seat_map.json` to the main seating_plan directory
2. Or modify `upload_plan.py` to use block-specific seat maps

## Troubleshooting

### "No images found"
- Check that images are in `.jpg`, `.jpeg`, `.png`, or `.bmp` format
- Verify CSFYP folder structure

### "Could not load image"
- Check image file is not corrupted
- Verify file path is correct

### Seat map not saving
- Make sure to press 's' before pressing 'q'
- Check file permissions in block folders

### Polygons not visible
- Ensure you've completed at least 3 points before pressing 'c'
- Check that polygons are being saved (press 'l' to list)

## Next Steps

After creating seat maps:
1. Review visualized images to verify accuracy
2. Update seat IDs to match your naming convention (e.g., `seat_c1r1`, `seat_c2r1`)
3. Integrate with your seating plan upload system
4. Test with actual seating plan PDFs

