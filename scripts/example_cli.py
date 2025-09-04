#!/usr/bin/env python3
"""
Example CLI script demonstrating the NSRDB wrapper functionality.

This script shows how to use the NSRDB wrapper programmatically,
replicating the workflow from NSRDB2EPW.ipynb.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from openweather.services.storage import StorageService
from openweather.services.nsrdb_wrapper import NSRDBWrapper


def main():
    """Main function demonstrating NSRDB wrapper usage."""
    
    print("🌤️  OpenWeather NSRDB Wrapper Example")
    print("=" * 50)
    
    # Initialize services
    storage_service = StorageService(Path("outputs"))
    nsrdb_wrapper = NSRDBWrapper(storage_service)
    
    # Example parameters (replicating the notebook)
    wkt = "POINT(-157.85894101843428 21.312174388689833)"  # Honolulu
    dataset = "nsrdb-GOES-aggregated-v4-0-0"
    interval = "60"
    years = ["2021", "2022"]  # Example years
    api_key = "YOUR_API_KEY_HERE"  # Replace with your actual API key
    email = "example@email.com"
    location = "Honolulu"
    state = "HI"
    country = "United States"
    
    print(f"📍 Location: {location}, {state}, {country}")
    print(f"🗺️  WKT: {wkt}")
    print(f"📊 Dataset: {dataset}")
    print(f"⏱️  Interval: {interval} minutes")
    print(f"📅 Years: {', '.join(years)}")
    print()
    
    # Check if API key is provided
    if api_key == "YOUR_API_KEY_HERE":
        print("❌ Please replace 'YOUR_API_KEY_HERE' with your actual NSRDB API key")
        print("   Get your API key from: https://developer.nrel.gov/signup/")
        return
    
    print("🚀 Starting NSRDB job...")
    print()
    
    try:
        # Run the NSRDB job (replicating notebook workflow)
        result = nsrdb_wrapper.run_nsrdb_job(
            wkt=wkt,
            dataset=dataset,
            interval=interval,
            years=years,
            api_key=api_key,
            email=email,
            location=location,
            state=state,
            country=country,
            convert_to_epw=True,
        )
        
        if result["success"]:
            print("✅ Job completed successfully!")
            print()
            
            # Display results
            print("📁 Generated Files:")
            if result.get("files"):
                csv_files = result["files"].get("csv", [])
                epw_files = result["files"].get("epw", [])
                
                if csv_files:
                    print(f"  📊 CSV Files ({len(csv_files)}):")
                    for csv_file in csv_files:
                        print(f"    - {Path(csv_file).name}")
                
                if epw_files:
                    print(f"  🌤️ EPW Files ({len(epw_files)}):")
                    for epw_file in epw_files:
                        print(f"    - {Path(epw_file).name}")
            
            # Display job summary
            if result.get("summary"):
                summary = result["summary"]
                print()
                print("📋 Job Summary:")
                print(f"  📁 Job Directory: {summary.get('job_name', 'N/A')}")
                print(f"  📊 Total Files: {summary.get('total_files', 0)}")
                print(f"  💾 Total Size: {summary.get('total_size_formatted', 'N/A')}")
                print(f"  🕒 Created: {summary.get('created', 'N/A')}")
            
            # Display logs
            if result.get("logs"):
                print()
                print("📝 Job Logs:")
                for log in result["logs"]:
                    print(f"  {log}")
        
        else:
            print("❌ Job failed!")
            if result.get("errors"):
                print("Errors:")
                for error in result["errors"]:
                    print(f"  - {error}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Please check your API key and try again.")


def show_available_datasets():
    """Show available datasets and their configurations."""
    print("📚 Available Datasets:")
    print("=" * 30)
    
    storage_service = StorageService(Path("outputs"))
    nsrdb_wrapper = NSRDBWrapper(storage_service)
    
    datasets = nsrdb_wrapper.get_dataset_names()
    
    for key, value in datasets.items():
        print(f"  {key.upper()}: {value}")
    
    print()
    print("📊 Dataset Coverage:")
    print("  CONUS: USA Continental and Mexico (2021-2023)")
    print("  Full-disc: USA and Americas (2018-2023)")
    print("  Aggregated: USA and Americas (1998-2023)")
    print("  TMY: USA and Americas (2022-2023)")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--datasets":
        show_available_datasets()
    else:
        main()
