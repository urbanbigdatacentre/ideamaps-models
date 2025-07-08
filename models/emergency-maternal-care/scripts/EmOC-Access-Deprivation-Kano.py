# %% [markdown]
# # Analysis of Emergency Obstetric Care (EmOC) in Nigeria, Kano
# > Note: This notebook requires the [environment dependencies](requirements.txt) to be installed
# > as well as either an [openrouteservice API key](https://openrouteservice.org/dev/#/signup) or a local instance of the ORS server.

# %% [markdown]
# ## Model Summary:
# 
# This notebook provides the means to generate a dataset that is described in the [model documentation](../kano/dataset-interpretability.md).
# 
# ## Workflow Summary:
# 
# The notebook gives an overview of the distribution of centres offering EmOC in the city, their classification and how they can be accessed during an emergency. Open source data from OpenStreetMap and tools (such as the openrouteservice) were used to create accessibility measures. Spatial analysis and other data analytics functions led to generating outputs within the 100x100m grid cells that categorised them into three levels: low, medium, and high.
# 
# * **Preprocessing**: Get data for EmOC facilities.
# * **Analysis for Offer**:
#     * Filter or classify EmOC facilities based on discussed criteria.
#     * Visualise EmOC faccilities in their categories.
# * **Analysis for Accessibility**:
#     * Compute travel times to facilities using openrouteservice API or other routing services.
#     * Generate areas for low, medium and high categories based on discussed criteria.
# * **Analysis for Demmand**:
#     * Downscale the popluation data to the 100x100m grid cells.
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

import rasterio
from rasterio.mask import mask

from shapely.geometry import Point

from pathlib import Path
from shapely.geometry import Polygon

import requests
import math
from math import *
from sklearn.preprocessing import MinMaxScaler

# %% [markdown]
# ### Setting up the public API Key from OpenRouteService
# In this study, users must obtain an ORS Matrix API key from the [OpenRouteService](https://openrouteservice.org/) platform and subsequently interacted with the OpenRouteService API through the instantiation of the OpenRouteService client. This is the OpenRouteService [API documentation](https://openrouteservice.org/dev/#/api-docs/introduction) for ORS Core-Version 9.0.0. 
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
# Read the api key from the .env file
%load_ext dotenv
%dotenv
api_key = os.getenv('OPENROUTESERVICE_API_KEY')
client = openrouteservice.Client(key=api_key)

# %% [markdown]
# ### Setting up relevant processing folders
# 
# There are different data sources used across the notebook. To handle these data sets, it is recommended to use three directories for input, temp and output data. Some of the files are related to healthcare facilities, population data. The healthcare facilities data is usualy the result of gathering global or national datasets and then carrying out local validation according to the local context. 
# 
# Despite being official, administrative boundaries may not reflect the actual patterns of human settlement or economic activity. Therefore, the team used the Functional Urban Area (FUA) as a complementary definition of the study areas. The FUA is defined by [the Joint Research Centre of the European Commission](https://commission.europa.eu/about/departments-and-executive-agencies/joint-research-centre_en) as the actual urban sprawl and human activities, encompassing the core city and economically or socially integrated surrounding regions. The FUA was obtained from [the Global Human Settlement Layer (GHSL) ](https://human-settlement.emergency.copernicus.eu/)dataset, which provides spatial data for functional urban areas worldwide. 
# 
# The following datasets are considered as input data for the analysis:
# 
# 
# * [Datasets of health facilities](../scripts/Kano/data-inputs/healthcare_facilities.geojson)
# * [Population: Women in childbearing age](../scripts/Kano/data-inputs/kano_nga_f_15_49_2015_1km.tif) from [WorldPop](https://hub.worldpop.org/geodata/summary?id=18447)
# * [Study Area](../../../docs/study-areas/grid-boundary-kano.gpkg) defined by the IDEAMAPS team

# %%
# Set paths to access Kano data
# Define directories
data_inputs = '../scripts/Kano/data-inputs/'
data_temp = '../scripts/Kano/data-temp/'
model_outputs = '../kano/'

# %% [markdown]
# ## 1. Data Collection

