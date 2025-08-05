#  Deploying the Morphological Informality Model (V2)



This folder contains all required code to model morphological informality based on building footprint data.


## 🛠️ Setup


1. **Clone the repository**:
    ```
    git clone https://github.com/urbanbigdatacentre/ideamaps-models.git
    cd ideamaps-models/models/morphological-informality/scripts
    ```


2. **Create a virtual environment using Conda**:
    ```
    conda env create ideamaps-models python=3.10
    conda activate ideamaps-models
    ```
3. **Install dependencies from requirements.txt file** using pip
   ```
   pip install -r requirements.txt
   ```


## 🏚️ Prepare Building and Road Data

Our model requires building and road data as inputs. We recommend using data from the [Overture Map Foundation](https://overturemaps.org/). Overture buildings and road data can be downloaded using their Python command-line tool [overturemaps-py](https://github.com/OvertureMaps/overturemaps-py).
```
pip install overturemaps
cd overturemaps
overturemaps download --bbox=*west,south,east,north longitude and latitude coordinates* -f geoparquet --type=*building/segment* -o *output file (.parquet)*
```


## ⚙️ Run Model

Follow these steps to obtain clusters of similar urban form types.

1. **Creation of urban form elements**

    Preprocess the building footprints:
    ```
    python preprocess_buildings.py -r *region of interest file* -b *building footprints file* -o *output dir*
    ```
   
    Generate tessellation cells for the building footprints:
    ```
    python morphological_tessellation.py -b *building footprints file* -o *output dir*
    ```
   
     Generate the building blocks:
     ```
     python building_blocks.py -r *region of interest file* -b *building footprints file* -t *tessellation file* -e *roads file* -o *output dir*
     ```
   

2. **Morphometrics computation**

    ```
    python morphometrics.py -m *metric or "all" to compute all metrics*-b *path to building footprints file* -t *path to tessellation file* -o *path the the output dir*
    ```
    Once all metrics are computed, they can be combined using ``morphometrics.py -m combine`` which will create the file ``primary.parquet``.

3. **Aggregation of morphometrics**

   The morphometrics dir corresponds to the output dir used in step 2.

   ```
   python aggregation.py -m *morphometrics dir* -b *builidng footprints file* -g *grid file* -o *output dir*
   ```
      
4. **Clustering of morphometrics**

   ```
   python clustering.py -m *path to the morphometrics file* -o *path the the output dir*
   ```

The resulting urban form clusters can be linked to irregular settlement layout and small, dense structures. These subdomains of unplanned urbanization constitute the indicators for morphological informality in our model.
