"""Tests for EPW functionality."""

import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path

from openweather.services.storage import StorageService
from openweather.services.nsrdb_wrapper import NSRDBWrapper


class TestStorageService:
    """Test storage service functionality."""
    
    def test_create_job_directory(self):
        """Test job directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageService(Path(temp_dir))
            
            wkt = "POINT(-76.5 42.4)"
            dataset = "test-dataset"
            years = ["2021", "2022"]
            
            job_dir = storage.create_job_directory(wkt, dataset, years)
            
            assert job_dir.exists()
            assert job_dir.is_dir()
            assert "42.4000_-76.5000" in job_dir.name
            assert "test-dataset" in job_dir.name
            assert "2021_2022" in job_dir.name
    
    def test_save_csv_file(self):
        """Test CSV file saving."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageService(Path(temp_dir))
            job_dir = Path(temp_dir) / "test_job"
            job_dir.mkdir()
            
            content = "Year,Month,Day,Temperature\n2021,1,1,20.5"
            filename = "test.csv"
            
            file_path = storage.save_csv_file(job_dir, content, filename)
            
            assert file_path.exists()
            assert file_path.name == filename
            assert file_path.read_text() == content
    
    def test_save_epw_file(self):
        """Test EPW file saving."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageService(Path(temp_dir))
            job_dir = Path(temp_dir) / "test_job"
            job_dir.mkdir()
            
            content = "LOCATION,Test Location,Test State,Test Country\nDATA PERIODS,1,1,Data"
            filename = "test.epw"
            
            file_path = storage.save_epw_file(job_dir, content, filename)
            
            assert file_path.exists()
            assert file_path.name == filename
            assert file_path.read_text() == content
    
    def test_format_file_size(self):
        """Test file size formatting."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageService(Path(temp_dir))
            
            assert storage.format_file_size(0) == "0 B"
            assert storage.format_file_size(1024) == "1.0 KB"
            assert storage.format_file_size(1024 * 1024) == "1.0 MB"
            assert storage.format_file_size(1024 * 1024 * 1024) == "1.0 GB"
    
    def test_get_job_summary(self):
        """Test job summary generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageService(Path(temp_dir))
            job_dir = Path(temp_dir) / "test_job"
            job_dir.mkdir()
            
            # Create test files
            (job_dir / "test1.csv").write_text("test content")
            (job_dir / "test2.epw").write_text("test content")
            
            summary = storage.get_job_summary(job_dir)
            
            assert summary["total_files"] == 2
            assert summary["csv_files"] == 1
            assert summary["epw_files"] == 1
            assert "test_job" in summary["job_name"]


class TestNSRDBWrapper:
    """Test NSRDB wrapper functionality."""
    
    def test_get_dataset_names(self):
        """Test dataset names retrieval."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageService(Path(temp_dir))
            wrapper = NSRDBWrapper(storage)
            
            datasets = wrapper.get_dataset_names()
            
            expected_keys = ['CONUS', 'full-disc', 'TMY', 'aggregated']
            for key in expected_keys:
                assert key in datasets
    
    def test_validate_inputs(self):
        """Test input validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageService(Path(temp_dir))
            wrapper = NSRDBWrapper(storage)
            
            # Test valid inputs
            errors = wrapper.validate_inputs(
                wkt="POINT(-76.5 42.4)",
                dataset="nsrdb-GOES-full-disc-v4-0-0",
                interval="60",
                years=["2021"],
                api_key="test-key",
                email="test@example.com"
            )
            assert len(errors) == 0
            
            # Test invalid WKT
            errors = wrapper.validate_inputs(
                wkt="INVALID",
                dataset="nsrdb-GOES-full-disc-v4-0-0",
                interval="60",
                years=["2021"],
                api_key="test-key",
                email="test@example.com"
            )
            assert len(errors) > 0
            assert any("WKT" in error for error in errors)
            
            # Test invalid dataset
            errors = wrapper.validate_inputs(
                wkt="POINT(-76.5 42.4)",
                dataset="invalid-dataset",
                interval="60",
                years=["2021"],
                api_key="test-key",
                email="test@example.com"
            )
            assert len(errors) > 0
            assert any("dataset" in error.lower() for error in errors)
            
            # Test invalid interval
            errors = wrapper.validate_inputs(
                wkt="POINT(-76.5 42.4)",
                dataset="nsrdb-GOES-full-disc-v4-0-0",
                interval="invalid",
                years=["2021"],
                api_key="test-key",
                email="test@example.com"
            )
            assert len(errors) > 0
            assert any("interval" in error.lower() for error in errors)
            
            # Test invalid years
            errors = wrapper.validate_inputs(
                wkt="POINT(-76.5 42.4)",
                dataset="nsrdb-GOES-full-disc-v4-0-0",
                interval="60",
                years=["invalid"],
                api_key="test-key",
                email="test@example.com"
            )
            assert len(errors) > 0
            assert any("year" in error.lower() for error in errors)
            
            # Test missing API key
            errors = wrapper.validate_inputs(
                wkt="POINT(-76.5 42.4)",
                dataset="nsrdb-GOES-full-disc-v4-0-0",
                interval="60",
                years=["2021"],
                api_key="",
                email="test@example.com"
            )
            assert len(errors) > 0
            assert any("API key" in error for error in errors)
            
            # Test invalid email
            errors = wrapper.validate_inputs(
                wkt="POINT(-76.5 42.4)",
                dataset="nsrdb-GOES-full-disc-v4-0-0",
                interval="60",
                years=["2021"],
                api_key="test-key",
                email="invalid-email"
            )
            assert len(errors) > 0
            assert any("email" in error.lower() for error in errors)


class TestEPWConversion:
    """Test EPW conversion functionality."""
    
    def test_convert_csv_to_epw_missing_file(self):
        """Test CSV to EPW conversion with missing file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageService(Path(temp_dir))
            wrapper = NSRDBWrapper(storage)
            
            result = wrapper.convert_csv_to_epw(
                csv_file_path="nonexistent.csv",
                location="Test",
                state="Test",
                country="Test"
            )
            
            assert result["success"] is False
            assert "not found" in result["errors"][0].lower()


