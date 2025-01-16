# Dataset Format

This platform provides storage for datasets about urban deprivation and assets in our PostgreSQL database. The datasets are loaded from a publicly accessible `csv` file and ingested into the platform using the `release-dataset.ipynb` notebook - found within the `scripts` folder of this repo. The datasets are stored in the `outputs` table in the database.


## Table of Contents

## About the Data
Datasets ingested into our platform study an aspect of urban deprivation. The outputs are geo-spatially referenced to areas of a chosen study city. To create the outputs, dataset owners can make geo-spatial references at any granularity. However in order to be uploaded to the platform - these must be aggregated to 100x100m grid cells. For more information about spatial aggregation - please reference the [ideamaps-datasets](https://github.com/urbanbigdatacentre/ideamaps-datasets) repository.

Datasets can be generated using a variety of techniques that are outside of the scope of this document. This platform is interested only in whether the datasets can be ingested into the platform and visualised on the map.

In order for this to happen - the datasets must form a very specific structure - seen below.

## Data Source
The datasets are stored in a `csv` file. The `csv` file must be publicly accessible and hosted on a server that can be accessed by the platform.

One such source might be an S3 bucket. Another effective source of the data is the [ideamaps-datasets](https://github.com/urbanbigdatacentre/ideamaps-datasets) repository. This repository contains folders for each of the domains of deprivation that the platform is interested in. Within each domain folder, there are subfolders for each of the study cities. Within each city folder, there are subfolders for each of the datasets that have been generated. The datasets are stored in `csv` files within these dataset folders.

Files uploaded here can be viewed or accessed in `raw` format. This is the format that the platform will use to ingest the datasets. Any other format will not be accepted.

## Data Structure

The datasets must be in a `csv` format with the following columns:
- `latitude` - The centroid latitude of the grid cell.
- `longitude` - The centroid longitude of the grid cell.
- `lat_min` - The minimum latitude of the grid cell.
- `lat_max` - The maximum latitude of the grid cell.
- `lon_min` - The minimum longitude of the grid cell.
- `lon_max` - The maximum longitude of the grid cell.
- `result` - The result of the dataset output. This must be either a 0 or a 1 or a 2 defined as an **integer**. Floats are not accepted.

### Latitude and Longitude Formats
The `latitude`, `longitude`, `lat_max`, `lat_min`, `lon_max` and `lon_min` columns must all be specified in Decimal Degrees (DD) format. This is the most common format for geo-spatial data and is the format that the platform uses to visualise the data on the map.

In Decimal Degrees format, the latitude and longitude are specified as floating point numbers. The latitude must be between -90 and 90 and the longitude must be between -180 and 180.

For more information on this please see this document from [Mapbox](https://docs.mapbox.com/help/glossary/lat-lon/).

### Result Column
The `result` column should hold the content of your dataset output. This should be a binary value of either `0` or `1` or `2`. The platform will visualise this output on the map using a colour scale. The colour scale is defined by the number of categories in the dataset output.

The `result` column is capable of holding either 2 or 3 categories. This must remain consistent throughout the datasets file. The categories must be defined in the following way:

##### 3 Categories
Example:     `Low, Medium, High`
Notes: 3 category definitions can ONLY be `Low`, `Medium`, and `High` - Please enter these categories in the order specified above. This order represents the value of the output in the format `Low = 0, Medium = 1, High = 2`.

##### 2 Categories
Example:     `Non-Slum, Slum,`
Notes: 2 category definitions can be defined flexibly - meaining any binary definition is acceptable. Please enter 2 categories in the these categories so that the lowest output value is defined first - i.e ` Non-Slum = 0, Slum = 1`.

## Data Example
Here is an example of the `csv` format required for a datasets file to be considered ready for ingestion into the platform.

| result | latitude     | longitude   | lon_min     | lat_min     | lon_max     | lat_max     |
|--------|--------------|-------------|-------------|-------------|-------------|-------------|
| 0      | -1.116531172 | 36.93855402 | 36.93805194 | -1.116935586| 36.9390561  | -1.116126759|
| 1      | -1.116531172 | 36.93955191 | 36.93904983 | -1.116935586| 36.94005399 | -1.116126759|
| 0      | -1.116531172 | 36.94054981 | 36.94004772 | -1.116935586| 36.94105189 | -1.116126759|
| 1      | -1.116531172 | 36.9415477  | 36.94104562 | -1.116935586| 36.94204978 | -1.116126759|
| 0      | -1.116531172 | 36.9425456  | 36.94204351 | -1.116935586| 36.94304768 | -1.116126759|

You can see a sample of the data in the `example-dataset-outputs.csv` file within this folder.
