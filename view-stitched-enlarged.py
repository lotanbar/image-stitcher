#!/usr/bin/env python3
"""
View Stitched Enlarged - View consecutive horizontal image pairs in enlarged format
Press 'm' to mark mismatches with 'z' suffix for counting grid columns
"""
import sys
import os
import re
from pathlib import Path
from PIL import Image
import tkinter as tk
from tkinter import ttk
from PIL import ImageTk
import subprocess

# ============================================================================
# CONFIGURATION - Change these file extensions to match your image types
# ============================================================================
VALID_EXTENSIONS = ('.png',)  # Add more like: ('.png', '.tif', '.tiff', '.jpg')
# ============================================================================

def sort_key(path):
    """Sort files numerically if they start with a number, otherwise alphabetically"""
    name = os.path.basename(path)
    m = re.match(r'^(\d+)\b', name)
    if m:
        return (0, int(m.group(1)))
    parts = re.findall(r'\d+|\D+', name.lower())
    norm = tuple(int(p) if p.isdigit() else p for p in parts)
    return (1, norm)

def show_notification(title, message, error=False):
    """Show a KDE notification dialog"""
    try:
        if error:
            subprocess.run(['kdialog', '--error', message, '--title', title], check=False)
        else:
            subprocess.run(['kdialog', '--msgbox', message, '--title', title], check=False)
    except:
        print(f"{title}: {message}")

