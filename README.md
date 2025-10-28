# Image Stitcher for Dolphin

Lightweight tool for stitching PNG/TIF images from the Dolphin file manager context menu on Fedora Linux.

## Features

**Image Stitcher:**
- Stitch images horizontally or vertically
- Alphabetical ordering • TIF output
- Auto-detects tile numbers and includes them in output filename (e.g., `stitched_horizontal_1-2_4_7-9.tif`)

**Grid Stitcher:**
- Stitch images in custom grid layouts (e.g., 3×4, 5×8)
- Calculate all possible grid configurations
- Find matching dimensions for partial input
- Stitch all grid variations at once
- Context menu integration
- Works with PNG and TIF/TIFF files
- Visual notifications

## Installation

```bash
./install.sh
```

Then restart Dolphin: `killall dolphin`

## Usage

**Stitch:** Select files → Right-click → Choose horizontal or vertical

**Grid Stitch:**
- **For all images in folder:** Right-click on folder → "Stitch in Custom Grid..." (fast, recommended)
- **For specific images:** Select files inside folder → Right-click → "Stitch in Custom Grid..." (slower with many files)

## Configuring File Types for Grid Stitcher

Edit `/usr/local/bin/grid-stitcher.py` and change the `VALID_EXTENSIONS` constant at the top:
```python
VALID_EXTENSIONS = ('.png',)  # Change to ('.png', '.tif', '.tiff', '.jpg') etc.
```

## Requirements

- Fedora Linux (or any Linux with KDE/Dolphin)
- Python 3.x
- Pillow library

## Common Issues

### "You are not authorized to execute this file"

**Plasma 6 Fix:** Desktop files must be executable. The `install.sh` script now handles this automatically by running:
```bash
chmod +x ~/.local/share/kio/servicemenus/*.desktop
```

If you still get this error after installation, manually run:
```bash
chmod +x ~/.local/share/kio/servicemenus/image-stitcher.desktop
chmod +x ~/.local/share/kio/servicemenus/grid-stitcher.desktop
killall dolphin
```

### Context menu doesn't appear

1. Select PNG or TIF files only
2. Restart Dolphin: `killall dolphin`
3. Verify files exist: `ls ~/.local/share/kio/servicemenus/`

### Script works from terminal but not from context menu

Verify the desktop files use full paths:
```
Exec=/usr/local/bin/image-stitcher.py horizontal %F
Exec=/usr/local/bin/grid-stitcher.py %F
```

## Technical Details

- **Stitching:** Alphabetical order, RGB conversion, white background fill, auto-numbered output with tile range detection
- **Security:** `X-KDE-AuthorizeAction=shell_access` enables shell command execution in KDE

## Uninstallation

```bash
sudo rm /usr/local/bin/image-stitcher.py /usr/local/bin/grid-stitcher.py
rm ~/.local/share/kio/servicemenus/image-stitcher.desktop
rm ~/.local/share/kio/servicemenus/grid-stitcher.desktop
```

## License

MIT License

## Contributing

Issues and pull requests welcome!
