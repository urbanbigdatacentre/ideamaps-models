# %% [markdown]
# # Analysis of Access to Health Care using openrouteservice - Kano
# > Note: All notebooks need the [environment dependencies](https://github.com/GIScience/openrouteservice-examples#local-installation)
# > as well as an [openrouteservice API key](https://openrouteservice.org/dev/#/signup) to run
# 
# prepare environment dependencies document

# %% [markdown]
# ## Abstract
# The rapid growth of urban areas has put substantial pressure on local services and infrastructure, particularly in African cities. With migrants moving into cities and transient households moving within cities, traditional means of collecting data (e.g., censuses and household surveys) are inadequate and often overlook informal settlements and households. As a consequence, there is a chronic lack of basic data about deprived households and entire settlements. Given that urban poor residents rely predominantly on private and informal service providers for healthcare and other services, they are rarely captured in routine service data, including health information management systems. This is especially true for women and young people who often work in the informal sector. 
# 
# In this example we will focus on access to healthcare of slum areas in Lagos (Nigeria) , Kano (Nigeria), and Nairobi (Kenya).Quantifying and visualizing such inequalities is the aim of this notebook.
# 
# The notebook gives an overview on health sites distribution in these three cities and the barriers with access to those by foot and by car. Open source data from OpenStreetMap and research ([Macharia, P.M. et al., 2023](https://doi.org/10.1038/s41597-023-02651-9)) were used to create accessibility walking and driving isochrones for each healthcare facility. Spatial join analysis was employed to integrate 100x100m grid cells with the isochrone layers, categorizing the barriers to healthcare access into three levels: low, medium, and high.
# 
# 
# ### Workflow:
# * **Preprocessing**: Get data for district boundaries, slum areas (100x100m grid cells) and health facilities.
# * **Analysis**:
#     * Compute accessibility to health care facilities using openrouteservice API
#     * Spatial join 100x100m grid cells with isochrone layers.
# * **Result**: Visualize results as maps.
# 
# 
# ### Datasets and Tools:
# * [Shapefile of district boundaries][boundaries] - Admin Level 2 (data from Humanitarian Data Exchange, 25/11/2015)
# * [Datasets of health facilities][facilities] (15/07/2023)
# * [openrouteservice][ors] - generate isochrones on the OpenStreetMap road network
# 
# [boundaries]: https://data.humdata.org/dataset/nigeria-admin-level-2
# [facilities]: https://doi.org/10.6084/m9.figshare.22689667.v2
# [ors]: https://openrouteservice.org/

# %% [markdown]
# # Python Workflow

# %% [markdown]
# This study integrates various Python geospatial analysis libraries and packages to support spatial data processing, visualization, and isochrone generation. The os module is used to interact with the operating system, managing file paths and reading environment variables such as API keys. folium library along with its MarkerCluster plugin, facilitates the creation of interactive maps for visualizing large-scale geospatial data. The openrouteservice.client serves as an interface to the OpenRouteService API, enabling the extraction of isochrones. pandas library for data analysis, provides functions for analyzing, cleaning, exploring, and manipulating data, while fiona supports reading and writing real-world data using multi-layered GIS formats, such as shapefiles. The shapely package is employed for the manipulation and analysis of planar geometric objects.

# %% [markdown]
# ## Setting up the virtual environment
# 
# ```bash
# # Create a new virtual environment
# python -m venv .venv
# activate .venv/bin/activate
# pip install -r requirements.txt
# ```
# 
# ## To run your notebook in VS Code
# 
# ```bash
# pip install -U ipykernel
# python -m ipykernel install --user --name=.venv
# ```

# %%
import os
from IPython.display import display
import requests

import folium
from folium.plugins import MarkerCluster
import openrouteservice
import time

import pandas as pd
import numpy as np
import fiona as fn
import geopandas as gpd
from shapely.geometry import shape, mapping
from shapely.geometry import Point
from shapely.geometry import box

import math

from pathlib import Path
from shapely.geometry import Polygon

import seaborn as sns



