# Metadata File Organizer - Process Folders & Subfolders

A professional Python application with a beautiful GUI that automatically organizes and processes files from folders and all their subfolders. The application intelligently detects file types using magic bytes (file signatures) and organizes them by category with optional metadata enhancement.

## ✨ Features

### 🔍 **Intelligent File Detection**
- **Magic Bytes Detection**: Uses file signatures to accurately identify file types, not just extensions
- **Extension Fallback**: Falls back to file extension detection when magic bytes fail
- **Comprehensive Format Support**: Supports 50+ file formats across 6 categories

### 📁 **Smart Organization**
- **Recursive Processing**: Automatically processes all files in the main folder and ALL subfolders
- **Category-Based Organization**: Groups files into logical categories (Images, Documents, Videos, etc.)
- **Metadata Enhancement**: Adds useful information to filenames (dimensions, duration, page count, etc.)
- **Duplicate Handling**: Automatically handles duplicate filenames with smart numbering

### 🎯 **Advanced Processing**
- **Batch Processing**: Process thousands of files efficiently
- **Real-time Progress**: Live progress bar and detailed logging
- **Error Handling**: Continues processing even if individual files fail
- **Extension Preservation**: Always preserves original file extensions

### 🖥️ **Professional GUI**
- **Modern Interface**: Clean, user-friendly design with proper styling
- **Real-time Logging**: Detailed processing logs with timestamps
- **Progress Tracking**: Visual progress bar and file-by-file status updates
- **Easy Navigation**: Quick access to input/output folders

## 📂 Supported File Types

### 🖼️ **Images**
- **Formats**: JPEG, PNG, BMP, TIFF, GIF, WebP, HEIC
- **Metadata Added**: Resolution (e.g., `photo_1920x1080_JPEG.jpg`)

### 📄 **Documents**
- **Formats**: PDF, DOCX, DOC, TXT, PPTX, PPT
- **Metadata Added**: 
  - PDF: Page count (e.g., `report_25pages.pdf`)
  - Word: Paragraph count (e.g., `document_150paragraphs.docx`)
  - PowerPoint: Slide count (e.g., `presentation_20slides.pptx`)
  - Text: Line count (e.g., `notes_500lines.txt`)

### 🎥 **Videos**
- **Formats**: MP4, AVI, MKV, MOV, WMV, FLV, WebM
- **Metadata Added**: Resolution and FPS (e.g., `movie_1920x1080_30fps.mp4`)

### 🎵 **Audio**
- **Formats**: MP3, FLAC, WAV, OGG, M4A, AAC
- **Metadata Added**: Duration and bitrate (e.g., `song_180s_320kbps.mp3`)

### 📦 **Archives**
- **Formats**: ZIP, RAR, 7Z, TAR, GZ
- **Organization**: Groups all compressed files together

### ⚙️ **Executables**
- **Formats**: EXE, MSI, DMG, DEB, RPM
- **Organization**: Separates executable files for security

## 🚀 Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Required Dependencies
Install all required packages using pip:

```bash
pip install Pillow PyPDF2 python-docx python-pptx opencv-python mutagen
```

Or install individual packages:
```bash
pip install Pillow          # Image processing
pip install PyPDF2          # PDF handling
pip install python-docx     # Word document processing
pip install python-pptx     # PowerPoint processing
pip install opencv-python   # Video processing
pip install mutagen         # Audio metadata extraction
```

### Download and Run
1. Download the `Metadata2File.py` script
2. Install dependencies (see above)
3. Run the application:

```bash
python Metadata2File.py
```

## 📖 How to Use

### Step 1: Launch the Application
```bash
python Metadata2File.py
```

### Step 2: Select Input Folder
1. Click **"Browse"** next to "Input Folder"
2. Select the folder containing files you want to organize
3. The application will automatically process ALL subfolders within this folder

### Step 3: Select Output Folder
1. Click **"Browse"** next to "Output Folder"
2. Choose where you want the organized files to be saved
3. The application will create category folders here automatically

### Step 4: Configure Options
- ✅ **"Organize files by type"**: Creates separate folders for Images, Documents, Videos, etc.
- ✅ **"Add metadata info to filenames"**: Enhances filenames with useful information

### Step 5: Start Processing
1. Click **"Start Processing"**
2. Watch the progress bar and log for real-time updates
3. Use **"Stop"** button if you need to cancel
4. Click **"Open Output Folder"** when complete to view results

## 📊 Example Output Structure

### With "Organize by type" enabled:
```
Output Folder/
├── Images/
│   ├── vacation_photo_4032x3024_JPEG.jpg
│   ├── screenshot_1920x1080_PNG.png
│   └── family_pic_3000x2000_HEIC.heic
├── Documents/
│   ├── report_25pages.pdf
│   ├── presentation_15slides.pptx
│   └── notes_300lines.txt
├── Videos/
│   ├── movie_1920x1080_30fps.mp4
│   └── clip_1280x720_60fps.mov
├── Audio/
│   ├── song_180s_320kbps.mp3
│   └── podcast_3600s_128kbps.mp3
└── Archives/
    ├── backup.zip
    └── photos.rar
```

### Without "Organize by type":
```
Output Folder/
├── vacation_photo_4032x3024_JPEG.jpg
├── report_25pages.pdf
├── movie_1920x1080_30fps.mp4
├── song_180s_320kbps.mp3
└── backup.zip
```

## 🛠️ Advanced Features

### Magic Bytes Detection
The application uses file signatures (magic bytes) to accurately identify files:
- **JPEG**: `FF D8 FF`
- **PNG**: `89 50 4E 47 0D 0A 1A 0A`
- **PDF**: `25 50 44 46` (%PDF)
- **ZIP**: `50 4B 03 04`
- And many more...

### Duplicate File Handling
If files with the same name exist, the application automatically adds numbers:
- `document.pdf`
- `document_1.pdf`
- `document_2.pdf`

### Error Recovery
- Continues processing even if individual files fail
- Detailed error logging for troubleshooting
- Shows summary of successful vs. failed files

## 🔧 Troubleshooting

### Missing Dependencies Error
If you see import errors, install missing packages:
```bash
pip install [package-name]
```

### Permission Errors
- Ensure you have read access to input folders
- Ensure you have write access to output folder
- Run as administrator if needed (Windows)

### Large File Processing
- The application handles large files efficiently
- Progress updates every 10 files to avoid log spam
- Use "Stop" button to cancel long-running operations

### Memory Usage
- The application processes files one at a time to minimize memory usage
- Suitable for processing thousands of files
- Large video files are analyzed without loading entirely into memory

## 📝 Log Information

The application provides detailed logging:
- **🔍** Folder scanning progress
- **📂** Subfolder processing status
- **🔄** File processing updates (every 10 files)
- **✅** Successful operations
- **❌** Error details with timestamps
- **📊** Final statistics and summary

## 🎯 Use Cases

- **Digital Photo Organization**: Sort photos from multiple folders by date and add resolution info
- **Document Management**: Organize work documents with page counts and metadata
- **Media Library Cleanup**: Sort mixed media files into proper categories
- **Backup Organization**: Process messy backup folders with thousands of files
- **Content Creation**: Organize project files by type with useful metadata
- **System Cleanup**: Sort downloads folder and other messy directories


---

**Made with ❤️ for efficient file organization**