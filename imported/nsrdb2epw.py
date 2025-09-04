import requests
import re
import pandas as pd
import urllib.parse
import time

import os
import csv
import numpy as np

import epw

def get_dataset_names():
    return {
        'CONUS': 'nsrdb-GOES-conus-v4-0-0',
        'full-disc': 'nsrdb-GOES-full-disc-v4-0-0',
        'TMY': 'nsrdb-GOES-tmy-v4-0-0',
        'aggregated': 'nsrdb-GOES-aggregated-v4-0-0'
    }

def nsrdb2epw(WKT, DATASET, INTERVAL, YEARS, API_KEY, RESULTS_DIR='results/', LOCATION='Unknown', STATE='New York', COUNTRY='United States', EMAIL='example@mail.com'):
    
    dataset_names = {
        'CONUS': 'nsrdb-GOES-conus-v4-0-0',
        'full-disc': 'nsrdb-GOES-full-disc-v4-0-0',
        'TMY': 'nsrdb-GOES-tmy-v4-0-0',
        'aggregated': 'nsrdb-GOES-aggregated-v4-0-0'
    }

    
    
    def get_points(wkt: str='POINT(-74.25820375161103+42.684861252913805)', dataset=dataset_names['full-disc']):
        req_template = 'https://maps-api.nrel.gov/bigdata/v2/sample-code?email=insert.your.email%40fake.com&wkt={}&attributes=dew_point&names=%272023%27,%272021%27&interval=15&to_utc=false&api_key=%7B%7BYOUR_API_KEY%7D%7D&dataset={}'
        req = req_template.format(wkt.replace(' ', '+'), dataset)
        response = requests.get(req)
        script = dict(response.json())['outputs']['script']
    
        pattern = r"POINTS = \[(.*?)\]"
        match = re.search(pattern, script, re.DOTALL)
        if not match:
            raise ValueError("POINTS block not found in the script")
    
        points_block = match.group(1)
        points_list = re.findall(r'\d+', points_block)
        points_list = [int(point) for point in points_list]
    
        return points_list
    
    
    def download_data():
        input_data = {
            'attributes': 'dew_point,ghi,air_temperature,wind_direction,surface_albedo,dhi,dni,surface_pressure,wind_speed',
            'interval': INTERVAL,
            'to_utc': 'false',
            'api_key': API_KEY,
            'email': EMAIL,
        }
        files_written = []
        for name in YEARS:
            print(f"Processing name: {name}")
            for id, location_ids in enumerate(POINTS):
                input_data['names'] = [name]
                input_data['location_ids'] = location_ids
                print(f'Making request for point group {id + 1} of {len(POINTS)}...')
    
                if '.csv' in BASE_URL:
                    url = BASE_URL + urllib.parse.urlencode(input_data, True)
                    # Note: CSV format is only supported for single point requests
                    # Suggest that you might append to a larger data frame
                    data = pd.read_csv(url)
                    print(f'Response data (you should replace this print statement with your processing): {data.shape}')
                    # You can use the following code to write it to a file
                    data.to_csv(RESULTS_DIR + '{}_{}.csv'.format(location_ids, name))
                    files_written.append(RESULTS_DIR + '{}_{}.csv'.format(location_ids, name))
                else:
                    headers = {
                      'x-api-key': API_KEY
                    }
                    data = get_response_json_and_handle_errors(requests.post(BASE_URL, input_data, headers=headers))
                    download_url = data['outputs']['downloadUrl']
                    # You can do with what you will the download url
                    print(data['outputs']['message'])
                    print(f"Data can be downloaded from this url when ready: {download_url}")
    
                    # Delay for 1 second to prevent rate limiting
                    time.sleep(1)
                print(f'Processed')
        return files_written
    
    
    def get_response_json_and_handle_errors(response: requests.Response) -> dict:
        """Takes the given response and handles any errors, along with providing
        the resulting json
    
        Parameters
        ----------
        response : requests.Response
            The response object
    
        Returns
        -------
        dict
            The resulting json
        """
        if response.status_code != 200:
            print(f"An error has occurred with the server or the request. The request response code/status: {response.status_code} {response.reason}")
            print(f"The response body: {response.text}")
            exit(1)
    
        try:
            response_json = response.json()
        except:
            print(f"The response couldn't be parsed as JSON, likely an issue with the server, here is the text: {response.text}")
            exit(1)
    
        if len(response_json['errors']) > 0:
            errors = '\n'.join(response_json['errors'])
            print(f"The request errored out, here are the errors: {errors}")
            exit(1)
        return response_json
    def relative_humidity(t, dew):
        return np.exp(17.62 * dew / (dew + 243.12) - 17.62 * t / (t + 243.12))
    def CSV2EPW(file):
        df = pd.read_csv(file, index_col=0, skiprows=2).reset_index(drop=True)
        df = df.drop(columns=df.columns[df.isna().sum() == df.shape[0]])
        metadata = pd.read_csv(file, index_col=0, nrows=1).reset_index(drop=True)
    
        year = df['Year'].iloc[0]
        interval = str((df['Hour'].iloc[1] - df['Hour'].iloc[0]) * 60 +  df['Minute'].iloc[1] - df['Minute'].iloc[0])
        
        a = epw.epw()
        epw_df = a.dataframe
        
        timezone, elevation, location_id = metadata['Local Time Zone'].iloc[0], metadata['Elevation'].iloc[0], metadata['Location ID'].iloc[0]
        lat, lon = metadata['Latitude'].iloc[0], metadata['Longitude'].iloc[0]
    
        a.headers = {'LOCATION': [LOCATION,
          STATE,
          COUNTRY,
          metadata['Source'].iloc[0],
          'XXX',
          lat,
          lon,
          timezone,
          elevation],
         'DESIGN CONDITIONS': ['1',
           'Climate Design Data 2009 ASHRAE Handbook',
           '',
           'Heating',
           '1',
           '3.8',
           '4.9',
           '-3.7',
           '2.8',
           '10.7',
           '-1.2',
           '3.4',
           '11.2',
           '12.9',
           '12.1',
           '11.6',
           '12.2',
           '2.2',
           '150',
           'Cooling',
           '8',
           '8.5',
           '28.3',
           '17.2',
           '25.7',
           '16.7',
           '23.6',
           '16.2',
           '18.6',
           '25.7',
           '17.8',
           '23.9',
           '17',
           '22.4',
           '5.9',
           '310',
           '16.1',
           '11.5',
           '19.9',
           '15.3',
           '10.9',
           '19.2',
           '14.7',
           '10.4',
           '18.7',
           '52.4',
           '25.8',
           '49.8',
           '23.8',
           '47.6',
           '22.4',
           '2038',
           'Extremes',
           '12.8',
           '11.5',
           '10.6',
           '22.3',
           '1.8',
           '34.6',
           '1.5',
           '2.3',
           '0.8',
           '36.2',
           '-0.1',
           '37.5',
           '-0.9',
           '38.8',
           '-1.9',
           '40.5'],
         'TYPICAL/EXTREME PERIODS': ['6',
         'Summer - Week Nearest Max Temperature For Period',
         'Extreme',
         '8/ 1',
         '8/ 7',
         'Summer - Week Nearest Average Temperature For Period',
         'Typical',
         '9/ 5',
         '9/11',
         'Winter - Week Nearest Min Temperature For Period',
         'Extreme',
         '2/ 1',
         '2/ 7',
         'Winter - Week Nearest Average Temperature For Period',
         'Typical',
         '2/15',
         '2/21',
         'Autumn - Week Nearest Average Temperature For Period',
         'Typical',
         '12/ 6',
         '12/12',
         'Spring - Week Nearest Average Temperature For Period',
         'Typical',
         '5/29',
         '6/ 4'],
         'GROUND TEMPERATURES': ['3',
         '.5',
         '',
         '',
         '',
         '10.86',
         '10.57',
         '11.08',
         '11.88',
         '13.97',
         '15.58',
         '16.67',
         '17.00',
         '16.44',
         '15.19',
         '13.51',
         '11.96',
         '2',
         '',
         '',
         '',
         '11.92',
         '11.41',
         '11.51',
         '11.93',
         '13.33',
         '14.60',
         '15.61',
         '16.15',
         '16.03',
         '15.32',
         '14.17',
         '12.95',
         '4',
         '',
         '',
         '',
         '12.79',
         '12.27',
         '12.15',
         '12.31',
         '13.10',
         '13.96',
         '14.74',
         '15.28',
         '15.41',
         '15.10',
         '14.42',
         '13.60'],
         'HOLIDAYS/DAYLIGHT SAVINGS': ['No', '0', '0', '0'],
         'COMMENTS 1': [metadata['Source'].iloc[0]],
         'COMMENTS 2': ['https://es.aap.cornell.edu/', 'https://github.com/kastnerp/NREL-PSB3-2-EPW'],
         'DATA PERIODS': ['1', '1', 'Data', 'Sunday', ' 1/ 1', '12/31']}
    
        dt = pd.date_range('01/01/' + str(year), periods=8760, freq='h')
        missing_values = np.array(np.ones(8760) * 999999).astype(int)
        
        epw_df['Year'] = dt.year.astype(int)
        epw_df['Month'] = dt.month.astype(int)
        epw_df['Day'] = dt.day.astype(int)
        epw_df['Hour'] = dt.hour.astype(int) + 1
        epw_df['Minute'] = dt.minute.astype(int)
        epw_df['Data Source and Uncertainty Flags'] = missing_values
        
        epw_df['Dry Bulb Temperature'] = df['Temperature'].values.flatten()
        
        epw_df['Dew Point Temperature'] = df['Dew Point'].values.flatten()
        
        epw_df['Relative Humidity'] = df.apply(lambda x: relative_humidity(x['Temperature'], x['Dew Point']),axis=1).apply(lambda x: int(np.round(x * 100))).values.flatten() # changes
        
        epw_df['Atmospheric Station Pressure'] = (df['Pressure']*100).values.flatten()
        epw_df['Extraterrestrial Horizontal Radiation'] = missing_values
        #
        epw_df['Extraterrestrial Direct Normal Radiation'] = missing_values
        #
        epw_df['Horizontal Infrared Radiation Intensity'] = missing_values
        #
        epw_df['Global Horizontal Radiation'] = df['GHI'].values.flatten()
        epw_df['Direct Normal Radiation'] = df['DNI'].values.flatten()
        epw_df['Diffuse Horizontal Radiation'] = df['DHI'].values.flatten()
        
        epw_df['Global Horizontal Illuminance'] = missing_values
        epw_df['Direct Normal Illuminance'] = missing_values
        epw_df['Diffuse Horizontal Illuminance'] = missing_values
        epw_df['Zenith Luminance'] = missing_values
        
        epw_df['Wind Direction'] = df['Wind Direction'].values.flatten().astype(int)
        epw_df['Wind Speed'] = df['Wind Speed'].values.flatten()
        
        epw_df['Total Sky Cover'] = missing_values # df['Cloud Type'].values.flatten() # changes
        # used if Horizontal IR Intensity missing
        epw_df['Opaque Sky Cover'] = missing_values # df['Cloud Type'].values.flatten() # changes
        #
        
        epw_df['Visibility'] = missing_values
        epw_df['Ceiling Height'] = missing_values
        epw_df['Present Weather Observation'] = missing_values
        #
        epw_df['Present Weather Codes'] = missing_values
        epw_df['Precipitable Water'] = missing_values # df['Precipitable Water'].values.flatten() # changes
        epw_df['Aerosol Optical Depth'] = missing_values
        #
        epw_df['Snow Depth'] = missing_values
        epw_df['Days Since Last Snowfall'] = missing_values
        epw_df['Albedo'] = df['Surface Albedo'].values.flatten()
        #
        
        epw_df['Liquid Precipitation Depth'] = missing_values
        epw_df['Liquid Precipitation Quantity'] = missing_values
        
        a.dataframe = epw_df
        
        d = "_"
        
        file_name = RESULTS_DIR + str(LOCATION) + d + str(lat) + d + str(lon) + d + str(year) + '.epw'
        a.write(file_name)
        print('Successfully written {}'.format(file_name))
    
    



    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
        print(f"Non-existent directory. New directory created at: {RESULTS_DIR}")
    
    POINTS = get_points(wkt=WKT, dataset=DATASET)
    BASE_URL = "https://developer.nrel.gov/api/nsrdb/v2/solar/{}-download.csv?".format(DATASET)
    assert len(POINTS) > 0
    files_written = download_data()
    for file in files_written:
        CSV2EPW(file)




