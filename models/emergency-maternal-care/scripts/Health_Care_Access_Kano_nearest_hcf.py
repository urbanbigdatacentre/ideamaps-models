# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.14.1
#   kernelspec:
#     display_name: Python
#     language: python
#     name: python3
# ---

# # Analysis of Emergency Obstetric Care (EmOC) in Kano
# > Note: All notebooks need the [environment dependencies](https://github.com/GIScience/openrouteservice-examples#local-installation)
# > as well as an [openrouteservice API key](https://openrouteservice.org/dev/#/signup) to run
#
# prepare environment dependencies document

# ## Abstract
# The rapid growth of urban areas has put substantial pressure on local services and infrastructure, particularly in African cities. With migrants moving into cities and transient households moving within cities, traditional means of collecting data (e.g., censuses and household surveys) are inadequate and often overlook informal settlements and households. As a consequence, there is a chronic lack of basic data about deprived households and entire settlements. Given that urban poor residents rely predominantly on private and informal service providers for healthcare and other services, they are rarely captured in routine service data, including health information management systems. This is even more critical for women in need of maternal health care. 
#
# Considering the different phases of maternity: antenatal care, interpartern or delivery, and postnatal care, the team decided to focus on interpartern or delivery phase being the most critical. The intertwined relationship between maternal health care and urban deprivation has been documented and described in the literature [Abascal et al., 2022](https://doi.org/10.1016/j.compenvurbsys.2022.101770). The IDEAMAPS Data Ecosystem team aims to analyse the conditions in which vulnerable communities relate to emergency maternal care (EmOC) in the city of Kano. To do so, the analysis is divided into three main components: 
# 1. **EmOC Offer**: Based on the geospatial database of travel times [(Macharia et al., 2023)](https://doi.org/10.1038/s41597-023-02651-9) and the team's field validation, we characterised 145 HC facilities offering EmOC in Kano, their service levels and relative costs.
# 2. **EmOC Accessibility**: The team used different routing services, including the OSM-based openrouteservice API, to calculate the travel times to the nearest EmOC facility for each 100x100m grid cell in Kano. 
# 3. **EmOC Demand**: The team discussed a set of socio-economic factors that determine the way communities from slums and other deprived areas demand or interact with EmOC services such as available income, employment, education, age, medical practitioners' age and gender as well as religious beliefs and social practices. despite not having access to specific data, the team discussed the potential impacts on demand for EmOC services in Kano based on these factors.
#
#
#
# ### Workflow:
#
# The notebook gives an overview of the distribution of centres offering EmOC in Kano, their classification and how they can be accessed by car. Open source data from OpenStreetMap and tools (such as the openrouteservice) were used to create accessibility measures such as travel times and isochrones. Spatial analysis and other data analytics functions led to generating outputs within the 100x100m grid cells that categorised them into three levels: low, medium, and high.
#
# * **Preprocessing**: Get data for EmOC facilities.
# * **Analysis for Offer**:
#     * Filter and classify EmOC facilities based on discussed criteria.
#     * Visualise EmOC faccilities in their categories.
# * **Analysis for Accessibility**:
#     * Compute travel times to facilities using openrouteservice API or other routing services.
#     * Generate areas for low, medium and high categories based on discussed criteria.
# * **Analysis for Demmand**:
#     * Derive socio-economic descriptors based on discussed criteria.
# * **Result**: Visualize results as maps and export model outputs.
#
#
# ### Datasets and Tools:
# * [A geospatial database of close to reality travel times to obstetric emergency care in 15 Nigerian conurbations](https://figshare.com/s/8868db0bf3fd18a9585d) - A curated list of health care facilities offering EmOC in Nigeria [(Macharia et al., 2023)](https://doi.org/10.1038/s41597-023-02651-9).
# * [openrouteservice](https://openrouteservice.org/) - generate isochrones on the OpenStreetMap road network
#

# # Python Workflow

# This study integrates various Python geospatial analysis libraries and packages to support spatial data processing, visualization, and isochrone generation. The os module is used to interact with the operating system, managing file paths and reading environment variables such as API keys. folium library along with its MarkerCluster plugin, facilitates the creation of interactive maps for visualizing large-scale geospatial data. The openrouteservice.client serves as an interface to the OpenRouteService API, enabling the extraction of isochrones. pandas library for data analysis, provides functions for analyzing, cleaning, exploring, and manipulating data, while fiona supports reading and writing real-world data using multi-layered GIS formats, such as shapefiles. The shapely package is employed for the manipulation and analysis of planar geometric objects.

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

