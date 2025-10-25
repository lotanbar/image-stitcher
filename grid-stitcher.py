#!/usr/bin/env python3
"""
Grid Stitcher - Stitch images in a custom grid layout with intelligent gap minimization
"""
import sys
import os
import re
import subprocess
import math
from pathlib import Path
from PIL import Image

def sort_key(path):
    name = os.path.basename(path)
    m = re.match(r'^(\d+)\b', name)
    if m:
        return (0, int(m.group(1)))
    parts = re.findall(r'\d+|\D+', name.lower())
    norm = tuple(int(p) if p.isdigit() else p for p in parts)
    return (1, norm)


def find_all_factors(n):
    """Find all factor pairs of n, excluding impractical ones."""
    factors = []
    for i in range(1, int(math.sqrt(n)) + 1):
        if n % i == 0:
            r, c = i, n // i
            # Filter out grids with dimension < 3 or aspect ratio > 10:1
            if r >= 3 and c >= 3:
                aspect_ratio = max(r, c) / min(r, c)
                if aspect_ratio <= 10:
                    factors.append((r, c))
    return factors

def find_optimal_grids_with_blanks(total_files, max_blanks=5):
    """
    Find all grids with up to max_blanks blank tiles.

    Returns:
        List of tuples: (rows, cols, blank_tiles, is_perfect)
    """
    options = set()

    # Check all numbers from total_files to total_files + max_blanks
    for target in range(total_files, total_files + max_blanks + 1):
        factors = find_all_factors(target)
        blank = target - total_files

        for r, c in factors:
            options.add((r, c, blank, blank == 0))

    # Convert to list and sort: perfect first, then by blanks, then by aspect ratio
    options_list = list(options)
    options_list.sort(key=lambda x: (not x[3], x[2], abs(x[0] - x[1])))

    return options_list

def show_grid_dialog(total_files):
    """
    Show tkinter GUI for grid configuration.
    Returns: (rows, cols) or None if cancelled
    """
    import tkinter as tk
    from tkinter import ttk

    result = {'rows': None, 'cols': None, 'stitch_all': False, 'grid_options': None}

    # Find all optimal grids
    grid_options = find_optimal_grids_with_blanks(total_files, max_blanks=5)

    def on_stitch():
        try:
            rows = int(row_entry.get())
            cols = int(col_entry.get())
            if rows > 0 and cols > 0:
                result['rows'] = rows
                result['cols'] = cols
                root.destroy()
        except ValueError:
            pass

    def on_stitch_all():
        """Stitch all grid configurations"""
        result['stitch_all'] = True
        result['grid_options'] = grid_options
        root.destroy()

    def on_swap():
        """Swap the values in rows and columns entries"""
        try:
            current_rows = row_entry.get()
            current_cols = col_entry.get()
            row_entry.delete(0, tk.END)
            row_entry.insert(0, current_cols)
            col_entry.delete(0, tk.END)
            col_entry.insert(0, current_rows)
        except:
            pass

    def on_cancel():
        root.destroy()

    def on_grid_click(event):
        selection = listbox.curselection()
        if selection:
            idx = selection[0]
            if idx < len(grid_options):
                rows, cols, blanks, is_perfect = grid_options[idx]
                row_entry.delete(0, tk.END)
                row_entry.insert(0, str(rows))
                col_entry.delete(0, tk.END)
                col_entry.insert(0, str(cols))

    # Create main window
    root = tk.Tk()
    root.title("Custom Grid Stitch")
    root.geometry("400x500")
    root.resizable(False, False)

    # Main frame with padding
    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Title
    title_label = ttk.Label(main_frame, text=f"Total files: {total_files}",
                           font=("", 12, "bold"))
    title_label.pack(pady=(0, 15))

    # Input frame
    input_frame = ttk.Frame(main_frame)
    input_frame.pack(pady=(0, 10))

    # Rows input
    row_frame = ttk.Frame(input_frame)
    row_frame.pack(pady=5)
    ttk.Label(row_frame, text="Rows:", width=10, anchor='e').pack(side=tk.LEFT, padx=(0, 5))
    row_entry = ttk.Entry(row_frame, width=15)
    row_entry.pack(side=tk.LEFT)

    # Columns input
    col_frame = ttk.Frame(input_frame)
    col_frame.pack(pady=5)
    ttk.Label(col_frame, text="Columns:", width=10, anchor='e').pack(side=tk.LEFT, padx=(0, 5))
    col_entry = ttk.Entry(col_frame, width=15)
    col_entry.pack(side=tk.LEFT)

    # Buttons - two rows
    button_frame = ttk.Frame(input_frame)
    button_frame.pack(pady=10)

    # First row of buttons
    button_row1 = ttk.Frame(button_frame)
    button_row1.pack()
    ttk.Button(button_row1, text="Stitch", command=on_stitch, width=10).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_row1, text="Swap", command=on_swap, width=10).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_row1, text="Cancel", command=on_cancel, width=10).pack(side=tk.LEFT, padx=5)

    # Second row
    button_row2 = ttk.Frame(button_frame)
    button_row2.pack(pady=(5, 0))
    ttk.Button(button_row2, text="Stitch All Matches", command=on_stitch_all, width=32).pack()

    # Separator
    ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=10)

    # Suggestions label
    ttk.Label(main_frame, text="Suggested Grids (click to select):",
             font=("", 10, "bold")).pack(pady=(0, 5))

    # Listbox with scrollbar
    list_frame = ttk.Frame(main_frame)
    list_frame.pack(fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(list_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                        font=("Courier", 10), height=15)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=listbox.yview)

    # Populate listbox
    for rows, cols, blanks, is_perfect in grid_options:
        if is_perfect:
            text = f"✓ {rows:3d}×{cols:<3d}  (0 blanks) PERFECT!"
            listbox.insert(tk.END, text)
            # Color perfect matches green
            listbox.itemconfig(listbox.size() - 1, fg='green', selectbackground='darkgreen')
        else:
            text = f"  {rows:3d}×{cols:<3d}  ({blanks} blank{'s' if blanks > 1 else ''})"
            listbox.insert(tk.END, text)

    # Bind click event
    listbox.bind('<<ListboxSelect>>', on_grid_click)

    # Bind Enter key to stitch
    root.bind('<Return>', lambda e: on_stitch())
    root.bind('<Escape>', lambda e: on_cancel())

    # Center window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")

    # Run dialog
    root.mainloop()

    if result['stitch_all']:
        return 'stitch_all', result['grid_options']
    elif result['rows'] and result['cols']:
        return result['rows'], result['cols']
    return None

