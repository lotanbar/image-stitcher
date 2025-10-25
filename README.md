# Image Stitcher & File Numberer for Dolphin

Lightweight tools for stitching and numbering PNG/TIF images from the Dolphin file manager context menu on Fedora Linux.

## Features

**Image Stitcher:**
- Stitch images horizontally or vertically
- Alphabetical ordering • TIF output

**File Numberer:**
- Add sequential numbers (1, 2, 3...)
- Remove numbers from files
- Handles multi-digit numbers

**Both:**
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

**Number:** Select files → Right-click → Number Files (1, 2, 3...)

**Unnumber:** Select numbered files → Right-click → Remove Numbers from Files

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
chmod +x ~/.local/share/kio/servicemenus/file-numberer.desktop
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
Exec=/usr/local/bin/file-numberer.py number %F
```

## Technical Details

- **Stitching:** Alphabetical order, RGB conversion, white background fill, auto-numbered output
- **Numbering:** Pattern `^\d+\s`, alphabetical sorting, duplicate detection
- **Security:** `X-KDE-AuthorizeAction=shell_access` enables shell command execution in KDE

## Uninstallation

```bash
sudo rm /usr/local/bin/image-stitcher.py /usr/local/bin/file-numberer.py
rm ~/.local/share/kio/servicemenus/image-stitcher.desktop
rm ~/.local/share/kio/servicemenus/file-numberer.desktop
```

## License

MIT License

## Contributing

Issues and pull requests welcome!
