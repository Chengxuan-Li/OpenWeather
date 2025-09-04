"""Dependency injection for OpenWeather application."""

from fastapi import Depends
from typing import Generator

from .config import settings
from .services.storage import StorageService
from .services.nsrdb_wrapper import NSRDBWrapper


def get_settings():
    """Get application settings."""
    return settings


def get_storage_service() -> StorageService:
    """Get storage service instance."""
    return StorageService(settings.outputs_dir)


def get_nsrdb_wrapper() -> NSRDBWrapper:
    """Get NSRDB wrapper instance."""
    storage_service = get_storage_service()
    return NSRDBWrapper(storage_service)