def stitch_grid(image_paths, rows, cols, silent=False):
    """
    Stitch images in a grid layout.

    Args:
        image_paths: List of image file paths (sorted)
        rows: Number of rows
        cols: Number of columns
        silent: If True, don't show notification (for batch processing)
    """
    if not image_paths:
        show_notification("Error", "No images provided", error=True)
        sys.exit(1)

    # Load all images
    images = []
    for path in image_paths:
        try:
            img = Image.open(path)
            # Force convert palette images to RGB
            if img.mode in ('P', 'PA', 'L', 'LA'):
                img = img.convert('RGB')
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            images.append(img)
        except Exception as e:
            show_notification("Error", f"Failed to load: {os.path.basename(path)}\n{str(e)}", error=True)
            sys.exit(1)

    if not images:
        show_notification("Error", "No valid images loaded", error=True)
        sys.exit(1)

    # Get max dimensions for tile size
    max_width = max(img.width for img in images)
    max_height = max(img.height for img in images)

    # Create result canvas
    total_width = cols * max_width
    total_height = rows * max_height
    result = Image.new('RGB', (total_width, total_height), (255, 255, 255))

    # Paste images in grid (left-to-right, top-to-bottom)
    for idx, img in enumerate(images):
        if idx >= rows * cols:
            break

        row = idx // cols
        col = idx % cols

        x_offset = col * max_width
        y_offset = row * max_height

        result.paste(img, (x_offset, y_offset))

    # Generate output filename
    first_image_path = Path(image_paths[0])
    output_dir = first_image_path.parent

    blank_tiles = (rows * cols) - len(images)
    base_filename = f"stitched_grid_{rows}x{cols}.tif"

    output_path = output_dir / base_filename

    # If file exists, add counter
    counter = 1
    while output_path.exists():
        output_path = output_dir / f"stitched_grid_{rows}x{cols}_{counter}.tif"
        counter += 1

    # Save as TIF
    try:
        result.save(output_path, format='TIFF')
        if not silent:
            msg = f"Successfully stitched {len(images)} image(s)\n\n"
            msg += f"Grid: {rows} rows × {cols} columns\n"
            if blank_tiles > 0:
                msg += f"Blank tiles: {blank_tiles}\n"
            msg += f"\nSaved to:\n{output_path.name}"
            show_notification("Success", msg, error=False)
    except Exception as e:
        if not silent:
            show_notification("Error", f"Failed to save stitched image\n{str(e)}", error=True)
        raise  # Re-raise so batch processing can catch it

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
        print(f"{title}: {message}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: grid-stitcher.py <image1> <image2> ...")
        sys.exit(1)

    image_files = sys.argv[1:]

    # Filter valid files
    valid_extensions = ('.png', '.tif', '.tiff')
    image_files = [f for f in image_files if f.lower().endswith(valid_extensions)]

    if not image_files:
        show_notification("Error", "No PNG or TIF files provided", error=True)
        sys.exit(1)

    # Sort alphabetically
    image_files = sorted(image_files, key=sort_key)

    # Show dialog and get grid configuration
    grid_config = show_grid_dialog(len(image_files))

    if grid_config is None:
        sys.exit(0)  # User cancelled

    # Check if user wants to stitch all
    if isinstance(grid_config, tuple) and grid_config[0] == 'stitch_all':
        _, grid_options = grid_config

        # Collect all unique grid combinations (including swapped versions)
        all_grids = set()
        for rows, cols, blanks, is_perfect in grid_options:
            all_grids.add((rows, cols))
            # Also add swapped version
            all_grids.add((cols, rows))

        # Sort for consistent ordering
        all_grids = sorted(all_grids)

        total_stitches = len(all_grids)
        success_count = 0
        error_count = 0
        errors = []

        for idx, (rows, cols) in enumerate(all_grids, 1):
            try:
                print(f"Stitching grid {idx}/{total_stitches}: {rows}x{cols}...")
                stitch_grid(image_files, rows, cols, silent=True)
                success_count += 1

                # Clear memory after each stitch
                import gc
                gc.collect()

            except Exception as e:
                error_count += 1
                errors.append(f"{rows}x{cols}: {str(e)}")

        # Show summary notification
        if error_count == 0:
            show_notification(
                "Stitch All Complete",
                f"Successfully stitched all {success_count} grid combinations!",
                error=False
            )
        else:
            error_msg = '\n'.join(errors[:3])
            if len(errors) > 3:
                error_msg += f"\n... and {len(errors) - 3} more errors"
            show_notification(
                "Stitch All Partial Success",
                f"Completed {success_count}/{total_stitches} stitches\n\nErrors:\n{error_msg}",
                error=True
            )
    else:
        # Single stitch mode
        rows, cols = grid_config
        stitch_grid(image_files, rows, cols)