# +
import os
from IPython.display import display
import requests

import folium
from folium.plugins import MarkerCluster
import openrouteservice
import time

import time
import pandas as pd
import numpy as np
import fiona as fn
import geopandas as gpd
from shapely.geometry import shape, mapping
from shapely.geometry import Point
from shapely.geometry import box
from scipy.spatial import cKDTree
from tqdm import tqdm

import rasterio
from rasterio.transform import xy
from rasterio.mask import mask
import rasterstats as rs
import math
# -


# ## Preprocessing
# In this study, users first requested an ORS Matrix API key from the [OpenRouteService](https://openrouteservice.org/) platform and subsequently interacted with the OpenRouteService API through the instantiation of the OpenRouteService client. This is the OpenRouteService [API documentation](https://openrouteservice.org/dev/#/api-docs/introduction) for ORS Core-Version 9.0.0. 
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

# Read the api key from the .env file
from dotenv import load_dotenv
# %load_ext dotenv
# %dotenv
api_key = os.getenv('OPENROUTESERVICE_API_KEY')
client = openrouteservice.Client(key=api_key)

# For this study different kind of data were used. The dataset on healthcare facilities is sourced from a research ([Macharia, P.M. et al., 2023](https://doi.org/10.1038/s41597-023-02651-9)) which provides A geospatial database of close-to-reality travel times to obstetric emergency care in 15 Nigerian conurbations. The dataset were filtered by state name to isolate facilities in Kano and converted CSV file to shapefile based on coordinates using [QGIS](https://qgis.org/). 
#
# The Level 2 administrative boundary data is sourced from [Humanitarian Data Exchange](https://data.humdata.org/) were used to correlate the isochrones and healthcare facility distribution with specific administrative regions. The data were filtered based on the administrative region name (lganame) to focus the analysis on Kano.
#
# Despite being official, administrative boundaries may not reflect the actual patterns of human settlement or economic activity. Therefore, the team used the Functional Urban Area (FUA) as a complementary definition of the study areas. The FUA is defined by [the Joint Research Centre of the European Commission](https://commission.europa.eu/about/departments-and-executive-agencies/joint-research-centre_en) as the actual urban sprawl and human activities, encompassing the core city and economically or socially integrated surrounding regions. The FUA was obtained from [the Global Human Settlement Layer (GHSL) ](https://human-settlement.emergency.copernicus.eu/)dataset, which provides spatial data for functional urban areas worldwide. 
#
# * [Datasets of health facilities](https://doi.org/10.6084/m9.figshare.22689667.v2) (15/07/2023)
# * [Shapefile of district boundaries](https://data.humdata.org/dataset/nigeria-admin-level-2) - Admin Level 2 (data from Humanitarian Data Exchange, 25/11/2015)
# * [Functional Urban Areas](https://human-settlement.emergency.copernicus.eu/download.php?ds=FUA) - data from Global Human Settlement Layer(2015)

# Set paths to access data
# Define directories
data_inputs = '../scripts/data_inputs/'
data_temp = '../scripts/data_temp/'
data_outputs = '../scripts/data_outputs/'

# ## 1. Data Collection

# ### Validated healthcare facilities
# note: to describe the process to validate healthcare facilities

healthcare_facilities_validated = gpd.read_file(data_inputs + 'healthcare_facilities_validated_Mar2025.geojson')

healthcare_facilities_validated

# ### Population Grid Data (1km resolution) from WorldPop
# note: explain the rational for female population between 15-49 years old

study_area = gpd.read_file(data_inputs + '100mGrid.gpkg')
raster_path = data_inputs + 'nga_f_15_49_2015_1km.tif'

# Clipping the population data to our study area

with rasterio.open(raster_path) as dataset:
    geometries = [study_area.geometry.unary_union.__geo_interface__]
    clipped_image, clipped_transform = mask(dataset, geometries, crop=True)
    band1 = clipped_image[0] # Read the first band of the raster

# Calculating the centroids for grid cells

rows, cols = np.where(band1 > 0)
grid_cells = [clipped_transform * (col + 0.5, row + 0.5) for row, col in zip(rows, cols)]
population_values = band1[rows, cols]

# +
grid_df = pd.DataFrame(grid_cells, columns=["longitude", "latitude"])
grid_df["population"] = population_values

grid_df["grid_code"] = np.random.choice(range(10000, 99999), size=len(grid_df), replace=False)
centroids_gdf = gpd.GeoDataFrame(grid_df, geometry=[Point(xy) for xy in zip(grid_df["longitude"], grid_df["latitude"])])
centroids_gdf.set_crs("EPSG:4326", inplace=True)

