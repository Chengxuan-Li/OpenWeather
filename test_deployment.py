#!/usr/bin/env python3
"""
Test script to verify the application works without pyproject.toml
"""

import sys
import subprocess
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import fastapi
        print("✅ fastapi imported successfully")
    except ImportError as e:
        print(f"❌ fastapi import failed: {e}")
        return False
    
    try:
        import uvicorn
        print("✅ uvicorn imported successfully")
    except ImportError as e:
        print(f"❌ uvicorn import failed: {e}")
        return False
    
    try:
        import jinja2
        print("✅ jinja2 imported successfully")
    except ImportError as e:
        print(f"❌ jinja2 import failed: {e}")
        return False
    
    try:
        import pydantic
        print("✅ pydantic imported successfully")
    except ImportError as e:
        print(f"❌ pydantic import failed: {e}")
        return False
    
    try:
        import pandas
        print("✅ pandas imported successfully")
    except ImportError as e:
        print(f"❌ pandas import failed: {e}")
        return False
    
    try:
        import numpy
        print("✅ numpy imported successfully")
    except ImportError as e:
        print(f"❌ numpy import failed: {e}")
        return False
    
    try:
        import shapely
        print("✅ shapely imported successfully")
    except ImportError as e:
        print(f"❌ shapely import failed: {e}")
        return False
    
    return True

def test_app_import():
    """Test that the openweather app can be imported"""
    print("\nTesting app import...")
    
    try:
        from openweather.main import app
        print("✅ openweather.main.app imported successfully")
        return True
    except ImportError as e:
        print(f"❌ openweather.main.app import failed: {e}")
        return False

def test_requirements():
    """Test that requirements.txt can be installed"""
    print("\nTesting requirements.txt...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--dry-run"
        ], capture_output=True, text=True, check=True)
        print("✅ requirements.txt install test passed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ requirements.txt install test failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing deployment configuration...")
    print("=" * 50)
    
    # Check if pyproject.toml is removed
    if Path("pyproject.toml").exists():
        print("❌ pyproject.toml still exists - this may cause issues")
    else:
        print("✅ pyproject.toml removed (good for deployment)")
    
    # Check if requirements.txt exists
    if Path("requirements.txt").exists():
        print("✅ requirements.txt exists")
    else:
        print("❌ requirements.txt missing")
        return False
    
    # Run tests
    tests = [
        test_requirements,
        test_imports,
        test_app_import,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready for deployment.")
        return True
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
