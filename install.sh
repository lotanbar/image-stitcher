#!/bin/bash
# Installation script for Image Stitcher tools

set -e

echo "Image Stitcher Installation"
echo "============================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo "Please do not run this script as root/sudo"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
if command -v dnf &> /dev/null; then
    echo "Installing Python Pillow via dnf..."
    sudo dnf install -y python3-pillow
else
    echo "dnf not found. Installing Pillow via pip..."
    pip3 install --user Pillow
fi

# Install the Python scripts
echo ""
echo "Installing image-stitcher.py..."
chmod +x image-stitcher.py
sudo cp image-stitcher.py /usr/local/bin/
sudo chmod +x /usr/local/bin/image-stitcher.py

echo "Installing grid-stitcher.py..."
chmod +x grid-stitcher.py
sudo cp grid-stitcher.py /usr/local/bin/
sudo chmod +x /usr/local/bin/grid-stitcher.py

echo "Installing view-stitched-enlarged.py..."
chmod +x view-stitched-enlarged.py
sudo cp view-stitched-enlarged.py /usr/local/bin/
sudo chmod +x /usr/local/bin/view-stitched-enlarged.py

# Create directory for desktop actions if it doesn't exist
echo ""
echo "Installing desktop actions for file managers..."
mkdir -p ~/.local/share/kio/servicemenus/

# Install the desktop files for Dolphin
cp image-stitcher.desktop ~/.local/share/kio/servicemenus/
cp grid-stitcher.desktop ~/.local/share/kio/servicemenus/
cp view-stitched-enlarged.desktop ~/.local/share/kio/servicemenus/

# Make desktop files executable (required for Plasma 6)
chmod +x ~/.local/share/kio/servicemenus/image-stitcher.desktop
chmod +x ~/.local/share/kio/servicemenus/grid-stitcher.desktop
chmod +x ~/.local/share/kio/servicemenus/view-stitched-enlarged.desktop

# Also install for general file managers that support .desktop actions
mkdir -p ~/.local/share/file-manager/actions/
cp image-stitcher.desktop ~/.local/share/file-manager/actions/
cp grid-stitcher.desktop ~/.local/share/file-manager/actions/
cp view-stitched-enlarged.desktop ~/.local/share/file-manager/actions/
chmod +x ~/.local/share/file-manager/actions/image-stitcher.desktop
chmod +x ~/.local/share/file-manager/actions/grid-stitcher.desktop
chmod +x ~/.local/share/file-manager/actions/view-stitched-enlarged.desktop

echo ""
echo "============================"
echo "Installation complete!"
echo ""
echo "You may need to:"
echo "1. Restart Dolphin (or logout/login)"
echo "2. Right-click on PNG/TIF files or folders"
echo ""
echo "Available actions:"
echo "  - Stitch Horizontally (Left to Right)"
echo "  - Stitch Vertically (Top to Bottom)"
echo "  - Stitch in Custom Grid..."
echo "  - View Stitched Enlarged..."
echo ""
