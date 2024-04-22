# Sharing Your Model Outputs With our [IDEAMAPS Data Ecosystem](http;//www.ideamapsnetwork.org)

This document describes how modellers can share their model ouputs with the IDEAMAPS Data Ecosystem. The IDEAMAPS Data Ecosystem is a platform that allows modellers to publish Machine Learning or Artificial Intelligence model outputs that describe urban deprivation and enable participative validation and improvement of the data. The participatory approach of our group has inspired this feature to encourage multiple stakeholders to generate, validate and use the model outputs to understand the living conditions in their cities. The platform offers a tool supported by [Hasura](https://hasura.io/) to allows modellers to share their model outputs in a structured way.

The following sections will describe in detail how a dataset that describes urban deprivation can be uploaded, shared and validated in our prlatfor.

## What is a model output?
A model output is a geospatial dataset that summarises the conditions of urban deprivation in a city. The dataset is usually generated using Machine Learning or Artificial Intelligence models by members of the IDEAMAPS Data Ecosystem. The dataset should be in a structured format that can be easily understood and processed by the tools provided by our platform. 

### Geospatial data grid
The IDEAMAPS Data Ecosystem visualises model outputs as an aggregated layer composed of a uniform gridded space. The grid itself is the one defined by the Global Human Settlements Layer (GHSL) and is composed of 100m x 1000m cells. Despite being a raster model, our project decided to use a vector format to store the model outputs. The vector format is more flexible and allows for easier processing and sharing of the data. The model outputs are expected to provide the coordinates of the cell centroids as well as the max and min coordinates that thefine the bouding box.

|latitude|longitude|min_latitude|min_longitude|max_latitude|max_longitude|value|
|--------|---------|------------|-------------|------------|-------------|-----|
|6.5244  | 3.3792  | 6.5240     | 3.3788      | 6.5248     | 3.3796      | 5   |
|6.5245  | 3.3793  | 6.5241     | 3.3789      | 6.5249     | 3.3797      | 7   |
|6.5246  | 3.3794  | 6.5242     | 3.3790      | 6.5250     | 3.3798      | 3   |

### Data Structures
The following is the expected data structure for a generic model output data set. The data structure is a dictionary with the following keys and example values:

| Field | Description | Example |
|--------|---------|------------|
| WKT | This is the geometry value for the grid cell. The geometry must be provided as an OGC-compliant Well Known Text with the four nodes of the gridcell | "POLYGON ((3.35774579148031 6.46650870826469,3.35874750561858 6.46650870826469,3.35874418174467 6.46569796096381,3.35774246859772 6.46569796096381,3.35774579148031 6.46650870826469))" |
| latitude | Grid's centroid latitude in degreees | 6.46610333468111 |
| longitude | Grid's centroid longitude in degreees | 3.35824498686059|
| lon_min  | Grid's minumum longitude in degreees | 3.35774246859772 |
| lat_min | Grid's minumum latitude in degreees | 6.46569796096381 |
| lon_max | Grid's maximal longitude in degreees | 3.35874750561858 |
| lat_max | Grid's maximal latitude in degreees | 6.46650870826469 |
| model_value | This is the model output value. It must be a numeric value between 0.0 and 1.0. Numbers wiht decimal values are also valid | 1 |

### Data structure for the tabular data
The expected dataset should have the following structure:

| WKT | model_value | latitude | longitude | lon_min | lat_min | lon_max | lat_max |
|-----|-------------|----------|-----------|---------|---------|---------|---------|
| "POLYGON ((3.35774579148031 6.46650870826469,3.35874750561858 6.46650870826469,3.35874418174467 6.46569796096381,3.35774246859772 6.46569796096381,3.35774579148031 6.46650870826469))" | "1" | 6.46610333468111 | 3.35824498686059 | 3.35774246859772 | 6.46569796096381 | 3.35874750561858 | 6.46650870826469 |
| "POLYGON ((3.34972544889479 6.46488721416079,3.35072716105056 6.46488721416079,3.35072384595702 6.46407646785558,3.34972213479231 6.46407646785558,3.34972544889479 6.46488721416079))" | "0" | 6.46448184107503 | 3.35022464767394 | 3.34972213479231 | 6.46407646785558 | 3.35072716105056 | 6.46488721416079 |
| "POLYGON ((3.35773582410999 6.46407646785558,3.35873753527471 6.46407646785558,3.35873421267864 6.46326572204809,3.35773250250486 6.46326572204809,3.35773582410999 6.46407646785558))" | "1" | 6.46367109501867 | 3.35823501864232 | 3.35773250250486 | 6.46326572204809 | 3.35873753527471 | 6.46407646785558 |
|...|...|...|...|...|...|...|...|



## File format
At the moment our ingestion pipeline supports plain text formats ".txt" or ".csv". In the near future, the team aims to standardise the ingestion pipeline to support geospatial data formats such as geoJSON and geoPackage.

## Model Output description and metadata
In addition to the model output data, the modeller is expected to provide a description of the model output and metadata that will serve to prepare it for visualisation in our platform. The metadata should include the following information:

| Item | Description | Example |
|--------|---------|------------|
| Country Name | Country where the model outputs are located | Nigeria |
| City Name | City from where the model outputs are generated | Lagos |
| Subdomain | This is the subdomain that is being modelled, a description of the domais of deprivation that we work with can be seen in our [concept paper](https://www.mdpi.com/2076-0760/9/5/80). At the moment, our platform supports only the following subdomains: [Morphological Informality](../../Sub-domains/MorphologicalInformality/), [healthcare](../../Sub-domains/Healthcare/MaternalHealth/), [housing](../../Sub-domains/Housing/), [water, sanitation and hygiene WASH](../../Sub-domains/WASH/)   | Overall Deprivation |
| Model Display Name | This will be the name that will be seen in the screen and will allow users to select the model for visualisation | Urban Deprivation Model |

Once the model is submitted, the quality control process starts automatically.


## Our Quality Control Process
Under construction :construction:

## Succesfull load and other feedback
Under construction :construction:

## Error codes 
Under construction :construction:

## Further info
Under construction :construction:

## Hasura endpoint 
Under construction :construction:

## How to use the Action
Under construction :construction:







This issue can be closed once the document has been created and uploaded to the /models repo within it's own isolated space.