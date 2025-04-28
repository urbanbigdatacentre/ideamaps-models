# %% [markdown]
# # Analysis of Emergency Maternal Care Deprivation in Kano and Lagos, Nigeria
# > Note: This notebook requires the local environment dependencies listed in our [requirements.txt] (requirements.txt) file. Use this file to install the required packages in a virtual environment.
# 
# > To excecute OpenRouteService functions, it is required to install the [library dependencies](https://github.com/GIScience/openrouteservice-examples#local-installation). You should either have an [openrouteservice API key](https://openrouteservice.org/dev/#/signup) or a local ORS environment to complete the analysis.
# 
# The model concepts and processes are described in our documentation. The [Dataset-interpretability](https://github.com/urbanbigdatacentre/ideamaps-models/blob/a4084fb650424ac575941cdacb71421aa882bae4/models/emergency-maternal-care/kano/dataset-interpretability.md) file describes the rationale behind this model.

# %% [markdown]
# ## Workflow:
# The notebook is divided into the following sections:
# 
# 1. Initial Setup
# 2. Data Preparation
# 3. Travel time estimates
# 4. Two-step floating catchment area (2SFCA) analysis
# 5. Results

# %% [markdown]
# ## 1. Initial Setup

# %% [markdown]
# ## Setting up the virtual environment
# 
# ```bash
# # Create a new virtual environment
# # It is recommended to create this virtual environment in the scripts folder
# python -m venv .venv
# 
# # Activate the virtual environment
# source .venv/bin/activate
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
from scipy.spatial import cKDTree
from tqdm import tqdm

import rasterio
from rasterio.transform import xy
from rasterio.mask import mask
import rasterstats as rs
import math

from pathlib import Path
from shapely.geometry import Polygon

# Used for scaling the data
from sklearn.preprocessing import MinMaxScaler

# Used for data analysis and visualization
import seaborn as sns
import matplotlib.pyplot as plt



# %% [markdown]
# ## Preprocessing
# In this study, users first requested an ORS Matrix API key from the [OpenRouteService](https://openrouteservice.org/) platform and subsequently interacted with the OpenRouteService API through the instantiation of the OpenRouteService client. This is the OpenRouteService [API documentation](https://openrouteservice.org/dev/#/api-docs/introduction) for ORS Core-Version 9.0.0. 
# 
# Generate a [API Key](https://openrouteservice.org/dev/#/home?tab=1) (Token) it is necessary to sign up at the OpenRouteService dashboard by using your E-mail address or sign up with your GitHub. After logging in, go to the Dashboard by clicking on your profile icon and navigate to the API Keys section. Click "Create API Key" to generate a free key and then choose a service plan (the free plan has limited requests per day). Copy the API Key and store it securely. 
# 
# OpenRouteService primarily uses API keys for authentication. However, if a token is required for certain endpoints, you can send a request with your API key in the Authorization header. This process facilitated various geospatial analysis functions, including isochrone generation.
# 

# %% [markdown]
# ### Option 1: Using an ORS API Key
# Make sure you have a .env file in the root directory with the following content:
# ```bash
#     OPENROUTESERVICE_API_KEY='your_api_key'
# ```

# %%
# %%
# Read the api key from the .env file
from dotenv import load_dotenv
%load_ext dotenv
%dotenv
api_key = os.getenv('OPENROUTESERVICE_API_KEY')
client = openrouteservice.Client(key=api_key)

# %% [markdown]
# ### Option 2: Using a local ORS service
# Make sure you have set a local service that runs the OSM-based ORS API. 
# ```r
#     # Insert R code from the local ORS service
# ```

# %% [markdown]
# For this study different kind of data were used. The dataset on healthcare facilities is sourced from a research ([Macharia, P.M. et al., 2023](https://doi.org/10.1038/s41597-023-02651-9)) which provides A geospatial database of close-to-reality travel times to obstetric emergency care in 15 Nigerian conurbations. The dataset were filtered by state name to isolate facilities in Kano and converted CSV file to shapefile based on coordinates using [QGIS](https://qgis.org/). 
# 
# The Level 2 administrative boundary data is sourced from [Humanitarian Data Exchange](https://data.humdata.org/) were used to correlate the isochrones and healthcare facility distribution with specific administrative regions. The data were filtered based on the administrative region name (lganame) to focus the analysis on Kano.
# 
# Despite being official, administrative boundaries may not reflect the actual patterns of human settlement or economic activity. Therefore, the team used the Functional Urban Area (FUA) as a complementary definition of the study areas. The FUA is defined by [the Joint Research Centre of the European Commission](https://commission.europa.eu/about/departments-and-executive-agencies/joint-research-centre_en) as the actual urban sprawl and human activities, encompassing the core city and economically or socially integrated surrounding regions. The FUA was obtained from [the Global Human Settlement Layer (GHSL) ](https://human-settlement.emergency.copernicus.eu/)dataset, which provides spatial data for functional urban areas worldwide. 
# 
# * [Datasets of health facilities](https://doi.org/10.6084/m9.figshare.22689667.v2) (15/07/2023)
# * [Shapefile of district boundaries](https://data.humdata.org/dataset/nigeria-admin-level-2) - Admin Level 2 (data from Humanitarian Data Exchange, 25/11/2015)
# * [Functional Urban Areas](https://human-settlement.emergency.copernicus.eu/download.php?ds=FUA) - data from Global Human Settlement Layer(2015)