# %% [markdown]
# ## Preprocessing
# In this study, users first requested an API key from the [OpenRouteService](https://openrouteservice.org/) platform and subsequently interacted with the OpenRouteService API through the instantiation of the OpenRouteService client. This is the OpenRouteService [API documentation](https://openrouteservice.org/dev/#/api-docs/introduction) for ORS Core-Version 9.0.0. 
# 
# Generate a [API Key](https://openrouteservice.org/dev/#/home?tab=1) (Token) it is necessary to sign up at the OpenRouteService dashboard by using your E-mail address or sign up with your GitHub. After logging in, go to the Dashboard by clicking on your profile icon and navigate to the API Keys section. Click "Create API Key" to generate a free key and then choose a service plan (the free plan has limited requests per day). Copy the API Key and store it securely. 
# 
# OpenRouteService primarily uses API keys for authentication. However, if a token is required for certain endpoints, you can send a request with your API key in the Authorization header. This process facilitated various geospatial analysis functions, including isochrone generation.
# 
# ### API Key
# Make sure you have a .env file in the root directory with the following content:
# ```bash
#     OPENROUTESERVICE_API_KEY='your_api_key'
# ```

# %%
# Read the api key from the .env file
from dotenv import load_dotenv
%load_ext dotenv
%dotenv
api_key = os.getenv('OPENROUTESERVICE_API_KEY')
ors = client.Client(key=api_key)

# %%
import openrouteservice
api_key = '5b3ce3597851110001cf62480c829160e12e4f8cae69c28d694ad1e1'
ors = openrouteservice.Client(key=api_key)

# %% [markdown]
# ## Setting up the OSR local client

# %%
import openrouteservice
base_url = 'http://localhost:8022/ors'
ors = openrouteservice.Client(base_url=base_url)

# %% [markdown]
# For this study different kind of data were used. The dataset on healthcare facilities is sourced from a research [GRID3 NGA - Health Facilities v2.0](https://data.grid3.org/datasets/a0ed9627a8b240ff8b315a84575754a4_0/explore) which provides A geospatial database of close-to-reality travel times to obstetric emergency care in 15 Nigerian conurbations. The dataset were filtered by state name to isolate facilities in Kano and converted CSV file to shapefile based on coordinates using [QGIS](https://qgis.org/). 
# 
# The Level 2 administrative boundary data is sourced from [Humanitarian Data Exchange](https://data.humdata.org/) were used to correlate the isochrones and healthcare facility distribution with specific administrative regions. The data were filtered based on the administrative region name (lganame) to focus the analysis on Kano.
# 
# * [Datasets of health facilities](https://data.grid3.org/datasets/a0ed9627a8b240ff8b315a84575754a4_0/explore) (15/07/2023)
# * [Shapefile of district boundaries](https://data.humdata.org/dataset/nigeria-admin-level-2) - Admin Level 2 (data from Humanitarian Data Exchange, 25/11/2015)

# %% [markdown]
# ### Option 1: Kano
# If you want to process data for the city of Kano, use the following code to filter the dataset. 

# %%
# Set paths to access Kano data
# Define directories
data_inputs = '../scripts/Kano/data-inputs/'
data_temp = '../scripts/Kano/data-temp/'
model_outputs = '../Kano-v2/'

# %% [markdown]
# ### Option 2: Lagos
# If you want to process data for the city of Kano, use the following code to filter the dataset. 

# %%
# Set paths to access Lagos data
# Define directories
data_inputs = '../scripts/Lagos/data-inputs/'
data_temp = '../scripts/Lagos/data-temp/'
model_outputs = '../lagos/'

# %% [markdown]
# ## Data Collection

# %% [markdown]
# ### 1.1 Administrative level 2

# %%
study_area = gpd.read_file(data_inputs + '100mGrid.gpkg')
districts = gpd.read_file(data_inputs + 'administrative_level2.geojson')

# %%
study_area['grid_id'] = range(len(study_area))

# %% [markdown]
# ### 2.1 Validated healthcare facilities
# note: to describe the process to validate healthcare facilities
# Due to the absence of local expert validation, the classification for validation is determine based on the ownership provided in the [GRID3 NGA - Health Facilities v2.0](https://data.grid3.org/datasets/a0ed9627a8b240ff8b315a84575754a4_0/explore).

# %%
healthcare_facilities_validated = gpd.read_file(data_inputs + 'healthcare_facilities.geojson')
healthcare_facilities_validated

# %%
print(healthcare_facilities_validated['ownership'].unique())

# %%
facilities = healthcare_facilities_validated[
    healthcare_facilities_validated['ownership'].isin(['Public', 'Unknown'])]

facilities



# %%
facilities = facilities.reset_index(drop=True)
facilities['hcf_id'] = facilities.index + 1
facilities

# %% [markdown]
# ### Create district dictionary and facilities dictionary
# In conducting geospatial analysis, we created dictionaries containing district information and healthcare facility information to achieve efficient data management and subsequent analysis.

