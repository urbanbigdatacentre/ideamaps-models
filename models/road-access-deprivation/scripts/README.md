#  Deploying the Road Access Deprivation Model (V1)



This folder contains all required code to model lack of road accessibility based on road network and building footprint data.

We refer to our publication for a detailed description of the methodology: [preprint](). 




## 🛠️ Setup


1. **Clone the repository**:
    ```
    git clone https://github.com/urbanbigdatacentre/ideamaps-models.git
    cd ideamaps-models/models/road-access-deprivation/scripts
    ```


2. **Create a virtual environment using Conda**:
    ```
    conda create -n ideamaps-models python=3.11
    conda activate ideamaps-models
    ```
3. **Install dependencies from requirements.txt file** using pip
   ```
   pip install -r requirements.txt
   ```


## 🏚️ Prepare the Data

Our model requires roads data with surface type (paved/unpaved) information and building footprints as inputs.

There are several providers for open building footprint data. We recommend using data from the [Overture Map Foundation](https://overturemaps.org/).


## ⚙️ Run Model

Follow these steps to obtain lack of road accessibility levels (low, medium, high).

1. **Compute the model parameters at the building level**

   ```
   python model_parameters.py -r *roads file* -t *road type attribute* -p *road type key for paved roads* -b *buildings file* -o *output file*
   ```

   The road file has to include a road type attribute indicating whether a road segment is paved or unpaved. The value of the road type attribute of paved roads is defined using the road type key argument. Roads with other values than the parsed key are considered unpaved.


2. **Aggregate the building-level model parameters to the grid level**

   ```
   python aggregation.py -b *building footprints file (.parquet)* -g *grid file* -o *output file (.parquet)*
   ```
    The IDEAMAPS grid files for Nairobi, Kenya, Lagos, Nigeria, and Kano, Nigeria, are stored in [this folder](https://github.com/urbanbigdatacentre/ideamaps-models/tree/dev/docs/study-areas) alongside a documentation of the grids.

    **Maximum distance cap:** Buildings whose nearest road is more than 250 m away are considered to have no reliable access to a road. For these buildings, the number of buildings in between (`buildings_in_between`) is set to a fixed value of 10 before averaging within each grid cell. The value 10 lies well above any threshold of practical interest, so such buildings push the cell mean towards high deprivation (`ra = 2`) without a distance measure entering the metric otherwise.


3. **Classify the grid cells**

   ```
   python model_output.py -p *aggregated grid file (.parquet)* -t *threshold* -o *output file (.parquet)*
   ```
   The parameter file is the output of step 2. The threshold is the mean number of buildings between a building and its nearest road at or above which a grid cell is classified as high road access deprivation (`ra = 2`). Below the threshold, the class depends on the mode of the road surface type: predominantly paved roads are low deprivation (`ra = 0`) and predominantly unpaved roads are medium deprivation (`ra = 1`). The preprint uses a threshold of 1. The result is written to the output file and contains the columns `ra` and `geometry`.


4. **Postprocessing (optional)**

   *Not implemented yet*: Improve the model by considering natural barriers.


## 📝 Reference

If you find this work useful, please cite:

```
@article{hafner2025towards,
  title={Towards Modeling Road Access Deprivation in Sub-Saharan Africa Based on a New Accessibility Metric and Road Quality},
  author={Hafner, Sebastian and Zhao, Qunshan and Alugbin, Bunmi and Baruwa, Kehinde and Cheruiyot, Caleb and Da'u, Sabitu Sa'adu and Du, Xingyi and Elias, Peter and Elsey, Helen and Engstrom, Ryan and others},
  journal={arXiv preprint arXiv:2512.02190},
  year={2025}
}
```