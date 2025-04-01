# IDEAMAPS Platform Validation Datasets
This document describes the validation dataset exports that the IDEAMAPS Data Ecosystem publishes for public access on Zenodo at the completion points of platform validation campaigns. 

##### Table of Contents
- [About Validation Datasets](#about-validation-datasets)
- [Accessing the Data](#accessing-the-data)
- [Pre-Processing](#pre-processing)
- [About Validation](#about-validation)
- [Structure of the Data](#structure-of-the-data)
- [Variable Descriptions](#variable-descriptions)

## About Validation Datasets
Users of the IDEAMAPS Data Ecosystem create validation datasets as they provide quantitative feedback on the platform's dataset. By exploring the datasets and reclassifying grid cells they believe are incorrectly classified, our community of users build up a validation dataset. These reclassifications are captured by the platform in order to provide a resource to improve the original data. The structure of the validation dataset export can be seen below - [Structure of the Data](#structure-of-the-data).

To give an example - gridded datasets on the IDEAMAPS Data Ecosystem platform typically consist of 100x100m grid cells classified as either Low (0) - Medium (1) - High (2). A user's validation of each grid cell means that the key value offering from the validation datasets is the reclassification of the grid cells value of Low (0) - Medium (1) - High (2) as per the user's validation.

Each validation dataset is created at its most granular level - meaning one row represents one validation. This is done so that our export packages can cater for the broadest use cases possible. The validation dataset also comes with enriched information about the user making each validation and of course links to the original value from the presented dataset.

## Contributors
Each user that contributed to a validation dataset will be listed in a CONTRIBUTORS file that is part of the dataset entry on Zenodo. Consent for this is granted in the process of creating an account wherein the user agrees to the terms and conditions of the platform. 

## License
Each validation dataset will be licensed using the CC BY-NC-SA 2.0 license - https://creativecommons.org/licenses/by-nc-sa/2.0/deed.en. This will be published as part of the Zenodo dataset entry in markdown format.

## Metadata
Each validation dataset will be published alongside a unique metadata file that describes the validation dataset and provides a link to the original dataset that was being validated. The format of the metadata file is described below:

```json
{
  "number-validations": 405,
  "campaign-start": "01/01/2025",
  "campaign-end": "01/01/2026", 
  "reason-for-campaign-end": "Focus Area Completion",
  "study-dataset-name": "Example Dataset",
  "study-dataset-city": "Lagos",
  "study-dataset-DOI": "https://doi.org/10.5281/zenodo.14699940"
}
```

## Accessing the Data
Access to the raw validation data is not permitted outside of the University of Glasgow. This is due to the sensitive nature of certain variables within the data.

Non-sensitive validation dataset exports are published on Zenodo as dataset entries at the completion point of validation campaigns. Links to these entries will be published on the platform as soon as the Zenodo entry has been created.

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
