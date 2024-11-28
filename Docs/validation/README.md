# IDEAMAPS Platform Validation Data
This document describes the validation

##### Table of Contents
- [Accessing the Data](#accessing-the-data)
- [Pre-Processing](#pre-processing)
- [About Validation](#about-validation)
- [Structure of the Data](#structure-of-the-data)
- [Variable Descriptions](#variable-descriptions)


## Accessing the Data
Access to the raw validation data is not permitted outside of the University of Glasgow. This is due to the sensitive nature of the certain variables within the data.

A non-sensitive version of the validation data is currently available from the Google Drive location here - [IDEAMAPS Validation Data](https://drive.google.com/drive/folders/1S2XXCmg9oRiFMWHympz830HNe-TD69sY)

## Pre-Processing
The validation data is pre-processed to remove any sensitive information. This includes the exclusion of the following variables:
- `user_location`
- `user_display_name`
- `user_email`

In addition - the data is also pre-processed so that validation made by IDEAMAPS staff members - also considered to be test data - is removed from the dataset. This is done by filtering out any records where the `user_email` is included within a blacklist.

## About Validation
The validation dataset contains the feedback of users on IDEAMAPS datasets. Users can  interact with grid cells on our map to validate the data they see. Each grid cell is either classified as (3 POINT: Low - Medium - High) OR (2 POINT: True - False) for the type of dataset you are currently exploring.

Validation means interacting with our grid cells. Users can double-click on grid cells to change their classification. Double-clicking on a Low (blue) grid cell two times will change it’s appearance to a Medium (orange) cell.

We record the input of users and store it in our database. This data can be passed to dataset owners to improve the quality of their datasets.

## Structure of the Data

The validation data is stored in a CSV file. The data is structured as follows:

- **id**: `UUID`
- **created_at**: `Timestamp`
- **validation**: `Float`
- **user_id**: `UUID`
- **user_background**: `List of strings`
- **user_map_usage**: `Float`
- **output_id**: `UUID`
- **output_model**: `UUID`
- **output_model_city_name**: `String`
- **output_model_city_country**: `String`
- **output_model_subdomain_name**: `String`
- **output_result**: `Integer`
- **output_latitude**: `Float`
- **output_longitude**: `Float`

## Variable Descriptions

#### `id`
A unique identifier for each record.

#### `created_at`
The date and time when the record was created, in ISO 8601 format.

#### `validation`
A numerical value representing the validation score.
The possible values for 3-Point Models are:
```javascript
{
  0: "Low",
  1: "Medium",
  2: "High"
}
```

#### `user_id`
A unique identifier for the user.

#### `user_background`
Categories or tags describing the user's background.

The possible values are:
```javascript
[
    {
      name: 'Community Member',
    },
    {
      name: 'Policy / Government',
    },
    {
      name: 'Research',
    },
    {
      name: 'NGO / Charity',
    },
    {
      name: 'Just Browsing',
    },
    {
      name: 'Someone Different',
    }
]
```

#### `user_map_usage`
A numerical value representing the user's map usage.

The possible values are:

```javascript
[
    {
        name: 'Never',
        value: 0,
    },
    {
        name: 'Rarely',
        value: 1,
    },
    {
        name: 'Sometimes',
        value: 2,
    },
    {
        name: 'Often',
        value: 3,
    },
    {
        name: 'Always',
        value: 4,
    }
]


```

#### `output_id`
A unique identifier for the output.

#### `output_model`
A unique identifier for the output model.

#### `output_model_city_name`
The name of the city associated with the output model.

#### `output_model_city_country`
The country of the city associated with the output model.

#### `output_model_subdomain_name`
The subdomain name of the output model.

#### `output_result`
A numerical value representing the output result.
The possible values for 3-Point Models are:
```javascript
{
  0: "Low",
  1: "Medium",
  2: "High"
}
```

#### `output_latitude`
The latitude coordinate of the output location.

#### `output_longitude`
The longitude coordinate of the output location.

## Contact
For any questions or queries, please contact the platform administrator at [andrew.c.c.clarke@glasgow.ac.uk](mailto:andrew.c.clarke@glasgow.ac.uk)