# %%
# these files will be generated during processing
isochrones_car_filename = data_temp + 'iso_union_car.shp'
isochrones_car_per_district_filename = data_temp + 'iso_car_per_district.shp'
isochrones_foot_filename = data_temp + 'iso_union_foot.shp'
isochrones_foot_per_district_filename = data_temp + 'iso_foot_per_district.shp'

# final file with all generated information
output_file = data_temp + 'districts_final.geojson'

# %%
districts_dictionary = {}
for _, feature in districts.iterrows():
    district_id = int(feature['OBJECTID'])
    districts_dictionary[district_id] = {
        'District Code': feature['LGACode'],
        'District Name': feature['LGAName'],
        'geometry': feature['geometry']
    }
print(f'created dictionary for {len(districts_dictionary)} districts')

facilities_dictionary = {}
for _, feature in facilities.iterrows():
    facility_id = int(feature['hcf_id'])
    facilities_dictionary[facility_id] = {
        'geometry': feature['geometry']
    }
print(f'created dictionary for {len(facilities_dictionary)} facilities')

# %% [markdown]
# ### An overview and look at a map of the districts and health facilities
# First a map were created with [Folium](https://python-visualization.github.io/folium/latest/) to visualize data manipulated in Python. The boundaries of the districts as well as the health sites were given as shapefiles, which were printed on the map. 

# %%
map_outline = folium.Map(tiles='Stamen Toner', location=[-18.812718, 46.713867], zoom_start=5, attr='Map tiles by Stamen Design, CC BY 3.0 — Map data © OpenStreetMap contributors')

# Import health facilities
cluster = MarkerCluster().add_to(map_outline)  # To cluster hospitals

for facility_id in facilities_dictionary:
    folium.Marker(list(reversed(facilities_dictionary[facility_id]['geometry'].coords[0]))).add_to(cluster)

# Import district boundaries
district_simp = []  # Initialize the list
for district_id in districts_dictionary:
    geom = shape(districts_dictionary[district_id]['geometry'])
    # we simplify the geometry just for the purpose of visualisation
    # be aware that some browsers e.g. chrome might fail to render the entire map if there are to many coordinates
    simp_geom = geom.simplify(0.005, preserve_topology=False)
    simp_coord = mapping(simp_geom)
    folium.GeoJson(simp_coord).add_to(map_outline)
    district_simp.append(simp_coord)

#change to variable
map_outline.save(os.path.join(data_temp + 'healthcare_facilities_overview.html'))
map_outline

# %% [markdown]
# ## Analysis
# We will follow these steps:
# * Get Isochrones from openrouteservice
# * Perform Spatial Join
# * Save output as GeoPackage file and CSV file

# %% [markdown]
# ### Get Isochrones from OpenRouteService
# Due to the limited road networks in the slum areas of these three cities, the accessibility of hospitals within a 10-minute range is of significant concern. Therefore, isochrones with 15 minutes walk range and 10 minutes car drive range around each hospital were created with the open source tool [OpenRouteService](https://openrouteservice.org/). This might take several minutes depending on the number of health facilities (currently we can send 40 requests per minute).

# %%
print(facilities['Local Validation'].unique())

# %% [markdown]
# ### 1. Calculating the isochrones for 10 minute driving

# %%
all_features = []

# Initialize request counter
request_counter = 0

# Create a dictionary to store isochrones by category
isochrones_by_category = {
    "Primary": [],
    "Secondary/Tertiary": []
}

# Loop through each category
for category in isochrones_by_category.keys():
    # Filter facilities by category
    group = facilities[facilities["Local Validation"] == category]

    for _, row in group.iterrows():
        loc = row["geometry"]
        facility_id = row["hcf_id"]
        facility_name = row["facility_name"]

        # Make sure geometry is a Point and get [lon, lat]
        if isinstance(loc, Point):
            coordinates = [loc.x, loc.y]
        else:
            print(f"Invalid geometry for: {row.get('facility_name', 'Unknown')} — Skipping")
            continue

        try:
            # Prepare request parameters
            iso_params = {
                "locations": [coordinates],
                "profile": "driving-car",
                "range_type": "distance",
                "range": [3300],  # 3.3km

                # "range": [600],  # 10 minutes
                # "attributes": ["area"]
            }

            # Request isochrone from ORS
            isochrone = ors.isochrones(**iso_params)

            for feature in isochrone['features']:
                properties = feature['properties']

                # Convert list fields to strings if needed
                for key, value in properties.items():
                    if isinstance(value, list):
                        properties[key] = ', '.join(map(str, value))

                # Add a new column for the category
                properties["Local Validation"] = category
                properties["facility_id"] = facility_id
                properties["facility_name"] = facility_name

                all_features.append({
                    'geometry': feature['geometry'],
                    'properties': properties
                })

            # Handle rate limiting
            request_counter += 1
            if request_counter % 35 == 0:
                print("Pausing for 60 seconds to respect API rate limits...")
                # Use this sleep when using the OSR instance hosted by HeiGIT
                # # time.sleep(60)
            if request_counter > 2500:
                print("Reached max request threshold.")
                break

        except Exception as e:
            print(f"Request failed for {row.get('facility_name', 'Unknown')}: {e}")