# %% [markdown]
# ### Option 1: Kano
# If you want to process data for the city of Kano, use the following code to filter the dataset. 
# 

# %%
# Set paths to access Kano data
# Define directories
data_inputs = '../scripts/Kano/data-inputs/'
data_temp = '../scripts/Kano/data-temp/'
model_outputs = '../kano/'

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
# ### 1.1 Validated healthcare facilities for Kano
# note: to describe the process to validate healthcare facilities

# %%
healthcare_facilities_validated = gpd.read_file(data_inputs + 'healthcare_facilities.geojson')

# %%
healthcare_facilities_validated

# %% [markdown]
# ### 1.2 Healthcare facilities in Lagos
# note: Due to the absence of local expert validation in Lagos, the classification for validation is determine based on the ownership provided in the [datasets of health facilities](https://doi.org/10.6084/m9.figshare.22689667.v2).

# %%
healthcare_facilities_validated = gpd.read_file(data_inputs + 'healthcare_facilities.geojson')

# %% [markdown]
# To assing the healthcare facilities to the different categories, we used the following criteria:
# - **Public**: Facilities owned by the government (1), the military (3) or the police (6) health authorities. 
# - **Private**: Facilities owned by private individuals or other organizations.

# %%
conditions = [
    healthcare_facilities_validated['specific_owner'].isin([1, 3, 6]),
    healthcare_facilities_validated['specific_owner'].isin([2, 4, 5])
]
choices = ['Public Comprehensive EmOC', 'Private Comprehensive EmOC']

# Explicitly set the default to a string
healthcare_facilities_validated['Validation'] = np.select(
    conditions, choices, default='Other'
)

# %%
healthcare_facilities_validated

# %% [markdown]
# ### 2. Population Grid Data (1km resolution) from WorldPop
# note: explain the rational for female population between 15-49 years old
# 
# ** Add a note to explain the process applies for the two cities **

# %%
study_area = gpd.read_file(data_inputs + '100mGrid.gpkg')
raster_path = data_inputs + 'nga_f_15_49_2015_1km.tif'

# %%
with rasterio.open(raster_path) as dataset:
    geometries = [study_area.geometry.unary_union.__geo_interface__]
    clipped_image, clipped_transform = mask(dataset, geometries, crop=True)
    band1 = clipped_image[0] # Read the first band of the raster

# %%
out_meta = dataset.meta.copy()
out_meta.update({
        "height": clipped_image.shape[1],
        "width": clipped_image.shape[2],
        "transform": clipped_transform
    })

# %%
with rasterio.open(data_inputs + 'lagos_nga_f_15_49_2015_1km.tif', "w", **out_meta) as dest:
    dest.write(clipped_image)

# %% [markdown]
# ### Adding population data at 1km grid to 100m grid

# %%
# reading in geotiff file as numpy array
def read_tif(file: Path):
    if not file.exists():
        raise FileNotFoundError(f'File {file} not found')

    with rasterio.open(file) as dataset:
        arr = dataset.read()  # (bands X height X width)
        nodata = dataset.nodata
        transform = dataset.transform
        crs = dataset.crs

    # Replace NoData value with NaN
    if nodata is not None:
        arr[arr == nodata] = np.nan

    return arr.transpose((1, 2, 0)), transform, crs

def raster2vector(arr, transform, crs) -> gpd.GeoDataFrame:
    height, width, bands = arr.shape

    # Generate pixel coordinates
    geometries = []
    pixel_values = []

    for row in range(height):
        for col in range(width):
            x_min, y_max = transform * (col, row)  # Top-left corner
            x_max, y_min = transform * (col + 1, row + 1)  # Bottom-right corner

            pixel_value = arr[row, col].tolist()[0]  # Convert numpy array to list
            polygon = Polygon([(x_min, y_max), (x_max, y_max), (x_max, y_min), (x_min, y_min)])

            geometries.append(polygon)
            pixel_values.append(pixel_value)

    # Convert to DataFrame
    gdf = gpd.GeoDataFrame({'pop_grid_pop': pixel_values, 'geometry': geometries}, crs=crs)

    return gdf