class TestGeometryValidation:
    """Test geometry validation functionality."""
    
    def test_validate_wkt_valid(self):
        """Test WKT validation with valid geometries."""
        from openweather.services.geometry import validate_wkt
        
        valid_wkts = [
            "POINT(-76.5 42.4)",
            "POLYGON((-76.5 42.4, -76.4 42.4, -76.4 42.5, -76.5 42.5, -76.5 42.4))",
            "MULTIPOLYGON(((-76.5 42.4, -76.4 42.4, -76.4 42.5, -76.5 42.5, -76.5 42.4)))"
        ]
        
        for wkt in valid_wkts:
            assert validate_wkt(wkt) is True
    
    def test_validate_wkt_invalid(self):
        """Test WKT validation with invalid geometries."""
        from openweather.services.geometry import validate_wkt
        
        invalid_wkts = [
            "",
            "INVALID",
            "POINT(invalid invalid)",
            "POLYGON(invalid)"
        ]
        
        for wkt in invalid_wkts:
            assert validate_wkt(wkt) is False
    
    def test_create_point_wkt(self):
        """Test point WKT creation."""
        from openweather.services.geometry import create_point_wkt
        
        lat, lon = 42.4, -76.5
        wkt = create_point_wkt(lat, lon)
        
        assert "POINT" in wkt
        assert str(lon) in wkt
        assert str(lat) in wkt
    
    def test_parse_point_from_wkt(self):
        """Test point parsing from WKT."""
        from openweather.services.geometry import parse_point_from_wkt
        
        wkt = "POINT(-76.5 42.4)"
        coords = parse_point_from_wkt(wkt)
        
        assert coords is not None
        assert coords[0] == 42.4  # lat
        assert coords[1] == -76.5  # lon


if __name__ == "__main__":
    pytest.main([__file__])