# %%
# Convert to GeoDataFrame if there are valid features
if all_features:
    iso_gdf = gpd.GeoDataFrame.from_features(all_features, crs="EPSG:4326")

    # Ensure 'Local Validation' is a string column
    iso_gdf["Local Validation"] = iso_gdf["Local Validation"].astype(str)
    iso_gdf["facility_id"] = iso_gdf["facility_id"].astype(str)
    iso_gdf["facility_name"] = iso_gdf["facility_name"].astype(str)

    # Save to a single GeoPackage file
    iso_gdf.to_file(data_temp + 'General_healthcare_iso_3_3km_car.gpkg', driver="GPKG")
    

# %% [markdown]
# ### 2. Calculating the isochrones for walking

# %%
all_features = []

# Initialize request counter
request_counter = 0

# Create a dictionary to store isochrones by category
isochrones_by_category = {
    "Primary": [],
    "Secondary/Tertiary": []
}

# Loop through each category
for category in isochrones_by_category.keys():
    # Filter facilities by category
    group = facilities[facilities["Local Validation"] == category]

    for _, row in group.iterrows():
        loc = row["geometry"]
        facility_id = row["hcf_id"]
        facility_name = row["facility_name"]

        # Make sure geometry is a Point and get [lon, lat]
        if isinstance(loc, Point):
            coordinates = [loc.x, loc.y]
        else:
            print(f"Invalid geometry for: {row.get('facility_name', 'Unknown')} — Skipping")
            continue

        try:
            # Prepare request parameters
            iso_params = {
                "locations": [coordinates],
                "profile": "driving-car",

                "range_type": "distance",
                "range": [1000],  # 1km

               # "range_type": "time",
               # "range": [900],  # 15 minutes

                "attributes": ["area"]
            }

            # Request isochrone from ORS
            isochrone = ors.isochrones(**iso_params)

            for feature in isochrone['features']:
                properties = feature['properties']

                # Convert list fields to strings if needed
                for key, value in properties.items():
                    if isinstance(value, list):
                        properties[key] = ', '.join(map(str, value))

                # Add a new column for the category
                properties["Local Validation"] = category
                properties["facility_id"] = facility_id
                properties["facility_name"] = facility_name

                all_features.append({
                    'geometry': feature['geometry'],
                    'properties': properties
                })

            # Handle rate limiting
            request_counter += 1
            if request_counter % 35 == 0:
                print("Pausing for 60 seconds to respect API rate limits...")
                # time.sleep(60)
            if request_counter > 2500:
                print("Reached max request threshold.")
                break

        except Exception as e:
            print(f"Request failed for {row.get('facility_name', 'Unknown')}: {e}")


# %%
# Convert to GeoDataFrame if there are valid features
if all_features:
    iso_gdf = gpd.GeoDataFrame.from_features(all_features, crs="EPSG:4326")

    # Ensure 'combination' is a string column
    iso_gdf["Local Validation"] = iso_gdf["Local Validation"].astype(str)
    iso_gdf["facility_id"] = iso_gdf["facility_id"].astype(str)
    iso_gdf["facility_name"] = iso_gdf["facility_name"].astype(str)

    # Save to a single GeoPackage file
    iso_gdf.to_file(data_temp + 'General_healthcare_iso_1km_walking.gpkg', driver="GPKG")

# %% [markdown]
# ### Spatial joins for the grid and isochrone layers using geopandas
# This study employed the GeoPandas library to perform a spatial join between isochrone data and 100x100m grid cells, which allowed for the analysis and evaluation of accessibility for each grid cell within the study area in these three cities, across different time intervals (specifically by walking or driving). Accessibility was classified as three levels: high, medium and low. The analysis results were exported in GeoPackage format to ensure both the persistent storage and reusability of the data. Additionally, all spatial datasets were maintained in the same coordinate reference system (EPSG:4326), which ensured consistency and accuracy in the spatial joins and subsequent analyses.

