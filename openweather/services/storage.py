"""Storage utilities for managing output files."""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .geometry import parse_point_from_wkt


def sanitize_location_name(name: str) -> str:
    """Sanitize location name to use only ASCII characters for file system compatibility."""
    if not name:
        return "Unknown"
    
    # Remove or replace non-ASCII characters
    # Keep only letters, numbers, spaces, and common punctuation
    sanitized = re.sub(r'[^\x00-\x7F]+', '', name)
    
    # Replace multiple spaces with single space
    sanitized = re.sub(r'\s+', ' ', sanitized)
    
    # Remove leading/trailing spaces
    sanitized = sanitized.strip()
    
    # If empty after sanitization, use default
    if not sanitized:
        return "Unknown"
    
    return sanitized


class StorageService:
    """Service for managing file storage and organization."""
    
    def __init__(self, base_output_dir: Path):
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(exist_ok=True)
    
    def create_job_directory(self, wkt: str, dataset: str, years: List[str], location: str = "Unknown Location", state: str = "Unknown State", country: str = "Planet Earth") -> Path:
        """Create a unique directory for a job."""
        # Create timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sanitize location names to ensure ASCII-only characters
        safe_location = sanitize_location_name(location)
        safe_state = sanitize_location_name(state)
        safe_country = sanitize_location_name(country)
        
        # Create job name: Location_State_Country_YYYYMMDDHHMMSS
        job_name = f"{safe_location}_{safe_state}_{safe_country}_{timestamp}"
        
        # For server deployment, always use the outputs directory
        if os.environ.get('RENDER') or os.environ.get('RAILWAY') or os.environ.get('HEROKU'):
            # Server environment - use outputs directory
            full_path = self.base_output_dir / job_name
        else:
            # Local environment - use user's downloads folder
            downloads_path = Path.home() / "Downloads"
            full_path = downloads_path / "OpenWeather" / job_name
        
        # Create all necessary directories
        full_path.mkdir(parents=True, exist_ok=True)
        
        return full_path
    
    def save_csv_file(self, job_dir: Path, content: str, filename: str) -> Path:
        """Save CSV content to file."""
        file_path = job_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def save_epw_file(self, job_dir: Path, content: str, filename: str) -> Path:
        """Save EPW content to file."""
        file_path = job_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def list_job_files(self, job_dir: Path) -> List[Path]:
        """List all files in a job directory."""
        if not job_dir.exists():
            return []
        
        files = []
        for file_path in job_dir.iterdir():
            if file_path.is_file():
                files.append(file_path)
        
        return sorted(files)
    
    def get_file_size(self, file_path: Path) -> int:
        """Get file size in bytes."""
        return file_path.stat().st_size if file_path.exists() else 0
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Clean up job directories older than specified hours."""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        cleaned_count = 0
        
        for job_dir in self.base_output_dir.iterdir():
            if job_dir.is_dir():
                try:
                    # Check if directory is old enough
                    dir_time = job_dir.stat().st_mtime
                    if dir_time < cutoff_time:
                        shutil.rmtree(job_dir)
                        cleaned_count += 1
                except (OSError, PermissionError):
                    # Skip directories that can't be removed
                    continue
        
        return cleaned_count
    
    def get_job_summary(self, job_dir: Path) -> dict:
        """Get summary information about a job directory."""
        if not job_dir.exists():
            return {}
        
        files = self.list_job_files(job_dir)
        csv_files = [f for f in files if f.suffix.lower() == '.csv']
        epw_files = [f for f in files if f.suffix.lower() == '.epw']
        
        total_size = sum(self.get_file_size(f) for f in files)
        
        return {
            'job_dir': str(job_dir),
            'job_name': job_dir.name,
            'total_files': len(files),
            'csv_files': len(csv_files),
            'epw_files': len(epw_files),
            'total_size': total_size,
            'total_size_formatted': self.format_file_size(total_size),
            'created': datetime.fromtimestamp(job_dir.stat().st_ctime).isoformat(),
            'files': [
                {
                    'name': f.name,
                    'size': self.get_file_size(f),
                    'size_formatted': self.format_file_size(self.get_file_size(f)),
                    'type': f.suffix.lower()
                }
                for f in files
            ]
        }
