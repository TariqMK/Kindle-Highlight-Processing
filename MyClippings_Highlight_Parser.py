"""
Kindle Highlights Processor - All-in-One GUI
A beautiful, dark-mode application for processing Kindle highlights

REQUIREMENTS:
Install the following packages before running:
    pip install customtkinter pillow tkinterdnd2

Or install all at once:
    pip install customtkinter pillow tkinterdnd2
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
import os
import re
import threading
from PIL import Image, ImageDraw, ImageFont
import textwrap
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    TkinterDnD = None
    DND_FILES = None
import json

# ============================================================================
# SCRIPT 1: Parse My Clippings.txt to Individual Files
# ============================================================================

def clean_file_content(file_path):
    """Remove bookmarks from the clippings file"""
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    lines = content.split("\n")
    new_lines = []
    last_bookmark_position = -1

    for i, line in enumerate(lines):
        if ("Your Bookmark" in line):
            new_lines.pop()
            last_bookmark_position = i
        if (last_bookmark_position == -1 or not i - last_bookmark_position < 4):
            new_lines.append(line)

    return "\n".join(new_lines)


def parse_clippings(content):
    """Parse clippings and organize by book"""
    books = {}
    pattern = r"(.*?) \((.*?)\)\n- (Your Highlight on .*? \| location .*?|Your Highlight at location .*?|Your Highlight on page .*?|Highlight on Page .*?)\n\n(.*?)\n=========="
    matches = re.findall(pattern, content, re.DOTALL)
    
    for match in matches:
        book_title = match[0].strip().encode('utf-8').decode('utf-8-sig').strip()
        author = match[1].strip()
        highlight_source = match[2].strip()
        highlight_text = match[3].strip()
        
        page_info = ''
        location_info = ''
        if 'page' in highlight_source.lower():
            page_info = highlight_source.split('|')[0].replace('Your Highlight on ', '').strip()
            location_info = highlight_source.split('|')[1].replace('location', '').strip()
        elif 'location' in highlight_source.lower():
            location_info = highlight_source.split('|')[0].replace('Your Highlight at ', '').strip()
        
        if book_title not in books:
            books[book_title] = []
        books[book_title].append((highlight_text, author, page_info, location_info))
    
    return books


def save_highlights_to_files(books, output_dir='Highlights_by_Book'):
    """Save highlights to individual book files"""
    os.makedirs(output_dir, exist_ok=True)
    results = []
    
    for book_title, highlights in books.items():
        stripped_title = book_title.split(':')[0].strip()
        file_name = re.sub(r'[<>:"/\\|?*]', '', stripped_title) + '.txt'
        file_path = os.path.join(output_dir, file_name)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            for i, (highlight_text, author, page_info, location) in enumerate(highlights, start=1):
                file.write(f"{i}. {highlight_text}\n\t<{book_title}>({author}) Your Highlight on {page_info} | location {location}\n\n")
        
        results.append((stripped_title, len(highlights)))
    
    return results


# ============================================================================
# SCRIPT 2: Simplify Highlights Format
# ============================================================================

def extract_book_info(text):
    """Extract book name and author from text"""
    match = re.search(r'<([^>]*)>\(([^)]*)\)', text)
    if match:
        book_name = match.group(1).split(':')[0].strip()
        author = match.group(2).strip()
        return book_name, author
    return None, None


def format_highlights(text, book_name, author):
    """Format highlights with separators and remove metadata"""
    header = f"{book_name}\n{author}\n\n---\n\n"
    text = re.sub(r'\n{2,}', '\n\n---\n\n', text)
    highlights = re.split(r'\n{2,}', text)
    formatted_highlights = []

    for highlight in highlights:
        if highlight.strip() and '<' in highlight and '>' in highlight:
            clean_highlight = re.sub(
                r'<.*?>\s*\(.*?\)\s*(Your Highlight on page \d+|Highlight on Page \d+ \| Loc\..*|Your Highlight at location \d+-\d+|Your Highlight on page \d+ \| location \d+-\d+).*$',
                '', highlight
            ).strip()
            if clean_highlight:
                formatted_highlights.append(clean_highlight)

    return header + '\n\n---\n\n'.join(formatted_highlights)


def read_file_with_encoding(filename):
    """Read file with various encodings"""
    encodings = ['utf-8', 'utf-8-sig', 'cp1252', 'iso-8859-1']
    for encoding in encodings:
        try:
            with open(filename, 'r', encoding=encoding) as file:
                text = file.read()
            return text.lstrip('\ufeff')
        except UnicodeDecodeError:
            continue
    raise ValueError("Could not read the file with any known encoding.")


def simplify_highlights(input_dir='Highlights_by_Book'):
    """Simplify all highlight files in directory"""
    results = []
    for filename in os.listdir(input_dir):
        if filename.endswith('.txt') and not filename.endswith('-S.txt'):
            filepath = os.path.join(input_dir, filename)
            text = read_file_with_encoding(filepath)
            
            book_name, author = extract_book_info(text)
            if book_name and author:
                formatted_text = format_highlights(text, book_name, author)
                output_filename = os.path.join(input_dir, f'{os.path.splitext(filename)[0]}-S.txt')
                with open(output_filename, 'w', encoding='utf-8') as output_file:
                    output_file.write(formatted_text)
                results.append(book_name)
    
    return results


# ============================================================================
# SCRIPT 3: Generate Quote Images
# ============================================================================

def generate_quote_images(input_dir='Highlights_by_Book', font_path='Files/Fonts/Vollkorn-Regular.ttf'):
    """Generate WebP images from simplified highlights"""
    # Configuration
    line_spacing = 15
    short_quote_threshold = 550
    original_image_width = 1080
    original_image_height = 1080
    larger_image_width = 1080
    larger_image_height = 1350
    side_padding = 20
    bottom_padding = 60
    
    results = []
    txt_files = [f for f in os.listdir(input_dir) if f.endswith('-S.txt')]
    
    for txt_file in txt_files:
        filepath = os.path.join(input_dir, txt_file)
        with open(filepath, 'r', encoding='utf-8') as file:
            text = file.read()
        
        sections = text.split('\n\n---\n\n')
        book_info = sections[0].split('\n')
        book_name = re.sub(r'[^\w\s]', '', book_info[0].strip())
        author = re.sub(r'[^\w\s]', '', book_info[1].strip())
        
        book_folder = os.path.join(input_dir, book_name)
        os.makedirs(book_folder, exist_ok=True)
        
        highlight_pattern = re.compile(r'\d{1,3}\.\s*', re.MULTILINE)
        sections[1:] = [highlight_pattern.sub('', section) for section in sections[1:]]
        
        image_count = 0
        for i, highlight in enumerate(sections[1:]):
            if not highlight.strip():
                continue
                
            highlight = highlight[0].capitalize() + highlight[1:]
            
            if len(highlight) <= short_quote_threshold:
                image_width, image_height = original_image_width, original_image_height
            else:
                image_width, image_height = larger_image_width, larger_image_height
            
            filename = f"Highlight_{i + 1:04}.webp"
            image = Image.new('RGB', (image_width, image_height), color='white')
            draw = ImageDraw.Draw(image)
            
            initial_font_size = 40
            font = ImageFont.truetype(font_path, int(initial_font_size))
            
            wrapped_text = textwrap.fill(highlight, width=43)
            wrapped_text_lines = wrapped_text.split('\n')
            wrapped_text_lines = [line.strip() for line in wrapped_text_lines if line.strip()]
            wrapped_text = '\n'.join(wrapped_text_lines)
            
            bbox = draw.textbbox((0, 0), wrapped_text, font=font, spacing=line_spacing)
            text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            
            text_x = (image_width - text_width) / 2
            text_y = (image_height - text_height) / 2
            
            draw.multiline_text((text_x, text_y), wrapped_text, fill='black', font=font, align="left", spacing=line_spacing)
            
            info_font = ImageFont.truetype(font_path, 27)
            info_text = f'{book_name} | {author}'.strip()
            info_text = re.sub(r'[^\w\s|]', '', info_text)
            
            info_size = draw.textbbox((0, 0), info_text, font=info_font)
            info_width, info_height = info_size[2] - info_size[0], info_size[3] - info_size[1]
            
            info_x = (image_width - info_width) / 2
            info_y = image_height - side_padding - info_height - bottom_padding
            
            draw.text((info_x, info_y), info_text, fill='black', font=info_font)
            
            image.save(os.path.join(book_folder, filename), format='WEBP', quality=85)
            image_count += 1
        
        results.append((book_name, image_count))
    
    return results


# ============================================================================
# GUI Application
# ============================================================================

class KindleHighlightsGUI:
    def __init__(self):
        # Set appearance mode and color theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create main window with drag-drop support if available
        if TkinterDnD:
            # Create TkinterDnD root first
            root = TkinterDnD.Tk()
            root.withdraw()  # Hide the Tk window
            
            # Create CTk window as Toplevel
            self.root = ctk.CTkToplevel(root)
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self._tk_root = root
        else:
            self.root = ctk.CTk()
            self._tk_root = None
        
        self.root.title("Kindle Highlights Processor")
        self.root.geometry("900x950")  # Reduced back to 950 since we now have scrolling
        
        # Load saved preferences
        self.config_file = os.path.join(os.path.expanduser("~"), ".kindle_highlights_config.json")
        self.load_preferences()
        
        # Processing control
        self.is_processing = False
        self.cancel_requested = False
        
        # Configure grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Create main scrollable frame that contains everything
        self.main_scroll_frame = ctk.CTkScrollableFrame(
            self.root,
            fg_color="transparent"
        )
        self.main_scroll_frame.grid(row=0, column=0, sticky="nsew")
        self.main_scroll_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.main_scroll_frame,
            text="Kindle Highlights Processor",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=40, pady=(40, 10), sticky="w")
        
        # Subtitle
        self.subtitle_label = ctk.CTkLabel(
            self.main_scroll_frame,
            text="Transform your Kindle highlights into beautiful quote images",
            font=ctk.CTkFont(size=15),
            text_color=("gray70", "gray50")
        )
        self.subtitle_label.grid(row=1, column=0, padx=40, pady=(0, 20), sticky="w")
        
        # File selection frame
        self.file_frame = ctk.CTkFrame(self.main_scroll_frame, corner_radius=15)
        self.file_frame.grid(row=2, column=0, padx=40, pady=(0, 20), sticky="ew")
        self.file_frame.grid_columnconfigure(1, weight=1)
        
        file_title = ctk.CTkLabel(
            self.file_frame,
            text="My Clippings File",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        file_title.grid(row=0, column=0, columnspan=3, padx=25, pady=(20, 15), sticky="w")
        
        # File path display
        self.file_path_var = tk.StringVar(value="No file selected - Click Browse or drag & drop file here")
        self.file_path_entry = ctk.CTkEntry(
            self.file_frame,
            textvariable=self.file_path_var,
            font=ctk.CTkFont(size=13),
            height=45,
            state="readonly",
            fg_color=("gray85", "gray20")
        )
        self.file_path_entry.grid(row=1, column=0, columnspan=2, padx=25, pady=(0, 20), sticky="ew")
        
        # Enable drag and drop if available
        if TkinterDnD and DND_FILES:
            self.file_path_entry.drop_target_register(DND_FILES)
            self.file_path_entry.dnd_bind('<<Drop>>', self.drop_file)
        
        # Browse button
        self.browse_button = ctk.CTkButton(
            self.file_frame,
            text="📁 Browse",
            command=self.browse_file,
            font=ctk.CTkFont(size=14, weight="bold"),
            width=120,
            height=45,
            corner_radius=10,
            fg_color=("#3b8ed0", "#1f6aa5"),
            hover_color=("#36719f", "#144870")
        )
        self.browse_button.grid(row=1, column=2, padx=(10, 25), pady=(0, 20), sticky="e")
        
        # Book selection frame (initially hidden)
        self.book_selection_frame = ctk.CTkFrame(self.main_scroll_frame, corner_radius=15)
        self.book_selection_frame.grid(row=3, column=0, padx=40, pady=(0, 20), sticky="ew")
        self.book_selection_frame.grid_columnconfigure(0, weight=1)
        self.book_selection_frame.grid_remove()  # Hidden by default
        
        book_selection_title = ctk.CTkLabel(
            self.book_selection_frame,
            text="Select Books to Process",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        book_selection_title.grid(row=0, column=0, padx=25, pady=(20, 10), sticky="w")
        
        # Buttons for select all/none
        self.book_buttons_frame = ctk.CTkFrame(self.book_selection_frame, fg_color="transparent")
        self.book_buttons_frame.grid(row=1, column=0, padx=25, pady=(0, 10), sticky="w")
        
        self.select_all_button = ctk.CTkButton(
            self.book_buttons_frame,
            text="Select All",
            command=self.select_all_books,
            font=ctk.CTkFont(size=12),
            width=100,
            height=30,
            corner_radius=8,
            fg_color=("#3b8ed0", "#1f6aa5"),
            hover_color=("#36719f", "#144870")
        )
        self.select_all_button.grid(row=0, column=0, padx=(0, 5))
        
        self.select_none_button = ctk.CTkButton(
            self.book_buttons_frame,
            text="Select None",
            command=self.select_none_books,
            font=ctk.CTkFont(size=12),
            width=100,
            height=30,
            corner_radius=8,
            fg_color=("gray60", "gray30"),
            hover_color=("gray50", "gray25")
        )
        self.select_none_button.grid(row=0, column=1, padx=5)
        
        # Scrollable frame for book checkboxes
        self.books_scroll_frame = ctk.CTkScrollableFrame(
            self.book_selection_frame,
            height=200,
            corner_radius=10,
            fg_color=("gray90", "gray17")
        )
        self.books_scroll_frame.grid(row=2, column=0, padx=25, pady=(0, 20), sticky="ew")
        self.books_scroll_frame.grid_columnconfigure(0, weight=1)
        
        # Dictionary to store book checkboxes
        self.book_vars = {}
        self.book_data = {}  # Store full book data
        
        # Output directory frame
        self.output_frame = ctk.CTkFrame(self.main_scroll_frame, corner_radius=15)
        self.output_frame.grid(row=4, column=0, padx=40, pady=(0, 20), sticky="ew")
        self.output_frame.grid_columnconfigure(1, weight=1)
        
        output_title = ctk.CTkLabel(
            self.output_frame,
            text="Output Directory",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        output_title.grid(row=0, column=0, columnspan=3, padx=25, pady=(20, 15), sticky="w")
        
        # Output directory display
        self.output_path_var = tk.StringVar(value=self.last_output_dir)
        self.output_path_entry = ctk.CTkEntry(
            self.output_frame,
            textvariable=self.output_path_var,
            font=ctk.CTkFont(size=13),
            height=45,
            state="readonly",
            fg_color=("gray85", "gray20")
        )
        self.output_path_entry.grid(row=1, column=0, columnspan=2, padx=25, pady=(0, 20), sticky="ew")
        
        # Browse output button
        self.output_browse_button = ctk.CTkButton(
            self.output_frame,
            text="📂 Browse",
            command=self.browse_output_dir,
            font=ctk.CTkFont(size=14, weight="bold"),
            width=120,
            height=45,
            corner_radius=10,
            fg_color=("#3b8ed0", "#1f6aa5"),
            hover_color=("#36719f", "#144870")
        )
        self.output_browse_button.grid(row=1, column=2, padx=(10, 25), pady=(0, 20), sticky="e")
        
        # Processing options frame
        self.options_frame = ctk.CTkFrame(self.main_scroll_frame, corner_radius=15)
        self.options_frame.grid(row=5, column=0, padx=40, pady=(0, 20), sticky="ew")
        
        options_title = ctk.CTkLabel(
            self.options_frame,
            text="Select Processing Steps",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        options_title.grid(row=0, column=0, padx=25, pady=(20, 15), sticky="w")
        
        # Checkboxes for each script
        self.script1_var = tk.BooleanVar(value=True)
        self.script1_check = ctk.CTkCheckBox(
            self.options_frame,
            text="Parse My Clippings.txt → Individual book files",
            variable=self.script1_var,
            font=ctk.CTkFont(size=15),
            checkbox_width=26,
            checkbox_height=26
        )
        self.script1_check.grid(row=1, column=0, padx=25, pady=10, sticky="w")
        
        self.script2_var = tk.BooleanVar(value=True)
        self.script2_check = ctk.CTkCheckBox(
            self.options_frame,
            text="Simplify highlights (remove metadata)",
            variable=self.script2_var,
            font=ctk.CTkFont(size=15),
            checkbox_width=26,
            checkbox_height=26
        )
        self.script2_check.grid(row=2, column=0, padx=25, pady=10, sticky="w")
        
        self.script3_var = tk.BooleanVar(value=True)
        self.script3_check = ctk.CTkCheckBox(
            self.options_frame,
            text="Generate quote images (WebP, quality 85)",
            variable=self.script3_var,
            font=ctk.CTkFont(size=15),
            checkbox_width=26,
            checkbox_height=26
        )
        self.script3_check.grid(row=3, column=0, padx=25, pady=(10, 20), sticky="w")
        
        # Buttons frame
        self.buttons_frame = ctk.CTkFrame(self.main_scroll_frame, fg_color="transparent")
        self.buttons_frame.grid(row=6, column=0, padx=40, pady=(0, 20), sticky="ew")
        self.buttons_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Process button
        self.process_button = ctk.CTkButton(
            self.buttons_frame,
            text="▶ Start Processing",
            command=self.start_processing,
            font=ctk.CTkFont(size=18, weight="bold"),
            height=55,
            corner_radius=12,
            fg_color=("#2fa572", "#1a7a4a"),
            hover_color=("#26885f", "#156038")
        )
        self.process_button.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="ew")
        
        # Cancel button
        self.cancel_button = ctk.CTkButton(
            self.buttons_frame,
            text="⏹ Cancel",
            command=self.cancel_processing,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=55,
            corner_radius=12,
            fg_color=("#d32f2f", "#b71c1c"),
            hover_color=("#c62828", "#a71a1a"),
            state="disabled"
        )
        self.cancel_button.grid(row=0, column=1, padx=(10, 0), pady=0, sticky="ew")
        
        # Console/Log frame
        self.log_frame = ctk.CTkFrame(self.main_scroll_frame, corner_radius=15)
        self.log_frame.grid(row=7, column=0, padx=40, pady=(0, 10), sticky="ew")
        self.log_frame.grid_rowconfigure(1, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)
        
        log_title = ctk.CTkLabel(
            self.log_frame,
            text="Processing Log",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        log_title.grid(row=0, column=0, padx=20, pady=(20, 8), sticky="w")
        
        # Text widget for log output with fixed height
        self.log_text = ctk.CTkTextbox(
            self.log_frame,
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=13),
            corner_radius=10,
            height=300  # Fixed height so it doesn't expand indefinitely
        )
        self.log_text.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        # Clear log button (below log frame)
        self.clear_button = ctk.CTkButton(
            self.main_scroll_frame,
            text="Clear Log",
            command=self.clear_log,
            font=ctk.CTkFont(size=14),
            height=40,
            corner_radius=10,
            fg_color=("gray55", "gray25"),
            hover_color=("gray45", "gray20")
        )
        self.clear_button.grid(row=8, column=0, padx=40, pady=(0, 40), sticky="ew")
        
        # Initial message
        self.log("┌─────────────────────────────────────────────────────────────┐")
        self.log("│  Welcome to Kindle Highlights Processor!                   │")
        self.log("└─────────────────────────────────────────────────────────────┘\n")
        self.log("📋 Instructions:")
        self.log("  1. Select 'My Clippings.txt' (Browse or drag & drop)")
        self.log("  2. Choose output directory (remembers last selection)")
        self.log("  3. Ensure 'Files/Fonts/Vollkorn-Regular.ttf' exists (for Step 3)")
        self.log("  4. Select processing steps and click 'Start Processing'\n")
        if not TkinterDnD:
            self.log("⚠️  Drag & drop not available (tkinterdnd2 not installed)")
            self.log("   Install with: pip install tkinterdnd2\n")
        self.log("Ready to process your highlights! ✨\n")
        
    def load_preferences(self):
        """Load saved preferences from config file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.last_output_dir = config.get('last_output_dir', os.getcwd())
            else:
                self.last_output_dir = os.getcwd()
        except:
            self.last_output_dir = os.getcwd()
    
    def save_preferences(self):
        """Save preferences to config file"""
        try:
            config = {'last_output_dir': self.output_path_var.get()}
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except:
            pass
    
    def browse_output_dir(self):
        """Open directory browser to select output location"""
        directory = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=self.output_path_var.get()
        )
        if directory:
            self.output_path_var.set(directory)
            self.save_preferences()
            self.log(f"📂 Output directory: {directory}")
    
    def drop_file(self, event):
        """Handle drag and drop file"""
        # Get the dropped file path (handle both {file} format and plain path)
        file_path = event.data
        # Remove curly braces if present
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
        
        file_path = file_path.strip()
        
        if os.path.isfile(file_path) and file_path.lower().endswith('.txt'):
            self.file_path_var.set(file_path)
            self.log(f"📁 File dropped: {os.path.basename(file_path)}")
            self.parse_and_show_books(file_path)
        else:
            messagebox.showerror("Invalid File", "Please drop a valid .txt file")
        
    def cancel_processing(self):
        """Cancel the current processing operation"""
        if self.is_processing:
            self.cancel_requested = True
            self.log("\n⚠️  Cancellation requested... stopping after current operation")
        
    def browse_file(self):
        """Open file browser to select My Clippings.txt"""
        filename = filedialog.askopenfilename(
            title="Select My Clippings.txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialdir=os.path.expanduser("~")
        )
        if filename:
            self.file_path_var.set(filename)
            self.log(f"📁 File selected: {os.path.basename(filename)}")
            self.parse_and_show_books(filename)
    
    def parse_and_show_books(self, filepath):
        """Parse the clippings file and display book selection"""
        try:
            self.log("📖 Parsing books from file...")
            content = clean_file_content(filepath)
            books = parse_clippings(content)
            
            # Clear existing checkboxes
            for widget in self.books_scroll_frame.winfo_children():
                widget.destroy()
            self.book_vars.clear()
            self.book_data = books
            
            # Create checkboxes for each book
            for i, (book_title, highlights) in enumerate(books.items()):
                var = tk.BooleanVar(value=True)  # Default to selected
                self.book_vars[book_title] = var
                
                # Create checkbox with book title and highlight count
                checkbox = ctk.CTkCheckBox(
                    self.books_scroll_frame,
                    text=f"{book_title} ({len(highlights)} highlights)",
                    variable=var,
                    font=ctk.CTkFont(size=13),
                    checkbox_width=22,
                    checkbox_height=22
                )
                checkbox.grid(row=i, column=0, padx=15, pady=5, sticky="w")
            
            # Show the book selection frame
            self.book_selection_frame.grid()
            
            self.log(f"✓ Found {len(books)} books. Select which ones to process.\n")
            
        except Exception as e:
            self.log(f"✗ Error parsing books: {str(e)}")
            messagebox.showerror("Parse Error", f"Could not parse books:\n{str(e)}")
    
    def select_all_books(self):
        """Select all books"""
        for var in self.book_vars.values():
            var.set(True)
        self.log("✓ All books selected")
    
    def select_none_books(self):
        """Deselect all books"""
        for var in self.book_vars.values():
            var.set(False)
        self.log("○ All books deselected")
        
    def log(self, message):
        """Add message to log"""
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.root.update_idletasks()
        
    def clear_log(self):
        """Clear the log"""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        
    def validate_prerequisites(self):
        """Check if required files exist"""
        if self.script1_var.get():
            clippings_path = self.file_path_var.get()
            if clippings_path == "No file selected - Click Browse or drag & drop file here" or not clippings_path:
                messagebox.showerror(
                    "Missing File", 
                    "❌ No file selected!\n\nPlease browse or drag & drop your 'My Clippings.txt' file."
                )
                return False
            if not os.path.exists(clippings_path):
                messagebox.showerror(
                    "File Not Found", 
                    f"❌ Selected file not found:\n\n{clippings_path}"
                )
                return False
            
            # Check if any books are selected
            if not self.book_data:
                messagebox.showerror(
                    "No Books Parsed",
                    "❌ Please select a My Clippings.txt file first to parse books."
                )
                return False
            
            selected_count = sum(1 for var in self.book_vars.values() if var.get())
            if selected_count == 0:
                messagebox.showwarning(
                    "No Books Selected",
                    "⚠️ Please select at least one book to process."
                )
                return False
        
        # Check output directory
        output_dir = self.output_path_var.get()
        if not output_dir or not os.path.exists(output_dir):
            messagebox.showerror(
                "Invalid Output Directory",
                "❌ Please select a valid output directory!"
            )
            return False
        
        if self.script2_var.get() or self.script3_var.get():
            highlights_dir = os.path.join(output_dir, "Highlights_by_Book")
            if not os.path.exists(highlights_dir):
                if not self.script1_var.get():
                    messagebox.showerror(
                        "Missing Folder", 
                        "❌ Highlights_by_Book folder not found!\n\nPlease run Step 1 first or enable it."
                    )
                    return False
        
        if self.script3_var.get():
            script_dir = os.path.dirname(os.path.abspath(__file__)) if os.path.dirname(os.path.abspath(__file__)) else '.'
            font_path = os.path.join(script_dir, "Files", "Fonts", "Vollkorn-Regular.ttf")
            if not os.path.exists(font_path):
                messagebox.showerror(
                    "Missing Font", 
                    f"❌ Font file not found!\n\nExpected location:\n{font_path}\n\nPlease ensure the font file exists."
                )
                return False
        
        return True
        
    def start_processing(self):
        """Start the processing in a separate thread"""
        if not (self.script1_var.get() or self.script2_var.get() or self.script3_var.get()):
            messagebox.showwarning("No Steps Selected", "⚠️ Please select at least one processing step!")
            return
        
        if not self.validate_prerequisites():
            return
        
        self.is_processing = True
        self.cancel_requested = False
        self.process_button.configure(state="disabled", text="⏳ Processing...")
        self.cancel_button.configure(state="normal")
        
        thread = threading.Thread(target=self.run_processing)
        thread.daemon = True
        thread.start()
        
    def run_processing(self):
        """Execute selected processing steps"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__)) if os.path.dirname(os.path.abspath(__file__)) else '.'
            output_base = self.output_path_var.get()
            
            # Script 1: Parse My Clippings
            if self.script1_var.get():
                if self.cancel_requested:
                    self.log("\n❌ Processing cancelled by user")
                    return
                    
                self.log("\n" + "═" * 63)
                self.log("STEP 1: Parsing My Clippings.txt")
                self.log("═" * 63)
                
                try:
                    clippings_path = self.file_path_var.get()
                    self.log(f"Reading: {os.path.basename(clippings_path)}")
                    
                    # Get selected books
                    selected_books = {title: data for title, data in self.book_data.items() 
                                     if self.book_vars.get(title, tk.BooleanVar(value=False)).get()}
                    
                    if not selected_books:
                        self.log("\n⚠️  No books selected! Aborting.")
                        messagebox.showwarning("No Books Selected", "Please select at least one book to process.")
                        return
                    
                    self.log(f"Processing {len(selected_books)} of {len(self.book_data)} books...")
                    
                    # Save to Highlights_by_Book in output directory
                    output_dir = os.path.join(output_base, "Highlights_by_Book")
                    results = save_highlights_to_files(selected_books, output_dir)
                    
                    self.log(f"\n✓ Successfully parsed {len(results)} books:")
                    for title, count in results:
                        if self.cancel_requested:
                            self.log("\n❌ Processing cancelled by user")
                            return
                        self.log(f"  • {title}: {count} highlights")
                    
                    self.log(f"\n✓ Step 1 completed! Files saved to: {output_dir}")
                except Exception as e:
                    self.log(f"\n✗ Error in Step 1: {str(e)}")
                    raise
            
            # Script 2: Simplify highlights
            if self.script2_var.get():
                if self.cancel_requested:
                    self.log("\n❌ Processing cancelled by user")
                    return
                    
                self.log("\n" + "═" * 63)
                self.log("STEP 2: Simplifying Highlights")
                self.log("═" * 63)
                
                try:
                    input_dir = os.path.join(output_base, "Highlights_by_Book")
                    
                    # Process files one by one with cancellation checks
                    for filename in os.listdir(input_dir):
                        if self.cancel_requested:
                            self.log("\n❌ Processing cancelled by user")
                            return
                            
                        if filename.endswith('.txt') and not filename.endswith('-S.txt'):
                            filepath = os.path.join(input_dir, filename)
                            text = read_file_with_encoding(filepath)
                            
                            book_name, author = extract_book_info(text)
                            if book_name and author:
                                formatted_text = format_highlights(text, book_name, author)
                                output_filename = os.path.join(input_dir, f'{os.path.splitext(filename)[0]}-S.txt')
                                with open(output_filename, 'w', encoding='utf-8') as output_file:
                                    output_file.write(formatted_text)
                                self.log(f"  ✓ Simplified: {book_name}")
                    
                    self.log(f"\n✓ Step 2 completed! Simplified files saved with '-S' suffix")
                except Exception as e:
                    self.log(f"\n✗ Error in Step 2: {str(e)}")
                    raise
            
            # Script 3: Generate images
            if self.script3_var.get():
                if self.cancel_requested:
                    self.log("\n❌ Processing cancelled by user")
                    return
                    
                self.log("\n" + "═" * 63)
                self.log("STEP 3: Generating Quote Images")
                self.log("═" * 63)
                
                try:
                    font_path = os.path.join(script_dir, "Files", "Fonts", "Vollkorn-Regular.ttf")
                    input_dir = os.path.join(output_base, "Highlights_by_Book")
                    
                    # Configuration
                    line_spacing = 15
                    short_quote_threshold = 550
                    original_image_width = 1080
                    original_image_height = 1080
                    larger_image_width = 1080
                    larger_image_height = 1350
                    side_padding = 20
                    bottom_padding = 60
                    
                    txt_files = [f for f in os.listdir(input_dir) if f.endswith('-S.txt')]
                    
                    for txt_file in txt_files:
                        if self.cancel_requested:
                            self.log("\n❌ Processing cancelled by user")
                            return
                            
                        filepath = os.path.join(input_dir, txt_file)
                        with open(filepath, 'r', encoding='utf-8') as file:
                            text = file.read()
                        
                        sections = text.split('\n\n---\n\n')
                        book_info = sections[0].split('\n')
                        book_name = re.sub(r'[^\w\s]', '', book_info[0].strip())
                        author = re.sub(r'[^\w\s]', '', book_info[1].strip())
                        
                        book_folder = os.path.join(input_dir, book_name)
                        os.makedirs(book_folder, exist_ok=True)
                        
                        highlight_pattern = re.compile(r'\d{1,3}\.\s*', re.MULTILINE)
                        sections[1:] = [highlight_pattern.sub('', section) for section in sections[1:]]
                        
                        image_count = 0
                        for i, highlight in enumerate(sections[1:]):
                            if self.cancel_requested:
                                self.log(f"  ⚠️  Cancelled during {book_name} (created {image_count} images)")
                                return
                                
                            if not highlight.strip():
                                continue
                                
                            highlight = highlight[0].capitalize() + highlight[1:]
                            
                            if len(highlight) <= short_quote_threshold:
                                image_width, image_height = original_image_width, original_image_height
                            else:
                                image_width, image_height = larger_image_width, larger_image_height
                            
                            filename = f"Highlight_{i + 1:04}.webp"
                            image = Image.new('RGB', (image_width, image_height), color='white')
                            draw = ImageDraw.Draw(image)
                            
                            initial_font_size = 40
                            font = ImageFont.truetype(font_path, int(initial_font_size))
                            
                            wrapped_text = textwrap.fill(highlight, width=43)
                            wrapped_text_lines = wrapped_text.split('\n')
                            wrapped_text_lines = [line.strip() for line in wrapped_text_lines if line.strip()]
                            wrapped_text = '\n'.join(wrapped_text_lines)
                            
                            bbox = draw.textbbox((0, 0), wrapped_text, font=font, spacing=line_spacing)
                            text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
                            
                            text_x = (image_width - text_width) / 2
                            text_y = (image_height - text_height) / 2
                            
                            draw.multiline_text((text_x, text_y), wrapped_text, fill='black', font=font, align="left", spacing=line_spacing)
                            
                            info_font = ImageFont.truetype(font_path, 27)
                            info_text = f'{book_name} | {author}'.strip()
                            info_text = re.sub(r'[^\w\s|]', '', info_text)
                            
                            info_size = draw.textbbox((0, 0), info_text, font=info_font)
                            info_width, info_height = info_size[2] - info_size[0], info_size[3] - info_size[1]
                            
                            info_x = (image_width - info_width) / 2
                            info_y = image_height - side_padding - info_height - bottom_padding
                            
                            draw.text((info_x, info_y), info_text, fill='black', font=info_font)
                            
                            image.save(os.path.join(book_folder, filename), format='WEBP', quality=85)
                            image_count += 1
                        
                        self.log(f"  ✓ {book_name}: {image_count} images created")
                    
                    self.log(f"\n✓ Step 3 completed! Images saved as WebP (quality: 85)")
                except Exception as e:
                    self.log(f"\n✗ Error in Step 3: {str(e)}")
                    raise
            
            if not self.cancel_requested:
                self.log("\n" + "═" * 63)
                self.log("🎉 ALL PROCESSING COMPLETED SUCCESSFULLY!")
                self.log("═" * 63)
                self.log(f"\nAll files are in: {os.path.join(output_base, 'Highlights_by_Book')}")
                
                self.root.after(0, lambda: messagebox.showinfo(
                    "Success! 🎉", 
                    f"Processing completed successfully!\n\nCheck the output folder:\n{output_base}"
                ))
            
        except Exception as e:
            self.log(f"\n\n❌ CRITICAL ERROR: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror(
                "Error", 
                f"An error occurred during processing:\n\n{str(e)}\n\nCheck the log for details."
            ))
        
        finally:
            self.is_processing = False
            self.cancel_requested = False
            self.root.after(0, lambda: self.process_button.configure(
                state="normal",
                text="▶ Start Processing"
            ))
            self.root.after(0, lambda: self.cancel_button.configure(state="disabled"))
    
    def on_closing(self):
        """Handle window closing"""
        if self._tk_root:
            self._tk_root.destroy()
        self.root.destroy()
    
    def run(self):
        """Start the GUI"""
        if self._tk_root:
            self._tk_root.mainloop()
        else:
            self.root.mainloop()


if __name__ == "__main__":
    app = KindleHighlightsGUI()
    app.run()
