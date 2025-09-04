"""UI router for web interface and form handling."""

import logging
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Request, Form, Query, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from ..config import settings
from ..services.nsrdb_wrapper import NSRDBWrapper
from ..services.storage import StorageService
from ..services.geometry import validate_wkt, create_point_wkt, parse_lat_lon_string

# Initialize services
storage_service = StorageService(settings.outputs_dir)
nsrdb_wrapper = NSRDBWrapper(storage_service)

# Initialize templates
templates = Jinja2Templates(directory=str(settings.templates_dir))

# Initialize router
router = APIRouter()


class JobRequest(BaseModel):
    """Job request model."""
    wkt: str
    dataset: str
    interval: str
    years: str  # Comma-separated years
    api_key: str
    email: str
    location: Optional[str] = "Unknown"
    state: Optional[str] = "Unknown"
    country: Optional[str] = "Unknown"
    convert_to_epw: bool = True


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main page with form and map."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "datasets": settings.dataset_names,
            "dataset_intervals": settings.dataset_intervals,
            "dataset_years": settings.dataset_years,
        }
    )


@router.get("/q", response_class=HTMLResponse)
async def query_interface(
    request: Request,
    wkt: Optional[str] = Query(None),
    dataset: Optional[str] = Query(None),
    interval: Optional[str] = Query(None),
    years: Optional[str] = Query(None),
    api_key: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    as_epw: Optional[bool] = Query(False),
):
    """
    Query interface that accepts URL parameters.
    
    If all required parameters are present, runs the job.
    If partial parameters are present, pre-fills the form.
    """
    # Check if we have all required parameters to run a job
    required_params = [wkt, dataset, interval, years, api_key, email]
    has_all_params = all(param is not None and param.strip() for param in required_params)
    
    if has_all_params:
        # Run the job
        try:
            # Parse years
            year_list = [y.strip() for y in years.split(",") if y.strip()]
            
            # Run NSRDB job
            result = nsrdb_wrapper.run_nsrdb_job(
                wkt=wkt,
                dataset=dataset,
                interval=interval,
                years=year_list,
                api_key=api_key,
                email=email,
                location=location or "Unknown",
                state=state or "Unknown",
                country=country or "Unknown",
                convert_to_epw=as_epw,
            )
            
            if result["success"]:
                return templates.TemplateResponse(
                    "results.html",
                    {
                        "request": request,
                        "result": result,
                        "job_summary": result.get("summary", {}),
                    }
                )
            else:
                return templates.TemplateResponse(
                    "error.html",
                    {
                        "request": request,
                        "errors": result.get("errors", ["Unknown error"]),
                        "datasets": settings.dataset_names,
                        "dataset_intervals": settings.dataset_intervals,
                        "dataset_years": settings.dataset_years,
                        "form_data": {
                            "wkt": wkt,
                            "dataset": dataset,
                            "interval": interval,
                            "years": years,
                            "api_key": api_key,
                            "email": email,
                            "location": location,
                            "state": state,
                            "country": country,
                            "convert_to_epw": as_epw,
                        }
                    }
                )
                
        except Exception as e:
            logging.error(f"Error running job: {e}")
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "errors": [str(e)],
                    "datasets": settings.dataset_names,
                    "dataset_intervals": settings.dataset_intervals,
                    "dataset_years": settings.dataset_years,
                    "form_data": {
                        "wkt": wkt,
                        "dataset": dataset,
                        "interval": interval,
                        "years": years,
                        "api_key": api_key,
                        "email": email,
                        "location": location,
                        "state": state,
                        "country": country,
                        "convert_to_epw": as_epw,
                    }
                }
            )
    
    # Pre-fill form with provided parameters
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "datasets": settings.dataset_names,
            "dataset_intervals": settings.dataset_intervals,
            "dataset_years": settings.dataset_years,
            "form_data": {
                "wkt": wkt or "",
                "dataset": dataset or "",
                "interval": interval or "",
                "years": years or "",
                "api_key": api_key or "",
                "email": email or "",
                "location": location or "",
                "state": state or "",
                "country": country or "",
                "convert_to_epw": as_epw,
            }
        }
    )


@router.post("/run", response_class=HTMLResponse)
async def run_job(
    request: Request,
    wkt: str = Form(...),
    dataset: str = Form(...),
    interval: str = Form(...),
    years: list = Form(...),
    api_key: str = Form(...),
    email: str = Form(...),
    location: str = Form("Unknown"),
    state: str = Form("Unknown"),
    country: str = Form("Unknown"),
    convert_to_epw: bool = Form(True),
):
    """Handle form submission and run NSRDB job."""
    try:
        # Parse years (handle both list and comma-separated string)
        if isinstance(years, list):
            year_list = [y.strip() for y in years if y.strip()]
        else:
            year_list = [y.strip() for y in years.split(",") if y.strip()]
        
        # Run NSRDB job
        result = nsrdb_wrapper.run_nsrdb_job(
            wkt=wkt,
            dataset=dataset,
            interval=interval,
            years=year_list,
            api_key=api_key,
            email=email,
            location=location,
            state=state,
            country=country,
            convert_to_epw=convert_to_epw,
        )
        
        if result["success"]:
            return templates.TemplateResponse(
                "results.html",
                {
                    "request": request,
                    "result": result,
                    "job_summary": result.get("summary", {}),
                }
            )
        else:
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "errors": result.get("errors", ["Unknown error"]),
                    "datasets": settings.dataset_names,
                    "dataset_intervals": settings.dataset_intervals,
                    "dataset_years": settings.dataset_years,
                    "form_data": {
                        "wkt": wkt,
                        "dataset": dataset,
                        "interval": interval,
                        "years": ",".join(years) if isinstance(years, list) else years,
                        "api_key": api_key,
                        "email": email,
                        "location": location,
                        "state": state,
                        "country": country,
                        "convert_to_epw": convert_to_epw,
                    }
                }
            )
            
    except Exception as e:
        logging.error(f"Error running job: {e}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "errors": [str(e)],
                "datasets": settings.dataset_names,
                "dataset_intervals": settings.dataset_intervals,
                "dataset_years": settings.dataset_years,
                "form_data": {
                    "wkt": wkt,
                    "dataset": dataset,
                    "interval": interval,
                    "years": ",".join(years) if isinstance(years, list) else years,
                    "api_key": api_key,
                    "email": email,
                    "location": location,
                    "state": state,
                    "country": country,
                    "convert_to_epw": convert_to_epw,
                }
            }
        )


@router.get("/wkt-from-point")
async def wkt_from_point(
    lat: float = Query(...),
    lon: float = Query(...),
    buffer: Optional[float] = Query(1.0),
):
    """Generate WKT from lat/lon point with optional buffer."""
    try:
        from ..services.geometry import wkt_from_point_with_buffer
        
        if buffer and buffer > 0:
            wkt = wkt_from_point_with_buffer(lat, lon, buffer)
        else:
            wkt = create_point_wkt(lat, lon)
        
        return {"wkt": wkt, "lat": lat, "lon": lon, "buffer": buffer}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error generating WKT: {str(e)}"
        )


@router.get("/validate-wkt")
async def validate_wkt_endpoint(wkt: str = Query(...)):
    """Validate WKT string."""
    is_valid = validate_wkt(wkt)
    return {"valid": is_valid, "wkt": wkt}


@router.get("/datasets")
async def get_datasets():
    """Get available datasets and their configurations."""
    return {
        "datasets": settings.dataset_names,
        "intervals": settings.dataset_intervals,
        "years": settings.dataset_years,
    }
