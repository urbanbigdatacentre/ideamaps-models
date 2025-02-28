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
from openrouteservice import client

import time
import pandas as pd
import numpy as np
import fiona as fn
import geopandas as gpd
from shapely.geometry import shape, mapping
# -


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
# * [Datasets of health facilities](https://doi.org/10.6084/m9.figshare.22689667.v2) (15/07/2023)
# * [Shapefile of district boundaries](https://data.humdata.org/dataset/nigeria-admin-level-2) - Admin Level 2 (data from Humanitarian Data Exchange, 25/11/2015)

# Set paths to access data
# Define directories
data_inputs = '../scripts/data_inputs/'
data_temp = '../scripts/data_temp/'
data_outputs = '../scripts/data_outputs/'

# Define file paths correctly
districts_filename = data_inputs + 'administrative_level2.shp'
health_facilities_filename = data_inputs + 'OnTIME_Nigeria_Masterlist_v2_20220928.csv'
EmOC_facilities = pd.read_csv(health_facilities_filename)

# ## Data Processing

# Select Data in Kano, state = 9 
EmOC_kano = EmOC_facilities[EmOC_facilities['state'] == 9].copy()
EmOC_kano.head()

EmOC_kano[['facility_level', 'owner', 'specific_owner']] = EmOC_kano[['facility_level', 'owner', 'specific_owner']].fillna(-1)

num_rows = len(EmOC_kano)
print("line:", num_rows)

# +
conditions = [
    (EmOC_kano['facility_level'].isin([1, 2])) &
    (EmOC_kano['owner'].isin([1, 2])) &
    (EmOC_kano['specific_owner'].isin([1, 3, 6])),

    (EmOC_kano['facility_level'].isin([1, 2])) &
    (EmOC_kano['owner'] == 2) &
    (EmOC_kano['specific_owner'].isin([2, 4])),

    (EmOC_kano['facility_level'].isin([0, -1])) &
    (EmOC_kano['owner'].isin([1, 2])) &
    (EmOC_kano['specific_owner'].isin([1, 3, 6, 2, 4, 5]))
]

values = [
    'Public_CEmOC',
    'Private_CEmOC',
    'Public_Private_BEmOC'
]

EmOC_kano['new_combination'] = np.select(conditions, values, default='Other')
EmOC_kano.head()
# -

new_combination_counts = EmOC_kano['new_combination'].value_counts()
print("\nnew_combination:\n", new_combination_counts)

gdf = gpd.GeoDataFrame(
    EmOC_kano,
    geometry=gpd.points_from_xy(EmOC_kano.longitude, EmOC_kano.latitude)
)
gdf.crs = 'EPSG:4326'
output_path = data_inputs + 'EmOC_kano.gpkg'
gdf.to_file("output_path", driver="GPKG")

# ## Analysis
# We will follow these steps:
# * Get Isochrones from openrouteservice
# * Perform Spatial Join
# * Save output as GeoPackage file and CSV file

# ### Get Duration Matrix from OpenRouteService

# ### Save Output as CSV file
