"""API router for JSON endpoints."""

import logging
import os
import zipfile
import tempfile
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import json
import asyncio

from ..config import settings
from ..services.nsrdb_wrapper import NSRDBWrapper
from ..services.storage import StorageService
from ..services.geometry import validate_wkt, create_point_wkt
from ..services.progress import progress_manager

# Initialize services
storage_service = StorageService(settings.outputs_dir)
nsrdb_wrapper = NSRDBWrapper(storage_service)

# Initialize router
router = APIRouter()


class JobRequest(BaseModel):
    """Job request model for API."""
    wkt: str
    dataset: str
    interval: str
    years: List[str]
    api_key: str
    email: str
    location: Optional[str] = "Unknown"
    state: Optional[str] = "Unknown"
    country: Optional[str] = "Unknown"
    convert_to_epw: bool = True


class JobResponse(BaseModel):
    """Job response model."""
    success: bool
    job_id: Optional[str] = None
    job_dir: Optional[str] = None
    files: Optional[dict] = None
    logs: Optional[List[str]] = None
    errors: Optional[List[str]] = None
    summary: Optional[dict] = None


class WKTRequest(BaseModel):
    """WKT generation request model."""
    lat: float
    lon: float
    buffer: Optional[float] = 1.0


def get_secret_api_key() -> Optional[str]:
    """Get API key from Render secret file."""
    try:
        # Try to read from Render secrets
        secret_path = Path("/etc/secrets/api.txt")
        if secret_path.exists():
            return secret_path.read_text().strip()
        
        # Fallback to local development
        local_secret_path = Path("api.txt")
        if local_secret_path.exists():
            return local_secret_path.read_text().strip()
        
        return None
    except Exception as e:
        logging.error(f"Error reading secret API key: {e}")
        return None


@router.post("/download", response_model=JobResponse)
async def api_download(request: JobRequest):
    """
    Run NSRDB job via API.
    
    This replicates the workflow from NSRDB2EPW.ipynb:
    - Validates inputs
    - Creates job directory
    - Calls nsrdb2epw.nsrdb2epw
    - Returns file paths and logs
    """
    try:
        # Handle secret API key
        api_key = request.api_key
        if api_key.lower() == "eslab":
            secret_key = get_secret_api_key()
            if secret_key:
                api_key = secret_key
            else:
                return JobResponse(
                    success=False,
                    errors=["Secret API key not found. Please check your configuration."]
                )
        
        result = nsrdb_wrapper.run_nsrdb_job(
            wkt=request.wkt,
            dataset=request.dataset,
            interval=request.interval,
            years=request.years,
            api_key=api_key,
            email=request.email,
            location=request.location,
            state=request.state,
            country=request.country,
            convert_to_epw=request.convert_to_epw,
        )
        
        return JobResponse(**result)
        
    except Exception as e:
        logging.error(f"API download failed: {e}")
        return JobResponse(
            success=False,
            errors=[str(e)]
        )


@router.get("/progress/{job_id}")
async def get_progress(job_id: str):
    """
    Get progress for a specific job.
    Returns current progress as JSON.
    """
    logging.info(f"Progress request for job: {job_id}")
    progress = progress_manager.get_progress(job_id)
    logging.info(f"Progress response: {progress}")
    return progress


@router.post("/convert-to-epw")
async def api_convert_to_epw(
    csv_file: UploadFile = File(...),
    location: str = "Unknown",
    state: str = "Unknown",
    country: str = "Unknown",
):
    """
    Convert uploaded CSV file to EPW format.
    
    This replicates the CSV2EPW function from nsrdb2epw.py
    """
    try:
        # Save uploaded file temporarily
        temp_dir = settings.outputs_dir / "temp"
        temp_dir.mkdir(exist_ok=True)
        
        temp_csv_path = temp_dir / f"temp_{csv_file.filename}"
        with open(temp_csv_path, "wb") as f:
            content = await csv_file.read()
            f.write(content)
        
        # Convert to EPW
        result = nsrdb_wrapper.convert_csv_to_epw(
            str(temp_csv_path),
            location=location,
            state=state,
            country=country,
        )
        
        if result["success"]:
            # Return the EPW file
            epw_path = Path(result["epw_file"])
            return FileResponse(
                epw_path,
                media_type="application/octet-stream",
                filename=epw_path.name
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Conversion failed: {result.get('errors', ['Unknown error'])}"
            )
            
    except Exception as e:
        logging.error(f"CSV to EPW conversion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversion failed: {str(e)}"
        )