# %% [markdown]
# ### Validated healthcare facilities - (Supply/Offer)
# For Kano, the classification for validation was determined with the assistance of local experts, based on data obtained from the [datasets of health facilities](https://doi.org/10.6084/m9.figshare.22689667.v2).

# %%
healthcare_facilities_validated = gpd.read_file(data_inputs + 'healthcare_facilities.geojson')

# %%
healthcare_facilities_validated

# %% [markdown]
# ### Population Grid Data (Demand)
# This data originally comes as a grid (1km resolution) from [WorldPop](https://hub.worldpop.org/geodata/summary?id=18447) to transform it into a 100x100m grid, we use a procedure explained below. 
# 
# Note: explain the process to scale down the population data. 
# note: explain the rational for female population between 15-49 years old.

# %%
study_area = gpd.read_file(data_inputs + '100mGrid.gpkg')
raster_path = data_inputs + 'nga_f_15_49_2015_1km.tif'

# %% [markdown]
# Clipping the population data to our study area

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
with rasterio.open(data_inputs + 'kano_nga_f_15_49_2015_1km.tif', "w", **out_meta) as dest:
    dest.write(clipped_image)

# %% [markdown]
# Calculating the centroids for grid cells

# %%
rows, cols = np.where(band1 > 0)
grid_cells = [clipped_transform * (col + 0.5, row + 0.5) for row, col in zip(rows, cols)]
population_values = band1[rows, cols]

# %%
grid_df = pd.DataFrame(grid_cells, columns=["longitude", "latitude"])
grid_df["population"] = population_values

grid_df["rowid"] = range(1, len(grid_df) + 1)
population_centroids_gdf = gpd.GeoDataFrame(grid_df, geometry=[Point(xy) for xy in zip(grid_df["longitude"], grid_df["latitude"])])
population_centroids_gdf.set_crs("EPSG:4326", inplace=True)

population_centroids_gdf.to_file(data_temp + "population_centroids.gpkg", driver="GPKG")

# %%
population_centroids_gdf

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

# %% [markdown]
# Building footprint data is used to estimate population distribution within each 1km cell. Building centroids are spatially joined to 100m grid cells. The number of buildings per 100m cell (bcount) is calculated.

# %%
# Count buildings per grid cell

# Loading Google building footprints
building_file = data_inputs + 'Kano_GOBv3.gpkg'
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

# %% [markdown]
# The population of each 1km grid is distributed to underlying 100m cells proportionally based on building density. Each 100m grid is assigned a weight equal to its share of the total building count within the 1km grid.

# %%
# Adding population data at 1km grid to finer grid

data_path = Path(data_inputs)

# Loading coarse pop data
pop_file = data_path / 'kano_nga_f_15_49_2015_1km.tif'
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
grid.to_file(data_temp + 'pop-grid-kano-centroids.gpkg', driver='GPKG')

# %% [markdown]
# ## 2. Spatial Analysis Pipeline
# 
# ### Travel time and dista calculation using OpenRouteService (ORS)
# 
# Using OpenRouteService (ORS) Matrix API to calculate the travel time and distance from each population grid centroid to the healthcare facility. There are two options to process the time and distance calculations: Using the public ORS API or using a local instance of the ORS server.
# 
# note: this will generate a file 'OD_matrix_healthcare_pop_grid'

# %%
origin_gdf = population_centroids_gdf
origin_name_column = 'grid_code'
destination_gdf = healthcare_facilities_validated.dropna(subset=['geometry'])
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

headers = {
    'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
    'Authorization': api_key,
    'Content-Type': 'application/json; charset=utf-8'
}

response = requests.post('https://api.openrouteservice.org/v2/matrix/driving-car', json=body, headers=headers)

# %%
distances = response.json().get('distances', [])
durations = response.json().get('durations', [])

# %%
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
    filtered = healthcare_facilities_validated[(destination_gdf.geometry.x == dest_x) & (destination_gdf.geometry.y == dest_y) ]
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

gpkg_path = data_temp + 'distance_duration_matrix_temp.gpkg'
gdf.to_file(gpkg_path, layer="duration_matrix", driver="GPKG")