def show_enlarged_viewer(image_paths):
    """
    Show consecutive horizontal pairs in an enlarged view.
    Press 'm' to mark the left image with 'z' suffix.
    Use arrow keys or buttons to navigate.
    """
    if len(image_paths) < 2:
        show_notification("Error", "Need at least 2 images for viewing pairs", error=True)
        return

    # Track current pair index (0 = images 1-2, 1 = images 2-3, etc.)
    state = {'current_idx': 0, 'jump_amount': 1}

    def is_marked(path):
        """Check if a file is marked with 'z' suffix"""
        filename = os.path.basename(path)
        name, _ = os.path.splitext(filename)
        return name.endswith('z')

    def add_red_border_to_stitched(img, border_width=15):
        """Add a red border around the entire stitched image"""
        bordered = Image.new('RGB',
                            (img.width + 2*border_width, img.height + 2*border_width),
                            (255, 0, 0))
        bordered.paste(img, (border_width, border_width))
        return bordered

    def stitch_pair(img1_path, img2_path):
        """Stitch two images horizontally"""
        img1 = Image.open(img1_path)
        img2 = Image.open(img2_path)

        # Force convert to RGB
        if img1.mode in ('P', 'PA', 'L', 'LA'):
            img1 = img1.convert('RGB')
        elif img1.mode != 'RGB':
            img1 = img1.convert('RGB')

        if img2.mode in ('P', 'PA', 'L', 'LA'):
            img2 = img2.convert('RGB')
        elif img2.mode != 'RGB':
            img2 = img2.convert('RGB')

        # Create horizontal stitch
        total_width = img1.width + img2.width
        total_height = max(img1.height, img2.height)
        result = Image.new('RGB', (total_width, total_height), (30, 30, 30))  # Dark background

        # Center images vertically
        y1_offset = (total_height - img1.height) // 2
        y2_offset = (total_height - img2.height) // 2
        result.paste(img1, (0, y1_offset))
        result.paste(img2, (img1.width, y2_offset))

        img1.close()
        img2.close()

        # Add red border around the ENTIRE stitched pair if the second image is marked
        if is_marked(img2_path):
            result = add_red_border_to_stitched(result)

        return result

    def get_display_image(pil_image, max_width=2400, max_height=1200):
        """Resize image to fit display while maintaining aspect ratio"""
        ratio = min(max_width / pil_image.width, max_height / pil_image.height)
        if ratio < 1:
            new_width = int(pil_image.width * ratio)
            new_height = int(pil_image.height * ratio)
            return pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return pil_image

    def calculate_gaps():
        """Calculate gaps from the beginning, between marked images, and to the end"""
        gaps = []
        marked_indices = []

        for idx, path in enumerate(image_paths):
            if is_marked(path):
                marked_indices.append(idx)

        # Calculate gaps: from start (0) to first mark, between marks, and to end
        if marked_indices:
            # First gap: from beginning (0) to first marked image
            if marked_indices[0] > 0:
                gaps.append(marked_indices[0])

            # Middle gaps: between consecutive marked images
            for i in range(1, len(marked_indices)):
                gap = marked_indices[i] - marked_indices[i-1]
                gaps.append(gap)

            # Last gap: from last marked image to the end
            last_gap = len(image_paths) - 1 - marked_indices[-1]
            if last_gap > 0:
                gaps.append(last_gap)

        return gaps, marked_indices

    def update_display():
        """Update the displayed image pair"""
        idx = state['current_idx']
        img1_path = image_paths[idx]
        img2_path = image_paths[idx + 1]

        # Create stitched pair
        stitched = stitch_pair(img1_path, img2_path)
        display_img = get_display_image(stitched)

        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(display_img)
        image_label.config(image=photo)
        image_label.image = photo  # Keep reference

        # Update labels
        img1_name = os.path.basename(img1_path)
        img2_name = os.path.basename(img2_path)
        pair_label.config(text=f"Pair {idx + 1}/{len(image_paths) - 1}: {img1_name} + {img2_name}")

        # Update gaps display with highlighting
        gaps, marked_indices = calculate_gaps()
        if gaps:
            # Find which gap corresponds to the current pair
            current_right_idx = idx + 1  # The second image in current pair
            gap_texts = []
            is_highlighted = []

            for gap_idx, gap in enumerate(gaps):
                # Gap 0: from start (0) to marked_indices[0]
                # Gap 1: from marked_indices[0] to marked_indices[1]
                # Gap N: from marked_indices[N-1] to end
                if gap_idx < len(marked_indices):
                    gap_end_idx = marked_indices[gap_idx]
                else:
                    # This is the last gap beyond all marked indices
                    gap_end_idx = len(image_paths) - 1

                # Highlight only if current right image is the END of this gap
                if gap_end_idx == current_right_idx:
                    gap_texts.append(str(gap))
                    is_highlighted.append(True)
                else:
                    gap_texts.append(str(gap))
                    is_highlighted.append(False)

            # Build display text with highlighting and line wrapping
            GAPS_PER_LINE = 25  # Number of gaps to show per line
            display_parts = ["Gaps: "]
            for i, (gap_text, highlighted) in enumerate(zip(gap_texts, is_highlighted)):
                # Add line break after every GAPS_PER_LINE gaps
                if i > 0 and i % GAPS_PER_LINE == 0:
                    display_parts.append("\n       ")  # Indent continuation lines
                elif i > 0:
                    display_parts.append("  ")

                if highlighted:
                    display_parts.append(f"⟦{gap_text}⟧")  # Use special brackets to show current position
                else:
                    display_parts.append(gap_text)

            # Add total count and sum of gaps on a new line
            gaps_sum = sum(gaps)
            display_parts.append(f"\n\nTotal: {len(gaps)}   |   Sum: {gaps_sum}")

            gaps_label.config(text="".join(display_parts), fg='#ff6666' if any(is_highlighted) else '#ffffff')
        else:
            gaps_label.config(text="Gaps: (none yet)", fg='#ffffff')

        # Update button states
        prev_btn.config(state=tk.NORMAL if idx > 0 else tk.DISABLED)
        next_btn.config(state=tk.NORMAL if idx < len(image_paths) - 2 else tk.DISABLED)

        stitched.close()
        display_img.close()

    def on_set_jump():
        """Set the jump amount from the entry"""
        try:
            amount = int(jump_entry.get())
            state['jump_amount'] = max(1, amount)  # Minimum jump is 1
            jump_entry.selection_clear()  # Clear text selection
            viewer.focus()  # Remove focus from entry
        except ValueError:
            jump_entry.delete(0, tk.END)
            jump_entry.insert(0, str(state['jump_amount']))

    def on_next():
        jump = state['jump_amount']
        max_idx = len(image_paths) - 2
        new_idx = min(state['current_idx'] + jump, max_idx)
        if new_idx != state['current_idx']:
            state['current_idx'] = new_idx
            update_display()

    def on_prev():
        jump = state['jump_amount']
        new_idx = max(state['current_idx'] - jump, 0)
        if new_idx != state['current_idx']:
            state['current_idx'] = new_idx
            update_display()

    def on_delete_left():
        """Delete the LEFT image of the current pair"""
        if len(image_paths) < 3:
            status_label.config(text="Cannot delete - need at least 2 images")
            return

        idx = state['current_idx']
        left_img_path = image_paths[idx]
        filename = os.path.basename(left_img_path)

        try:
            # Delete the file
            os.remove(left_img_path)

            # Remove from image_paths list
            image_paths.pop(idx)

            # Adjust current index if needed
            if state['current_idx'] >= len(image_paths) - 1:
                state['current_idx'] = len(image_paths) - 2

            update_display()
            status_label.config(text=f"Deleted: {filename}")
        except Exception as e:
            status_label.config(text=f"Error deleting: {str(e)}")

    def on_add_blank():
        """Add a blank tile BEFORE the left image of the current pair"""
        idx = state['current_idx']
        left_img_path = image_paths[idx]

        # Get directory and sample image to determine tile size
        base_dir = os.path.dirname(left_img_path)

        # Open first image to get dimensions
        sample_img = Image.open(left_img_path)
        width, height = sample_img.width, sample_img.height
        sample_img.close()

        # Find a unique filename that sorts before all existing files
        # Use underscore prefix which sorts before numbers and letters
        ext = os.path.splitext(left_img_path)[1]
        counter = 1
        while True:
            blank_filename = f"_blank_{counter:03d}{ext}"
            blank_path = os.path.join(base_dir, blank_filename)
            if not os.path.exists(blank_path):
                break
            counter += 1

        # Create blank white image
        try:
            blank_img = Image.new('RGB', (width, height), (255, 255, 255))
            blank_img.save(blank_path)
            blank_img.close()

            # Insert into image_paths list at current position
            image_paths.insert(idx, blank_path)

            # Stay at the same visual position (but now it's idx+1 due to insertion)
            state['current_idx'] = idx

            update_display()
            status_label.config(text=f"Added blank: {blank_filename}")
        except Exception as e:
            status_label.config(text=f"Error adding blank: {str(e)}")

    def on_mark_mismatch():
        """Toggle 'z' suffix on the RIGHT (second) image of the current pair"""
        idx = state['current_idx']
        right_img_path = image_paths[idx + 1]  # Mark the SECOND image

        # Parse filename
        base_dir = os.path.dirname(right_img_path)
        filename = os.path.basename(right_img_path)
        name, ext = os.path.splitext(filename)

        # Toggle 'z' suffix
        if name.endswith('z'):
            # Remove 'z' suffix
            new_name = name[:-1]
            new_filename = f"{new_name}{ext}"
            action = "Unmarked"
        else:
            # Add 'z' suffix
            new_name = f"{name}z"
            new_filename = f"{new_name}{ext}"
            action = "Marked"

        new_path = os.path.join(base_dir, new_filename)

        # Rename file
        try:
            os.rename(right_img_path, new_path)
            # Update the path in our list
            image_paths[idx + 1] = new_path  # Update the second image
            # Refresh display to show new filename
            update_display()
            status_label.config(text=f"{action}: {new_filename}")
        except Exception as e:
            status_label.config(text=f"Error: {str(e)}")

    def stitch_grid(rows, cols, tile_count, open_after=False):
        """
        Stitch images in a grid layout and optionally open the result.

        Args:
            rows: Number of rows
            cols: Number of columns
            tile_count: Number of tiles to use from the beginning
            open_after: If True, open the stitched image with default app

        Returns:
            output_path or None if failed
        """
        if not image_paths:
            status_label.config(text="No images to stitch")
            return None

        # Limit to requested number of tiles
        paths_to_use = image_paths[:tile_count]

        # Load all images
        images = []
        for path in paths_to_use:
            try:
                img = Image.open(path)
                # Force convert palette images to RGB
                if img.mode in ('P', 'PA', 'L', 'LA'):
                    img = img.convert('RGB')
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                images.append(img)
            except Exception as e:
                status_label.config(text=f"Failed to load: {os.path.basename(path)}")
                return None

        if not images:
            status_label.config(text="No valid images loaded")
            return None

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
        first_image_path = Path(paths_to_use[0])
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
            msg = f"Stitched {len(images)} images as {cols}×{rows}"
            if blank_tiles > 0:
                msg += f" ({blank_tiles} blank{'s' if blank_tiles > 1 else ''})"
            status_label.config(text=msg)

            # Close all images
            for img in images:
                img.close()
            result.close()

            # Open the file if requested
            if open_after:
                try:
                    subprocess.Popen(['xdg-open', str(output_path)])
                except Exception as e:
                    status_label.config(text=f"Stitched but failed to open: {str(e)}")

            return output_path

        except Exception as e:
            status_label.config(text=f"Failed to save: {str(e)}")
            for img in images:
                img.close()
            result.close()
            return None

    def on_stitch_grid():
        """Handle stitch button click"""
        try:
            rows = int(row_entry.get())
            cols = int(col_entry.get())
            tile_count = int(tile_count_entry.get())

            if rows <= 0 or cols <= 0:
                status_label.config(text="Rows and columns must be > 0")
                return

            if tile_count <= 0:
                status_label.config(text="Tile count must be > 0")
                return

            if tile_count > len(image_paths):
                status_label.config(text=f"Tile count cannot exceed {len(image_paths)}")
                return

            open_after = open_after_var.get()
            stitch_grid(rows, cols, tile_count, open_after)
        except ValueError:
            status_label.config(text="Please enter valid numbers for all fields")

    def update_multiplication(*args):
        """Update the multiplication display when rows or cols change"""
        try:
            rows_val = row_entry.get().strip()
            cols_val = col_entry.get().strip()
            if rows_val and cols_val:
                rows = int(rows_val)
                cols = int(cols_val)
                result = rows * cols
                mult_label.config(text=f"{cols} × {rows} = {result}")
            else:
                mult_label.config(text="")
        except ValueError:
            mult_label.config(text="")

    # Create viewer window
    viewer = tk.Tk()
    viewer.title("Enlarged Stitch Viewer")

    # Dark mode styling
    viewer.configure(bg='#1e1e1e')

    # Maximize window (Linux-compatible)
    viewer.attributes('-zoomed', True)

    style = ttk.Style()
    style.theme_use('clam')
    style.configure('Dark.TFrame', background='#1e1e1e')
    style.configure('Dark.TLabel', background='#1e1e1e', foreground='#ffffff')
    style.configure('Dark.TButton', background='#2d2d2d', foreground='#ffffff',
                   borderwidth=1, relief='flat')
    style.map('Dark.TButton',
             background=[('active', '#3d3d3d'), ('pressed', '#4d4d4d')])

    # Main frame
    main_frame = ttk.Frame(viewer, padding="10", style='Dark.TFrame')
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Top controls
    control_frame = ttk.Frame(main_frame, style='Dark.TFrame')
    control_frame.pack(pady=(0, 10))

    pair_label = ttk.Label(control_frame, text="", font=("", 12, "bold"), style='Dark.TLabel')
    pair_label.pack()

    # Navigation buttons with jump control
    nav_frame = ttk.Frame(main_frame, style='Dark.TFrame')
    nav_frame.pack(pady=(0, 10))

    prev_btn = ttk.Button(nav_frame, text="← Previous (Left Arrow)", command=on_prev, width=25, style='Dark.TButton')
    prev_btn.pack(side=tk.LEFT, padx=5)

    mark_btn = ttk.Button(nav_frame, text="Toggle Mark (Z)", command=on_mark_mismatch, width=25, style='Dark.TButton')
    mark_btn.pack(side=tk.LEFT, padx=5)

    next_btn = ttk.Button(nav_frame, text="Next (Right Arrow) →", command=on_next, width=25, style='Dark.TButton')
    next_btn.pack(side=tk.LEFT, padx=5)

    # Jump amount control
    jump_control_frame = ttk.Frame(nav_frame, style='Dark.TFrame')
    jump_control_frame.pack(side=tk.LEFT, padx=15)

    jump_label = tk.Label(jump_control_frame, text="Jump:", bg='#1e1e1e', fg='#ffffff', font=("", 10))
    jump_label.pack(side=tk.LEFT, padx=(0, 5))

    jump_entry = tk.Entry(jump_control_frame, width=8, bg='#2d2d2d', fg='#ffffff',
                          insertbackground='#ffffff', relief='flat', font=("", 10))
    jump_entry.insert(0, "1")
    jump_entry.pack(side=tk.LEFT, padx=(0, 5))

    jump_set_btn = ttk.Button(jump_control_frame, text="Set", command=on_set_jump, width=6, style='Dark.TButton')
    jump_set_btn.pack(side=tk.LEFT)

    # Gaps display - use tk.Label instead of ttk for color support
    gaps_label = tk.Label(main_frame, text="Gaps: (none yet)", font=("", 14, "bold"),
                         bg='#1e1e1e', fg='#ffffff')
    gaps_label.pack(pady=(5, 5))

    # Status label
    status_label = ttk.Label(main_frame, text="Press 'Z' to toggle mark  |  'B' to add blank  |  'R' to delete left image", font=("", 10), style='Dark.TLabel')
    status_label.pack(pady=(0, 10))

    # Multiplication result display (above inputs)
    mult_label = tk.Label(main_frame, text="", font=("", 12, "bold"),
                         bg='#1e1e1e', fg='#66b3ff')
    mult_label.pack(pady=(5, 5))

    # Grid stitching controls
    stitch_frame = ttk.Frame(main_frame, style='Dark.TFrame')
    stitch_frame.pack(pady=(10, 10))

    # Columns input
    col_frame = ttk.Frame(stitch_frame, style='Dark.TFrame')
    col_frame.pack(side=tk.LEFT, padx=5)
    ttk.Label(col_frame, text="Cols:", style='Dark.TLabel').pack(side=tk.LEFT, padx=(0, 5))
    col_entry = tk.Entry(col_frame, width=8, bg='#2d2d2d', fg='#ffffff',
                        insertbackground='#ffffff', relief='flat', font=("", 10))
    col_entry.pack(side=tk.LEFT)

    # Rows input
    row_frame = ttk.Frame(stitch_frame, style='Dark.TFrame')
    row_frame.pack(side=tk.LEFT, padx=5)
    ttk.Label(row_frame, text="Rows:", style='Dark.TLabel').pack(side=tk.LEFT, padx=(0, 5))
    row_entry = tk.Entry(row_frame, width=8, bg='#2d2d2d', fg='#ffffff',
                        insertbackground='#ffffff', relief='flat', font=("", 10))
    row_entry.pack(side=tk.LEFT)

    # Use first N tiles input
    tile_count_frame = ttk.Frame(stitch_frame, style='Dark.TFrame')
    tile_count_frame.pack(side=tk.LEFT, padx=5)
    ttk.Label(tile_count_frame, text="Use first:", style='Dark.TLabel').pack(side=tk.LEFT, padx=(0, 5))
    tile_count_entry = tk.Entry(tile_count_frame, width=8, bg='#2d2d2d', fg='#ffffff',
                                insertbackground='#ffffff', relief='flat', font=("", 10))
    tile_count_entry.insert(0, str(len(image_paths)))
    tile_count_entry.pack(side=tk.LEFT)
    ttk.Label(tile_count_frame, text="tiles", style='Dark.TLabel').pack(side=tk.LEFT, padx=(5, 0))

    # Stitch button
    stitch_btn = ttk.Button(stitch_frame, text="Stitch Grid", command=lambda: on_stitch_grid(),
                           width=15, style='Dark.TButton')
    stitch_btn.pack(side=tk.LEFT, padx=5)

    # Open after stitch checkbox
    open_after_var = tk.BooleanVar(value=False)
    open_check = tk.Checkbutton(stitch_frame, text="Open after stitch",
                               variable=open_after_var, bg='#1e1e1e', fg='#ffffff',
                               selectcolor='#2d2d2d', activebackground='#1e1e1e',
                               activeforeground='#ffffff')
    open_check.pack(side=tk.LEFT, padx=5)

    # Image display (centered)
    image_frame = ttk.Frame(main_frame, style='Dark.TFrame')
    image_frame.pack(fill=tk.BOTH, expand=True)

    image_label = ttk.Label(image_frame, anchor='center')
    image_label.place(relx=0.5, rely=0.5, anchor='center')

    # Key bindings
    viewer.bind('<Left>', lambda _: on_prev())
    viewer.bind('<Right>', lambda _: on_next())
    viewer.bind('z', lambda _: on_mark_mismatch())
    viewer.bind('Z', lambda _: on_mark_mismatch())
    viewer.bind('b', lambda _: on_add_blank())
    viewer.bind('B', lambda _: on_add_blank())
    viewer.bind('r', lambda _: on_delete_left())
    viewer.bind('R', lambda _: on_delete_left())
    viewer.bind('<Escape>', lambda _: viewer.destroy())
    jump_entry.bind('<Return>', lambda _: on_set_jump())

    # Bind entry changes to update multiplication
    row_entry.bind('<KeyRelease>', update_multiplication)
    col_entry.bind('<KeyRelease>', update_multiplication)

    # Initial display
    update_display()

    # Center window
    viewer.update_idletasks()
    x = (viewer.winfo_screenwidth() // 2) - (viewer.winfo_width() // 2)
    y = (viewer.winfo_screenheight() // 2) - (viewer.winfo_height() // 2)
    viewer.geometry(f"+{x}+{y}")

    viewer.mainloop()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: view-stitched-enlarged.py <directory_or_files...>")
        sys.exit(1)

    # Collect image files from arguments (can be directories or files)
    image_files = []

    for arg in sys.argv[1:]:
        if os.path.isdir(arg):
            # If directory, find all valid images in it
            for filename in os.listdir(arg):
                filepath = os.path.join(arg, filename)
                if os.path.isfile(filepath) and filename.lower().endswith(VALID_EXTENSIONS):
                    image_files.append(filepath)
        elif os.path.isfile(arg):
            # If file, check if it's valid
            if arg.lower().endswith(VALID_EXTENSIONS):
                image_files.append(arg)

    if not image_files:
        ext_list = ', '.join(VALID_EXTENSIONS)
        show_notification("Error", f"No images found with extensions: {ext_list}", error=True)
        sys.exit(1)

    # Sort the files
    image_files = sorted(image_files, key=sort_key)

    # Launch viewer
    show_enlarged_viewer(image_files)
