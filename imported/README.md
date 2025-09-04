# NSRDB to EPW Pipeline
## Introduction
This notebook allows the downloading of climate data and automtic conversion into EPW files for any year (where available dataset exists on NSRDB) for almost every location in the Americas.

### Conceptual steps

+ Gather your query location as a [WKT geometry](https://libgeos.org/specifications/wkt/) (in WGS84 CRS, could be Point, Polygon, MultiPolygon, etc. but a minimum working example is a Point) and prepare it as a string
+ Determine the dataset you would like to query, and the appropriate temporal resolutions and the years you neeed.
+ Obtain an API key. You can [sign up for your API key](https://developer.nrel.gov/signup/).
+ Translate the geometry into NSRDB point_ids (automated by the pipeline, no need to worry)
+ Get the weather data about the associated point_ids and parse them into DataFrames and write them as CSVs (automated by the pipeline, no need to worry)
+ Translate these DataFrames into EPW files and write them (automated by the pipeline, no need to worry)

### Credits

The dataset and a interactive web portal is available via [NSRDB Data Viewer](https://nsrdb.nrel.gov/data-viewer). This pipeline takes advantage of the sample query code provided here.

Thanks to [Patrick's script](https://github.com/building-energy/epw/blob/master/epw/epw.py) we have a ready-made workflow for EPW file generation.

## Steps
### 1. Prepare your WKT geometry

Prepare your WKT geometry representing the area of investigation as a string. Further guidance available [here](https://libgeos.org/specifications/wkt/).

A minimum working example is a Point, such as `POINT(-76.48408307172359 42.45094507085529)` is the location of Cornell AAP.

### 2. Determine the right temporal resolution and coverage

By referring to the table below, determine the right temporal resolution and coverage.

Datasets and their coverage:

|Geographies|Name|Temporal Resolution|Geographical Resolution|Years (Inclusive)|
|------|------|------|------|------|
|USA Continental and Mexico|`nsrdb-GOES-conus`|5, 30, 60min|2km|2021-23|
|USA and Americas|`nsrdb-GOES-full-disc`|10, 30, 60min|2km|2018-23|
|USA and Americas|`nsrdb-GOES-aggregated`|30, 60min|4km|1998-23|
|USA and Americas|`nsrdb-GOES-tmy`|60min| |2022-23|

### 3. Obtain an API key
You are suggested to [sign up for your API key](https://developer.nrel.gov/signup/) before working with the script. For lab purposes you can use the key provided (it is my key actually so pay attention to the payload if you are doing batch downloads for larger regions).

### 4. Run the script with the inputs

Provide the inputs for the script to run.