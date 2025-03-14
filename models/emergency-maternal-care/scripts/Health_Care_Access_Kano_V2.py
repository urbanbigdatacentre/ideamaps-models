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
ors = client.Client(key=api_key)

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

health_facilities_validated = data_inputs + 'Healthcare_facilities_validated.csv'
healthcare_facilities = pd.read_csv(health_facilities_validated)

# +
# Filter the rows where the 'Validation of HCFs Categorization' column Public/Private Basic EmOC
valid_categories = ['Public Comprehensive EmOC']
healthcare_facilities = healthcare_facilities[healthcare_facilities['Validation of HCFs Categorization'].isin(valid_categories)]

# Create geometry column from longitude and latitude
healthcare_facilities['geometry'] = [Point(np.array([lon, lat])) for lon, lat in zip(healthcare_facilities['longitude'], healthcare_facilities['latitude'])]

# Convert to GeoDataFrame with the correct CRS
healthcare_facilities = gpd.GeoDataFrame(healthcare_facilities, geometry='geometry', crs="EPSG:4326")

# Save the filtered GeoDataFrame as a GeoPackage
healthcare_facilities.to_file(data_inputs + 'healthcare_facilities_validated.gpkg', driver="GPKG")
# -

healthcare_facilities

# ### Population Grid Data (1km resolution) from WorldPop

FUA = gpd.read_file(data_inputs + 'functional_area.gpkg')
# Read the raster dataset
raster_path = data_inputs + 'nga_f_15_49_2015_1km.tif'

# +
# Ensure raster dataset is open within the 'with' block
with rasterio.open(raster_path) as dataset:
    population_data = dataset.read(1)  # Read the first band of the raster
    transform = dataset.transform  # Get affine transformation parameters
    
    # Clip the raster using the FUA geometry
    geometries = [FUA.geometry.unary_union.__geo_interface__]
    clipped_image, clipped_transform = mask(dataset, geometries, crop=True)

    # Update the metadata for the clipped image
    clipped_meta = dataset.meta.copy()
    clipped_meta.update({
        "height": clipped_image.shape[1],
        "width": clipped_image.shape[2],
        "transform": clipped_transform
    })
    
    # Extract the centroids of non-zero population grid cells from the clipped image
    rows, cols = np.where(clipped_image[0] > 0)  # Use clipped_image to get non-zero population
    grid_cells = [[*transform * (col + 0.5, row + 0.5)] for row, col in zip(rows, cols)]

    # Get the population values for these non-zero grid cells
    population_values = clipped_image[0][rows, cols]  # Extract population values for non-zero cells

# Filter out grid cells with population greater than 50
grid_cells_filtered = []
population_filtered = []

for i in range(len(population_values)):
    if population_values[i] > 50:  # Only include grid cells with population > 50
        grid_cells_filtered.append(grid_cells[i])
        population_filtered.append(population_values[i])

# +
# Save the grid cells (centroids) with population data to a CSV
grid_df = pd.DataFrame(grid_cells, columns=["longitude", "latitude"])
grid_df['population'] = population_values  # Add the population count for each grid cell

# Generate unique grid codes
uid_set = set()
def generate_unique_uid():
    uid = np.random.randint(10000, 100000)
    while uid in uid_set:
        uid = np.random.randint(10000, 100000)
    uid_set.add(uid)
    return uid

grid_df['grid_code'] = [generate_unique_uid() for _ in range(len(grid_df))]

# Save the DataFrame to CSV
grid_csv_path = data_inputs + 'population_centroids.csv'
grid_df.to_csv(grid_csv_path, index=False)
# -

grid_df

# ## 2. Spatial Analysis Pipeline
# ### Using OpenRouteService (ORS) Matrix API to calculate the travel time and distance from each population grid centroid to the nearest healthcare facility 

# insert your ORS api key
api_key = '5b3ce3597851110001cf6248ff032155cbce4db1a0e2e70efb739a13'
client = openrouteservice.Client(key=api_key)

healthcare_facilities = gpd.read_file(data_inputs + 'healthcare_facilities_validated.gpkg')
grid_df = gpd.read_file(data_inputs + 'population_centroids.gpkg')

origin_gdf = grid_df
origin_name_column = 'grid_code'
destination_gdf = healthcare_facilities.dropna(subset=['geometry'])
destination_name_column = 'facility_name'

# +
origin_gdf["longitude"] = origin_gdf.geometry.x
origin_gdf["latitude"] = origin_gdf.geometry.y

destination_gdf["longitude"] = destination_gdf.geometry.x
destination_gdf["latitude"] = destination_gdf.geometry.y
# -

origins = list(zip(origin_gdf.geometry.x, origin_gdf.geometry.y))
destinations = list(zip(destination_gdf.geometry.x, destination_gdf.geometry.y))
locations = origins + destinations

origins_index = list(range(0, len(origins)))
destinations_index = list(range(len(origins), len(locations)))

# +
batch_size = 20 # batch processing, 20 grids per time
request_counter = 0
duration_matrix = []

for i in range(0, len(origins), batch_size):
    if request_counter == 40:
        time.sleep(60)
        request_counter = 0  

    sources_batch = origins[i:i + batch_size]
    body = {
        "locations": sources_batch + destinations,
        "sources": list(range(len(sources_batch))),  
        "destinations": list(range(len(sources_batch), len(sources_batch) + len(destinations))),  
        "metrics": ['distance', 'duration']
    }

    try:
        response = requests.post('https://api.openrouteservice.org/v2/matrix/driving-car', json=body, headers=headers)
        response.raise_for_status()  

        duration_matrix.append(response.json())
        request_counter += 1

        if len(duration_matrix) % 50 == 0:
            time.sleep(20)

    except requests.exceptions.RequestException as err:
        time.sleep(10)