# %% [markdown]
# ### Option 2: Using a local ORS service
# Make sure you have set a local service that runs the OSM-based ORS API. 
# ```r
# # Insert R code from the local ORS service
# ```
# 
# ### Procedure for Computing the OD Matrix Using a Local Docker Environment
# 
# This section outlines the steps required to compute the Origin-Destination (OD) matrix using a local Docker environment. 
# 
# 1. **Set Up Docker Environment**:
# 
# 2. **Prepare Input Data**:
# 
# 3. **Run the OD Matrix Computation Script**:
# 
# 4. **Monitor the Process**:
# 
# 5. **Retrieve and Validate Output**:
# 
# ### Diego please add description here

# %% [markdown]
# ## Processing OD Matrix

# %% [markdown]
# Population data is the result of combining 1km grid data with 100m grid data. See [Section 2]() for more details.

# %%
# If not loaded yet, read from the temporary folder
centroids_df = gpd.read_file(data_temp +'pop-grid-kano-centroids.gpkg')
centroids_df

# %%
# If not loaded yet, read from the temporary folder
matrix_df = pd.read_csv(data_temp +'OD-matrix-kano-access-emoc.csv')
matrix_df

# %% [markdown]
# **GRID CELLS WITHOUT TRAVEL TIME ESTIMATE**
# 
# If a grid cell has a NULL value in the travel estimate, we will remove it from the analysis. This is because we cannot calculate the 2SFCA without a travel time estimate.

# %%
# Removing rows with NaN values in the 'duration_seconds' column
matrix_df = matrix_df.dropna(subset=['duration_seconds'])
matrix_df

# %% [markdown]
# To process the OD Matrix we need merge it to create an integrated dataset that combines data from the healthcare facilities and population grid.For doing so, we will use the pandas library and join functions based on the id columns of all datasets.

# %%
pop_centroids_hcf = pd.merge(matrix_df, centroids_df[['rowid', 'longitude', 'latitude', 'lon_min', 'lat_min', 'lon_max', 'lat_max','bcount','pop_grid_bcount', 'pop_grid_pop', 'pop', 'geometry']], 
                     left_on='destination_id', right_on='rowid', how='left')
pop_centroids_hcf

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

# %% [markdown]
# Merging the dataframe than contains the od matrix (with the healthcare facility class) and the population data with the full information about health care facilities.

# %%
distances_duration_matrix = pd.merge(pop_centroids_hcf, healthcare_facilities_validated[['hcf_id','facility_name', 'longitude', 'latitude', 'Local_Validation']], 
                     left_on='hcf_uid', right_on='hcf_id', how='left')

# %%
distances_duration_matrix = distances_duration_matrix.rename(columns={
    "longitude": "dest_lon",
    "latitude": "dest_lat"
})
distances_duration_matrix = distances_duration_matrix.drop(columns=['hcf_uid'])

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

distances_duration_matrix

# %%
# creat subsets based on categories of 'Validation of HCFs Categorization'
categories = {
    "public_comprehensive_EmOC": ["Public Comprehensive EmOC"],
    "private_comprehensive_EmOC": ["Private Comprehensive EmOC"],
    "private_basic_EmOC": ["Private Basic EmOC"],
    "public_basic_EmOC": ["Public Basic EmOC"]
}

subsets = {
    key: distances_duration_matrix[
        distances_duration_matrix['Local_Validation'].str.contains('|'.join(values), na=False)
    ]
    for key, values in categories.items()
}

public_CEmOC = subsets["public_comprehensive_EmOC"]
private_CEmOC = subsets["private_comprehensive_EmOC"]
public_BEmOC = subsets["public_basic_EmOC"]
private_BEmOC = subsets["private_basic_EmOC"]

# %%
# Step 2: Define a function to get 3 smallest duration_seconds per grid_id for each category
def get_closest_3(df, n=3):
    return df.groupby('grid_id').apply(lambda x: x.nsmallest(n, 'duration_seconds')).reset_index(drop=True)

# %%
# Step 3: If the subsets are already created for each category, we apply the function to each subset:
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
# ## Enhanced Two-Step Floating Catchment Area (E2SFCA) method

# %%
# Function
from math import *
d = 10 * 60 # try max duration 5/10mins/15mins/20 car, under estimation of travel time and traffic condition realted to the selected data sourse 
W = 0.01
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
origin_dest_acc = origin_dest  # Backup

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

