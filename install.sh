#!/bin/bash
# Installation script for Image Stitcher tool

set -e

echo "Image Stitcher Installation Script"
echo "==================================="
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

# Install the Python script
echo ""
echo "Installing image-stitcher.py..."
chmod +x image-stitcher.py
sudo cp image-stitcher.py /usr/local/bin/
sudo chmod +x /usr/local/bin/image-stitcher.py

# Create directory for desktop actions if it doesn't exist
echo ""
echo "Installing desktop action for file managers..."
mkdir -p ~/.local/share/kio/servicemenus/

# Install the desktop file for Dolphin
cp image-stitcher.desktop ~/.local/share/kio/servicemenus/

# Also install for general file managers that support .desktop actions
mkdir -p ~/.local/share/file-manager/actions/
cp image-stitcher.desktop ~/.local/share/file-manager/actions/

echo ""
echo "==================================="
echo "Installation complete!"
echo ""
echo "You may need to:"
echo "1. Restart Dolphin (or logout/login)"
echo "2. Right-click on PNG files and look for 'Stitch Images' submenu"
echo ""
echo "Usage:"
echo "- Select multiple PNG files in Dolphin"
echo "- Right-click → Stitch Images → Choose direction"
echo "- Output TIF will be created in the same directory"
echo ""