epsg = 'EPSG:32632'

# %%
# Preparing grid
grid_file = data_inputs + '100mGrid.gpkg'
grid = gpd.read_file(grid_file)
grid = grid.to_crs(epsg)
grid['grid_id'] = range(len(grid))
grid = grid[['grid_id', 'geometry','rowid', 'latitude', 'lat_min', 'lat_max', 'longitude', 'lon_min','lon_max']].set_geometry('geometry')
grid

# %%
# Count buildings per grid cell

# Loading Google building footprints
building_file = data_inputs + 'Lagos_GOBv3.gpkg'
buildings = gpd.read_file(building_file)
buildings = buildings.to_crs(epsg)
buildings['centroid'] = buildings['geometry'].centroid

# Joining buildings to grid
grid_buildings = grid.sjoin(buildings.set_geometry('centroid').drop(columns='geometry'), how='inner', predicate='intersects')
grid_buildings = grid_buildings.groupby('grid_id')

# Counting buildings per grid
building_counts = grid_buildings.size().rename('bcount')

# Adding building count to grid cells
grid = grid.merge(building_counts, on='grid_id', how='left')

# Assign building count 0 to cells with no buildings (NaN)
grid['bcount'] = grid['bcount'].fillna(0)
grid

# %%
# Adding population data at 1km grid to finer grid
from pathlib import Path

data_path = Path(data_inputs)

# Loading coarse pop data
pop_file = data_path / 'lagos_nga_f_15_49_2015_1km.tif'
pop_raster, transform, crs = read_tif(pop_file)

# Converting the raster grid to vector data
pop_grid = raster2vector(pop_raster, transform, crs)
pop_grid = pop_grid.to_crs(epsg)
pop_grid['pop_grid_id'] = range(len(pop_grid))
# pop_grid.to_parquet(data_path / 'sanity_check_pop.parquet')

# Assign coarse population data to finer grid based on the centroid locations of the finer grid cells
grid['centroid'] = grid['geometry'].centroid
grid = gpd.sjoin(grid.set_geometry('centroid'), pop_grid, how='left', predicate='within')
print(grid.columns)
grid = grid[['grid_id', 'bcount', 'pop_grid_id', 'geometry','rowid', 'latitude', 'lat_min', 'lat_max',
       'longitude', 'lon_min', 'lon_max']]
grid.head()

# %%


print("Min value in raster:", np.min(pop_raster))


# %%
with rasterio.open(pop_file) as ds:
    print("NoData value:", ds.nodata)


# %%
print(grid['bcount'].sum())

# %%
# Calculate population weight (fraction of total population count that should be assigned to cell based on its building count)
grid_grouped_pop = grid.groupby('pop_grid_id')
building_count_pop = grid_grouped_pop['bcount'].sum().rename('pop_grid_bcount')
grid = grid.merge(building_count_pop, on='pop_grid_id', how='left')
grid['pop_weight'] = grid['bcount'] / grid['pop_grid_bcount']

# Compute disaggregated population count based on weight and building count at coarser cell level
grid = grid.merge(pop_grid, on='pop_grid_id', how='left')
grid['pop'] = grid['pop_grid_pop'] * grid['pop_weight']
grid.head()

# %%
# Saving to file
grid = grid.drop(columns=["geometry_y"])
grid.head()


# %%
grid = grid.set_geometry("geometry_x")
grid = grid.to_crs(4326)
grid.to_file(data_temp + 'pop_grid.gpkg', driver='GPKG')

# %% [markdown]
# ## 3. Estimating travel times (Spatial Analysis Pipeline) 
# ### Using OpenRouteService (ORS) Matrix API to calculate the travel time and distance from each population grid centroid to the healthcare facility 
# 
# note: this will generate a file 'OD_matrix_healthcare_pop_grid'

# %%
origin_gdf = centroids_df
origin_name_column = 'grid_code'
destination_gdf = healthcare_facilities.dropna(subset=['geometry'])
destination_name_column = 'facility_name'

# %%
origins = list(zip(origin_gdf.geometry.x, origin_gdf.geometry.y))

# %%
destinations = list(zip(destination_gdf.geometry.x, destination_gdf.geometry.y))

# %%
locations = origins + destinations

# %%
origins_index = list(range(0, len(origins)))
destinations_index = list(range(len(origins), len(locations)))

# %%
body = {'locations': locations,
       'destinations': destinations_index,
       'sources': origins_index,
       'metrics': ['distance', 'duration']}

