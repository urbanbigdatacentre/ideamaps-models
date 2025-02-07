#  Deploying the Morphological Informality Model (V3)



This folder contains all required code to model morphological informality based on building footprint data.

We refer to our publication for a detailed description of the methodology: [preprint](). 




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

   ```
   python geoelements.py -r *path to region of interest file* -b *path to building footprints file*  -r *path to edges file* -o *path the output dir*
   ```

2. **Morphometrics computation**

   ```
   python morphometrics.py -b *path to building footprints file* -t *path to tessellation file* -o *path the the output dir*
   ```

3. **Aggregation of morphometrics**

   The morphometrics dir corresponds to the output dir used in step 2.

   ```
   python aggregation.py -m *path to the morphometrics dir* -b *path to the builidng footprints file* -g *path to the grid file* -o *path the the output dir*
   ```
      
4. **Clustering of morphometrics**

   ```
   python clustering.py -m *path to the morphometrics file* -o *path the the output dir*
   ```

The resulting urban form clusters can be linked to irregular settlement layout and small, dense structures. These subdomains of unplanned urbanization constitute the indicators for morphological informality in our model.


## 📝 Reference

If you find this work useful, please cite:

```

```