# %%
# Read grid cells and isochrones from the GeoPackage file
# Ensure both GeoDataFrames have the same CRS (EPSG:4326)
isochrones_foot_gdf = gpd.read_file(data_temp + 'General_healthcare_iso_1km_walking.gpkg')
isochrones_car_gdf = gpd.read_file(data_temp + 'General_healthcare_iso_3_3km_car.gpkg')

# %%
# We just consider the isochrones for priary healthcare facilities
isochrones_foot_gdf = isochrones_foot_gdf[isochrones_foot_gdf['Local Validation'] == 'Primary']
isochrones_car_gdf = isochrones_car_gdf[isochrones_car_gdf['Local Validation'] == 'Primary']

# %%
target_crs = "EPSG:4326"
isochrones_foot_gdf = isochrones_foot_gdf.to_crs(target_crs)
isochrones_car_gdf = isochrones_car_gdf.to_crs(target_crs)
study_area = study_area.to_crs(target_crs)

# %% [markdown]
# Spatial join to count the number of isochrones for 1km walking distance falling in each grid cell
# 

# %%
joined = gpd.sjoin(isochrones_foot_gdf, study_area, how="inner", predicate="intersects")

isochrone_count = joined.groupby("grid_id").size().reset_index(name='iso_walk_1k_count')

study_area["iso_walk_1k_count"] = 0
study_area.loc[isochrone_count["grid_id"], "iso_walk_1k_count"] = isochrone_count["iso_walk_1k_count"].values

study_area


# %% [markdown]
# Spatial join to count the number of isochrones for 3.3km driving distance falling in each grid cell. Values are appended to the previously created grid cells.

# %%
joined = gpd.sjoin(isochrones_car_gdf, study_area, how="inner", predicate="intersects")

isochrone_count = joined.groupby("grid_id").size().reset_index(name='iso_3_3km_count')

study_area["iso_3_3km_count"] = 0
study_area.loc[isochrone_count["grid_id"], "iso_3_3km_count"] = isochrone_count["iso_3_3km_count"].values

study_area


# %%
# Save the updated grid cells if needed

 # Save to a single GeoPackage file
study_area.to_file(data_temp + 'grid_count_iso_1km_3_3km.gpkg', driver="GPKG")

# %% [markdown]
# Define the categories for healtcare access deprivation:
# - High: 0-1 isochrones at 1km walking distance and 0-2 isochrones at 3.3km driving distance
# - Medium: 2-4 isochrones at 1km walking distance and 3+ isochrones at 3.3km driving distance
# - Low: 5+ isochrones at 1km walking distance 

# %%

study_area["result"] = study_area.apply(
    lambda row: 2 if row["iso_walk_1k_count"] <= 1
    else 1 if 2 >= row["iso_walk_1k_count"] <= 4 and row["iso_3_3km_count"] >=20
    else 1 if 5 >= row["iso_walk_1k_count"] <= 10 and row["iso_3_3km_count"] >=10
    else 0,
    axis=1
)

study_area

# %% [markdown]
# ## Save output as GeoPackage file

# %%
# Save the updated grid cells if needed

 # Save to a single GeoPackage file
study_area.to_file(data_temp + 'general_healthcare_outputs.gpkg', driver="GPKG")

# %% [markdown]
# ### Save Output as CSV file

# %%
study_area.to_csv(model_outputs + 'output.csv', 
                           columns=['latitude', 'longitude', 'lat_min', 'lat_max', 'lon_min', 'lon_max', 'result'])

# %% [markdown]
# ## Further analysis

# %%
#
# Scatter plot with count of isochrones

sns.scatterplot(data=study_area, x='iso_walk_1k_count', y='iso_3_3km_count', hue='result', palette='Set1')

# %%
# 2. Calculate the number of hospitals reachable within a 15-minute walk
foot_joined = gpd.sjoin(study_area, isochrones_foot_gdf, how="left", predicate="intersects")
foot_counts = foot_joined.groupby(foot_joined.index)["hcf_id"].nunique()
study_area["facilities_15min_walk"] = study_area.index.map(foot_counts).fillna(0).astype(int)

# %%
# 3. Classify Access Deprivation Level
def classify_deprivation(drive, walk):
    if drive >= 5:
        return "0" # low deprivation
    elif walk <= 1:
        return "2" # high deprivation
    else:
        return "1" # medium deprivation

study_area["result"] = study_area.apply(
    lambda row: classify_deprivation(row["facilities_10min_drive"], row["facilities_15min_walk"]),
    axis=1
)