# %%
headers = {
    'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
    'Authorization': api_key,
    'Content-Type': 'application/json; charset=utf-8'
}

# %%
response = requests.post('https://api.openrouteservice.org/v2/matrix/driving-car', json=body, headers=headers)

# %%
distances = response.json().get('distances', [])
durations = response.json().get('durations', [])

# %%
distances_duration_matrix = []

# %%
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

# %%
# Convert the results into a DataFrame
matrix_df = pd.DataFrame(distances_duration_matrix, columns=[
    'grid_code','origin_lat', 'origin_lon',
    'destination_name', 'dest_lat', 'dest_lon','min_duration'
])

# %%
# Save to CSV
merged_df = pd.merge(matrix_df, grid_df[['grid_code', 'population']], on='grid_code', how='left')
merged_df.to_csv(data_temp + 'distance_duration_matrix_temp.csv', index=False)

# %%
merged_df

# %%
geometry = [Point(xy) for xy in zip(merged_df['dest_lon'], merged_df['dest_lat'])]
gdf = gpd.GeoDataFrame(merged_df, geometry=geometry, crs="EPSG:4326")

# %%
gpkg_path = data_temp + 'distance_duration_matrix_temp.gpkg'
gdf.to_file(gpkg_path, layer="duration_matrix", driver="GPKG")

# %% [markdown]
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

# %% [markdown]
# ## Selecting the Healthcare facilities pool based on the OD Matrix

# %%
matrix_df = pd.read_csv(data_temp +'lagos-od-matrix-tenclosest.csv')

# need to normalise the filenames

# %%
matrix_df

# %% [markdown]
# **GRID CELLS WITHOUT TRAVEL TIME ESTIMATE**
# If a grid cell has a NULL value in the travel estimate, we will remove it from the analysis. This is because we cannot calculate the 2SFCA without a travel time estimate.

# %%
# Calculate the percentage of missing values in the 'duration_seconds' column
percentage_na = (matrix_df['duration_seconds'].isna().sum() / len(matrix_df)) * 100
print(percentage_na)


# %% [markdown]
# Removing the grid cells with NULL values in the travel time estimate will help us to avoid errors in the analysis.

# %%
# Removing rows with NaN values in the 'duration_seconds' column
matrix_df = matrix_df.dropna(subset=['duration_seconds'])



# %% [markdown]
# ## Combining the OD matrix and the population data
# 
# Population data is the result of combining 1km grid data with 100m grid data. See [Section 2]() for more details.

# %%
# If stating the process here, read the file again
centroids_df = gpd.read_file(data_temp + 'pop_grid.gpkg')

# %%
centroids_df

# %% [markdown]
# Note: The OD matrix contains ids for every grid cell ('destination_id') and the healtcare facilities ('origin_id').
# 

# %%
pop_centroids_hcf = pd.merge(matrix_df, centroids_df[['rowid', 'longitude', 'latitude', 'lon_min', 'lat_min', 'lon_max', 'lat_max','bcount','pop_grid_bcount', 'pop_grid_pop', 'pop', 'geometry']], 
                     left_on='destination_id', right_on='rowid', how='left')

# %%
pop_centroids_hcf

# %% [markdown]
# ## Option 1: Kano

# %% [markdown]
# To make the dataframe easier to read, we will rename the columns in the dataframe.

# %%
pop_centroids_hcf = pop_centroids_hcf.rename(columns={
    "longitude": "origin_lon",
    "latitude": "origin_lat",
    "lon_min": "origin_lon_min",
    "lat_min": "origin_lat_min",
    "lon_max": "origin_lon_max",
    "lat_max": "origin_lat_max",
    "rowid": "grid_id",
    "origin_id": "hcf_uid",
    "pop": "population"
})
columns_to_keep = ["grid_id", "origin_lon", "origin_lat", "origin_lon_min","origin_lat_min","origin_lon_max","origin_lat_max","population", "bcount","pop_grid_bcount", "pop_grid_pop","geometry", "hcf_uid", "duration_seconds", "distance_km"]
pop_centroids_hcf = pop_centroids_hcf[columns_to_keep]

# %%
pop_centroids_hcf

# %%
distances_duration_matrix = pd.merge(pop_centroids_hcf, healthcare_facilities_validated[['hcf_id','facility_name', 'longitude', 'latitude', 'Local_Validation']], 
                     left_on='hcf_uid', right_on='hcf_id', how='left')

# %%
distances_duration_matrix = distances_duration_matrix.rename(columns={
    "longitude": "dest_lon",
    "latitude": "dest_lat"
})
distances_duration_matrix = distances_duration_matrix.drop(columns=['hcf_uid'])

