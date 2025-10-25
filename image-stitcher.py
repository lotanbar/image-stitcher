#!/usr/bin/env python3
"""
Image Stitcher - Stitch PNG/TIF images horizontally or vertically
"""
import sys
import os
import subprocess
from pathlib import Path
from PIL import Image

def stitch_images(image_paths, direction='horizontal'):
    """
    Stitch images together horizontally or vertically.
    Supports PNG and TIF/TIFF files.
    
    Args:
        image_paths: List of image file paths (sorted by name)
        direction: 'horizontal' or 'vertical'
    """
    if not image_paths:
        show_notification("Error", "No images provided", error=True)
        sys.exit(1)
    
    # Filter only PNG and TIF files
    valid_extensions = ('.png', '.tif', '.tiff')
    image_paths = [p for p in image_paths if p.lower().endswith(valid_extensions)]
    
    if not image_paths:
        show_notification("Error", "No PNG or TIF files provided", error=True)
        sys.exit(1)
    
    # Sort images by filename
    image_paths = sorted(image_paths, key=lambda x: os.path.basename(x))
    
    # Load all images
    images = []
    for path in image_paths:
        try:
            img = Image.open(path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            images.append(img)
        except Exception as e:
            show_notification("Error", f"Failed to load image: {os.path.basename(path)}\n{str(e)}", error=True)
            sys.exit(1)
    
    if not images:
        show_notification("Error", "No valid images loaded", error=True)
        sys.exit(1)
    
    # Calculate dimensions for stitched image
    if direction == 'horizontal':
        total_width = sum(img.width for img in images)
        max_height = max(img.height for img in images)
        result = Image.new('RGB', (total_width, max_height), (255, 255, 255))
        
        x_offset = 0
        for img in images:
            result.paste(img, (x_offset, 0))
            x_offset += img.width
    else:  # vertical
        max_width = max(img.width for img in images)
        total_height = sum(img.height for img in images)
        result = Image.new('RGB', (max_width, total_height), (255, 255, 255))
        
        y_offset = 0
        for img in images:
            result.paste(img, (0, y_offset))
            y_offset += img.height
    
    # Generate output filename in the same directory as first image
    first_image_path = Path(image_paths[0])
    output_dir = first_image_path.parent
    output_path = output_dir / f"stitched_{direction}.tif"
    
    # If file exists, add number
    counter = 1
    while output_path.exists():
        output_path = output_dir / f"stitched_{direction}_{counter}.tif"
        counter += 1
    
    # Save as TIF
    try:
        result.save(output_path, format='TIFF')
        show_notification("Success", f"Successfully stitched {len(image_paths)} files\n\nSaved to:\n{output_path.name}", error=False)
    except Exception as e:
        show_notification("Error", f"Failed to save stitched image\n{str(e)}", error=True)
        sys.exit(1)
    
    # Close all images
    for img in images:
        img.close()

def show_notification(title, message, error=False):
    """Show a KDE notification dialog"""
    try:
        if error:
            subprocess.run(['kdialog', '--error', message, '--title', title], check=False)
        else:
            subprocess.run(['kdialog', '--msgbox', message, '--title', title], check=False)
    except:
        # Fallback to console if kdialog not available
        print(f"{title}: {message}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: image-stitcher.py [horizontal|vertical] <image1> <image2> ...")
        sys.exit(1)
    
    direction = sys.argv[1]
    if direction not in ['horizontal', 'vertical']:
        print("Error: Direction must be 'horizontal' or 'vertical'")
        sys.exit(1)
    
    image_files = sys.argv[2:]
    stitch_images(image_files, direction)
