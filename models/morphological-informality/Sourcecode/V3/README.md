#  Deploying the Morphological Informality Model (V3)



This folder contains all required code to model morphological informality based on building footprint data.

We refer to our publication for a detailed description of the methodology: [preprint](). 




## 🛠️ Setup


1. **Clone the repository**:
    ```
    git clone https://github.com/urbanbigdatacentre/ideamaps-models.git
    cd ideamaps-models/Sub-domains/MorphologicalInformality/Sourcecode/V3
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


## 🏚️ Prepare Building Footprint Data

Our model requires building footprints as input data. There are several providers for open building footprint data. We recommend using data from the [Overture Map Foundation](https://overturemaps.org/).


## ⚙️ Run Model

Follow these steps to obtain clusters of similar urban form types.

1. **Create the basic urban form elements**

   ```
   python geoelements.py -e *path to the file* -b *path to the builidng footprints file* -o *path the the output dir*
   ```

2. **Create the basic urban form elements**

   ```
   python morphometrics.py -b *path to building footprints file* -t *path to tessellation file* -o *path the the output dir*
   ```

3. **Create the basic urban form elements**

   The morphometrics dir corresponds to the output dir used in step 2.

   ```
   python aggregation.py -m *path to the morphometrics dir* -b *path to the builidng footprints file* -g *path to the grid file* -o *path the the output dir*
   ```
      
4. **Create the basic urban form elements**

   ```
   python clustering.py -m *path to the morphometrics file* -o *path the the output dir*
   ```

The resulting urban form clusters can be linked to morphological informality.


## 📝 Reference

If you find this work useful, please cite:

```

```