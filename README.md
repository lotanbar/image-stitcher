# Image Stitcher for Dolphin

A lightweight tool for stitching PNG and TIF images directly from the Dolphin file manager context menu on Fedora Linux.

## Features

- **Stitch horizontally** (left to right) or **vertically** (top to bottom)
- Works with **PNG and TIF/TIFF** files (can mix both)
- Images stitched in **alphabetical filename order**
- **Context menu integration** - right-click and stitch
- **Visual notifications** on success/error
- Output saved as **TIF** in the same directory

## Use Cases

Perfect for:
- Stitching map tiles into complete maps
- Combining screenshot segments
- Creating panoramas from image sequences
- Building composite images from rows/columns

## Installation

### One-Command Install

```bash
./install.sh
```

### Manual Steps

If you prefer to see what's happening:

```bash
# Install dependencies
sudo dnf install -y python3-pillow

# Install the script
sudo cp image-stitcher.py /usr/local/bin/
sudo chmod +x /usr/local/bin/image-stitcher.py

# Install context menu integration
mkdir -p ~/.local/share/kio/servicemenus/
cp image-stitcher.desktop ~/.local/share/kio/servicemenus/

# Restart Dolphin
killall dolphin
```

## Usage

1. Select multiple PNG/TIF files in Dolphin
2. Right-click on the selection
3. Choose:
   - **Stitch Horizontally (Left to Right)** - creates horizontal strip
   - **Stitch Vertically (Top to Bottom)** - creates vertical strip
4. A notification will appear when complete
5. Find the output TIF file in the same directory

### Example Workflow

**Building a map from tiles:**
1. Stitch tiles horizontally to create rows: `tile_01.png`, `tile_02.png`, `tile_03.png` → `stitched_horizontal.tif`
2. Repeat for each row
3. Stitch all rows vertically to create the complete map

## Requirements

- **OS**: Fedora Linux (or any Linux with KDE/Dolphin)
- **Python**: 3.x
- **Libraries**: Pillow (PIL)
- **File Manager**: Dolphin (may work with other KDE file managers)

## Technical Details

### File Handling
- Images are sorted alphabetically by filename before stitching
- All images converted to RGB mode for consistency
- White background fills any height/width differences
- Output format: TIF (uncompressed)
- Auto-numbering if output file already exists (`stitched_horizontal_1.tif`, etc.)

### Security Note
The desktop file includes `X-KDE-AuthorizeAction=shell_access` to allow Dolphin to execute the script. This is required for context menu actions that run shell commands in KDE.

## Troubleshooting

### "You are not authorized to execute this file" error
This was the original issue. The fix is already included in `image-stitcher.desktop`:
```
X-KDE-AuthorizeAction=shell_access
```
This line authorizes the context menu action to run shell commands.

### Context menu doesn't appear
1. Make sure you selected PNG or TIF files
2. Restart Dolphin: `killall dolphin`
3. Check the desktop file is in the right location: `~/.local/share/kio/servicemenus/`

### Script works from terminal but not from context menu
Ensure the desktop file uses the full path:
```
Exec=/usr/local/bin/image-stitcher.py horizontal %F
```

## Uninstallation

```bash
sudo rm /usr/local/bin/image-stitcher.py
rm ~/.local/share/kio/servicemenus/image-stitcher.desktop
```

## License

MIT License - feel free to use and modify as needed.

## Contributing

Issues and pull requests welcome!
