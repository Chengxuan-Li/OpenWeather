"""Tests for the OpenWeather API endpoints."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from openweather.main import app

client = TestClient(app)


class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_health_check(self):
        """Test that health check returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestDatasets:
    """Test dataset endpoints."""
    
    def test_get_datasets(self):
        """Test that datasets endpoint returns available datasets."""
        response = client.get("/datasets")
        assert response.status_code == 200
        data = response.json()
        assert "datasets" in data
        assert "intervals" in data
        assert "years" in data
        
        # Check that expected datasets are present
        expected_datasets = ["conus", "full-disc", "tmy", "aggregated"]
        for dataset in expected_datasets:
            assert dataset in data["datasets"]


class TestWKTValidation:
    """Test WKT validation endpoints."""
    
    def test_validate_wkt_valid_point(self):
        """Test WKT validation with valid point."""
        wkt = "POINT(-76.5 42.4)"
        response = client.get(f"/validate-wkt?wkt={wkt}")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["wkt"] == wkt
    
    def test_validate_wkt_invalid(self):
        """Test WKT validation with invalid WKT."""
        wkt = "INVALID"
        response = client.get(f"/validate-wkt?wkt={wkt}")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["wkt"] == wkt
    
    def test_wkt_from_point(self):
        """Test WKT generation from lat/lon."""
        lat = 42.4
        lon = -76.5
        response = client.get(f"/wkt-from-point?lat={lat}&lon={lon}")
        assert response.status_code == 200
        data = response.json()
        assert "wkt" in data
        assert data["lat"] == lat
        assert data["lon"] == lon


class TestAPIEndpoints:
    """Test API endpoints."""
    
    def test_api_health(self):
        """Test API health endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_api_datasets(self):
        """Test API datasets endpoint."""
        response = client.get("/api/datasets")
        assert response.status_code == 200
        data = response.json()
        assert "datasets" in data
    
    def test_api_validate_wkt(self):
        """Test API WKT validation endpoint."""
        wkt = "POINT(-76.5 42.4)"
        response = client.get(f"/api/validate-wkt?wkt={wkt}")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
    
    def test_api_wkt_from_point(self):
        """Test API WKT generation endpoint."""
        lat = 42.4
        lon = -76.5
        response = client.get(f"/api/wkt-from-point?lat={lat}&lon={lon}")
        assert response.status_code == 200
        data = response.json()
        assert "wkt" in data


class TestUIEndpoints:
    """Test UI endpoints."""
    
    def test_index_page(self):
        """Test that index page loads."""
        response = client.get("/")
        assert response.status_code == 200
        assert "OpenWeather" in response.text
    
    def test_query_interface_partial_params(self):
        """Test query interface with partial parameters."""
        response = client.get("/q?wkt=POINT(-76.5 42.4)")
        assert response.status_code == 200
        assert "OpenWeather" in response.text
    
    def test_query_interface_all_params(self):
        """Test query interface with all parameters (should fail without valid API key)."""
        params = {
            "wkt": "POINT(-76.5 42.4)",
            "dataset": "nsrdb-GOES-full-disc-v4-0-0",
            "interval": "60",
            "years": "2021",
            "api_key": "INVALID_KEY",
            "email": "test@example.com"
        }
        response = client.get("/q", params=params)
        assert response.status_code == 200
        # Should show error page since API key is invalid
        assert "error" in response.text.lower() or "invalid" in response.text.lower()


class TestFormSubmission:
    """Test form submission."""
    
    def test_form_submission_invalid(self):
        """Test form submission with invalid data."""
        form_data = {
            "wkt": "INVALID",
            "dataset": "invalid-dataset",
            "interval": "invalid",
            "years": "invalid",
            "api_key": "",
            "email": "invalid-email"
        }
        response = client.post("/run", data=form_data)
        assert response.status_code == 200
        # Should show error page
        assert "error" in response.text.lower()


class TestFileEndpoints:
    """Test file download endpoints."""
    
    def test_download_nonexistent_file(self):
        """Test downloading a file that doesn't exist."""
        response = client.get("/api/download-file/nonexistent/file.csv")
        assert response.status_code == 404
    
    def test_download_file_path_traversal(self):
        """Test that path traversal is prevented."""
        response = client.get("/api/download-file/../../../etc/passwd")
        assert response.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__])
