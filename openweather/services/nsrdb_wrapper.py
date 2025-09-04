"""NSRDB wrapper service for calling the imported nsrdb2epw functionality."""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Add the imported directory to the path so we can import nsrdb2epw
imported_path = Path(__file__).parent.parent.parent / "imported"
sys.path.insert(0, str(imported_path))

try:
    import nsrdb2epw
    import epw
except ImportError as e:
    logging.error(f"Failed to import nsrdb2epw: {e}")
    raise

from .storage import StorageService
from .geometry import validate_wkt
from .progress import progress_manager


class NSRDBWrapper:
    """Wrapper for NSRDB to EPW pipeline functionality."""
    
    def __init__(self, storage_service: StorageService):
        self.storage = storage_service
        self.logger = logging.getLogger(__name__)
    
    def get_dataset_names(self) -> Dict[str, str]:
        """Get available dataset names."""
        return nsrdb2epw.get_dataset_names()
    
    def validate_inputs(
        self,
        wkt: str,
        dataset: str,
        interval: str,
        years: List[str],
        api_key: str,
        email: str,
    ) -> List[str]:
        """Validate all inputs and return list of errors."""
        errors = []
        
        # Validate WKT
        if not wkt or not validate_wkt(wkt):
            errors.append("Invalid WKT geometry string")
        
        # Validate dataset
        dataset_names = self.get_dataset_names()
        if dataset not in dataset_names.values():
            errors.append(f"Invalid dataset. Must be one of: {list(dataset_names.keys())}")
        
        # Validate interval
        if not interval or not interval.isdigit():
            errors.append("Interval must be a positive integer")
        
        # Validate years
        if not years:
            errors.append("At least one year must be specified")
        else:
            for year in years:
                if not year.isdigit() or len(year) != 4:
                    errors.append(f"Invalid year format: {year}")
        
        # Validate API key
        if not api_key or len(api_key.strip()) == 0:
            errors.append("API key is required")
        
        # Validate email
        if not email or '@' not in email:
            errors.append("Valid email address is required")
        
        return errors
    
    def _convert_dataset_to_short_name(self, dataset: str) -> str:
        """Convert full dataset name to short name for nsrdb2epw function."""
        dataset_names = self.get_dataset_names()
        # Find the key (short name) for the given value (full name)
        for short_name, full_name in dataset_names.items():
            if full_name == dataset:
                return short_name
        # If not found, return the original (assuming it's already a short name)
        return dataset
    
    def run_nsrdb_job(
        self,
        wkt: str,
        dataset: str,
        interval: str,
        years: List[str],
        api_key: str,
        email: str,
        location: str = "Unknown",
        state: str = "Unknown",
        country: str = "Unknown",
        convert_to_epw: bool = True,
    ) -> Dict[str, Any]:
        """
        Run NSRDB job and return results.
        
        This replicates the workflow from NSRDB2EPW.ipynb:
        - Validates inputs
        - Creates job directory
        - Calls nsrdb2epw.nsrdb2epw
        - Returns file paths and logs
        """
        try:
            # Validate inputs
            errors = self.validate_inputs(wkt, dataset, interval, years, api_key, email)
            if errors:
                return {
                    "success": False,
                    "errors": errors,
                    "files": [],
                    "logs": []
                }
            
            # Create job directory
            job_dir = self.storage.create_job_directory(wkt, dataset, years)
            job_id = job_dir.name  # Use directory name as job ID
            
            # Initialize progress tracking - use unique years count
            unique_years = len(set(years))
            progress_manager.create_job(job_id, unique_years)
            
            self.logger.info(f"Starting NSRDB job in directory: {job_dir}")
            
            # Prepare logs
            logs = []
            logs.append(f"Job started at: {job_dir}")
            logs.append(f"WKT: {wkt}")
            logs.append(f"Dataset: {dataset}")
            logs.append(f"Interval: {interval}")
            logs.append(f"Years: {', '.join(years)}")
            logs.append(f"Location: {location}, {state}, {country}")
            
            # Convert dataset to short name for nsrdb2epw function
            short_dataset = self._convert_dataset_to_short_name(dataset)
            
            # Call the imported nsrdb2epw function
            # This replicates the notebook cell: nsrdb2epw(WKT, DATASET, INTERVAL, YEARS, API_KEY, ...)
            self.logger.info(f"Calling nsrdb2epw with dataset: {short_dataset}, interval: {interval}, years: {years}")
            self.logger.info(f"API Key (first 10 chars): {api_key[:10]}...")
            self.logger.info(f"WKT: {wkt}")
            self.logger.info(f"Email: {email}")
            
            # Call the patched nsrdb2epw function with correct API key and email handling
            self.logger.info(f"Calling nsrdb2epw with dataset: {dataset}, interval: {interval}, years: {years}")
            
            # Create a patched version that handles the API correctly
            def patched_nsrdb2epw(WKT, DATASET, INTERVAL, YEARS, API_KEY, RESULTS_DIR='results/', LOCATION='Unknown', STATE='New York', COUNTRY='United States', EMAIL='example@mail.com'):
                # Deduplicate years to avoid processing the same year multiple times
                unique_years = list(set(YEARS))
                self.logger.info(f"Processing unique years: {unique_years} (original: {YEARS})")
                """Patched version of nsrdb2epw that uses correct API key and email."""
                
                import os
                import time
                import urllib.parse
                import requests
                import re
                
                # Get points using maps API with generic email
                maps_email = "user@example.com"
                req_template = 'https://maps-api.nrel.gov/bigdata/v2/sample-code?email={}&wkt={}&attributes=dew_point,ghi,air_temperature,wind_direction,surface_albedo,dhi,dni,surface_pressure,wind_speed&names=2023&interval=60&to_utc=false&api_key={}&dataset={}'
                req = req_template.format(maps_email, WKT.replace(' ', '+'), API_KEY, DATASET)
                
                response = requests.get(req)
                if response.status_code != 200:
                    raise Exception(f"Maps API returned status {response.status_code}: {response.text}")
                
                response_json = response.json()
                script = response_json['outputs']['script']
                
                # Extract POINTS from the script
                pattern = r"POINTS = \[(.*?)\]"
                match = re.search(pattern, script, re.DOTALL)
                if not match:
                    raise ValueError("POINTS block not found in the script")
                
                points_block = match.group(1)
                points_list = re.findall(r'\d+', points_block)
                POINTS = [int(point) for point in points_list]
                
                # Set up the base URL
                BASE_URL = f"https://developer.nrel.gov/api/nsrdb/v2/solar/{DATASET}-download.csv?"
                
                # Download data
                input_data = {
                    'attributes': 'dew_point,ghi,air_temperature,wind_direction,surface_albedo,dhi,dni,surface_pressure,wind_speed',
                    'interval': INTERVAL,
                    'to_utc': 'false',
                    'api_key': API_KEY,
                    'email': EMAIL,
                }
                
                files_written = []
                total_points = len(POINTS)
                total_downloads = len(unique_years) * total_points
                completed_downloads = 0
                completed_conversions = 0
                
                for year_idx, name in enumerate(unique_years):
                    self.logger.info(f"Processing year: {name} ({year_idx + 1}/{len(unique_years)})")
                    for point_idx, location_ids in enumerate(POINTS):
                        input_data['names'] = [name]
                        input_data['location_ids'] = location_ids
                        
                        url = BASE_URL + urllib.parse.urlencode(input_data, True)
                        
                        # Download CSV data
                        data = nsrdb2epw.pd.read_csv(url)
                        self.logger.info(f'Response data shape: {data.shape}')
                        
                        # Write CSV file
                        csv_filename = f'{location_ids}_{name}.csv'
                        csv_filepath = os.path.join(RESULTS_DIR, csv_filename)
                        data.to_csv(csv_filepath)
                        files_written.append(csv_filepath)
                        
                        # Update download progress
                        completed_downloads += 1
                        download_progress = (completed_downloads / total_downloads) * 100
                        self.logger.info(f"Download progress: {download_progress:.1f}% ({completed_downloads}/{total_downloads})")
                        
                        # Update progress manager
                        progress_manager.update_download_progress(job_id, name, str(location_ids))
                        
                        # Convert to EPW using our own conversion function
                        self.logger.info(f"Converting {csv_filepath} to EPW...")
                        self.convert_csv_to_epw(csv_filepath, LOCATION, STATE, COUNTRY)
                        
                        # Update conversion progress
                        completed_conversions += 1
                        conversion_progress = (completed_conversions / total_downloads) * 100
                        self.logger.info(f"Conversion progress: {conversion_progress:.1f}% ({completed_conversions}/{total_downloads})")
                        
                        # Update progress manager
                        progress_manager.update_conversion_progress(job_id, name, str(location_ids))
                        
                        # Delay for 1 second to prevent rate limiting
                        time.sleep(1)
                
                return files_written
            
            # Call our patched function
            patched_nsrdb2epw(
                wkt,
                dataset,
                interval,
                years,
                api_key,
                RESULTS_DIR=str(job_dir) + "/",
                LOCATION=location,
                STATE=state,
                COUNTRY=country,
                EMAIL=email
            )
            
            # Mark job as completed
            progress_manager.complete_job(job_id)
            
            # Get generated files
            files = self.storage.list_job_files(job_dir)
            csv_files = [f for f in files if f.suffix.lower() == '.csv']
            epw_files = [f for f in files if f.suffix.lower() == '.epw']
            
            logs.append(f"Job completed successfully")
            logs.append(f"Generated {len(csv_files)} CSV files")
            logs.append(f"Generated {len(epw_files)} EPW files")
            
            return {
                "success": True,
                "job_id": job_id,
                "job_dir": str(job_dir),
                "files": {
                    "csv": [str(f) for f in csv_files],
                    "epw": [str(f) for f in epw_files],
                    "all": [str(f) for f in files]
                },
                "logs": logs,
                "summary": self.storage.get_job_summary(job_dir)
            }
            
        except KeyError as e:
            if "'outputs'" in str(e):
                self.logger.error(f"NSRDB API error - invalid response format: {e}")
                return {
                    "success": False,
                    "errors": ["NSRDB API returned an invalid response. This could be due to an invalid API key, incorrect dataset name, or API service issues."],
                    "files": [],
                    "logs": logs if 'logs' in locals() else ["Job failed due to API response error"]
                }
            else:
                self.logger.error(f"KeyError in NSRDB job: {e}")
                return {
                    "success": False,
                    "errors": [f"Configuration error: {str(e)}"],
                    "files": [],
                    "logs": logs if 'logs' in locals() else ["Job failed due to configuration error"]
                }
        except Exception as e:
            self.logger.error(f"NSRDB job failed: {e}")
            return {
                "success": False,
                "errors": [str(e)],
                "files": [],
                "logs": logs if 'logs' in locals() else ["Job failed to start"]
            }
    
    def convert_csv_to_epw(
        self,
        csv_file_path: str,
        location: str = "Unknown",
        state: str = "Unknown",
        country: str = "Unknown",
    ) -> Dict[str, Any]:
        """
        Convert a CSV file to EPW format.
        
        This replicates the CSV2EPW function from nsrdb2epw.py
        """
        try:
            csv_path = Path(csv_file_path)
            if not csv_path.exists():
                return {
                    "success": False,
                    "errors": ["CSV file not found"]
                }
            
            # Create output directory
            output_dir = csv_path.parent
            output_dir.mkdir(exist_ok=True)
            
            # Read CSV and convert to EPW
            # This replicates the CSV2EPW function call
            df = nsrdb2epw.pd.read_csv(csv_file_path, index_col=0, skiprows=2).reset_index(drop=True)
            df = df.drop(columns=df.columns[df.isna().sum() == df.shape[0]])
            metadata = nsrdb2epw.pd.read_csv(csv_file_path, index_col=0, nrows=1).reset_index(drop=True)
            
            year = df['Year'].iloc[0]
            interval = str((df['Hour'].iloc[1] - df['Hour'].iloc[0]) * 60 + df['Minute'].iloc[1] - df['Minute'].iloc[0])
            
            a = epw.epw()
            epw_df = a.dataframe
            
            timezone, elevation, location_id = metadata['Local Time Zone'].iloc[0], metadata['Elevation'].iloc[0], metadata['Location ID'].iloc[0]
            lat, lon = metadata['Latitude'].iloc[0], metadata['Longitude'].iloc[0]
            
            # Set headers (replicating the notebook workflow)
            a.headers = {
                'LOCATION': [
                    location, state, country, metadata['Source'].iloc[0], 'XXX',
                    lat, lon, timezone, elevation
                ],
                'DESIGN CONDITIONS': [
                    '1', 'Climate Design Data 2009 ASHRAE Handbook', '', 'Heating', '1',
                    '3.8', '4.9', '-3.7', '2.8', '10.7', '-1.2', '3.4', '11.2', '12.9',
                    '12.1', '11.6', '12.2', '2.2', '150', 'Cooling', '8', '8.5', '28.3',
                    '17.2', '25.7', '16.7', '23.6', '16.2', '18.6', '25.7', '17.8',
                    '23.9', '17', '22.4', '5.9', '310', '16.1', '11.5', '19.9', '15.3',
                    '10.9', '19.2', '14.7', '10.4', '18.7', '52.4', '25.8', '49.8',
                    '23.8', '47.6', '22.4', '2038', 'Extremes', '12.8', '11.5', '11.5',
                    '10.6', '22.3', '1.8', '34.6', '1.5', '2.3', '0.8', '36.2', '-0.1',
                    '37.5', '-0.9', '38.8', '-1.9', '40.5'
                ],
                'TYPICAL/EXTREME PERIODS': [
                    '6', 'Summer - Week Nearest Max Temperature For Period', 'Extreme',
                    '8/ 1', '8/ 7', 'Summer - Week Nearest Average Temperature For Period',
                    'Typical', '9/ 5', '9/11', 'Winter - Week Nearest Min Temperature For Period',
                    'Extreme', '2/ 1', '2/ 7', 'Winter - Week Nearest Average Temperature For Period',
                    'Typical', '2/15', '2/21', 'Autumn - Week Nearest Average Temperature For Period',
                    'Typical', '12/ 6', '12/12', 'Spring - Week Nearest Average Temperature For Period',
                    'Typical', '5/29', '6/ 4'
                ],
                'GROUND TEMPERATURES': [
                    '3', '.5', '', '', '', '10.86', '10.57', '11.08', '11.88', '13.97',
                    '15.58', '16.67', '17.00', '16.44', '15.19', '13.51', '11.96', '2',
                    '', '', '', '11.92', '11.41', '11.51', '11.93', '13.33', '14.60',
                    '15.61', '16.15', '16.03', '15.32', '14.17', '12.95', '4', '', '',
                    '', '12.79', '12.27', '12.15', '12.31', '13.10', '13.96', '14.74',
                    '15.28', '15.41', '15.10', '14.42', '13.60'
                ],
                'HOLIDAYS/DAYLIGHT SAVINGS': ['No', '0', '0', '0'],
                'COMMENTS 1': [metadata['Source'].iloc[0]],
                'COMMENTS 2': ['https://es.aap.cornell.edu/', 'https://github.com/kastnerp/NREL-PSB3-2-EPW'],
                'DATA PERIODS': ['1', '1', 'Data', 'Sunday', ' 1/ 1', '12/31']
            }
            
            # Create datetime range (replicating notebook workflow)
            dt = nsrdb2epw.pd.date_range('01/01/' + str(year), periods=8760, freq='h')
            missing_values = nsrdb2epw.np.array(nsrdb2epw.np.ones(8760) * 999999).astype(int)
            
            # Populate EPW dataframe (replicating notebook workflow)
            epw_df['Year'] = dt.year.astype(int)
            epw_df['Month'] = dt.month.astype(int)
            epw_df['Day'] = dt.day.astype(int)
            epw_df['Hour'] = dt.hour.astype(int) + 1
            epw_df['Minute'] = dt.minute.astype(int)
            epw_df['Data Source and Uncertainty Flags'] = missing_values
            epw_df['Dry Bulb Temperature'] = df['Temperature'].values.flatten()
            epw_df['Dew Point Temperature'] = df['Dew Point'].values.flatten()
            # Define relative_humidity function locally
            def relative_humidity(t, dew):
                return nsrdb2epw.np.exp(17.62 * dew / (dew + 243.12) - 17.62 * t / (t + 243.12))
            
            epw_df['Relative Humidity'] = df.apply(
                lambda x: relative_humidity(x['Temperature'], x['Dew Point']),
                axis=1
            ).apply(lambda x: int(nsrdb2epw.np.round(x * 100))).values.flatten()
            epw_df['Atmospheric Station Pressure'] = (df['Pressure']*100).values.flatten()
            epw_df['Extraterrestrial Horizontal Radiation'] = missing_values
            epw_df['Extraterrestrial Direct Normal Radiation'] = missing_values
            epw_df['Horizontal Infrared Radiation Intensity'] = missing_values
            epw_df['Global Horizontal Radiation'] = df['GHI'].values.flatten()
            epw_df['Direct Normal Radiation'] = df['DNI'].values.flatten()
            epw_df['Diffuse Horizontal Radiation'] = df['DHI'].values.flatten()
            epw_df['Global Horizontal Illuminance'] = missing_values
            epw_df['Direct Normal Illuminance'] = missing_values
            epw_df['Diffuse Horizontal Illuminance'] = missing_values
            epw_df['Zenith Luminance'] = missing_values
            epw_df['Wind Direction'] = df['Wind Direction'].values.flatten().astype(int)
            epw_df['Wind Speed'] = df['Wind Speed'].values.flatten()
            epw_df['Total Sky Cover'] = missing_values
            epw_df['Opaque Sky Cover'] = missing_values
            epw_df['Visibility'] = missing_values
            epw_df['Ceiling Height'] = missing_values
            epw_df['Present Weather Observation'] = missing_values
            epw_df['Present Weather Codes'] = missing_values
            epw_df['Precipitable Water'] = missing_values
            epw_df['Aerosol Optical Depth'] = missing_values
            epw_df['Snow Depth'] = missing_values
            epw_df['Days Since Last Snowfall'] = missing_values
            epw_df['Albedo'] = df['Surface Albedo'].values.flatten()
            epw_df['Liquid Precipitation Depth'] = missing_values
            epw_df['Liquid Precipitation Quantity'] = missing_values
            
            a.dataframe = epw_df
            
            # Generate output filename (replicating notebook workflow)
            d = "_"
            epw_filename = f"{location}{d}{lat}{d}{lon}{d}{year}.epw"
            epw_file_path = output_dir / epw_filename
            
            # Write EPW file
            a.write(str(epw_file_path))
            
            return {
                "success": True,
                "epw_file": str(epw_file_path),
                "csv_file": csv_file_path,
                "location": location,
                "year": year,
                "lat": lat,
                "lon": lon
            }
            
        except Exception as e:
            self.logger.error(f"CSV to EPW conversion failed: {e}")
            return {
                "success": False,
                "errors": [str(e)]
            }
