#  Deploying the Morphological Informality Model (V2)

This folder contains the code to model morphological informality from building footprints and roads.
The model describes two indicators of unplanned urbanization, **irregular settlement layout (ISL)** and
**small, dense structures (SDS)**, with urban morphometrics aggregated to a 100 m grid. The grid cells are
clustered separately for each indicator, the clusters representing the indicators are selected per city, and the
indicators are combined into low (0), medium (1), and high (2) morphological informality.


## 🛠️ Setup

1. **Clone the repository**:
    ```
    git clone https://github.com/urbanbigdatacentre/ideamaps-models.git
    cd ideamaps-models/models/morphological-informality/scripts
    ```

2. **Create the environment with [uv](https://docs.astral.sh/uv/)**:
    ```
    uv sync
    ```
   This installs Python 3.11 and the pinned dependencies from `pyproject.toml` / `uv.lock` into `.venv`.
   Run the scripts with `uv run python <script>.py ...` (or activate the environment with `source .venv/bin/activate`).

   If the repository is located on a file system without symlink support (e.g., an exFAT external drive),
   place the environment elsewhere:
    ```
    export UV_PROJECT_ENVIRONMENT=~/.venvs/morphological-informality
    uv sync
    ```


## 🏚️ Input Data

| Input | Description |
|---|---|
| Region of interest | Polygon(s) of the study area (any format readable by GeoPandas, e.g., `.gpkg`) |
| Building footprints | Polygons (`.parquet` or any format readable by GeoPandas). The V2 deployments used [Google Open Buildings (V3)](https://sites.research.google/open-buildings/) |
| Roads | Lines from [OpenStreetMap](https://www.openstreetmap.org/), downloaded with `osm_roads_download.py` (see below) |
| Grid | 100 m grid cells covering the region of interest (polygons) |

All inputs can be provided in any CRS; the scripts reproject the data to the local UTM zone for the computations.

**Roads.** `osm_roads_download.py` downloads the OSM road network for a bounding box (longitude/latitude), keeps
vehicular roads only (motorway, trunk, primary, secondary, tertiary, residential, living street, service, and
unclassified, including link roads), and represents two-way roads by a single edge. The output is written to
`roads.parquet` in the output dir:
```
python osm_roads_download.py -w *west* -s *south* -e *east* -n *north* -o *output dir*
```

Alternatively, buildings and roads from the [Overture Maps Foundation](https://overturemaps.org/) can be used, e.g.,
downloaded with [overturemaps-py](https://github.com/OvertureMaps/overturemaps-py)
(`overturemaps download --bbox=*west,south,east,north* -f geoparquet --type=*building/segment* -o *output file*`).
The scripts then select roads based on the Overture `subtype` and `class` attributes.


## ⚙️ Run Model

All commands are run from this folder (prefix them with `uv run` if the environment is not activated). Several
scripts write a file called `buildings.parquet`, so we recommend a separate output dir per step. The output dirs must
exist before running a script. The example below uses the following layout:
```
mkdir -p work/{roads,buildings,tessellation,streets,morphometrics,grid,clusters,model}
```

### 1. Urban form elements

**Preprocess the building footprints.** Buildings intersecting the region of interest are cleaned: duplicate
geometries are removed, invalid geometries are fixed, multi-part polygons are exploded, structures smaller than
10 m² are merged with an adjacent building (or removed if isolated), and buildings that would collapse, split, or
overlap in the tessellation are removed. Each building gets an id (`uID`).
```
python preprocess_buildings.py -r *region of interest file* -b *building footprints file* -o work/buildings
```

**Generate the morphological tessellation** (one cell per building, limited to 100 m around buildings). Buildings
without a tessellation cell are removed, so the script writes both the tessellation and the updated buildings:
```
python morphological_tessellation.py -b work/buildings/buildings.parquet -o work/tessellation
```

**Preprocess the street network and link buildings to streets.** Roads intersecting the region of interest are
selected and merged at nodes of degree two; each building is linked to its nearest street segment within 500 m
(`nID`). Outputs: `edges.parquet` and `buildings.parquet` (with `uID` and `nID`).
```
python street_network.py -r *region of interest file* -b work/tessellation/buildings.parquet -e work/roads/roads.parquet -o work/streets
```

### 2. Morphometrics

**Building and tessellation morphometrics.** Use `-m all` to compute all metrics (one `.parquet` file per metric):
```
python building_morphometrics.py -m all -b work/streets/buildings.parquet -t work/tessellation/tessellation.parquet -e work/streets/edges.parquet -o work/morphometrics
```

**Road morphometrics** (orientation of the streets, sampled every 10 m):
```
python road_morphometrics.py -m strOri -r work/streets/edges.parquet -o work/morphometrics
```

> ⚠️ Metrics that already exist in the morphometrics dir (and the cached graph `queen_1_graph.pkl`) are loaded instead
> of recomputed. Use an empty morphometrics dir when the input data changes.

| Metric | Element | Description |
|---|---|---|
| `sdbAre` | Building | Area |
| `stbOri` | Building | Orientation (deviation from the cardinal directions, 0–45°) |
| `mtbAli` | Building | Alignment (mean orientation difference to neighboring buildings) |
| `mtbNDi_log` | Building | Neighbor distance (log-transformed mean distance to neighboring buildings) |
| `strAli` | Building | Street alignment (orientation difference to the nearest street; 45° if no street within 500 m) |
| `sdcAre` | Tessellation cell | Area |
| `stcOri` | Tessellation cell | Orientation (deviation from the cardinal directions, 0–45°) |
| `sicCAR` | Tessellation cell | Area ratio (building area / cell area) |
| `mtcWNe` | Tessellation cell | Weighted neighbors (number of neighboring cells / cell perimeter) |
| `strOri` | Street | Orientation (deviation from the cardinal directions, 0–45°) |

Neighbors are defined by first-order queen contiguity of the tessellation cells.

### 3. Aggregation to the grid

Buildings (and their tessellation cells) are assigned to grid cells by their centroids and street sample points by
location. Orientations are aggregated with the Shannon entropy of a kernel density estimate (`kdes_*`), the other
metrics with the median (`md_*`); in addition, the number of buildings (`bcount`), the summed building area within
each grid cell (`sum_sdbAre`), and the number of street sample points (`rcount`) are computed. Only grid cells
containing buildings are kept; `grid_id` is the row number (starting at 1) in the grid file.
```
python aggregation.py -m work/morphometrics -b work/streets/buildings.parquet -g *grid file* -o work/grid
```
Output: `morphometrics_grid.parquet` (in the CRS of the grid file).

### 4. Clustering

Grid cells with at least three buildings are clustered with k-means (random seed `-s`, default 7), separately for the
ISL features (`kdes_stbOri`, `md_mtbAli`, `kdes_stcOri`, `kdes_strOri`, `md_strAli`) and the SDS features
(`sum_sdbAre`, `bcount`, `md_sdbAre`, `md_mtbNDi_log`, `md_sicCAR`, `md_mtcWNe`), after standardizing the features.
Missing values are set to 0.
```
python clustering.py -m work/grid/morphometrics_grid.parquet -o work/clusters
```
Outputs:
- `clusters.parquet`: cluster labels `isl_c{k}` and `sds_c{k}` for k = 6, 8, 10, 12, 14 (-1 for grid cells with fewer than three buildings)
- `centroids_isl_k{k}.csv`, `centroids_sds_k{k}.csv`: cluster centroids (standardized features)
- `elbow.png`: elbow plots for k = 1–15
- `kmeans_models.pkl`: fitted scalers and k-means models

The stored models can be applied to the morphometrics of another area (e.g., a subset of the city) to assign each
grid cell to the nearest cluster of the city-wide clustering:
```
python clustering.py -m *morphometrics file of the other area* -a work/clusters/kmeans_models.pkl -o *output dir*
```

### 5. Indicator-based model

The clusters are interpreted (e.g., together with local stakeholders) to select the clusters that represent each
indicator. Cluster letters A, B, C, ... correspond to cluster numbers 0, 1, 2, ... A grid cell has high morphological
informality (2) if both indicators are present, medium (1) if one is present, and low (0) otherwise. The optional
grid file adds grid cells without buildings (low).
```
python indicatorbasedmodel.py -c work/clusters/clusters.parquet --sds-clusters *cluster numbers* --isl-clusters *cluster numbers* --sds-n-clusters 10 --isl-n-clusters 10 -g *grid file* -o work/model
```
Output: `model.parquet` with the indicators (`sds`, `isl`) and morphological informality (`mi`).

For example, the Nairobi model (V2) uses 10 clusters for both indicators with `--sds-clusters 2 --isl-clusters 0 5 8 2 4 7`
(SDS: C; ISL: A, F, I, C, E, H).
