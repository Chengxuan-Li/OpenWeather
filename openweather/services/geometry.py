"""Geometry utilities for WKT handling and validation."""

import re
from typing import Optional, Tuple

from shapely.geometry import Point, Polygon, MultiPolygon, shape
from shapely.wkt import loads
from shapely.errors import ShapelyError


def validate_wkt(wkt: str) -> bool:
    """Validate WKT string format."""
    if not wkt or not isinstance(wkt, str):
        return False
    
    try:
        geom = loads(wkt)
        return geom.is_valid
    except (ShapelyError, ValueError):
        return False


def parse_point_from_wkt(wkt: str) -> Optional[Tuple[float, float]]:
    """Extract lat/lon from WKT point string."""
    if not validate_wkt(wkt):
        return None
    
    try:
        geom = loads(wkt)
        if isinstance(geom, Point):
            return (geom.y, geom.x)  # lat, lon
        elif isinstance(geom, (Polygon, MultiPolygon)):
            # Return centroid for polygons
            centroid = geom.centroid
            return (centroid.y, centroid.x)  # lat, lon
        return None
    except Exception:
        return None


def create_point_wkt(lat: float, lon: float) -> str:
    """Create WKT point string from lat/lon."""
    point = Point(lon, lat)  # WKT uses (lon, lat) order
    return point.wkt


def create_polygon_wkt(coordinates: list[Tuple[float, float]]) -> str:
    """Create WKT polygon string from list of (lat, lon) coordinates."""
    # Convert to (lon, lat) for WKT
    wkt_coords = [(lon, lat) for lat, lon in coordinates]
    polygon = Polygon(wkt_coords)
    return polygon.wkt


def wkt_from_point_with_buffer(lat: float, lon: float, buffer_km: float = 1.0) -> str:
    """Create WKT polygon from point with buffer radius."""
    point = Point(lon, lat)
    # Convert km to degrees (approximate)
    buffer_degrees = buffer_km / 111.0
    buffered = point.buffer(buffer_degrees)
    return buffered.wkt


def extract_coordinates_from_wkt(wkt: str) -> Optional[list[Tuple[float, float]]]:
    """Extract coordinates from WKT string."""
    if not validate_wkt(wkt):
        return None
    
    try:
        geom = loads(wkt)
        if isinstance(geom, Point):
            return [(geom.y, geom.x)]  # lat, lon
        elif isinstance(geom, Polygon):
            coords = list(geom.exterior.coords)
            return [(lat, lon) for lon, lat in coords]  # Convert to lat, lon
        elif isinstance(geom, MultiPolygon):
            coords = []
            for poly in geom.geoms:
                coords.extend([(lat, lon) for lon, lat in poly.exterior.coords])
            return coords
        return None
    except Exception:
        return None


def is_valid_lat_lon(lat: float, lon: float) -> bool:
    """Validate latitude and longitude values."""
    return -90 <= lat <= 90 and -180 <= lon <= 180


def parse_lat_lon_string(lat_lon_str: str) -> Optional[Tuple[float, float]]:
    """Parse lat,lon string into tuple."""
    try:
        # Handle various formats: "lat,lon", "lat, lon", "lat;lon", etc.
        parts = re.split(r'[,;\s]+', lat_lon_str.strip())
        if len(parts) != 2:
            return None
        
        lat = float(parts[0])
        lon = float(parts[1])
        
        if not is_valid_lat_lon(lat, lon):
            return None
        
        return (lat, lon)
    except (ValueError, IndexError):
        return None
