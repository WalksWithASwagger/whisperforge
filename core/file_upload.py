"""
Enhanced File Upload Component for WhisperForge
Beautiful drag-and-drop interface with progress tracking
"""

import streamlit as st
import time
from typing import Optional, List, Dict, Any
import mimetypes
import os
from pathlib import Path

class FileUploadManager:
    """Enhanced file upload manager with beautiful UI and progress tracking"""
    
    def __init__(self):
        self.supported_formats = {
            'audio': ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac', '.wma'],
            'video': ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'],
            'text': ['.txt', '.md', '.pdf', '.docx']
        }
        self.max_file_size = 25 * 1024 * 1024  # 25MB
        
    def create_upload_zone(self, 
                          accept_types: List[str] = None, 
                          max_files: int = 1,
                          show_preview: bool = True) -> Optional[Any]:
        """Create a beautiful drag-and-drop upload zone"""
        
        if accept_types is None:
            accept_types = self.supported_formats['audio']
            
        # Generate accepted file types string
        accept_str = ', '.join(accept_types)
        
        # Create the upload zone HTML
        upload_html = f"""
        <div class="upload-zone-container">
            <div class="upload-zone" id="upload-zone">
                <div class="upload-icon">
                    <div class="upload-icon-inner">📁</div>
                </div>
                <div class="upload-text">
                    <h3>Drop your files here</h3>
                    <p>or click to browse</p>
                    <div class="upload-info">
                        <span class="supported-formats">Supported: {accept_str}</span>
                        <span class="max-size">Max size: {self.max_file_size // (1024*1024)}MB</span>
                    </div>
                </div>
            </div>
        </div>
        """
        
        upload_css = """
        <style>
        .upload-zone-container {
            margin: 20px 0;
        }
        
        .upload-zone {
            border: 2px dashed rgba(121, 40, 202, 0.3);
            border-radius: var(--card-radius);
            padding: 40px 20px;
            text-align: center;
            background: linear-gradient(135deg, 
                rgba(121, 40, 202, 0.02) 0%, 
                rgba(66, 151, 233, 0.02) 100%);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }
        
        .upload-zone:hover {
            border-color: rgba(121, 40, 202, 0.6);
            background: linear-gradient(135deg, 
                rgba(121, 40, 202, 0.05) 0%, 
                rgba(66, 151, 233, 0.05) 100%);
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(121, 40, 202, 0.15);
        }
        
        .upload-zone.drag-over {
            border-color: var(--accent-primary);
            background: linear-gradient(135deg, 
                rgba(121, 40, 202, 0.1) 0%, 
                rgba(66, 151, 233, 0.1) 100%);
            transform: scale(1.02);
        }
        
        .upload-zone::before {
            content: "";
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, 
                transparent, 
                rgba(121, 40, 202, 0.1), 
                transparent);
            transition: left 0.5s ease;
        }
        
        .upload-zone:hover::before {
            left: 100%;
        }
        
        .upload-icon {
            margin-bottom: 16px;
            position: relative;
        }
        
        .upload-icon-inner {
            font-size: 48px;
            opacity: 0.7;
            transition: all 0.3s ease;
            display: inline-block;
        }
        
        .upload-zone:hover .upload-icon-inner {
            opacity: 1;
            transform: scale(1.1) rotate(5deg);
        }
        
        .upload-text h3 {
            color: var(--text-primary);
            font-size: 1.2rem;
            margin: 0 0 8px 0;
            font-weight: 600;
        }
        
        .upload-text p {
            color: var(--text-secondary);
            margin: 0 0 16px 0;
            font-size: 0.9rem;
        }
        
        .upload-info {
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
        }
        
        .supported-formats, .max-size {
            font-size: 0.8rem;
            color: var(--text-muted);
            background: rgba(255, 255, 255, 0.05);
            padding: 4px 8px;
            border-radius: 4px;
            font-family: var(--terminal-font);
        }
        
        .file-preview {
            background: var(--bg-secondary);
            border-radius: var(--card-radius);
            padding: 15px;
            margin: 15px 0;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .file-preview-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .file-info {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .file-icon {
            font-size: 24px;
        }
        
        .file-details h4 {
            margin: 0;
            color: var(--text-primary);
            font-size: 0.9rem;
        }
        
        .file-details p {
            margin: 2px 0 0 0;
            color: var(--text-secondary);
            font-size: 0.8rem;
        }
        
        .file-actions {
            display: flex;
            gap: 8px;
        }
        
        .file-action-btn {
            background: rgba(121, 40, 202, 0.1);
            border: 1px solid rgba(121, 40, 202, 0.3);
            color: var(--text-primary);
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .file-action-btn:hover {
            background: rgba(121, 40, 202, 0.2);
            border-color: rgba(121, 40, 202, 0.5);
        }
        
        .file-action-btn.danger {
            background: rgba(248, 114, 114, 0.1);
            border-color: rgba(248, 114, 114, 0.3);
        }
        
        .file-action-btn.danger:hover {
            background: rgba(248, 114, 114, 0.2);
            border-color: rgba(248, 114, 114, 0.5);
        }
        </style>
        """
        
        # Display the upload zone
        st.markdown(upload_css + upload_html, unsafe_allow_html=True)
        
        # Use Streamlit's file uploader (hidden behind custom UI)
        uploaded_file = st.file_uploader(
            "Choose file",
            type=[ext[1:] for ext in accept_types],  # Remove the dot
            key=f"uploader_{hash(str(accept_types))}",
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            if show_preview:
                self._show_file_preview(uploaded_file)
            return uploaded_file
            
        return None
    
    def _show_file_preview(self, file):
        """Show preview of uploaded file"""
        file_size = self._format_file_size(file.size)
        file_type = self._get_file_type(file.name)
        
        preview_html = f"""
        <div class="file-preview">
            <div class="file-preview-header">
                <div class="file-info">
                    <div class="file-icon">{self._get_file_icon(file_type)}</div>
                    <div class="file-details">
                        <h4>{file.name}</h4>
                        <p>{file_size} • {file_type.upper()}</p>
                    </div>
                </div>
                <div class="file-actions">
                    <button class="file-action-btn">✅ Ready</button>
                </div>
            </div>
        </div>
        """
        
        st.markdown(preview_html, unsafe_allow_html=True)
    
    def _get_file_icon(self, file_type: str) -> str:
        """Get icon for file type"""
        icons = {
            'audio': '🎵',
            'video': '🎬', 
            'text': '📄',
            'pdf': '📕',
            'doc': '📘',
            'unknown': '📁'
        }
        return icons.get(file_type, icons['unknown'])
    
    def _get_file_type(self, filename: str) -> str:
        """Determine file type from filename"""
        ext = Path(filename).suffix.lower()
        
        for file_type, extensions in self.supported_formats.items():
            if ext in extensions:
                return file_type
                
        if ext in ['.pdf']:
            return 'pdf'
        elif ext in ['.doc', '.docx']:
            return 'doc'
            
        return 'unknown'
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes/(1024**2):.1f} MB"
        else:
            return f"{size_bytes/(1024**3):.1f} GB"
    
    def validate_file(self, file) -> Dict[str, Any]:
        """Validate uploaded file"""
        errors = []
        warnings = []
        
        # Check file size
        if file.size > self.max_file_size:
            errors.append(f"File size ({self._format_file_size(file.size)}) exceeds maximum allowed size ({self._format_file_size(self.max_file_size)})")
        
        # Check file type
        file_type = self._get_file_type(file.name)
        if file_type == 'unknown':
            errors.append(f"Unsupported file type: {Path(file.name).suffix}")
        
        # Check if file is empty
        if file.size == 0:
            errors.append("File is empty")
        
        # Audio specific validations
        if file_type == 'audio':
            if file.size < 1024:  # Very small audio file
                warnings.append("Audio file seems very small - please ensure it contains actual audio content")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'file_type': file_type,
            'file_size': file.size,
            'formatted_size': self._format_file_size(file.size)
        }