# %%
supply_map = {
    'Public Comprehensive EmOC': 1,
    'Private Comprehensive EmOC': 0.7,
    'Public Basic EmOC': 0.5,
    'Private Basic EmOC': 0.35
}

# %%
origin_dest_acc['supply'] = origin_dest_acc['Local_Validation'].map(supply_map)
origin_dest_acc['supply_demand_ratio'] = origin_dest_acc['supply'] / origin_dest_acc['Pop_W_S']
origin_dest_acc['supply_demand_ratio'].replace([np.inf, -np.inf, np.nan], 0, inplace=True)

# %%
# Calculate Rj * Weight for Each Grid Cell
origin_dest_acc['supply_W'] = origin_dest_acc['supply_demand_ratio'] * origin_dest_acc.Weight

# %%
# Compute Accessibility Index (Ai) for Each Grid Cell
origin_dest_acc['Accessibility'] = origin_dest_acc.groupby('grid_id')['supply_W'].transform('sum')

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
gpkg_path = data_temp + 'acc_score_3closest.gpkg'
gdf.to_file(gpkg_path, layer="acc_score_3closest", driver="GPKG")

# %% [markdown]
# # 4. Grouping by grid ID to prepare the final output file
# There is a need to update this part of the code

# %%
# Read the GeoPackage file (if starting from this section)
results_grid = gpd.read_file(data_temp + 'aacc_score_3closest.gpkg')

# %%
results_grid = results_grid[['grid_id', 'origin_lon', 'origin_lat', 'origin_lon_min', 'origin_lat_min', 'origin_lon_max', 'origin_lat_max', 'Accessibility_standard', 'geometry']]

# %%
# Group by multiple columns and calculate the mean for numeric columns
# results_grid = results_grid.groupby(['grid_id', 'origin_lon', 'origin_lat', 'origin_lon_min', 'origin_lat_min', 'origin_lon_max', 'origin_lat_max', 'Accessibility_standard']).count().reset_index()
results_grid = results_grid.drop_duplicates(['grid_id', 'origin_lon', 'origin_lat', 'origin_lon_min', 'origin_lat_min', 'origin_lon_max', 'origin_lat_max', 'Accessibility_standard', 'geometry'])
type(results_grid)

# %%
# save the results to a new GeoPackage file
output_gpkg_path = data_temp + 'emergency-maternal-care-deprivation-access.gpkg'
results_grid.to_file(output_gpkg_path, layer='emergency-maternal-care-deprivation-access', driver='GPKG')

# %%
results_grid

# %% [markdown]
# ### Setting values for Low medium and High categories
# 
# We started by defining equal value division, and modified the thesholds to a value that is more legible and easier to interpret. Every model should have their own thresholds based on the data distribution of the three categories. 
# 
# Note: For Kano, we excluded grid cells with index values below 0.000001 that indicated very low population and a small number of buildings.  

# %%
results_grid['result'] = -1
results_grid.loc[results_grid['Accessibility_standard'] > 0.000001, 'result'] = 2
results_grid.loc[results_grid['Accessibility_standard'] > 0.005, 'result'] = 1
results_grid.loc[results_grid['Accessibility_standard'] > 0.02, 'result'] = 0

# %%
category_counts = results_grid['result'].value_counts()
print(category_counts)

# %% [markdown]
# ### Setting values for focus areas
# 
# We defined the focus areas based on values for the different thresholds. We aim at participants helping us to confirm the selection of the city-specific thresholds.

# %%
category_counts = results_grid['focused'].value_counts()
print(category_counts)

# %%
results_grid['focused'] = 0
# Focus areas between the Low category and the excluded cells due to low population or no buildings
results_grid.loc[(results_grid['Accessibility_standard'] > 0.000001) & (results_grid['Accessibility_standard'] < 0.0000015), 'focused'] = 1
# Focus areas between the Medium and High categories
results_grid.loc[(results_grid['Accessibility_standard'] > 0.003) & (results_grid['Accessibility_standard'] < 0.006), 'focused'] = 1
# Focus areas between the Low and Medium categories
results_grid.loc[(results_grid['Accessibility_standard'] > 0.019) & (results_grid['Accessibility_standard'] < 0.03), 'focused'] = 1

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