centroids_gdf.to_file(data_temp + "population_centroids.gpkg", driver="GPKG")
# -

centroids_gdf

# ## 2. Spatial Analysis Pipeline 
# ### Using OpenRouteService (ORS) Matrix API to calculate the travel time and distance from each population grid centroid to the healthcare facility 
#
# note: this will generate a file 'OD_matrix_healthcare_pop_grid'

origin_gdf = centroids_df
origin_name_column = 'grid_code'
destination_gdf = healthcare_facilities.dropna(subset=['geometry'])
destination_name_column = 'facility_name'

origins = list(zip(origin_gdf.geometry.x, origin_gdf.geometry.y))

destinations = list(zip(destination_gdf.geometry.x, destination_gdf.geometry.y))

locations = origins + destinations

origins_index = list(range(0, len(origins)))
destinations_index = list(range(len(origins), len(locations)))

# +
body = {'locations': locations,
       'destinations': destinations_index,
       'sources': origins_index,
       'metrics': ['distance', 'duration']}

headers = {
    'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
    'Authorization': api_key,
    'Content-Type': 'application/json; charset=utf-8'
}

response = requests.post('https://api.openrouteservice.org/v2/matrix/driving-car', json=body, headers=headers)
# -

distances = response.json().get('distances', [])
durations = response.json().get('durations', [])

# +
distances_duration_matrix = []

# Iterate over each origin (grid)
for origin_index, origin in origin_gdf.iterrows():
    origin_name = origin[origin_name_column]
    origin_x = origin.geometry.x
    origin_y = origin.geometry.y
    origin_distances = distances[origin_index]
    origin_durations = durations[origin_index]

    # find the minimum duration and the index of the minimum duration
    min_duration = min(origin_durations)
    min_index = origin_durations.index(min_duration)
    destination_index = destinations_index[min_index]
    dest_x, dest_y = locations[destination_index]
    filtered = healthcare_facilities[(destination_gdf.geometry.x == dest_x) & (destination_gdf.geometry.y == dest_y) ]
    destination_row = filtered.iloc[0]
    dest_name = destination_row[destination_name_column]

        # Append both the distance and duration for this origin-destination pair
    distances_duration_matrix.append([
            origin_name, origin_y, origin_x,
            dest_name, dest_y, dest_x,
            min_duration
        ])

# Convert the results into a DataFrame
matrix_df = pd.DataFrame(distances_duration_matrix, columns=[
    'grid_code','origin_lat', 'origin_lon',
    'destination_name', 'dest_lat', 'dest_lon','min_duration'
])
# -

# Save to CSV
merged_df = pd.merge(matrix_df, grid_df[['grid_code', 'population']], on='grid_code', how='left')
merged_df.to_csv(data_temp + 'distance_duration_matrix_temp.csv', index=False)

merged_df

# +
geometry = [Point(xy) for xy in zip(merged_df['dest_lon'], merged_df['dest_lat'])]
gdf = gpd.GeoDataFrame(merged_df, geometry=geometry, crs="EPSG:4326")

gpkg_path = data_temp + 'distance_duration_matrix_temp.gpkg'
gdf.to_file(gpkg_path, layer="duration_matrix", driver="GPKG")
# -

#
#
#
#
#
#
#
#
#
#
#
#

# ## Processing OD Matrix

matrix_df = pd.read_csv(data_temp +'OD_matrix_healthcare_pop_grid.csv')

matrix_df

# We will select one facility for each gird cell

# +
# 1. Calculate the minimum duration_seconds for each destination_id
shortest_times = matrix_df.groupby("destination_rowid_id")["duration_seconds"].min().reset_index()

# 2. Use idxmin() to ensure each destination_id only keeps the row with the shortest duration_seconds
idx_min_duration = matrix_df.groupby('destination_rowid_id')['duration_seconds'].idxmin()

# 3. Keep only the rows with the shortest duration_seconds for each destination_id
matrix_df_min = matrix_df.loc[idx_min_duration]

# 4. Merge the shortest times with matrix_df
matrix_df = matrix_df_min.merge(shortest_times, on=["destination_rowid_id", "duration_seconds"], how="inner")
# -

matrix_df

centroids_df = gpd.read_file(data_temp + 'population_centroids_ROWID.geojson')

centroids_df

pop_centroids_closest_hcf = centroids_df.merge(matrix_df, left_on="rowid", right_on="destination_rowid_id", how="left")

