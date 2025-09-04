"""UI router for web interface."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import os

from fastapi import APIRouter, Request, HTTPException, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ..config import settings
from ..services.nsrdb_wrapper import NSRDBWrapper
from ..services.storage import StorageService, sanitize_location_name
from ..services.progress import progress_manager

# Initialize services
storage_service = StorageService(settings.outputs_dir)
nsrdb_wrapper = NSRDBWrapper(storage_service)

# Initialize router
router = APIRouter()

# Templates
templates = Jinja2Templates(directory=settings.templates_dir)


def get_storage_service() -> StorageService:
    """Dependency to get storage service."""
    return storage_service


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


def extract_download_path(file_path: str) -> str:
    """Extract the correct download path for a file."""
    # For server deployment, files are in outputs directory
    if os.environ.get('RENDER') or os.environ.get('RAILWAY') or os.environ.get('HEROKU'):
        # Server environment - use job_name/filename format
        path_parts = Path(file_path).parts
        if len(path_parts) >= 2:
            return f"{path_parts[-2]}/{path_parts[-1]}"
        else:
            return path_parts[-1] if path_parts else ""
    else:
        # Local environment - use the original path format
        path_parts = Path(file_path).parts
        if len(path_parts) >= 2:
            return f"{path_parts[-2]}/{path_parts[-1]}"
        else:
            return path_parts[-1] if path_parts else ""


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main page with form."""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "datasets": settings.dataset_names,
        "dataset_intervals": settings.dataset_intervals,
        "dataset_years": settings.dataset_years,
    })


@router.get("/q", response_class=HTMLResponse)
async def query_interface(
    request: Request,
    wkt: Optional[str] = None,
    dataset: Optional[str] = None,
    interval: Optional[str] = None,
    years: Optional[str] = None,
    api_key: Optional[str] = None,
    email: Optional[str] = None,
    location: Optional[str] = None,
    state: Optional[str] = None,
    country: Optional[str] = None,
    convert_to_epw: Optional[str] = None,
):
    """Query interface - pre-fill form or run job."""
    
    # Pre-fill form with query parameters
    form_data = {
        "wkt": wkt or "",
        "dataset": dataset or "",
        "interval": interval or "",
        "years": years or "",
        "api_key": api_key or "",
        "email": email or "",
        "location": location or "",
        "state": state or "",
        "country": country or "",
        "convert_to_epw": convert_to_epw == "true",
    }
    
    # If all required parameters are present, run the job
    required_params = ["wkt", "dataset", "interval", "years", "api_key", "email"]
    if all(form_data.get(param) for param in required_params):
        try:
            # Parse years string to list
            years_list = [y.strip() for y in form_data["years"].split(",")]
            
            # Handle secret API key
            api_key = form_data["api_key"]
            if api_key.lower() == "eslab":
                secret_key = get_secret_api_key()
                if secret_key:
                    api_key = secret_key
                else:
                    return templates.TemplateResponse("error.html", {
                        "request": request,
                        "error": "Secret API key not found",
                        "details": ["Please check your configuration."],
                        "datasets": settings.dataset_names,
                        "dataset_intervals": settings.dataset_intervals,
                        "dataset_years": settings.dataset_years,
                    })
            
            result = nsrdb_wrapper.run_nsrdb_job(
                wkt=form_data["wkt"],
                dataset=form_data["dataset"],
                interval=form_data["interval"],
                years=years_list,
                api_key=api_key,
                email=form_data["email"],
                location=form_data["location"],
                state=form_data["state"],
                country=form_data["country"],
                convert_to_epw=form_data["convert_to_epw"],
            )
            
            if result["success"]:
                return RedirectResponse(url=f"/results/{result['job_id']}", status_code=302)
            else:
                return templates.TemplateResponse("error.html", {
                    "request": request,
                    "error": "Job failed",
                    "details": result.get("errors", ["Unknown error"]),
                    "datasets": settings.dataset_names,
                    "dataset_intervals": settings.dataset_intervals,
                    "dataset_years": settings.dataset_years,
                })
                
        except Exception as e:
            logging.error(f"Query interface error: {e}")
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": "An error occurred",
                "details": [str(e)],
                "datasets": settings.dataset_names,
                "dataset_intervals": settings.dataset_intervals,
                "dataset_years": settings.dataset_years,
            })
    
    # Otherwise, show form with pre-filled values
    return templates.TemplateResponse("index.html", {
        "request": request,
        "form_data": form_data,
        "datasets": settings.dataset_names,
        "dataset_intervals": settings.dataset_intervals,
        "dataset_years": settings.dataset_years,
    })


