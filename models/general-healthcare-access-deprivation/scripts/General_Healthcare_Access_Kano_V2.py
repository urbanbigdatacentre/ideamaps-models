# %% [markdown]
# # Analysis of General Healthcare Access in Nigeria, Kano
# > Note: This notebook requires the [environment dependencies](requirements.txt) to be installed
# > as well as either an [openrouteservice API key](https://openrouteservice.org/dev/#/signup) or a local instance of the ORS server.

# %% [markdown]
# ## Model Summary:
# 
# This notebook provides the means to generate a dataset that is described in the [model documentation](../Kano-v2/dataset-interpretability.md).
# 
# ## Workflow Summary:
# 
# The notebook gives an overview of the distribution of centres offering general healthcare in the city. Open source data from OpenStreetMap and tools (such as the openrouteservice) were used to create accessibility measures. Spatial analysis and other data analytics functions led to generating outputs within the 100x100m grid cells that categorised them into three levels: low, medium, and high.
# 
# * **Preprocessing**: Get data for general healthcare facilities.
# * **Analysis for Offer**:
#     * Filter or classify general healthcare facilities based on discussed criteria.
#     * Visualise general healthcare faccilities in their categories.
# * **Analysis for Accessibility**:
#     * Compute isochrones to facilities using openrouteservice API or other routing services.
#     * Generate areas for low, medium and high categories based on discussed criteria.
# * **Analysis for Demmand**:
#     * Derive socio-economic descriptors based on discussed criteria.
# 
# * **Result**: Generate results as GIS-compatible files.
# 
# 
# ### Datasets and Tools:
# * [openrouteservice](https://openrouteservice.org/) - generate isochrones on the OpenStreetMap road network

# %% [markdown]
# #  Workflow
# 
# Make sure you have the required packages installed. You can install them using pip:
# 
# ```bash
# pip install -r requirements.txt
# ```

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
import geopandas as gpd
import os
import numpy as np
import pandas as pd

import openrouteservice
from dotenv import load_dotenv
import folium
from folium.plugins import MarkerCluster

import rasterio
from rasterio.mask import mask
import ast

from pathlib import Path
from shapely.geometry import Polygon
from shapely.geometry import shape, mapping
from shapely.geometry import Point

import requests
from math import *
from sklearn.preprocessing import MinMaxScaler
import seaborn as sns
import time

# %% [markdown]
# ### Setting up the public API Key from OpenRouteService
# In this study, users must obtain an ORS Matrix API key from the [OpenRouteService](https://openrouteservice.org/) platform and subsequently interacted with the OpenRouteService API through the instantiation of the OpenRouteService client. This is the OpenRouteService [API documentation](https://openrouteservice.org/dev/#/api-docs/introduction) for ORS Core-Version 9.0.0. 
# 
# Generate a [API Key](https://openrouteservice.org/dev/#/home?tab=1) (Token) it is necessary to sign up at the OpenRouteService dashboard by using your E-mail address or sign up with your GitHub. After logging in, go to the Dashboard by clicking on your profile icon and navigate to the API Keys section. Click "Create API Key" to generate a free key and then choose a service plan (the free plan has limited requests per day). Copy the API Key and store it securely. 
# 
# OpenRouteService primarily uses API keys for authentication. However, if a token is required for certain endpoints, you can send a request with your API key in the Authorization header. This process facilitated various geospatial analysis functions, including isochrone generation.

# %% [markdown]
# ### Using an ORS API Key
# Make sure you have a .env file in the root directory with the following content:
# ```bash
#     OPENROUTESERVICE_API_KEY='your_api_key'
# ```

# %%
# %%
# Read the api key from the .env file
%load_ext dotenv
%dotenv
api_key = os.getenv('OPENROUTESERVICE_API_KEY')
ors = openrouteservice.Client(key=api_key)

# %% [markdown]
# ### Setting up relevant processing folders
# 
# There are different data sources used across the notebook. To handle these data sets, it is recommended to use three directories for input, temp and output data. Some of the files are related to healthcare facilities, population data. The healthcare facilities data is sourced from [GRID3 NGA - Health Facilities v2.0](https://data.grid3.org/datasets/a0ed9627a8b240ff8b315a84575754a4_0/explore).
# 
# Despite being official, administrative boundaries may not reflect the actual patterns of human settlement or economic activity. Therefore, the team used the Functional Urban Area (FUA) as a complementary definition of the study areas. The FUA is defined by [the Joint Research Centre of the European Commission](https://commission.europa.eu/about/departments-and-executive-agencies/joint-research-centre_en) as the actual urban sprawl and human activities, encompassing the core city and economically or socially integrated surrounding regions. The FUA was obtained from [the Global Human Settlement Layer (GHSL) ](https://human-settlement.emergency.copernicus.eu/)dataset, which provides spatial data for functional urban areas worldwide. 
# 
# The following datasets are considered as input data for the analysis:
# 
# 
# * [Datasets of health facilities](../scripts/Kano/data-inputs/healthcare_facilities.geojson)
# * [Study Area](../../../docs/study-areas/grid-boundary-kano.gpkg) defined by the IDEAMAPS team