pop_centroids_closest_hcf

pop_centroids_closest_hcf = pop_centroids_closest_hcf.rename(columns={
    "longitude": "origin_lon",
    "latitude": "origin_lat",
    "rowid": "grid_id",
    "origin_hcf_id": "hcf_uid"
})
columns_to_keep = ["origin_lon", "origin_lat", "population", "grid_id", "geometry", "hcf_uid", "duration_seconds", "distance_km"]
pop_centroids_closest_hcf = pop_centroids_closest_hcf[columns_to_keep]

pop_centroids_closest_hcf

distances_duration_matrix = pd.merge(pop_centroids_closest_hcf, healthcare_facilities_validated[['hcf_id', 'facility_name', 'longitude', 'latitude']], 
                     left_on='hcf_uid', right_on='hcf_id', how='left')

distances_duration_matrix = distances_duration_matrix.rename(columns={
    "longitude": "dest_lon",
    "latitude": "dest_lat"
})

distances_duration_matrix

# Review and remove
origin_dest = distances_duration_matrix

# ## Enhanced Two-Step Floating Catchment Area (E2SFCA) method

# Function
from math import *
d = 10 * 60 # try max duration 10mins/30mins car, under estimation of travel time and traffic condition realted to the selected data sourse 
W = 0.5
beta = - d ** 2 / log(W)
print(beta)

print(origin_dest.head())

# +
# Convert 'duration' to numeric, coercing errors to NaN
origin_dest['duration_seconds'] = pd.to_numeric(origin_dest['duration_seconds'], errors='coerce')

# Drop rows with NaN values in 'duration' column
origin_dest = origin_dest.dropna(subset=['duration_seconds'])
origin_dest['grid_id'] = pd.to_numeric(origin_dest['grid_id'], errors='coerce')

origin_dest_acc = origin_dest  # Backup
# -

# Apply Gaussian decay function to calculate the weight of each grid to healthcare 
# facilities based on the travel duration. d is the travel time and beta is the decay 
# parameter previously calculated.
# The weight decreases as the duration increases, meaning facilities that are further away have less impact.
origin_dest_acc['Weight'] = origin_dest_acc['duration_seconds'].apply(lambda d: round(math.exp(-d**2/beta), 8))


# Compute the Weighted Population (Pop_W), the population of each grid cell is multiplied 
# by the corresponding weight to calculate the weighted population.
origin_dest_acc['Pop_W'] = origin_dest_acc['population'] * origin_dest_acc['Weight']

origin_dest_acc

# Sum the Weighted Population
origin_dest_sum = origin_dest_acc.groupby(by='hcf_id')['Pop_W'].sum().reset_index()

origin_dest_sum

# Merge the Sum of Weighted Population Back into the Original Data
origin_dest_acc = origin_dest_acc.merge(origin_dest_sum, on='hcf_id')

origin_dest_acc

# supply value is set to 1 for simplicity (capacity of HCF)
supply = 1
# in the future, we will link supply with ownership and EmOC service level
origin_dest_acc = origin_dest_acc.rename(columns={'Pop_W_y': 'Pop_W_S'})  # Pop_W_S: Population Weight Sum

# Compute the Supply-Demand Ratio (Rj)
origin_dest_acc['supply_demand_ratio'] = 1 / origin_dest_acc.Pop_W_S
origin_dest_acc['supply_demand_ratio'].replace([np.inf, np.nan], 0, inplace=True)

# Calculate Rj * Weight for Each Grid Cell
origin_dest_acc['supply_W'] = origin_dest_acc['supply_demand_ratio'] * origin_dest_acc.Weight

# Compute Accessibility Index (Ai) for Each Grid Cell
origin_dest_acc['Accessibility'] = origin_dest_acc.groupby('grid_id')['supply_W'].transform('sum')

# +
# Normalize
from sklearn.preprocessing import MinMaxScaler

scaler = MinMaxScaler()
origin_dest_acc['Accessibility_standard'] = scaler.fit_transform(origin_dest_acc[['Accessibility']])
# -

origin_dest_acc

max(origin_dest_acc.Accessibility_standard)

# +
geometry = [Point(xy) for xy in zip(origin_dest_acc['origin_lon'], origin_dest_acc['origin_lat'])]
gdf = gpd.GeoDataFrame(origin_dest_acc, geometry=geometry, crs="EPSG:4326")

gpkg_path = data_outputs + 'acc_score_closest.gpkg'
gdf.to_file(gpkg_path, layer="acc_score_closest", driver="GPKG")
# -


