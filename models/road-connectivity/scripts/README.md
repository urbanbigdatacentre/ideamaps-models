#  Deploying the Road Connectivity Model (V0)



This folder contains all required code to model lack of road accessibility based on road network and building footprint data.

We refer to our publication for a detailed description of the methodology: [preprint](). 




## 🛠️ Setup


1. **Clone the repository**:
    ```
    git clone https://github.com/urbanbigdatacentre/ideamaps-models.git
    cd ideamaps-models/models/road-connectivity/scripts
    ```


2. **Create a virtual environment using Conda**:
    ```
    conda env create ideamaps-models python=3.9
    conda activate ideamaps-models
    ```
3. **Install dependencies from requirements.txt file** using pip
   ```
   pip install -r requirements.txt
   ```


## 🏚️ Prepare the Data

Our model requires building footprints as input data. There are several providers for open building footprint data. We recommend using data from the [Overture Map Foundation](https://overturemaps.org/).


## ⚙️ Run Model

Follow these steps to obtain lack of road accessibility levels (low, medium, high).

1. **Compute the model parameters at the building level**

   ```
   python model_parameters.py -e *path to the file* -b *path to the builidng footprints file* -o *path the the output dir*
   ```

2. **Aggregate the building-level model parameters to the grid level**

   ```
   python aggregation.py -b *building footprints file (.parquet)* -g *grid file* -o *output file (.parquet)*
   ```
    The IDEAMAPS grid files for Nairobi, Kenya, Lagos, Nigeria, and Kano, Nigeria, are stored in [this folder](https://github.com/urbanbigdatacentre/ideamaps-models/tree/dev/docs/study-areas) alongside a documentation of the grids.

3. **Postprocessing (optional)**

   Improve the model by considering natural barriers.

   ```
   python aggregation.py -m *path to the morphometrics dir* -b *path to the builidng footprints file* -g *path to the grid file* -o *path the the output dir*
   ```


## 📝 Reference

If you find this work useful, please cite:

```

```