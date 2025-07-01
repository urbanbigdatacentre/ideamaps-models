# 🏥 Deploying the Emergency Obstetric Care (EmOC) Access Deprivation Model – Lagos

This folder contains all required code and input data to assess emergency maternal care (EmOC) access deprivation for Lagos, Nigeria, using a spatial model based on the 2-step floating catchment area (2SFCA) method.

We refer to our publication for a detailed description of the methodology: [Document](https://docs.google.com/document/d/1dGsay3PzLPfFJ8P2z702lm-oXsCebGyoMiSjkgl5jr4/edit?tab=t.0#heading=h.xm1wdqmjz1kd).

## 📁 Folder Structure

- `EmOC-Access-Deprivation-Lagos.ipynb`: Main notebook to run the 2SFCA access model.
- `EmOC-Access-Deprivation-Lagos.py`: Python script version of the model.
- `Lagos/data_inputs/`: Contains all required input data.
- `Lagos/data_temp/`: Temporary files created during intermediate processing steps.

## 🛠️ Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/urbanbigdatacentre/ideamaps-models.git
   
   cd ideamaps-models/models/emergency-maternal-care/scripts
2. **Create a virtual environment**

    ```bash
    python -m venv .venv
    
    activate .venv/bin/activate
3. **Install dependencies from requirements.txt file using pip**

   ```bash
   pip install -r requirements.txt
4. **Set up the Jupyter kernel (for VS Code or Jupyter Notebooks)**

   ```bash
   pip install -U ipykernel
   
   python -m ipykernel install --user --name=.venv

## 📊 Data Sources

### 1. **Study Area**  
   The IDEAMAPS Data Ecosystem grid files for Nairobi, Kenya, Lagos, Nigeria, and Kano, Nigeria, are available in [here](https://github.com/urbanbigdatacentre/ideamaps-models/tree/dev/docs/study-areas) alongside a documentation of the grids.  
   **Format**: GeoPackage

### 2. **Population Grid**  
   Gridded data (1km resolution) representing women of childbearing age (15–49 years), sourced from [WorldPop Nigeria](https://hub.worldpop.org/geodata/summary?id=18447).  
   **Format**: GeoTIFF

### 3. **Healthcare Facilities**  
   Based on the geospatial database of travel times to healthcare facilities by [Macharia et al., 2023](https://doi.org/10.6084/m9.figshare.22689667.v2), the classification for validation is determine based on the ownership.  
   **Format**: GeoPackage or CSV (with facility attributes and coordinates)

## 🚀 Running the Model

Follow these steps to obtain lack of Emergency Obstetric Care accessibility levels (low, medium, high).

### 1. **Open the notebook:**  
   `EmOC-Access-Deprivation-Lagos.ipynb`

### 2. **Configure input paths:**  
   Ensure all input paths are correctly set in the notebook.

### 3. **Aggregate population data:**  
   Aggregate the population data from a 1 km grid to a 100 m × 100 m resolution using [Google Building Footprints](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_Research_open-buildings_v3_polygons).

### 4. **Calculate OD Matrix Using OpenRouteService (ORS) Matrix API**  

   Includes estimated travel times and distances from each population grid centroid to the healthcare facility. There are two options for computing travel time and distance:

   - **Option A: Public ORS API**

     Requires an API key from [openrouteservice.org](https://openrouteservice.org/).

     ```bash
     OPENROUTESERVICE_API_KEY = 'your_api_key'
     api_key = os.getenv('OPENROUTESERVICE_API_KEY')
     client = openrouteservice.Client(key=api_key)
     ```

   - **Option B: Local ORS Instance of the ORS server**

     add descriptions here

### 5. **Applying the Two-Step Floating Catchment Area (2SFCA) Method**

   - **Catchment definition** — For each facility, a surrounding area is defined using a travel time threshold.

   - **Supply-to-demand ratio calculation** — The capacity of the facility is divided by the population within its catchment.

   - **Aggregation** — For each demand location (a grid cell with population count), accessibility scores are calculated by summing the ratios of nearby facilities within its own catchment.

Note: Ensure all data preprocessing steps are complete and the required input files are available.
Further methodological details can be found in the [dataset-interpretability](https://github.com/urbanbigdatacentre/ideamaps-models/blob/dev/models/emergency-maternal-care/lagos/dataset-interpretability.md) documentation.

## 📎 Outputs

Review the outputs in the [output folder](https://github.com/urbanbigdatacentre/ideamaps-models/blob/dev/models/emergency-maternal-care/lagos):

- `image-examples/`
- `dataset-interpretability.md`
- `dataset-metadata.json`
- `model-outputs.csv`