# %% [markdown]
# **Review** descriptions for this procedures

# %%
distances_duration_matrix

# %%
category_counts = healthcare_facilities_validated['Local_Validation'].value_counts()
print(category_counts)

# %%
distances_duration_matrix['Local_Validation'] = distances_duration_matrix['Local_Validation'].replace({
    'Public/Private Basic EmOC': 'Private Basic EmOC',
    'Public/Private comprehensive EmOC (missionary Hospital)': 'Private Comprehensive EmOC'
})

# %%
selected_categories = ['Public Comprehensive EmOC', 'Private Comprehensive EmOC', 
                       'Private Basic EmOC', 'Public Basic EmOC']

# %%
distances_duration_matrix = distances_duration_matrix[
    distances_duration_matrix['Local_Validation'].isin(selected_categories)]

# %%
distances_duration_matrix

# %%
# creat subsets based on categories of 'Validation of HCFs Categorization'
categories = {
    "public_comprehensive_EmOC": ["Public Comprehensive EmOC"],
    "private_comprehensive_EmOC": ["Private Comprehensive EmOC"],
    "private_basic_EmOC": ["Private Basic EmOC"],
    "public_basic_EmOC": ["Public Basic EmOC"]
}

# %%
subsets = {
    key: distances_duration_matrix[
        distances_duration_matrix['Local_Validation'].str.contains('|'.join(values), na=False)
    ]
    for key, values in categories.items()
}

# %%
public_CEmOC = subsets["public_comprehensive_EmOC"]
private_CEmOC = subsets["private_comprehensive_EmOC"]
public_BEmOC = subsets["public_basic_EmOC"]
private_BEmOC = subsets["private_basic_EmOC"]

# %%
public_CEmOC

# %%
# Step 2: Define a function to get 3 smallest duration_seconds per grid_id for each category
def get_closest_3(df, n=3):
    return df.groupby('grid_id').apply(lambda x: x.nsmallest(n, 'duration_seconds')).reset_index(drop=True)

# %%
# If the subsets are already created for each category, we apply the function to each subset:
public_CEmOC_closest_3 = get_closest_3(public_CEmOC)
private_CEmOC_closest_3 = get_closest_3(private_CEmOC)
public_BEmOC_closest_3 = get_closest_3(public_BEmOC)
private_BEmOC_closest_3 = get_closest_3(private_BEmOC)

# %%
# Step 4: Concatenate the filtered results into a single DataFrame
distances_duration_matrix = pd.concat([
    public_CEmOC_closest_3, private_CEmOC_closest_3,
    public_BEmOC_closest_3, private_BEmOC_closest_3
])

# %% [markdown]
# distances_duration_matrix = distances_duration_matrix.groupby('grid_id').apply(lambda x: x.nsmallest(3, 'duration_seconds')).reset_index(drop=True)

# %%
distances_duration_matrix

# %%
geometry = [Point(xy) for xy in zip(distances_duration_matrix['origin_lon'], distances_duration_matrix['origin_lat'])]
gdf = gpd.GeoDataFrame(distances_duration_matrix, geometry=geometry, crs="EPSG:4326")

# %%
gpkg_path = data_temp + 'distances_duration_3_closet_Emoc.gpkg'
gdf.to_file(gpkg_path, layer="distances_duration_3_closet_Emoc", driver="GPKG")

# %%
# Review and remove
origin_dest = distances_duration_matrix

# %% [markdown]
# ## Option 2: Lagos
# This option differ from the Kano option in the validation data being estimated as part of the OD matrix estimation and the selection of healthcare facilities in the pool. 

# %%
pop_centroids_hcf = pop_centroids_hcf.rename(columns={
    "longitude": "origin_lon",
    "latitude": "origin_lat",
    "lon_min": "origin_lon_min",
    "lat_min": "origin_lat_min",
    "lon_max": "origin_lon_max",
    "lat_max": "origin_lat_max",
    "rowid": "grid_id",
    "origin_id": "hcf_uid",
    "pop": "population"
})
columns_to_keep = ["grid_id", "origin_lon", "origin_lat", "origin_lon_min","origin_lat_min","origin_lon_max","origin_lat_max",
                   "population", "bcount","pop_grid_bcount", "pop_grid_pop","geometry", "hcf_uid", "duration_seconds", "distance_km", "validation"]
pop_centroids_hcf = pop_centroids_hcf[columns_to_keep]

# %% [markdown]
# Merging the dataframe than contains the od matrix (with the healthcare facility class) and the population data with the full information about health care facilities.