print(f"Completed {len(duration_matrix)} requests.")

# +
response = requests.post('https://api.openrouteservice.org/v2/matrix/driving-car', json=body, headers=headers)

print(f"Status Code: {response.status_code}")

print(f"Response Content: {response.text}")
# -

distances = response.json()['distances']
distances

durations = response.json()['durations']
durations

# +
for origin_index, item in origin_gdf.iterrows():
    origin_name = item[origin_name_column]
    origin_x = item.geometry.x
    origin_y = item.geometry.y
    origin_durations = durations[origin_index]

    min_duration, min_index = min((duration, idx) for idx, duration in enumerate(origin_durations))
    destination_index = destinations_index[min_index]
    destination_x, destination_y = locations[destination_index]

    distance = distances[origin_index][min_index]

    filtered = healthcare_facilities[
        (destination_gdf.geometry.x == destination_x) & (destination_gdf.geometry.y == destination_y)
    ]

    if not filtered.empty:
        destination_row = filtered.iloc[0]
        destination_name = destination_row[destination_name_column]
        
duration_matrix.append(
    [origin_name, origin_y, origin_x, destination_name, destination_y, destination_x, distance, min_duration])
# -

# Origin: population grid cell, Desitination: HCF
results_df = pd.DataFrame(results, columns=["origin_name","origin_lon", "origin_lat", "destination_name","dest_lon", "dest_lat", "distance", "duration"])
output_csv = data_inputs + 'nearest_facility_travel_time.csv'
results_df.to_csv(output_csv, index=False)

matrix_df = pd.DataFrame(duration_matrix, 
                  columns =['origin_name', 'origin_lon', 'origin_lat', 'destination_name', 'dest_lon', 'dest_lat', 'distance', 'duration'])
matrix_df

# +
output_file = 'matrix.gpkg'
output_path = os.path.join(output_folder, output_file)

origin_gdf.to_file(driver='GPKG', filename=output_path, layer='origins')
destination_gdf.to_file(driver='GPKG', filename=output_path, layer='destinations')
matrix_gdf.to_file(driver='GPKG', filename=output_path, layer='duration_matrix')
# -

# ## Enhanced Two-Step Floating Catchment Area (E2SFCA) method

origin_dest = pd.read_csv(data_inputs + 'nearest_facility_travel_time.csv')

# Function
from math import *
d = 10 * 60 # try max duration 10mins car
W = 0.1
beta = - d ** 2 / log(W)
print(beta)

# Generate a unique code for Each HCF
origin_dest['unique_code'] = origin_dest[['dest_lon', 'dest_lat']].apply(lambda x: hash(tuple(x)), axis=1)
origin_dest['grid_code'] = origin_dest[['origin_lon', 'origin_lat']].apply(lambda x: hash(tuple(x)), axis=1)

print(origin_dest.head())

# +
# Convert 'duration' to numeric, coercing errors to NaN
origin_dest['duration'] = pd.to_numeric(origin_dest['duration'], errors='coerce')

# Drop rows with NaN values in 'duration' column
origin_dest = origin_dest.dropna(subset=['duration'])
origin_dest['grid_code'] = pd.to_numeric(origin_dest['grid_code'], errors='coerce')

origin_dest_acc = origin_dest  # Backup
# -

# Apply Gaussian decay function to calculate the weight of each grid to healthcare facilities based on the travel duration. d is the travel time and beta is the decay parameter previously calculated.
# The weight decreases as the duration increases, meaning facilities that are further away have less impact.
origin_dest_acc['Weight'] = origin_dest_acc['duration'].apply(lambda d: round(math.exp(-d**2/beta), 8))


# Compute the Weighted Population (Pop_W), the population of each grid cell is multiplied by the corresponding weight to calculate the weighted population.
origin_dest_acc['Pop_W'] = origin_dest_acc['grid_code'] * origin_dest_acc['Weight']

# Sum the Weighted Population for Each Healthcare Facility
# It aggregates the population from all grid cells contributing to each healthcare facility
origin_dest_sum = origin_dest_acc.groupby(by='unique_code')['Pop_W'].sum().reset_index()

# Merge the Sum of Weighted Population Back into the Original Data
origin_dest_acc = origin_dest_acc.merge(origin_dest_sum, on='unique_code')

# supply value is set to 1 for simplicity (capacity of HCF)
supply = 1
origin_dest_acc = origin_dest_acc.rename(columns={'Pop_W_y': 'Pop_W_S'})  # Pop_W_S: Population Weight Sum

# Compute the Supply-Demand Ratio (Rj)
origin_dest_acc['supply_demand_ratio'] = 1 / origin_dest_acc.Pop_W_S
origin_dest_acc['supply_demand_ratio'].replace([np.inf, np.nan], 0, inplace=True)

# Calculate Rj * Weight for Each Grid Cell
origin_dest_acc['supply_W'] = origin_dest_acc['supply_demand_ratio'] * origin_dest_acc.Weight

# Compute Accessibility Index (Ai) for Each Grid Cell
origin_dest_acc['Accessibility'] = origin_dest_acc.groupby('grid_code')['supply_W'].transform('sum')

# +
# Normalize
from sklearn.preprocessing import MinMaxScaler

scaler = MinMaxScaler()
origin_dest_acc['Accessibility_standard'] = scaler.fit_transform(origin_dest_acc[['Accessibility']])
# -

origin_dest_acc