@router.get("/wkt-from-point")
async def api_wkt_from_point(lat: float, lon: float, buffer: Optional[float] = 1.0):
    """Generate WKT from lat/lon point with optional buffer."""
    try:
        from ..services.geometry import wkt_from_point_with_buffer
        
        if buffer and buffer > 0:
            wkt = wkt_from_point_with_buffer(lat, lon, buffer)
        else:
            wkt = create_point_wkt(lat, lon)
        
        return {
            "wkt": wkt,
            "lat": lat,
            "lon": lon,
            "buffer": buffer
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error generating WKT: {str(e)}"
        )


@router.get("/validate-wkt")
async def api_validate_wkt(wkt: str):
    """Validate WKT string."""
    is_valid = validate_wkt(wkt)
    return {
        "valid": is_valid,
        "wkt": wkt
    }


@router.get("/datasets")
async def api_get_datasets():
    """Get available datasets and their configurations."""
    return {
        "datasets": settings.dataset_names,
        "intervals": settings.dataset_intervals,
        "years": settings.dataset_years,
    }


@router.get("/download-file/{file_path:path}")
async def download_file(file_path: str):
    """Download a specific file from the outputs directory."""
    try:
        # For server deployment, files are in outputs directory
        if os.environ.get('RENDER') or os.environ.get('RAILWAY') or os.environ.get('HEROKU'):
            # Server environment - look in outputs directory
            full_path = settings.outputs_dir / file_path
        else:
            # Local environment - try multiple possible locations
            possible_paths = [
                settings.outputs_dir / file_path,
                Path.home() / "Downloads" / "OpenWeather" / file_path,
                Path.cwd() / "OpenWeather" / file_path
            ]
            
            # Find the first existing path
            full_path = None
            for path in possible_paths:
                if path.exists():
                    full_path = path
                    break
            
            if not full_path:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found"
                )
        
        # Security check: ensure file is within allowed directories
        allowed_dirs = [
            settings.outputs_dir.resolve(),
            (Path.home() / "Downloads" / "OpenWeather").resolve(),
            (Path.cwd() / "OpenWeather").resolve()
        ]
        
        file_resolved = full_path.resolve()
        is_allowed = any(file_resolved.is_relative_to(allowed_dir) for allowed_dir in allowed_dirs)
        
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        if not full_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        return FileResponse(
            full_path,
            media_type="application/octet-stream",
            filename=full_path.name
        )
        
    except Exception as e:
        logging.error(f"File download failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(e)}"
        )


@router.get("/download-zip/{job_id}")
async def download_zip(job_id: str):
    """Download all files from a job as a zip file."""
    try:
        # Try to find the job directory in multiple locations
        possible_dirs = [
            settings.outputs_dir / job_id,
            Path.home() / "Downloads" / "OpenWeather" / job_id,
            Path.cwd() / "OpenWeather" / job_id,
        ]
        
        job_dir = None
        for dir_path in possible_dirs:
            if dir_path.exists():
                job_dir = dir_path
                break
        
        if not job_dir:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Create a temporary zip file
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
            with zipfile.ZipFile(tmp_file.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add all files from the job directory
                for file_path in job_dir.iterdir():
                    if file_path.is_file():
                        zipf.write(file_path, file_path.name)
            
            # Return the zip file
            return FileResponse(
                tmp_file.name,
                media_type="application/zip",
                filename=f"{job_id}.zip"
            )
        
    except Exception as e:
        logging.error(f"Zip download failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Zip download failed: {str(e)}"
        )


@router.get("/job-summary/{job_name}")
async def get_job_summary(job_name: str):
    """Get summary information about a specific job."""
    try:
        job_dir = settings.outputs_dir / job_name
        if not job_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        summary = storage_service.get_job_summary(job_dir)
        return summary
        
    except Exception as e:
        logging.error(f"Job summary failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summary failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "datasets_available": len(settings.dataset_names)
    }
