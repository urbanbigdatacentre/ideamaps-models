# IDEAMAPS Validation Data: Road Access Deprivation – Kano, Nigeria

This dataset contains user-contributed validation records for modelled outputs estimating **road access deprivation** in **Kano, Nigeria**. The data was generated and validated via the [IDEAMAPS Data Ecosystem](https://ideamaps.org), a collaborative platform for mapping urban deprivation using local knowledge and scientific models.

---

## 📦 Contents

- `validation-kano-road-access-deprivation.csv`: Main dataset with 21 validation records
- `metadata.json`: Describes the structure, fields, and context of the dataset
- `LICENSE.md`: (CC BY-NC 4.0) license for dataset use
- `CONTRIBUTORS.md`: List of user display names that contributed to the validation dataset

---

## 🧠 About the Data

> **Campaign Status:** Ongoing

> **Validation Dataset Generated:** 03-06-2025


Users of the IDEAMAPS Data Ecosystem create validation datasets as they provide quantitative feedback on the platform's dataset. By exploring the datasets and reclassifying grid cells they believe are incorrectly classified, our community of users build up a validation dataset. These reclassifications are captured by the platform in order to provide a resource to improve the original data.

Each row represents a validation submitted by a platform user assessing a modelled prediction about urban deprivation. Users indicate how accurate they believe the output is based on their local knowledge or expertise.

To give an example - gridded datasets on the IDEAMAPS Data Ecosystem platform typically consist of 100x100m grid cells classified as either Low (0) - Medium (1) - High (2). A user's validation of each grid cell means that the key value offering from the validation datasets is the reclassification of the grid cells value of Low (0) - Medium (1) - High (2) as per the user's validation.

Each validation dataset is created at its most granular level - meaning one row represents one validation. This is done so that our export packages can cater for the broadest use cases possible. The validation dataset also comes with enriched information about the user making each validation and of course links to the original value from the presented dataset.

**Key Fields:**
- `validation`: User's rating of model accuracy
    - `0` = Low
    - `1` = Medium
    - `2` = High
- `user_background`: Self-described background of the validator (e.g. `['Research']`, `['Community Member']`)
- `user_map_usage`: Self-rated experience using maps (scale: 1–3)
- `output_result`: Model classification at a specific location
- `output_latitude` / `output_longitude`: Geolocation of the validated output

---

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

## Use Cases

This dataset is useful for:

- **Ground truthing** geospatial datasets of urban deprivation using local input
- Supporting **urban planning and health access policy research**

---

## Licensing and Attribution
**License:** Creative Commons Attribution 4.0 International (CC BY 4.0)

**Citation:** If using this data, please cite:

> IDEAMAPS Data Ecosystem. (2025). Validation Data: Road Access Deprivation – Kano, Nigeria [Data set]. Zenodo. https://doi.org/xxxx/zenodo.xxxxxxxx

## Contact
For any questions or queries, please contact the platform administrator at [andrew.c.c.clarke@glasgow.ac.uk](mailto:andrew.c.clarke@glasgow.ac.uk)
