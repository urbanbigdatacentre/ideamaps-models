# 🏥 Deploying the General Healthcare Access Deprivation Model – Lagos

This folder contains all required code and input data to assess general healthcare access deprivation for Lagos, Nigeria, using a spatial modeling approach based on the isochrones.

We refer to our publication for a detailed description of the methodology: [Document](https://docs.google.com/document/d/1_eq75BEtiBSDKMXuYPQ2AixcUFI7EIN9/edit).

## 📁 Folder Structure

- `General_Healthcare_Access_Lagos_V2.ipynb`: Main notebook to run the general healthcare access model.
- `General_Healthcare_Access_Lagos_V2.py`: Python script version of the model.
- `Lagos/data_inputs/`: Contains all required input data.
- `Lagos/data_temp/`: Temporary files created during intermediate processing steps.

## 🛠️ Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/urbanbigdatacentre/ideamaps-models.git
   
   cd ideamaps-models/models/general-healthcare-access-deprivation/scripts
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

### 2. **Healthcare Facilities**  
   Based on data from the [GRID3 NGA - Health Facilities v2.0](https://data.grid3.org/datasets/a0ed9627a8b240ff8b315a84575754a4_0/explore) repository, the classification for validation is determined by facility ownership and level.  
   **Format**: GeoPackage or CSV (with facility attributes and coordinates)

## 🚀 Running the Model

Follow these steps to obtain deprivation levels (low, medium, high) of General Healthcare.

### 1. **Open the notebook:**  
   `General_Healthcare_Access_Lagos_V2.ipynb`

### 2. **Configure input paths:**  
   Ensure all input paths are correctly set in the notebook.

### 3. **Calculate Isochrones Using OpenRouteService (ORS)**  

   Generate walking and driving catchment areas (isochrones) around healthcare facilities using the OpenRouteService (ORS) Isochrone API, specifying distance-based thresholds to define accessible service areas.

   Requires an API key from [openrouteservice.org](https://openrouteservice.org/).

   ```bash
   OPENROUTESERVICE_API_KEY = 'your_api_key'
   api_key = os.getenv('OPENROUTESERVICE_API_KEY')
   client = openrouteservice.Client(key=api_key)
   ```

### 4. **Assessing Accessibility Using Isochrones**

General healthcare access deprivation is evaluated by performing spatial joins between isochrone polygons and 100 × 100 m grid cells in study area.

 - **Spatial join using GeoPandas** - Isochrones representing healthcare facility catchment areas (based on fixed travel distances thresholds) are spatially joined with the grid cells. This allows analysis of accessibility at a fine spatial resolution across the study areas.

 - **Aggregating results** - A spatial join is performed for both walking and driving isochrones, and the number of intersecting isochrones for each grid cell is counted.

- **Accessibility classification** - Healthcare access deprivation levels are define based on criteria applied to the isochrone counts.

Note: Ensure all data preprocessing steps are complete and the required input files are available.
Further methodological details can be found in the [dataset-interpretability](../Lagos-v2/dataset-interpretability.md) documentation.

## 📎 Outputs

Review the outputs in the [output folder](../Lagos-v2):

- `image-examples/`
- `dataset-interpretability.md`
- `dataset-metadata.json`
- `model-outputs.csv`

  
| Authors                   | Email Address                                      |
|---------------------------|----------------------------------------------------|
| Diego Pajarito Grajales  | Diego.PajaritoGrajales@glasgow.ac.uk               |
| Xingyi Du                | Xingyi.Du@glasgow.ac.uk                            |
