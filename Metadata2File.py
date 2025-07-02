import os
import sys
import shutil
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
    
    def __init__(self):
        self.processed_files = []
        self.errors = []
        self.file_stats = {}
    
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
                    return category, format_type, detection_method
            
            # Check by file extension as fallback
            ext = Path(file_path).suffix.lower()
            for category, extensions in self.SUPPORTED_FORMATS.items():
                if ext in extensions:
                    detection_method = "file_extension"
                    format_type = ext[1:]  # Remove the dot
                    return category, format_type, detection_method
            
            # Unknown file type
            detection_method = "unknown"
            return 'Other', 'unknown', detection_method
            
        except Exception as e:
            detection_method = "error"
            return 'Error', str(e), detection_method
    
    def get_image_info(self, file_path: str) -> str:
        """Get basic image information"""
        try:
            with Image.open(file_path) as img:
                info = f"{img.size[0]}x{img.size[1]}_{img.format}"
                return info
        except Exception as e:
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
                return info
            return "unknown"
        except Exception as e:
            return "unknown"
    
    def get_audio_info(self, file_path: str) -> str:
        """Get basic audio information"""
        try:
            audio_file = mutagen.File(file_path)
            if audio_file and hasattr(audio_file, 'info'):
                duration = int(audio_file.info.length)
                bitrate = getattr(audio_file.info, 'bitrate', 0)
                info = f"{duration}s_{bitrate}kbps"
                return info
            return "unknown"
        except Exception as e:
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
            
            return info
        except Exception as e:
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
        
        return new_filename
    
    def get_all_files_from_folder(self, input_folder: str) -> List[str]:
        """Get all files from folder and all its subfolders"""
        files = []
        
        try:
            # Walk through all directories and subdirectories
            for root, dirs, filenames in os.walk(input_folder):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    files.append(file_path)
        except Exception as e:
            print(f"Error scanning folder {input_folder}: {str(e)}")
        
        return files
    
    def process_and_organize_files(self, input_folder: str, output_folder: str, 
                                 organize_by_type: bool = True, 
                                 add_metadata_to_filename: bool = True,
                                 progress_callback=None,
                                 log_callback=None) -> Dict:
        """Process files and organize them in output folder"""
        
        if log_callback:
            log_callback(f"🔍 Scanning input folder and all subfolders: {input_folder}")
        
        results = {
            'total_files': 0,
            'processed_files': 0,
            'errors': [],
            'categories': {},
            'subfolders_scanned': 0
        }
        
        # Get all files from input folder and subfolders
        files = self.get_all_files_from_folder(input_folder)
        
        # Count unique subfolders scanned
        subfolders = set()
        for file_path in files:
            subfolder = os.path.dirname(file_path)
            subfolders.add(subfolder)
        
        results['total_files'] = len(files)
        results['subfolders_scanned'] = len(subfolders)
        
        if log_callback:
            log_callback(f"📁 Found {len(subfolders)} folders with {len(files)} files to process")
        
        for i, file_path in enumerate(files):
            try:
                if progress_callback:
                    progress_callback(i + 1, len(files), os.path.basename(file_path))
                
                # Get relative path from input folder to maintain folder structure info
                relative_path = os.path.relpath(file_path, input_folder)
                subfolder_name = os.path.dirname(relative_path)
                
                if log_callback and subfolder_name:
                    log_callback(f"📂 Processing from subfolder: {subfolder_name}")
                
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
                
                if log_callback:
                    log_callback(f"❌ Error processing {os.path.basename(file_path)}: {str(e)}")
        
        return results


class FileOrganizerGUI:
    """Beautiful GUI for the file organizer"""
    
    def __init__(self, root):
        self.root = root
        self.processor = FileProcessor()
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.organize_by_type = tk.BooleanVar(value=True)
        self.add_metadata_to_filename = tk.BooleanVar(value=True)
        self.processing = False
        
        self.setup_gui()
    
    def setup_gui(self):
        """Setup the GUI interface"""
        self.root.title("File Organizer - Process Folders & Subfolders")
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
        title_label = ttk.Label(main_frame, text="File Organizer - Process Folders & Subfolders", 
                               style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Input folder selection
        ttk.Label(main_frame, text="Input Folder (Will process all subfolders):", style='Header.TLabel').grid(
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
                  style='Custom.TButton').grid(row=0, column=3)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Status label
        self.status_var = tk.StringVar(value="Ready to process files from folders and subfolders")
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
        folder = filedialog.askdirectory(title="Select Input Folder (Will process all subfolders)")
        if folder:
            self.input_folder.set(folder)
            self.log(f"✅ Input folder selected: {folder}")
            self.log(f"📁 Will process all files in this folder and its subfolders")
    
    def select_output_folder(self):
        """Select output folder"""
        folder = filedialog.askdirectory(title="Select Output Folder (Organized Files)")
        if folder:
            self.output_folder.set(folder)
            self.log(f"✅ Output folder selected: {folder}")
    
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
        # Only log every 10th file to avoid spam
        if current % 10 == 0 or current == total:
            self.log(f"🔄 Processing: {filename} ({current}/{total})")
    
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
        self.log(f"📂 Input folder: {self.input_folder.get()}")
        self.log(f"📂 Output folder: {self.output_folder.get()}")
        self.log(f"📋 Organize by type: {self.organize_by_type.get()}")
        self.log(f"📋 Add metadata to filenames: {self.add_metadata_to_filename.get()}")
        self.log(f"📋 All files will keep their original extensions")
        
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
                self.update_progress,
                self.log
            )
            
            self.log(f"✅ Processing completed!")
            self.log(f"📊 Scanned {results['subfolders_scanned']} folders")
            self.log(f"📊 Total files found: {results['total_files']}")
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
            message += f"Folders scanned: {results['subfolders_scanned']}\n"
            message += f"Total files found: {results['total_files']}\n"
            message += f"Successfully processed: {results['processed_files']}\n"
            if results['errors']:
                message += f"Errors: {len(results['errors'])}\n"
            message += f"\nFiles organized in: {self.output_folder.get()}"
            
            messagebox.showinfo("Success", message)
            
        except Exception as e:
            self.log(f"❌ Error during processing: {str(e)}")
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
        print(f"Application error: {str(e)}")


if __name__ == "__main__":
    main()