# %%
distances_duration_matrix = pd.merge(pop_centroids_hcf, healthcare_facilities_validated[['hcf_id','facility_name', 'longitude', 'latitude']], 
                     left_on='hcf_uid', right_on='hcf_id', how='left')

# %%
distances_duration_matrix = distances_duration_matrix.rename(columns={
    "longitude": "dest_lon",
    "latitude": "dest_lat"
})
distances_duration_matrix = distances_duration_matrix.drop(columns=['hcf_uid'])

# %% [markdown]
# DEscrfibe

# %%
geometry = [Point(xy) for xy in zip(distances_duration_matrix['origin_lon'], distances_duration_matrix['origin_lat'])]
gdf = gpd.GeoDataFrame(distances_duration_matrix, geometry=geometry, crs="EPSG:4326")

# %%
gpkg_path = data_temp + 'distances_duration_3_closet_Emoc.gpkg'
gdf.to_file(gpkg_path, layer="distances_duration_3_closet_Emoc", driver="GPKG")

# %%
# Review and remove
origin_dest = distances_duration_matrix

# %% [markdown]
# ## Enhanced Two-Step Floating Catchment Area (E2SFCA) method

# %%
# Function
from math import *
d = 10 * 60 # try max duration 5/10mins/15mins/20 car, under estimation of travel time and traffic condition realted to the selected data sourse 
W = 0.01 # try 0.1, 0.05, 0.01, 0.75
beta = - d ** 2 / log(W)
print(beta)

# %%
print(origin_dest.head())

# %%
# Convert 'duration' to numeric, coercing errors to NaN
origin_dest = origin_dest.copy()
origin_dest['duration_seconds'] = pd.to_numeric(origin_dest['duration_seconds'], errors='coerce')

# %%
# Drop rows with NaN values in 'duration' column
origin_dest = origin_dest.dropna(subset=['duration_seconds'])
origin_dest['grid_id'] = pd.to_numeric(origin_dest['grid_id'], errors='coerce')

# %%
origin_dest_acc = origin_dest

# %%
# Apply Gaussian decay function to calculate the weight of each grid to healthcare 
# facilities based on the travel duration. d is the travel time and beta is the decay 
# parameter previously calculated.
# The weight decreases as the duration increases, meaning facilities that are further away have less impact.
origin_dest_acc['Weight'] = origin_dest_acc['duration_seconds'].apply(lambda d: round(math.exp(-d**2/beta), 8))

# %%
# Compute the Weighted Population (Pop_W), the population of each grid cell is multiplied 
# by the corresponding weight to calculate the weighted population.
origin_dest_acc['Pop_W'] = origin_dest_acc['population'] * origin_dest_acc['Weight']

# %%
origin_dest_acc

# %%
# Sum the Weighted Population
origin_dest_sum = origin_dest_acc.groupby(by='hcf_id')['Pop_W'].sum().reset_index()

# %%
origin_dest_sum

# %%
# Merge the Sum of Weighted Population Back into the Original Data
origin_dest_acc = origin_dest_acc.merge(origin_dest_sum, on='hcf_id')

# %%
origin_dest_acc

# %%
# supply value is set to 1 for simplicity (capacity of HCF)
# supply = 1
# in the future, we will link supply with ownership and EmOC service level
origin_dest_acc = origin_dest_acc.rename(columns={'Pop_W_y': 'Pop_W_S'})  # Pop_W_S: Population Weight Sum

# %% [markdown]
# Compute the Supply-Demand Ratio (Rj)
# origin_dest_acc['supply_demand_ratio'] = 1 / origin_dest_acc.Pop_W_S
# origin_dest_acc['supply_demand_ratio'].replace([np.inf, np.nan], 0, inplace=True)

# %%
supply_map = {
    'Public Comprehensive EmOC': 1,
    'Private Comprehensive EmOC': 0.7,
    'Public Basic EmOC': 0.5,
    'Private Basic EmOC': 0.35
}

# %% [markdown]
# Option 1: Kano
# 

# %%
origin_dest_acc['supply'] = origin_dest_acc['Local_Validation'].map(supply_map)


# %% [markdown]
# Option 2: Lagos

# %%
origin_dest_acc['supply'] = origin_dest_acc['validation'].map(supply_map)


# %%
origin_dest_acc['supply_demand_ratio'] = origin_dest_acc['supply'] / origin_dest_acc['Pop_W_S']
origin_dest_acc['supply_demand_ratio'].replace([np.inf, -np.inf, np.nan], 0, inplace=True)

# %%
# Calculate Rj * Weight for Each Grid Cell
origin_dest_acc['supply_W'] = origin_dest_acc['supply_demand_ratio'] * origin_dest_acc.Weight