# %%
# Set paths to access Kano data
# Define directories
data_inputs = '../scripts/Kano/data-inputs/'
data_temp = '../scripts/Kano/data-temp/'
model_outputs = '../Kano-v2/'

# %% [markdown]
# ## Data Collection

# %% [markdown]
# ### 1.1 Study area and Administrative level 2

# %%
study_area = gpd.read_file(data_inputs + 'grid-boundary-kano.gpkg')
districts = gpd.read_file(data_inputs + 'administrative_level2.geojson')

# %%
# Adding a grid_id to the gridcells in the study area
study_area['grid_id'] = range(len(study_area))

# %% [markdown]
# ### 1.2 General Healthcare Facilities
# 
# Due to the absence of local expert validation, the classification for validation is determine based on the ownership provided in the [GRID3 NGA - Health Facilities v2.0](https://data.grid3.org/datasets/a0ed9627a8b240ff8b315a84575754a4_0/explore).

# %%
healthcare_facilities = gpd.read_file(data_inputs + 'healthcare_facilities.geojson')
healthcare_facilities

# %%
print(healthcare_facilities['ownership'].unique())

# %% [markdown]
# Since local validation of the healthcare facilities was not possible for the Lagos study area, the classfication of facilities offering general healthcare was made based on the ownership provided in the GRID3 NGA - Health Facilities v2.0 dataset.
# - Public: For those where the ownership was reported.
# - Unknown: To not exclude facilities potentially offering general healthcare in slums or other deprived areas.

# %%
facilities = healthcare_facilities[
    healthcare_facilities['ownership'].isin(['Public', 'Unknown'])]

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
# Due to the limited road networks in the slum areas of these three cities, the accessibility of hospitals within a 10-minute range is of significant concern. Therefore, isochrones with 1km walk range and 3.3km car drive range around each hospital were created with the open source tool [OpenRouteService](https://openrouteservice.org/). This might take several minutes depending on the number of health facilities.

# %%
print(facilities['Local Validation'].unique())

# %% [markdown]
# ### 1. Calculating the isochrones for 3.3km driving

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
# ### 2. Calculating the isochrones for 1km walking

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
# ## Spatial joins for the grid and isochrone layers using geopandas
# This study employed the GeoPandas library to perform a spatial join between isochrone data and 100x100m grid cells, which allowed for the analysis and evaluation of accessibility for each grid cell within the study area in these three cities, across different time intervals (specifically by walking or driving). Accessibility was classified as three levels: high, medium and low. The analysis results were exported in GeoPackage format to ensure both the persistent storage and reusability of the data. Additionally, all spatial datasets were maintained in the same coordinate reference system (EPSG:4326), which ensured consistency and accuracy in the spatial joins and subsequent analyses.

# %%
# Read grid cells and isochrones from the GeoPackage file
# Ensure both GeoDataFrames have the same CRS (EPSG:4326)
isochrones_foot_gdf = gpd.read_file(data_temp + 'General_healthcare_iso_1km_walking.gpkg')
isochrones_car_gdf = gpd.read_file(data_temp + 'General_healthcare_iso_3_3km_car.gpkg')

# %% [markdown]
# ### Spatial joins for the grid and isochrone layers using geopandas
# Considering the different column names.

# %%
# We just consider the isochrones for prixary healthcare facilities
isochrones_foot_gdf = isochrones_foot_gdf[isochrones_foot_gdf['Local Validation'] == 'Primary']
isochrones_car_gdf = isochrones_car_gdf[isochrones_car_gdf['Local Validation'] == 'Primary']

# %% [markdown]
# ## Aggregating the results to the grid cell level 

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
# ### Define the categories for healtcare access deprivation based on the critera.

# %%
# If needed, read the gridcells and isochrones from the GeoPackage file
study_area = gpd.read_file(data_temp + 'grid_count_iso_1km_3_3km.gpkg')
study_area

# %%
study_area["result"] = study_area.apply(
    lambda row: 2 if row["iso_walk_1k_count"] <= 1
    else 1 if (row["iso_walk_1k_count"] < 4) or (row["iso_3_3km_count"] < 15)
    else 0,
    axis=1
)

study_area

# %% [markdown]
# Define the focus areas

# %%
study_area["focused"] = study_area.apply(
    lambda row: 1 if (1 <= row["iso_walk_1k_count"] <= 2) # and (row["iso_3_3km_count"] < 10)
    else 0,
    axis=1
)

# %%
# Save output as a GeoPackage file
study_area.to_file(data_temp + 'general_healthcare_outputs.gpkg', driver="GPKG")

# %%
# Save Output as CSV file
study_area.to_csv(model_outputs + 'output.csv', 
                           columns=['latitude', 'longitude', 'lat_min', 'lat_max', 'lon_min', 'lon_max', 'result', 'focused'],
                           index=False)

# %% [markdown]
# ## Further analysis

# %%
# Scatter plot with count of isochrone
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


