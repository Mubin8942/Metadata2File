import os
import sys
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import threading
import time
from datetime import datetime

# GUI imports
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

# File processing imports
from PIL import Image
from PIL.ExifTags import TAGS
import PyPDF2
import docx
from pptx import Presentation
import cv2
import mutagen
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis

class FileLogger:
    """Dedicated logger for file type detection and processing"""
    
    def __init__(self, log_directory: str = None):
        if log_directory is None:
            # Use the directory where the main script is located
            log_directory = os.path.dirname(os.path.abspath(__file__))
        
        self.log_directory = log_directory
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory if it doesn't exist
        os.makedirs(self.log_directory, exist_ok=True)
        
        # Create timestamp for log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Main log file for all operations
        self.main_log_file = os.path.join(self.log_directory, f"file_organizer_{timestamp}.log")
        
        # Specific log file for file type detection
        self.detection_log_file = os.path.join(self.log_directory, f"file_detection_{timestamp}.log")
        
        # Setup main logger
        self.main_logger = logging.getLogger('FileOrganizer')
        self.main_logger.setLevel(logging.INFO)
        
        # Setup file type detection logger
        self.detection_logger = logging.getLogger('FileTypeDetection')
        self.detection_logger.setLevel(logging.INFO)
        
        # Create formatters
        main_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        detection_formatter = logging.Formatter(
            '%(asctime)s - FILE: %(filename)s - DETECTED: %(category)s/%(format_type)s - METHOD: %(method)s - SIZE: %(size)s bytes',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Create and configure main file handler
        main_handler = logging.FileHandler(self.main_log_file, encoding='utf-8')
        main_handler.setLevel(logging.INFO)
        main_handler.setFormatter(main_formatter)
        
        # Create and configure detection file handler
        detection_handler = logging.FileHandler(self.detection_log_file, encoding='utf-8')
        detection_handler.setLevel(logging.INFO)
        detection_handler.setFormatter(detection_formatter)
        
        # Add handlers to loggers
        self.main_logger.addHandler(main_handler)
        self.detection_logger.addHandler(detection_handler)
        
        # Prevent duplicate logs
        self.main_logger.propagate = False
        self.detection_logger.propagate = False
    
    def log_main(self, level: str, message: str):
        """Log main application events"""
        if level.upper() == 'INFO':
            self.main_logger.info(message)
        elif level.upper() == 'WARNING':
            self.main_logger.warning(message)
        elif level.upper() == 'ERROR':
            self.main_logger.error(message)
        elif level.upper() == 'DEBUG':
            self.main_logger.debug(message)
    
    def log_file_detection(self, filename: str, file_path: str, category: str, 
                          format_type: str, detection_method: str, file_size: int):
        """Log file type detection details"""
        # Create a custom log record with additional fields
        record = logging.LogRecord(
            name='FileTypeDetection',
            level=logging.INFO,
            pathname=file_path,
            lineno=0,
            msg='',
            args=(),
            exc_info=None
        )
        
        # Add custom attributes
        record.filename = filename
        record.category = category
        record.format_type = format_type
        record.method = detection_method
        record.size = file_size
        
        # Log the record
        for handler in self.detection_logger.handlers:
            handler.emit(record)
    
    def create_summary_log(self, results: Dict):
        """Create a summary log file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = os.path.join(self.log_directory, f"processing_summary_{timestamp}.log")
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("FILE ORGANIZER PROCESSING SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Processing completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"STATISTICS:\n")
            f.write(f"Total files found: {results['total_files']}\n")
            f.write(f"Successfully processed: {results['processed_files']}\n")
            f.write(f"Errors encountered: {len(results['errors'])}\n\n")
            
            f.write("FILES BY CATEGORY:\n")
            for category, count in results['categories'].items():
                f.write(f"  {category}: {count} files\n")
            
            if results['errors']:
                f.write(f"\nERRORS:\n")
                for error in results['errors']:
                    f.write(f"  File: {error['file_path']}\n")
                    f.write(f"  Error: {error['error']}\n")
                    f.write(f"  Time: {error['timestamp']}\n\n")


class FileProcessor:
    """Professional file processor that organizes files by type"""
    
    SUPPORTED_FORMATS = {
        'Images': ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif', '.webp', '.heic'],
        'Documents': ['.pdf', '.docx', '.doc', '.txt', '.pptx', '.ppt'],
        'Videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'],
        'Audio': ['.mp3', '.flac', '.wav', '.ogg', '.m4a', '.aac'],
        'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz'],
        'Executables': ['.exe', '.msi', '.dmg', '.deb', '.rpm']
    }
    
    def __init__(self, logger: FileLogger = None):
        self.processed_files = []
        self.errors = []
        self.file_stats = {}
        self.logger = logger
    
    def detect_file_type(self, file_path: str) -> Tuple[str, str, str]:
        """Detect file type by reading file signature/magic bytes"""
        filename = os.path.basename(file_path)
        file_size = 0
        detection_method = "unknown"
        
        try:
            file_size = os.path.getsize(file_path)
            
            with open(file_path, 'rb') as f:
                header = f.read(32)
            
            # File signatures (magic bytes)
            signatures = {
                b'\xFF\xD8\xFF': ('Images', 'jpeg'),
                b'\x89PNG\r\n\x1a\n': ('Images', 'png'),
                b'GIF87a': ('Images', 'gif'),
                b'GIF89a': ('Images', 'gif'),
                b'BM': ('Images', 'bmp'),
                b'ftypheic': ('Images', 'heic'),  # HEIC magic bytes
                b'ftypheix': ('Images', 'heic'),  # HEIC variant
                b'ftypmif1': ('Images', 'heic'),  # HEIC variant
                b'ftypmsf1': ('Images', 'heic'),  # HEIC variant
                b'RIFF': ('Videos', 'webp'),  # Could also be WAV
                b'\x00\x00\x00\x18ftypmp4': ('Videos', 'mp4'),
                b'\x00\x00\x00\x20ftypM4V': ('Videos', 'mp4'),
                b'%PDF': ('Documents', 'pdf'),
                b'PK\x03\x04': ('Documents', 'office'),  # ZIP-based (docx, pptx)
                b'ID3': ('Audio', 'mp3'),
                b'\xFF\xFB': ('Audio', 'mp3'),
                b'\xFF\xF3': ('Audio', 'mp3'),
                b'fLaC': ('Audio', 'flac'),
                b'OggS': ('Audio', 'ogg'),
                b'PK': ('Archives', 'zip'),
                b'Rar!': ('Archives', 'rar'),
                b'7z\xBC\xAF\'27\x1C': ('Archives', '7z'),
                b'MZ': ('Executables', 'exe'),
            }
            
            # Check file signatures first
            for sig, (category, format_type) in signatures.items():
                if header.startswith(sig):
                    detection_method = "magic_bytes"
                    if self.logger:
                        self.logger.log_file_detection(
                            filename, file_path, category, format_type, 
                            detection_method, file_size
                        )
                    return category, format_type, detection_method
            
            # Check by file extension as fallback
            ext = Path(file_path).suffix.lower()
            for category, extensions in self.SUPPORTED_FORMATS.items():
                if ext in extensions:
                    detection_method = "file_extension"
                    format_type = ext[1:]  # Remove the dot
                    if self.logger:
                        self.logger.log_file_detection(
                            filename, file_path, category, format_type, 
                            detection_method, file_size
                        )
                    return category, format_type, detection_method
            
            # Unknown file type
            detection_method = "unknown"
            if self.logger:
                self.logger.log_file_detection(
                    filename, file_path, 'Other', 'unknown', 
                    detection_method, file_size
                )
            return 'Other', 'unknown', detection_method
            
        except Exception as e:
            detection_method = "error"
            if self.logger:
                self.logger.log_main('ERROR', f"Error detecting file type for {filename}: {str(e)}")
                self.logger.log_file_detection(
                    filename, file_path, 'Error', str(e), 
                    detection_method, file_size
                )
            return 'Error', str(e), detection_method
    
    def get_image_info(self, file_path: str) -> str:
        """Get basic image information"""
        try:
            with Image.open(file_path) as img:
                info = f"{img.size[0]}x{img.size[1]}_{img.format}"
                if self.logger:
                    self.logger.log_main('INFO', f"Image info extracted: {os.path.basename(file_path)} - {info}")
                return info
        except Exception as e:
            if self.logger:
                self.logger.log_main('WARNING', f"Could not extract image info for {os.path.basename(file_path)}: {str(e)}")
            return "unknown"
    
    def get_video_info(self, file_path: str) -> str:
        """Get basic video information"""
        try:
            cap = cv2.VideoCapture(file_path)
            if cap.isOpened():
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                cap.release()
                info = f"{width}x{height}_{fps}fps"
                if self.logger:
                    self.logger.log_main('INFO', f"Video info extracted: {os.path.basename(file_path)} - {info}")
                return info
            return "unknown"
        except Exception as e:
            if self.logger:
                self.logger.log_main('WARNING', f"Could not extract video info for {os.path.basename(file_path)}: {str(e)}")
            return "unknown"
    
    def get_audio_info(self, file_path: str) -> str:
        """Get basic audio information"""
        try:
            audio_file = mutagen.File(file_path)
            if audio_file and hasattr(audio_file, 'info'):
                duration = int(audio_file.info.length)
                bitrate = getattr(audio_file.info, 'bitrate', 0)
                info = f"{duration}s_{bitrate}kbps"
                if self.logger:
                    self.logger.log_main('INFO', f"Audio info extracted: {os.path.basename(file_path)} - {info}")
                return info
            return "unknown"
        except Exception as e:
            if self.logger:
                self.logger.log_main('WARNING', f"Could not extract audio info for {os.path.basename(file_path)}: {str(e)}")
            return "unknown"
    
    def get_document_info(self, file_path: str) -> str:
        """Get basic document information"""
        ext = Path(file_path).suffix.lower()
        try:
            info = "document"
            if ext == '.pdf':
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    info = f"{len(reader.pages)}pages"
            elif ext in ['.docx', '.doc']:
                doc = docx.Document(file_path)
                info = f"{len(doc.paragraphs)}paragraphs"
            elif ext in ['.pptx', '.ppt']:
                prs = Presentation(file_path)
                info = f"{len(prs.slides)}slides"
            elif ext == '.txt':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = len(f.readlines())
                    info = f"{lines}lines"
            
            if self.logger and info != "document":
                self.logger.log_main('INFO', f"Document info extracted: {os.path.basename(file_path)} - {info}")
            return info
        except Exception as e:
            if self.logger:
                self.logger.log_main('WARNING', f"Could not extract document info for {os.path.basename(file_path)}: {str(e)}")
            return "document"
    
    def create_organized_filename(self, file_path: str, category: str) -> str:
        """Create an organized filename with metadata info"""
        original_name = Path(file_path).stem
        extension = Path(file_path).suffix  # Keep original case of extension
        
        # Ensure extension exists
        if not extension:
            # Try to determine extension from detected format
            _, format_type, _ = self.detect_file_type(file_path)
            if format_type and format_type != 'unknown':
                extension = f".{format_type}"
            else:
                extension = ".unknown"
        
        # Get file info based on category
        info = ""
        if category == 'Images':
            info = self.get_image_info(file_path)
        elif category == 'Videos':
            info = self.get_video_info(file_path)
        elif category == 'Audio':
            info = self.get_audio_info(file_path)
        elif category == 'Documents':
            info = self.get_document_info(file_path)
        
        # Create organized filename - ALWAYS include extension
        if info and info != "unknown":
            new_filename = f"{original_name}_{info}{extension}"
        else:
            new_filename = f"{original_name}{extension}"
        
        if self.logger:
            self.logger.log_main('INFO', f"Filename created: {os.path.basename(file_path)} -> {new_filename}")
        
        return new_filename
    
    def process_and_organize_files(self, input_folder: str, output_folder: str, 
                                 organize_by_type: bool = True, 
                                 add_metadata_to_filename: bool = True,
                                 progress_callback=None) -> Dict:
        """Process files and organize them in output folder"""
        if self.logger:
            self.logger.log_main('INFO', f"Starting file processing - Input: {input_folder}, Output: {output_folder}")
            self.logger.log_main('INFO', f"Options - Organize by type: {organize_by_type}, Add metadata: {add_metadata_to_filename}")
        
        results = {
            'total_files': 0,
            'processed_files': 0,
            'errors': [],
            'categories': {}
        }
        
        files = []
        
        # Collect all files
        for root, dirs, filenames in os.walk(input_folder):
            for filename in filenames:
                files.append(os.path.join(root, filename))
        
        results['total_files'] = len(files)
        
        if self.logger:
            self.logger.log_main('INFO', f"Found {len(files)} files to process")
        
        for i, file_path in enumerate(files):
            try:
                if progress_callback:
                    progress_callback(i + 1, len(files), os.path.basename(file_path))
                
                # Detect file type
                category, format_type, detection_method = self.detect_file_type(file_path)
                
                # Create destination folder
                if organize_by_type:
                    dest_folder = os.path.join(output_folder, category)
                else:
                    dest_folder = output_folder
                
                os.makedirs(dest_folder, exist_ok=True)
                
                # Create filename (with or without metadata) - ALWAYS preserve extension
                original_filename = os.path.basename(file_path)
                original_name = Path(file_path).stem
                original_extension = Path(file_path).suffix
                
                # Ensure extension exists
                if not original_extension:
                    # Try to determine extension from detected format
                    if format_type and format_type != 'unknown':
                        original_extension = f".{format_type}"
                    else:
                        original_extension = ".unknown"
                
                if add_metadata_to_filename:
                    new_filename = self.create_organized_filename(file_path, category)
                else:
                    # Even without metadata, ensure extension is preserved
                    new_filename = f"{original_name}{original_extension}"
                
                # Handle duplicate filenames
                dest_path = os.path.join(dest_folder, new_filename)
                counter = 1
                base_name, ext = os.path.splitext(new_filename)
                
                while os.path.exists(dest_path):
                    new_filename = f"{base_name}_{counter}{ext}"
                    dest_path = os.path.join(dest_folder, new_filename)
                    counter += 1
                
                # Copy the file
                shutil.copy2(file_path, dest_path)
                
                if self.logger:
                    self.logger.log_main('INFO', f"File processed: {original_filename} -> {dest_path}")
                
                # Update statistics
                if category not in results['categories']:
                    results['categories'][category] = 0
                results['categories'][category] += 1
                results['processed_files'] += 1
                
            except Exception as e:
                error_info = {
                    'file_path': file_path,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                results['errors'].append(error_info)
                
                if self.logger:
                    self.logger.log_main('ERROR', f"Error processing file {file_path}: {str(e)}")
        
        if self.logger:
            self.logger.log_main('INFO', f"Processing completed - {results['processed_files']} files processed, {len(results['errors'])} errors")
            self.logger.create_summary_log(results)
        
        return results


class FileOrganizerGUI:
    """Beautiful GUI for the file organizer"""
    
    def __init__(self, root):
        self.root = root
        self.logger = FileLogger()  # Initialize logger
        self.processor = FileProcessor(self.logger)  # Pass logger to processor
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.organize_by_type = tk.BooleanVar(value=True)
        self.add_metadata_to_filename = tk.BooleanVar(value=True)
        self.processing = False
        
        self.setup_gui()
        
        # Log application start
        self.logger.log_main('INFO', 'File Organizer application started')
        self.log(f"📝 Logging enabled - Log files location: {self.logger.log_directory}")
        self.log(f"📝 Main log: {os.path.basename(self.logger.main_log_file)}")
        self.log(f"📝 Detection log: {os.path.basename(self.logger.detection_log_file)}")
    
    def setup_gui(self):
        """Setup the GUI interface"""
        self.root.title("Professional File Organizer & Processor")
        self.root.geometry("950x800")
        self.root.configure(bg='#f0f0f0')
        
        # Configure styles
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), background='#f0f0f0')
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'), background='#f0f0f0')
        style.configure('Custom.TButton', font=('Arial', 10))
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="File Organizer & Processor with Logging", 
                               style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Input folder selection
        ttk.Label(main_frame, text="Input Folder (Source Files):", style='Header.TLabel').grid(
            row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Entry(input_frame, textvariable=self.input_folder, width=65).grid(
            row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(input_frame, text="Browse", command=self.select_input_folder,
                  style='Custom.TButton').grid(row=0, column=1)
        
        # Output folder selection
        ttk.Label(main_frame, text="Output Folder (Organized Files):", style='Header.TLabel').grid(
            row=3, column=0, sticky=tk.W, pady=(0, 5))
        
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Entry(output_frame, textvariable=self.output_folder, width=65).grid(
            row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(output_frame, text="Browse", command=self.select_output_folder,
                  style='Custom.TButton').grid(row=0, column=1)
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Processing Options", padding="10")
        options_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Checkbutton(options_frame, text="Organize files by type (Images, Documents, etc.)",
                       variable=self.organize_by_type).grid(row=0, column=0, sticky=tk.W, pady=2)
        
        ttk.Checkbutton(options_frame, text="Add metadata info to filenames (size, duration, etc.)",
                       variable=self.add_metadata_to_filename).grid(row=1, column=0, sticky=tk.W, pady=2)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=(0, 20))
        
        self.start_button = ttk.Button(button_frame, text="Start Processing", 
                                      command=self.start_processing,
                                      style='Custom.TButton')
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="Stop", 
                                     command=self.stop_processing,
                                     style='Custom.TButton', state='disabled')
        self.stop_button.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Button(button_frame, text="Clear Log", command=self.clear_log,
                  style='Custom.TButton').grid(row=0, column=2, padx=(0, 10))
        
        ttk.Button(button_frame, text="Open Output Folder", command=self.open_output_folder,
                  style='Custom.TButton').grid(row=0, column=3, padx=(0, 10))
        
        ttk.Button(button_frame, text="Open Log Folder", command=self.open_log_folder,
                  style='Custom.TButton').grid(row=0, column=4)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Status label
        self.status_var = tk.StringVar(value="Ready to process files")
        ttk.Label(main_frame, textvariable=self.status_var).grid(
            row=8, column=0, columnspan=3, pady=(0, 10))
        
        # Log area
        ttk.Label(main_frame, text="Processing Log:", style='Header.TLabel').grid(
            row=9, column=0, sticky=tk.W, pady=(10, 5))
        
        self.log_text = ScrolledText(main_frame, width=85, height=15, 
                                    font=('Consolas', 9))
        self.log_text.grid(row=10, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Supported formats info
        formats_frame = ttk.LabelFrame(main_frame, text="Supported File Types", padding="10")
        formats_frame.grid(row=11, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        formats_text = "🖼️ Images: JPEG, PNG, BMP, TIFF, GIF, WebP, HEIC\n"
        formats_text += "📄 Documents: PDF, DOCX, DOC, TXT, PPTX, PPT\n"
        formats_text += "🎥 Videos: MP4, AVI, MKV, MOV, WMV, FLV, WebM\n"
        formats_text += "🎵 Audio: MP3, FLAC, WAV, OGG, M4A, AAC\n"
        formats_text += "📦 Archives: ZIP, RAR, 7Z, TAR, GZ\n"
        formats_text += "⚙️ Executables: EXE, MSI, DMG, DEB, RPM"
        
        ttk.Label(formats_frame, text=formats_text, font=('Arial', 9)).grid(
            row=0, column=0, sticky=tk.W)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(10, weight=1)
        input_frame.columnconfigure(0, weight=1)
        output_frame.columnconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
    
    def select_input_folder(self):
        """Select input folder"""
        folder = filedialog.askdirectory(title="Select Input Folder (Source Files)")
        if folder:
            self.input_folder.set(folder)
            self.log(f"✅ Input folder selected: {folder}")
            self.logger.log_main('INFO', f"Input folder selected: {folder}")
    
    def select_output_folder(self):
        """Select output folder"""
        folder = filedialog.askdirectory(title="Select Output Folder (Organized Files)")
        if folder:
            self.output_folder.set(folder)
            self.log(f"✅ Output folder selected: {folder}")
            self.logger.log_main('INFO', f"Output folder selected: {folder}")
    
    def open_output_folder(self):
        """Open output folder in file explorer"""
        if self.output_folder.get() and os.path.exists(self.output_folder.get()):
            if sys.platform == "win32":
                os.startfile(self.output_folder.get())
            elif sys.platform == "darwin":
                os.system(f"open '{self.output_folder.get()}'")
            else:
                os.system(f"xdg-open '{self.output_folder.get()}'")
            self.log(f"📁 Opened output folder: {self.output_folder.get()}")
        else:
            messagebox.showwarning("Warning", "Output folder not set or doesn't exist")
    
    def open_log_folder(self):
        """Open log folder in file explorer"""
        if os.path.exists(self.logger.log_directory):
            if sys.platform == "win32":
                os.startfile(self.logger.log_directory)
            elif sys.platform == "darwin":
                os.system(f"open '{self.logger.log_directory}'")
            else:
                os.system(f"xdg-open '{self.logger.log_directory}'")
            self.log(f"📁 Opened log folder: {self.logger.log_directory}")
        else:
            messagebox.showwarning("Warning", "Log folder doesn't exist")
    
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def clear_log(self):
        """Clear the log"""
        self.log_text.delete(1.0, tk.END)
        self.log("📝 Log cleared")
    
    def update_progress(self, current, total, filename):
        """Update progress bar and status"""
        progress = (current / total) * 100
        self.progress_var.set(progress)
        self.status_var.set(f"Processing {current}/{total}: {filename}")
        self.log(f"🔄 Processing: {filename}")
    
    def start_processing(self):
        """Start the processing in a separate thread"""
        if not self.input_folder.get():
            messagebox.showerror("Error", "Please select an input folder")
            return
        
        if not self.output_folder.get():
            messagebox.showerror("Error", "Please select an output folder")
            return
        
        if not os.path.exists(self.input_folder.get()):
            messagebox.showerror("Error", "Input folder does not exist")
            return
        
        # Create output folder if it doesn't exist
        os.makedirs(self.output_folder.get(), exist_ok=True)
        
        self.processing = True
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        
        self.log(f"🚀 Starting file processing and organization...")
        self.log(f"📋 Options: Organize by type = {self.organize_by_type.get()}")
        self.log(f"📋 Options: Add metadata to filenames = {self.add_metadata_to_filename.get()}")
        self.log(f"📋 All files will keep their original extensions for proper viewing")
        self.log(f"📝 Detailed logs are being saved to: {self.logger.log_directory}")
        
        self.logger.log_main('INFO', 'Starting file processing session')
        
        # Start processing in a separate thread
        thread = threading.Thread(target=self.process_files)
        thread.daemon = True
        thread.start()
    
    def process_files(self):
        """Process files in background thread"""
        try:
            results = self.processor.process_and_organize_files(
                self.input_folder.get(),
                self.output_folder.get(),
                self.organize_by_type.get(),
                self.add_metadata_to_filename.get(),
                self.update_progress
            )
            
            self.log(f"✅ Processing completed!")
            self.log(f"📊 Total files: {results['total_files']}")
            self.log(f"✔️ Successfully processed: {results['processed_files']}")
            
            # Log category statistics
            for category, count in results['categories'].items():
                self.log(f"   📁 {category}: {count} files")
            
            if results['errors']:
                self.log(f"❌ Errors encountered: {len(results['errors'])}")
                for error in results['errors']:
                    self.log(f"   Error: {Path(error['file_path']).name} - {error['error']}")
            
            self.status_var.set("Processing completed successfully!")
            
            # Show completion dialog
            message = f"Processing completed!\n\n"
            message += f"Total files: {results['total_files']}\n"
            message += f"Successfully processed: {results['processed_files']}\n"
            if results['errors']:
                message += f"Errors: {len(results['errors'])}\n"
            message += f"\nFiles organized in: {self.output_folder.get()}\n"
            message += f"Logs saved in: {self.logger.log_directory}\n\n"
            message += f"Log files created:\n"
            message += f"• Main log: {os.path.basename(self.logger.main_log_file)}\n"
            message += f"• Detection log: {os.path.basename(self.logger.detection_log_file)}\n"
            message += f"• Summary log: processing_summary_*.log"
            
            messagebox.showinfo("Success", message)
            
        except Exception as e:
            self.log(f"❌ Error during processing: {str(e)}")
            self.logger.log_main('ERROR', f"Fatal error during processing: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        
        finally:
            self.processing = False
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.progress_var.set(0)
    
    def stop_processing(self):
        """Stop the processing"""
        self.processing = False
        self.log("⏹️ Processing stopped by user")
        self.logger.log_main('WARNING', 'Processing stopped by user')
        self.status_var.set("Processing stopped")


def main():
    """Main function to run the application"""
    # Check if required packages are installed
    required_packages = {
        'Pillow': 'PIL',
        'PyPDF2': 'PyPDF2',
        'python-docx': 'docx',
        'python-pptx': 'pptx',
        'opencv-python': 'cv2',
        'mutagen': 'mutagen'
    }
    
    missing_packages = []
    
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print("❌ Missing required packages. Please install them using:")
        print(f"pip install {' '.join(missing_packages)}")
        input("Press Enter to exit...")
        return
    
    # Create and run the GUI
    root = tk.Tk()
    app = FileOrganizerGUI(root)
    
    # Center the window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f'+{x}+{y}')
    
    try:
        root.mainloop()
    except Exception as e:
        if hasattr(app, 'logger'):
            app.logger.log_main('ERROR', f"Application error: {str(e)}")
        print(f"Application error: {str(e)}")
    finally:
        if hasattr(app, 'logger'):
            app.logger.log_main('INFO', 'File Organizer application closed')


if __name__ == "__main__":
    main()