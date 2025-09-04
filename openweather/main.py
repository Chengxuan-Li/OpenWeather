"""Main FastAPI application."""

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .config import settings
from .routers import ui, api

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Create FastAPI app
app = FastAPI(
    title="OpenWeather",
    version="0.1.0",
    description="Web interface for NSRDB to EPW pipeline",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = settings.static_dir
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include routers
app.include_router(ui.router, tags=["UI"])
app.include_router(api.router, prefix="/api", tags=["API"])


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint redirects to main page."""
    return ui.index(request)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": "OpenWeather",
        "version": "0.1.0",
        "debug": settings.debug
    }


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors."""
    return HTMLResponse(
        content="""
        <html>
            <head><title>404 - Not Found</title></head>
            <body>
                <h1>404 - Not Found</h1>
                <p>The requested resource was not found.</p>
                <a href="/">Go to Home</a>
            </body>
        </html>
        """,
        status_code=404
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors."""
    return HTMLResponse(
        content="""
        <html>
            <head><title>500 - Internal Server Error</title></head>
            <body>
                <h1>500 - Internal Server Error</h1>
                <p>An internal server error occurred.</p>
                <a href="/">Go to Home</a>
            </body>
        </html>
        """,
        status_code=500
    )


def main():
    """Main entry point for the application."""
    import uvicorn
    
    uvicorn.run(
        "openweather.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