def create_upload_progress_indicator(filename: str, progress: float = 0.0):
    """Create a progress indicator for file upload"""
    progress_html = f"""
    <div class="upload-progress-container">
        <div class="upload-progress-header">
            <span class="upload-filename">📤 {filename}</span>
            <span class="upload-percentage">{progress:.0f}%</span>
        </div>
        <div class="upload-progress-bar">
            <div class="upload-progress-fill" style="width: {progress}%"></div>
            <div class="upload-progress-shimmer" style="width: {progress}%"></div>
        </div>
        <div class="upload-status">
            {'Uploading...' if progress < 100 else 'Upload complete!'}
        </div>
    </div>
    """
    
    progress_css = """
    <style>
    .upload-progress-container {
        background: var(--bg-secondary);
        border-radius: var(--card-radius);
        padding: 15px;
        margin: 10px 0;
        border: 1px solid rgba(121, 40, 202, 0.2);
    }
    
    .upload-progress-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    
    .upload-filename {
        color: var(--text-primary);
        font-weight: 500;
        font-size: 0.9rem;
    }
    
    .upload-percentage {
        color: var(--accent-primary);
        font-family: var(--terminal-font);
        font-weight: 600;
    }
    
    .upload-progress-bar {
        height: 4px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 2px;
        position: relative;
        overflow: hidden;
        margin-bottom: 8px;
    }
    
    .upload-progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #7928CA, #FF0080);
        border-radius: 2px;
        transition: width 0.3s ease;
    }
    
    .upload-progress-shimmer {
        position: absolute;
        top: 0;
        left: 0;
        height: 100%;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255, 255, 255, 0.2), 
            transparent);
        animation: shimmer 1.5s ease-in-out infinite;
    }
    
    .upload-status {
        color: var(--text-secondary);
        font-size: 0.8rem;
        text-align: center;
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    </style>
    """
    
    return st.markdown(progress_css + progress_html, unsafe_allow_html=True)

def simulate_upload_progress(filename: str, duration: float = 2.0):
    """Simulate upload progress for demonstration"""
    progress_container = st.empty()
    
    steps = 20
    for i in range(steps + 1):
        progress = (i / steps) * 100
        
        with progress_container:
            create_upload_progress_indicator(filename, progress)
        
        if i < steps:
            time.sleep(duration / steps)
    
    return True 