# %%
# Compute Accessibility Index (Ai) for Each Grid Cell
origin_dest_acc['Accessibility'] = origin_dest_acc.groupby('grid_id')['supply_W'].transform('sum')

# %% [markdown]
# To normalise the accesibility index, we use the sklearn library. 
# Double check you have installed the library
# ```bash
# pip install -U scikit-learn
# ```
# ```python
# from sklearn.preprocessing import MinMaxScaler
# 

# %%
# Normalize
scaler = MinMaxScaler()
origin_dest_acc['Accessibility_standard'] = scaler.fit_transform(origin_dest_acc[['Accessibility']])

# %%
origin_dest_acc

# %%
max(origin_dest_acc.Accessibility_standard)

# %%
gdf = gpd.GeoDataFrame(origin_dest_acc, geometry='geometry', crs="EPSG:4326")
gpkg_path = data_temp + 'acc_score_3_closet_Emoc_d10_w0.01_supply_weighted.gpkg'
gdf.to_file(gpkg_path, layer="acc_score_3_closet_Emoc_d10_w0.01_supply_weighted", driver="GPKG")

# %% [markdown]
# ### Results analysis Distribution Diagram

# %%
# If not load
origin_dest_acc = gpd.read_file(data_temp + 'acc_score_3_closet_Emoc_d10_w0.01_supply_weighted.gpkg')

# %%
sns.displot(origin_dest_acc['duration_seconds']/60, kde=True)

# %%
plt.title('Distribution of Duration')
plt.xlabel('Travel time')
plt.ylabel('Frequency')
plt.show()          

# %%
# 3. distribution plot of population/duration
sns.scatterplot(x='Accessibility_standard', y='population', data=origin_dest_acc)

# %%
plt.xlabel('Accessibility Score')
plt.ylabel('Population')

# %%
plt.show()

# %%
plt.figure(figsize=(10, 6))
sns.histplot(data=origin_dest_acc, x='Local_Validation')

# %%
plt.title('Histogram')
plt.xlabel('Local Validation')
plt.ylabel('Count')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# %%
plt.figure(figsize=(20, 7))
sns.histplot(
    data=origin_dest_acc,
    x='facility_name',
    discrete=True,
    color='skyblue',
    edgecolor='black'
)

# %%
plt.title('Facility Name Distribution', fontsize=16)
plt.xlabel('Facility Name', fontsize=12)
plt.ylabel('Count', fontsize=12)
plt.xticks(rotation=60, ha='right', fontsize=10)
plt.tight_layout()
plt.show()

# %%
import geopandas as gpd
import seaborn as sns
import matplotlib.pyplot as plt
import re
import os
from matplotlib import gridspec

# %%
data_folder = 'data_outputs/acc_score_3_closest_Emoc'

# %%
file_names = [f for f in os.listdir(data_folder) if f.endswith('.gpkg')] 

# %%
fig = plt.figure(figsize=(20, 15))
gs = gridspec.GridSpec(4, 5, figure=fig)

# %%
y_labels = ['5min', '10min', '15min', '20min']
x_labels = [0.75, 0.5, 0.1, 0.05, 0.01]

