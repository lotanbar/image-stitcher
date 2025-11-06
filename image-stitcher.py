#!/usr/bin/env python3
"""
Image Stitcher - Stitch PNG/TIF images horizontally or vertically
"""
import sys
import os
import re
import subprocess
from pathlib import Path
from PIL import Image

# Increase PIL decompression bomb limit for large TIFF files
Image.MAX_IMAGE_PIXELS = None  # Disable limit entirely, or set to a large number like 1000000000

def sort_key(path):
    name = os.path.basename(path)
    m = re.match(r'^(\d+)\b', name)
    if m:
        return (0, int(m.group(1)))
    parts = re.findall(r'\d+|\D+', name.lower())
    norm = tuple(int(p) if p.isdigit() else p for p in parts)
    return (1, norm)


def extract_tile_number(filename):
    """
    Extract the tile number from a numbered filename.
    Expected format: '1 filename.ext', '42 filename.ext', etc.
    Returns None if no number found.
    """
    match = re.match(r'^(\d+)\s', filename)
    if match:
        return int(match.group(1))
    return None

def format_tile_ranges(numbers):
    """
    Convert a list of numbers into a compact string with ranges.
    Example: [1, 2, 4, 7, 8, 9] -> "1-2_4_7-9"
    """
    if not numbers:
        return ""

    numbers = sorted(set(numbers))  # Remove duplicates and sort
    ranges = []
    start = numbers[0]
    end = numbers[0]

    for i in range(1, len(numbers)):
        if numbers[i] == end + 1:
            end = numbers[i]
        else:
            if start == end:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{end}")
            start = numbers[i]
            end = numbers[i]

    # Add the last range
    if start == end:
        ranges.append(str(start))
    else:
        ranges.append(f"{start}-{end}")

    return "_".join(ranges)

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
    image_paths = sorted(image_paths, key=sort_key)

    # Extract tile numbers from filenames
    tile_numbers = []
    for path in image_paths:
        filename = os.path.basename(path)
        tile_num = extract_tile_number(filename)
        if tile_num is not None:
            tile_numbers.append(tile_num)

    # Use libvips for memory-efficient stitching (handles hundreds of GB)
    # vips uses streaming processing with minimal RAM usage

    # Generate output filename
    first_image_path = Path(image_paths[0])
    output_dir = first_image_path.parent

    # Create filename with tile numbers if available
    if tile_numbers:
        tile_str = format_tile_ranges(tile_numbers)
        base_filename = f"stitched_{direction}_{tile_str}.tif"
    else:
        base_filename = f"stitched_{direction}.tif"

    output_path = output_dir / base_filename

    # If file exists, add number
    counter = 1
    while output_path.exists():
        if tile_numbers:
            tile_str = format_tile_ranges(tile_numbers)
            output_path = output_dir / f"stitched_{direction}_{tile_str}_{counter}.tif"
        else:
            output_path = output_dir / f"stitched_{direction}_{counter}.tif"
        counter += 1

    # Stitch using libvips
    try:
        # vips arrayjoin needs all images to have same number of bands
        # Convert RGBA to RGB if needed
        temp_files = []
        normalized_paths = []

        for img_path in image_paths:
            # Check image bands using vipsheader
            result = subprocess.run(['vipsheader', img_path], capture_output=True, text=True)
            if '4 bands' in result.stdout:
                # Has alpha channel - flatten it
                temp_path = str(output_dir / f".tmp_flat_{Path(img_path).name}")
                subprocess.run(['vips', 'flatten', img_path, temp_path],
                             capture_output=True, text=True, check=True)
                temp_files.append(temp_path)
                normalized_paths.append(temp_path)
            else:
                normalized_paths.append(img_path)

        # Build vips arrayjoin command
        # --across 1 means vertical stacking (1 column), more means horizontal
        across = 1 if direction == 'vertical' else len(normalized_paths)

        # vips arrayjoin expects a single string with space-separated filenames
        # Paths with spaces need to be escaped with backslashes
        escaped_paths = [path.replace(' ', r'\ ') for path in normalized_paths]
        images_string = ' '.join(escaped_paths)
        cmd = ['vips', 'arrayjoin', images_string, str(output_path), '--across', str(across)]

        # Print command for debugging
        print(f"\n=== vips Command ===")
        print(f"Command: {' '.join(cmd)}")
        print(f"Number of images: {len(image_paths)}")
        print(f"Output: {output_path}")
        print("=" * 50)

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Clean up temp files
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except:
                pass

        # Print stdout if any
        if result.stdout:
            print(f"vips stdout: {result.stdout}")

        show_notification("Success", f"Successfully stitched {len(image_paths)} files\n\nSaved to:\n{output_path.name}", error=False)
    except subprocess.CalledProcessError as e:
        # Clean up temp files on error
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except:
                pass

        error_msg = f"vips stitching failed\n\n"
        error_msg += f"Return code: {e.returncode}\n"
        error_msg += f"STDERR: {e.stderr}\n"
        error_msg += f"STDOUT: {e.stdout}\n"
        error_msg += f"Command: {' '.join(cmd)}"

        print(f"\n=== ERROR ===")
        print(error_msg)
        print("=" * 50)

        show_notification("Error", error_msg, error=True)
        sys.exit(1)
    except Exception as e:
        # Clean up temp files on error
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except:
                pass

        show_notification("Error", f"Failed to stitch images\n{str(e)}", error=True)
        sys.exit(1)

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