@router.post("/run")
async def run_job(
    request: Request,
    wkt: str = Form(...),
    dataset: str = Form(...),
    interval: str = Form(...),
    years: str = Form(...),
    api_key: str = Form(...),
    email: str = Form(...),
    location: str = Form(""),
    state: str = Form(""),
    country: str = Form(""),
    convert_to_epw: bool = Form(True),
    storage_service: StorageService = Depends(get_storage_service),
):
    """Run NSRDB job and return results."""
    try:
        # Parse years string to list
        years_list = [y.strip() for y in years.split(",")]
        
        # Sanitize location names
        safe_location = sanitize_location_name(location)
        safe_state = sanitize_location_name(state)
        safe_country = sanitize_location_name(country)
        
        # Handle secret API key
        if api_key.lower() == "eslab":
            secret_key = get_secret_api_key()
            if secret_key:
                api_key = secret_key
            else:
                return {
                    "success": False,
                    "errors": ["Secret API key not found. Please check your configuration."]
                }
        
        # Create job directory
        job_dir = storage_service.create_job_directory(
            wkt=wkt,
            dataset=dataset,
            years=years_list,
            location=safe_location,
            state=safe_state,
            country=safe_country,
        )
        
        # Get job ID for progress tracking
        job_id = job_dir.name
        
        # Run the job in background thread
        import threading
        
        def run_job_in_background():
            try:
                nsrdb_wrapper.run_nsrdb_job(
                    wkt=wkt,
                    dataset=dataset,
                    interval=interval,
                    years=years_list,
                    api_key=api_key,
                    email=email,
                    location=safe_location,
                    state=safe_state,
                    country=safe_country,
                    convert_to_epw=convert_to_epw,
                )
            except Exception as e:
                logging.error(f"Background job error: {e}")
                progress_manager.fail_job(job_id, str(e))
        
        # Start background thread
        thread = threading.Thread(target=run_job_in_background)
        thread.daemon = True
        thread.start()
        
        # Return immediately with job ID for progress tracking
        return {
            "success": True,
            "job_id": job_id,
            "message": "Job started in background"
        }
        
    except Exception as e:
        logging.error(f"Run job error: {e}")
        return {
            "success": False,
            "errors": [str(e)]
        }


@router.get("/results/{job_id}", response_class=HTMLResponse)
async def view_results(request: Request, job_id: str):
    """View results for a specific job."""
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
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get job summary
        summary = storage_service.get_job_summary(job_dir)
        
        # Prepare file paths for download
        if summary.get("files"):
            for file_info in summary["files"]:
                file_path = job_dir / file_info["name"]
                file_info["download_path"] = extract_download_path(str(file_path))
        
        return templates.TemplateResponse("results.html", {
            "request": request,
            "result": {
                "success": True,
                "job_id": job_id,
                "job_dir": str(job_dir),
                "summary": summary,
                "files": {
                    "csv": [str(job_dir / f["name"]) for f in summary.get("files", []) if f["type"] == ".csv"],
                    "epw": [str(job_dir / f["name"]) for f in summary.get("files", []) if f["type"] == ".epw"],
                },
                "logs": summary.get("logs", []),
            }
        })
        
    except Exception as e:
        logging.error(f"View results error: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Error loading results",
            "details": [str(e)],
            "datasets": settings.dataset_names,
            "dataset_intervals": settings.dataset_intervals,
            "dataset_years": settings.dataset_years,
        })


@router.get("/error", response_class=HTMLResponse)
async def error_page(request: Request, error: str = "An error occurred", details: str = ""):
    """Error page."""
    return templates.TemplateResponse("error.html", {
        "request": request,
        "error": error,
        "details": [details] if details else [],
        "datasets": settings.dataset_names,
        "dataset_intervals": settings.dataset_intervals,
        "dataset_years": settings.dataset_years,
    })
