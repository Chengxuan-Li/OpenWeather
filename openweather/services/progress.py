"""Progress tracking service for NSRDB jobs."""

import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ProgressManager:
    """Manages progress tracking for NSRDB jobs."""
    
    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
    
    def create_job(self, job_id: str, total_years: int, total_points: int = 1) -> None:
        """Create a new job progress tracker."""
        total_downloads = total_years * total_points
        self.jobs[job_id] = {
            'created_at': datetime.now(),
            'total_years': total_years,
            'total_points': total_points,
            'total_downloads': total_downloads,
            'completed_downloads': 0,
            'completed_conversions': 0,
            'current_year': None,
            'current_point': None,
            'status': 'pending',
            'download_progress': 0.0,
            'conversion_progress': 0.0
        }
        logger.info(f"Created progress tracker for job {job_id}: {total_years} years, {total_points} points")
    
    def update_download_progress(self, job_id: str, year: str, point_id: str) -> None:
        """Update download progress for a specific year and point."""
        if job_id not in self.jobs:
            logger.warning(f"Job {job_id} not found in progress tracker")
            return
        
        job = self.jobs[job_id]
        job['completed_downloads'] += 1
        job['current_year'] = year
        job['current_point'] = point_id
        job['download_progress'] = (job['completed_downloads'] / job['total_downloads']) * 100
        job['status'] = 'downloading'
        
        logger.info(f"Job {job_id}: Download progress {job['download_progress']:.1f}% ({job['completed_downloads']}/{job['total_downloads']})")
    
    def update_conversion_progress(self, job_id: str, year: str, point_id: str) -> None:
        """Update conversion progress for a specific year and point."""
        if job_id not in self.jobs:
            logger.warning(f"Job {job_id} not found in progress tracker")
            return
        
        job = self.jobs[job_id]
        job['completed_conversions'] += 1
        job['current_year'] = year
        job['current_point'] = point_id
        job['conversion_progress'] = (job['completed_conversions'] / job['total_downloads']) * 100
        job['status'] = 'converting'
        
        logger.info(f"Job {job_id}: Conversion progress {job['conversion_progress']:.1f}% ({job['completed_conversions']}/{job['total_downloads']})")
    
    def complete_job(self, job_id: str) -> None:
        """Mark job as completed."""
        if job_id not in self.jobs:
            logger.warning(f"Job {job_id} not found in progress tracker")
            return
        
        job = self.jobs[job_id]
        job['status'] = 'completed'
        job['download_progress'] = 100.0
        job['conversion_progress'] = 100.0
        job['completed_at'] = datetime.now()
        
        logger.info(f"Job {job_id} completed")
    
    def fail_job(self, job_id: str, error: str) -> None:
        """Mark job as failed."""
        if job_id not in self.jobs:
            logger.warning(f"Job {job_id} not found in progress tracker")
            return
        
        job = self.jobs[job_id]
        job['status'] = 'failed'
        job['error'] = error
        job['failed_at'] = datetime.now()
        
        logger.error(f"Job {job_id} failed: {error}")
    
    def get_progress(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current progress for a job."""
        if job_id not in self.jobs:
            return None
        
        job = self.jobs[job_id]
        return {
            'job_id': job_id,
            'status': job['status'],
            'download_progress': job['download_progress'],
            'conversion_progress': job['conversion_progress'],
            'current_year': job['current_year'],
            'current_point': job['current_point'],
            'total_years': job['total_years'],
            'total_points': job['total_points'],
            'completed_downloads': job['completed_downloads'],
            'total_downloads': job['total_downloads'],
            'completed_conversions': job['completed_conversions'],
            'created_at': job['created_at'].isoformat() if job['created_at'] else None,
            'completed_at': job['completed_at'].isoformat() if 'completed_at' in job else None,
            'error': job.get('error')
        }
    
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Clean up old completed jobs."""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        cleaned_count = 0
        
        job_ids_to_remove = []
        for job_id, job in self.jobs.items():
            if job['status'] in ['completed', 'failed']:
                job_time = job['created_at'].timestamp()
                if job_time < cutoff_time:
                    job_ids_to_remove.append(job_id)
        
        for job_id in job_ids_to_remove:
            del self.jobs[job_id]
            cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old jobs")
        
        return cleaned_count


# Global progress manager instance
progress_manager = ProgressManager()
