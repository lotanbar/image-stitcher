#!/usr/bin/env python3
"""
Grid Stitcher - Stitch images in a custom grid layout with intelligent gap minimization
"""
import sys
import os
import re
import subprocess
import math
import time
from pathlib import Path
from PIL import Image

# ============================================================================
# CONFIGURATION - Change these file extensions to match your image types
# ============================================================================
VALID_EXTENSIONS = ('.png',)  # Add more like: ('.png', '.tif', '.tiff', '.jpg')
# ============================================================================

# Log immediately when script starts
print(f"[{time.time():.3f}] ===== SCRIPT START at {time.strftime('%H:%M:%S')} =====", flush=True)
print(f"[{time.time():.3f}] Python PID: {os.getpid()}", flush=True)
print(f"[{time.time():.3f}] Arguments count: {len(sys.argv)}", flush=True)

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

    # Convert to list and sort: by columns (ascending)
    options_list = list(options)
    options_list.sort(key=lambda x: x[1])  # Sort by columns (x[1])

    return options_list

def show_grid_dialog(total_files):
    """
    Show tkinter GUI for grid configuration.
    Returns: (rows, cols) or None if cancelled
    """
    import tkinter as tk
    from tkinter import ttk
    import time

    print(f"[{time.time():.3f}] show_grid_dialog() called with {total_files} files")

    result = {'rows': None, 'cols': None, 'stitch_all': False, 'stitch_selected': False, 'grid_options': None, 'file_count': total_files}

    # Don't calculate grid options immediately - let user trigger it
    grid_options = []
    print(f"[{time.time():.3f}] Initialized grid_options")

    def get_effective_file_count():
        """Get the current file count from the input field"""
        try:
            count = int(file_count_entry.get())
            if count > 0 and count <= total_files:
                return count
        except ValueError:
            pass
        return total_files

    def on_stitch():
        try:
            rows = int(row_entry.get())
            cols = int(col_entry.get())
            if rows > 0 and cols > 0:
                result['rows'] = rows
                result['cols'] = cols
                result['file_count'] = get_effective_file_count()
                root.destroy()
        except ValueError:
            pass

    def on_stitch_all_or_selected():
        """Stitch all or selected grid configurations"""
        selected_indices = listbox.curselection()

        if selected_indices:
            # User has selected specific items
            result['stitch_selected'] = True
            result['grid_options'] = [grid_options[i] for i in selected_indices]
        else:
            # No selection, stitch all
            result['stitch_all'] = True
            result['grid_options'] = grid_options

        result['file_count'] = get_effective_file_count()
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

    def update_button_text(*args):
        """Update button text based on selection"""
        selected_count = len(listbox.curselection())
        if selected_count > 0:
            stitch_all_button.config(text=f"Stitch Selected ({selected_count})")
        else:
            stitch_all_button.config(text="Stitch All Matches")

    def on_calculate_all():
        """Calculate and display all possible grid configurations"""
        nonlocal grid_options

        # Calculate all options using the effective file count
        effective_count = get_effective_file_count()
        grid_options = find_optimal_grids_with_blanks(effective_count, max_blanks=25)

        # Clear and populate listbox
        listbox.delete(0, tk.END)
        for rows, cols, blanks, is_perfect in grid_options:
            if is_perfect:
                text = f"✓ {cols:3d}×{rows:<3d}  (0 blanks) PERFECT!"
                listbox.insert(tk.END, text)
                # Color perfect matches green
                listbox.itemconfig(listbox.size() - 1, fg='green', selectbackground='darkgreen')
            else:
                text = f"  {cols:3d}×{rows:<3d}  ({blanks} blank{'s' if blanks > 1 else ''})"
                listbox.insert(tk.END, text)

    def on_calculate_other():
        """Calculate possible values for the empty dimension"""
        nonlocal grid_options

        try:
            rows_val = row_entry.get().strip()
            cols_val = col_entry.get().strip()
            effective_count = get_effective_file_count()

            # Check if exactly one field is filled
            if rows_val and not cols_val:
                # User filled rows, calculate possible cols
                rows = int(rows_val)
                if rows <= 0:
                    return

                # Find all grids with this row count (±5 around the value, up to 25 blanks)
                options = []
                for row_offset in range(-5, 6):  # -5 to +5 around user's value
                    test_rows = rows + row_offset
                    if test_rows < 3:
                        continue

                    for target in range(effective_count, effective_count + 26):  # up to 25 blanks
                        if target % test_rows == 0:
                            cols = target // test_rows
                            blanks = target - effective_count
                            # Apply same filters as find_all_factors
                            if cols >= 3:
                                aspect_ratio = max(test_rows, cols) / min(test_rows, cols)
                                if aspect_ratio <= 10:
                                    options.append((test_rows, cols, blanks, blanks == 0))

                grid_options = sorted(options, key=lambda x: x[1])  # Sort by columns

            elif cols_val and not rows_val:
                # User filled cols, calculate possible rows
                cols = int(cols_val)
                if cols <= 0:
                    return

                # Find all grids with this column count (±5 around the value, up to 25 blanks)
                options = []
                for col_offset in range(-5, 6):  # -5 to +5 around user's value
                    test_cols = cols + col_offset
                    if test_cols < 3:
                        continue

                    for target in range(effective_count, effective_count + 26):  # up to 25 blanks
                        if target % test_cols == 0:
                            rows = target // test_cols
                            blanks = target - effective_count
                            # Apply same filters as find_all_factors
                            if rows >= 3:
                                aspect_ratio = max(rows, test_cols) / min(rows, test_cols)
                                if aspect_ratio <= 10:
                                    options.append((rows, test_cols, blanks, blanks == 0))

                grid_options = sorted(options, key=lambda x: x[1])  # Sort by columns
            else:
                # Either both filled or both empty
                return

            # Clear and populate listbox
            listbox.delete(0, tk.END)
            if not grid_options:
                listbox.insert(tk.END, "No valid configurations found")
            else:
                for rows, cols, blanks, is_perfect in grid_options:
                    if is_perfect:
                        text = f"✓ {cols:3d}×{rows:<3d}  (0 blanks) PERFECT!"
                        listbox.insert(tk.END, text)
                        listbox.itemconfig(listbox.size() - 1, fg='green', selectbackground='darkgreen')
                    else:
                        text = f"  {cols:3d}×{rows:<3d}  ({blanks} blank{'s' if blanks > 1 else ''})"
                        listbox.insert(tk.END, text)

        except ValueError:
            pass

    def on_grid_click(event):
        selection = listbox.curselection()
        # Only fill input fields if exactly one item is selected
        if len(selection) == 1:
            idx = selection[0]
            if idx < len(grid_options):
                rows, cols, blanks, is_perfect = grid_options[idx]
                row_entry.delete(0, tk.END)
                row_entry.insert(0, str(rows))
                col_entry.delete(0, tk.END)
                col_entry.insert(0, str(cols))

    # Create main window
    print(f"[{time.time():.3f}] Creating tkinter window...")
    root = tk.Tk()
    print(f"[{time.time():.3f}] Tk() created")
    root.title("Custom Grid Stitch")
    root.geometry("550x650")
    root.resizable(True, True)
    print(f"[{time.time():.3f}] Window configured")

    # Main frame with padding
    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Title with file count selector
    title_frame = ttk.Frame(main_frame)
    title_frame.pack(pady=(0, 15))

    ttk.Label(title_frame, text=f"Total files: {total_files}  |  Use:",
             font=("", 11, "bold")).pack(side=tk.LEFT, padx=(0, 5))

    file_count_entry = ttk.Entry(title_frame, width=8)
    file_count_entry.pack(side=tk.LEFT, padx=(0, 5))
    file_count_entry.insert(0, str(total_files))

    ttk.Label(title_frame, text="files from start",
             font=("", 11)).pack(side=tk.LEFT)

    # Input frame
    input_frame = ttk.Frame(main_frame)
    input_frame.pack(pady=(0, 10))

    # Columns input (now first)
    col_frame = ttk.Frame(input_frame)
    col_frame.pack(pady=5)
    ttk.Label(col_frame, text="Columns:", width=10, anchor='e').pack(side=tk.LEFT, padx=(0, 5))
    col_entry = ttk.Entry(col_frame, width=15)
    col_entry.pack(side=tk.LEFT)

    # Rows input (now second)
    row_frame = ttk.Frame(input_frame)
    row_frame.pack(pady=5)
    ttk.Label(row_frame, text="Rows:", width=10, anchor='e').pack(side=tk.LEFT, padx=(0, 5))
    row_entry = ttk.Entry(row_frame, width=15)
    row_entry.pack(side=tk.LEFT)

    # Buttons - three rows
    button_frame = ttk.Frame(input_frame)
    button_frame.pack(pady=10)

    # First row of buttons
    button_row1 = ttk.Frame(button_frame)
    button_row1.pack()
    ttk.Button(button_row1, text="Stitch", command=on_stitch, width=10).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_row1, text="Swap", command=on_swap, width=10).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_row1, text="Cancel", command=on_cancel, width=10).pack(side=tk.LEFT, padx=5)

    # Second row - Calculation buttons
    button_row2 = ttk.Frame(button_frame)
    button_row2.pack(pady=(5, 0))
    ttk.Button(button_row2, text="Calculate All Options", command=on_calculate_all, width=32).pack()

    # Third row
    button_row3 = ttk.Frame(button_frame)
    button_row3.pack(pady=(5, 0))
    ttk.Button(button_row3, text="Find Matching Dimension", command=on_calculate_other, width=32).pack()

    # Fourth row
    button_row4 = ttk.Frame(button_frame)
    button_row4.pack(pady=(5, 0))
    stitch_all_button = ttk.Button(button_row4, text="Stitch All Matches", command=on_stitch_all_or_selected, width=32)
    stitch_all_button.pack()

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
                        font=("Courier", 10), height=15, selectmode=tk.EXTENDED)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=listbox.yview)

    # Don't populate listbox initially - let user trigger it with buttons
    listbox.insert(tk.END, "Click 'Calculate All Options' or 'Find Matching Dimension' to see suggestions")

    # Bind click event and selection change
    listbox.bind('<<ListboxSelect>>', on_grid_click)
    listbox.bind('<<ListboxSelect>>', update_button_text, add='+')

    # Bind Enter key to stitch
    root.bind('<Return>', lambda e: on_stitch())
    root.bind('<Escape>', lambda e: on_cancel())

    # Center window
    print(f"[{time.time():.3f}] Centering window...")
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    print(f"[{time.time():.3f}] Window centered")

    # Run dialog
    print(f"[{time.time():.3f}] Starting mainloop (dialog should be visible now)")
    root.mainloop()
    print(f"[{time.time():.3f}] Mainloop ended")

    if result['stitch_all']:
        return 'stitch_all', result['grid_options'], result['file_count']
    elif result['stitch_selected']:
        return 'stitch_selected', result['grid_options'], result['file_count']
    elif result['rows'] and result['cols']:
        return result['rows'], result['cols'], result['file_count']
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
    base_filename = f"stitched_grid_{cols}x{rows}.tif"

    output_path = output_dir / base_filename

    # If file exists, add counter
    counter = 1
    while output_path.exists():
        output_path = output_dir / f"stitched_grid_{cols}x{rows}_{counter}.tif"
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
    import time

    print(f"[{time.time():.3f}] Script started")

    if len(sys.argv) < 2:
        print("Usage: grid-stitcher.py <directory_or_files...>")
        sys.exit(1)

    print(f"[{time.time():.3f}] Got {len(sys.argv) - 1} arguments")

    # Collect image files from arguments (can be directories or files)
    image_files = []

    for arg in sys.argv[1:]:
        if os.path.isdir(arg):
            # If directory, find all valid images in it
            print(f"[{time.time():.3f}] Scanning directory: {arg}")
            for filename in os.listdir(arg):
                filepath = os.path.join(arg, filename)
                if os.path.isfile(filepath) and filename.lower().endswith(VALID_EXTENSIONS):
                    image_files.append(filepath)
            print(f"[{time.time():.3f}] Found {len(image_files)} images in directory")
        elif os.path.isfile(arg):
            # If file, check if it's valid
            if arg.lower().endswith(VALID_EXTENSIONS):
                image_files.append(arg)

    print(f"[{time.time():.3f}] Total valid image files: {len(image_files)}")

    if not image_files:
        ext_list = ', '.join(VALID_EXTENSIONS)
        show_notification("Error", f"No images found with extensions: {ext_list}", error=True)
        sys.exit(1)

    # Don't sort yet - just show the dialog with the count
    # Sorting will happen after user commits to stitching
    # Show dialog and get grid configuration
    print(f"[{time.time():.3f}] Opening dialog...")
    grid_config = show_grid_dialog(len(image_files))
    print(f"[{time.time():.3f}] Dialog closed")

    if grid_config is None:
        sys.exit(0)  # User cancelled

    # NOW sort the files since user committed to stitching
    print(f"[{time.time():.3f}] Sorting files...")
    image_files = sorted(image_files, key=sort_key)
    print(f"[{time.time():.3f}] Sorting complete")

    # Check if user wants to stitch all or selected
    if isinstance(grid_config, tuple) and grid_config[0] in ('stitch_all', 'stitch_selected'):
        mode, grid_options, file_count = grid_config

        # Limit image files to the requested count from the beginning
        image_files = image_files[:file_count]
        print(f"[{time.time():.3f}] Using first {file_count} files for stitching")

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
        title = "Stitch Selected Complete" if mode == 'stitch_selected' else "Stitch All Complete"
        if error_count == 0:
            show_notification(
                title,
                f"Successfully stitched {success_count} grid combination{'s' if success_count > 1 else ''}!",
                error=False
            )
        else:
            error_msg = '\n'.join(errors[:3])
            if len(errors) > 3:
                error_msg += f"\n... and {len(errors) - 3} more errors"
            title = "Stitch Selected Partial Success" if mode == 'stitch_selected' else "Stitch All Partial Success"
            show_notification(
                title,
                f"Completed {success_count}/{total_stitches} stitches\n\nErrors:\n{error_msg}",
                error=True
            )
    else:
        # Single stitch mode
        rows, cols, file_count = grid_config

        # Limit image files to the requested count from the beginning
        image_files = image_files[:file_count]
        print(f"[{time.time():.3f}] Using first {file_count} files for stitching")

        stitch_grid(image_files, rows, cols)
