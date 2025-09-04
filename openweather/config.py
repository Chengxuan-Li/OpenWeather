"""Configuration settings for OpenWeather application."""

from pathlib import Path
from typing import Dict, List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent
    outputs_dir: Path = Field(default=Path(__file__).parent.parent / "outputs", env="OUTPUTS_DIR")
    static_dir: Path = Field(default=Path(__file__).parent / "static", env="STATIC_DIR")
    templates_dir: Path = Field(default=Path(__file__).parent / "templates", env="TEMPLATES_DIR")
    
    # NSRDB API Configuration
    nsrdb_api_base_url: str = Field(default="https://developer.nrel.gov/api/nsrdb/v2/", env="NSRDB_API_BASE_URL")
    
    # Dataset configurations
    dataset_names: Dict[str, str] = {
        'conus': 'nsrdb-GOES-conus-v4-0-0',
        'full-disc': 'nsrdb-GOES-full-disc-v4-0-0', 
        'aggregated': 'nsrdb-GOES-aggregated-v4-0-0',
        'tmy': 'nsrdb-GOES-tmy-v4-0-0'
    }
    
    dataset_intervals: Dict[str, List[str]] = {
        'conus': ['5', '30', '60'],
        'full-disc': ['10', '30', '60'],
        'aggregated': ['30', '60'],
        'tmy': ['60']
    }
    
    dataset_years: Dict[str, List[str]] = {
        'conus': [str(year) for year in range(2021, 2025)],  # 2021-2024
        'full-disc': [str(year) for year in range(2018, 2025)],  # 2018-2024
        'aggregated': [str(year) for year in range(1998, 2025)],  # 1998-2024
        'tmy': [str(year) for year in range(2022, 2025)]  # 2022-2024
    }
    
    # Application settings
    app_name: str = Field(default="OpenWeather", env="APP_NAME")
    app_version: str = Field(default="0.1.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8080, env="PORT")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