# %%
for i, file_name in enumerate(file_names):
    file_path = os.path.join(data_folder, file_name)
    gdf = gpd.read_file(file_path)

    match = re.search(r'd(\d+)', file_name)
    if match:
        d_value = int(match.group(1))
        y_position = 3 - (d_value // 5 - 1)

    match = re.search(r'w(\d+\.\d+)', file_name)
    if match:
        w_value = float(match.group(1))
        x_position = x_labels.index(w_value)

    ax = fig.add_subplot(gs[y_position, x_position])
    
    sns.scatterplot(x='Accessibility_standard', y='population', data=gdf, ax=ax)
    ax.set_xlabel('Accessibility Score')
    ax.set_ylabel('Population')

# %%
plt.tight_layout()
output_image_path = 'data_outputs/output_image.png'
plt.savefig(output_image_path, bbox_inches='tight', dpi=300)

# %%
plt.show()

# %% [markdown]
# # 4. Grouping by grid ID to prepare the final output file
# There is a need to update this part of the code

# %%
# Read the GeoPackage file (if starting from this section)
results_grid = gpd.read_file(data_temp + 'acc_score_3_closet_Emoc_d10_w0.01_supply_weighted.gpkg')

# %%
results_grid = results_grid[['grid_id', 'origin_lon', 'origin_lat', 'origin_lon_min', 'origin_lat_min', 'origin_lon_max', 'origin_lat_max', 'Accessibility_standard', 'geometry']]

# %% [markdown]
# Group by multiple columns and calculate the mean for numeric columns
# results_grid = results_grid.groupby(['grid_id', 'origin_lon', 'origin_lat', 'origin_lon_min', 'origin_lat_min', 'origin_lon_max', 'origin_lat_max', 'Accessibility_standard']).count().reset_index()

# %%
results_grid = results_grid.drop_duplicates(['grid_id', 'origin_lon', 'origin_lat', 'origin_lon_min', 'origin_lat_min', 'origin_lon_max', 'origin_lat_max', 'Accessibility_standard', 'geometry'])

# %%
# save the results to a new GeoPackage file
output_gpkg_path = data_temp + 'emergency-maternal-care-deprivation-access.gpkg'
results_grid.to_file(output_gpkg_path, layer='emergency-maternal-care-deprivation-access', driver='GPKG')

# %%
type(results_grid)

# %%
results_grid

# %% [markdown]
# ### Setting values for Low medium and High categories
# 
# We started by defining equal value division, and modified the thesholds to a value that is more legible and easier to interpret. Every model should have their own thresholds based on the data distribution of the three categories. 
# 
# Note: For Kano, we excluded grid cells with index values below 0.000001 that indicated very low population and a small number of buildings.  

# %% [markdown]
# Option 1: Kano
# Values are specific for each city and should be adjusted based on the data distribution of the three categories. 
# 

# %%
results_grid['result'] = -1
results_grid.loc[results_grid['Accessibility_standard'] > 0.000001, 'result'] = 2
results_grid.loc[results_grid['Accessibility_standard'] > 0.005, 'result'] = 1
results_grid.loc[results_grid['Accessibility_standard'] > 0.02, 'result'] = 0

# %% [markdown]
# Option 2: Lagos
# Values are specific for each city and should be adjusted based on the data distribution of the three categories. 

# %%
results_grid['result'] = -1
results_grid.loc[results_grid['Accessibility_standard'] >= 0, 'result'] = 2
results_grid.loc[results_grid['Accessibility_standard'] > 0.007, 'result'] = 1
results_grid.loc[results_grid['Accessibility_standard'] > 0.015, 'result'] = 0

# %% [markdown]
# ### Setting values for focus areas
# 
# We defined the focus areas based on values for the different thresholds. We aim at participants helping us to confirm the selection of the city-specific thresholds.

# %% [markdown]
# Option 1: Kano
# 

# %%
results_grid['focused'] = 0
# Focus areas between the Low category and the excluded cells due to low population or no buildings
results_grid.loc[(results_grid['Accessibility_standard'] > 0.000001) & (results_grid['Accessibility_standard'] < 0.0000015), 'focused'] = 1
# Focus areas between the Medium and High categories
results_grid.loc[(results_grid['Accessibility_standard'] > 0.003) & (results_grid['Accessibility_standard'] < 0.006), 'focused'] = 1
# Focus areas between the Low and Medium categories
results_grid.loc[(results_grid['Accessibility_standard'] > 0.019) & (results_grid['Accessibility_standard'] < 0.03), 'focused'] = 1

# %% [markdown]
# Option 2: Lagos

# %%
results_grid['focused'] = 0
# Focus areas between the Low category and city expansion areas
# results_grid.loc[(results_grid['Accessibility_standard'] > 0.000001) & (results_grid['Accessibility_standard'] < 0.0000015), 'focused'] = 1
# Focus areas between the Medium and High categories
results_grid.loc[(results_grid['Accessibility_standard'] > 0.005) & (results_grid['Accessibility_standard'] < 0.009), 'focused'] = 1
# Focus areas between the Low and Medium categories
results_grid.loc[(results_grid['Accessibility_standard'] > 0.014) & (results_grid['Accessibility_standard'] < 0.016), 'focused'] = 1

# %%
results_grid

# %%
results_grid = results_grid.loc[results_grid['result'] != -1]

# %%
results_grid = results_grid.rename(columns={
    'origin_lon': 'longitude',
    'origin_lat': 'latitude',
    'origin_lon_min': 'lon_min',
    'origin_lat_min': 'lat_min',
    'origin_lon_max': 'lon_max',
    'origin_lat_max': 'lat_max'
})

# %%
results_grid

# %%
# Save the results to a new GeoPackage file
output_gpkg_path = data_temp + 'emergency-maternal-care-deprivation-access-class.gpkg'
results_grid.to_file(output_gpkg_path, layer='emergency-maternal-care-deprivation-access-class', driver='GPKG')

# %%
# Save the results to a CSV file in the format required by the IDEAMAPS data ecosystem
results_table = results_grid.drop(columns=['Accessibility_standard', 'grid_id', 'geometry'])
results_table.to_csv(model_outputs + 'model-output.csv', index=False)

# %%
results_table


