# Directory of Resources for Platform Datasets 

Datasets describing different aspects of urban deprivation or assets can be put forward for presentation and validation on the IDEAMAPS Data Ecosystem platform.

This directory contains documents that help clarify the expectations for those datasets.

## Directory Contents

- [README.md](README.md): This document catalogues the different resources for datasets that are uploaded to the IDEAMAPS Data Ecosystem platform.
- [dataset-format.md](dataset-format.md): This document describes the expected structure of the datasets that are uploaded to the IDEAMAPS Data Ecosystem platform.
- [dataset-interpretability.md](dataset-interpretability.md): An example of the interpretability document that accompanies the datasets that are uploaded to the IDEAMAPS Data Ecosystem platform.
- [dataset-metadata.md](dataset-metadata.md): This document describes the expected structure of the metadata that accompanies the datasets that are uploaded to the IDEAMAPS Data Ecosystem platform.
- [dataset-metadata.json](dataset-metadata.json): This is an example of a `dataset-metadata.json` file that should accompany the datasets that are uploaded to the IDEAMAPS Data Ecosystem platform.
- [dataset-licensing.md](dataset-licensing.md): This document describes the licensing requirements for datasets that are uploaded to the IDEAMAPS Data Ecosystem platform.
- [criteria-for-inclusion.md](criteria-for-inclusion.md): This document describes the criteria for inclusion of datasets on the IDEAMAPS Data Ecosystem platform.
- [example-dataset.csv](example-dataset.csv): An example dataset that can be used to understand the expected format of datasets that are uploaded to the IDEAMAPS Data Ecosystem platform.
- [/image-examples](image-examples): A directory containing example images that should be used to guide users on the type of images that should be uploaded alongside datasets.

## Quick Start Guide
Below is a short summary of the content of the documents in this directory:

#### Formats
Datasets should be in tabular `.csv` format with each row representing a 100x100m grid cell within a set study area. The columns should include `latitude`, `longitude`, `lat_min`, `lat_max`, `lon_min`, `lon_max`, and `result`. The `result` column should contain a binary value of either `0` or `1` or `2` and the `focused` column should contain a binary value of either `0` or `1`.

#### Focus Areas
Datasets can have focus areas that are of particular interest to the data owner. These areas can be highlighted in the dataset using the `focused` column. Dataset owners should choose grid cells that are of particular interest to them and mark them as `1` in the `focused` column. These areas will be highlighted on the interface for users to focus validation efforts on. Once all focus areas have been satisfactorily validated - the validation dataset will be provided to the data owner.

#### Interpretability
Each dataset must be accompanied by an interpretability document that explains how the dataset should be interpreted. This document should be written in non-technical language and should be accessible to a wide audience. The document should be in `.md` format and can contain images and other linked content.

#### Metadata
Each dataset must be accompanied by a metadata document that describes the dataset in detail. This document should be written in `.json` format and should contain information about the dataset such as the dataset name, the dataset owner, the dataset description, the dataset categories, and the dataset licensing attribution.

#### Licensing
Each dataset must be accompanied by a licensing document that describes the terms of use of the dataset. This document should be written in `.md` format and should contain information about the dataset licensing attribution.

#### Image Examples
Each dataset should be accompanied by a set of image examples that demonstrate or represent the dataset categories in some way. These images should be square and should be named according to the dataset categories - `result` column. For example, if the dataset categories are `Low`, `Medium`, and `High`, the images should be named `example-model-low.png`, `example-model-medium.png`, and `example-model-high.png`.

## Upload Process
Datasets shown on the IDEAMAPS Data Ecosystem platform are subject to a review process - the criteria for which are outlined in the [criteria-for-inclusion.md](criteria-for-inclusion.md) document.

Once a dataset has been approved for validation purposes on the platform - the upload and ingestion processes may begin. 

To upload a dataset to the IDEAMAPS Data Ecosystem platform, the following steps should be followed:

1. Prepare the dataset and its resources according to the guidelines set out in this directory.
2. Ensure that you have access to the `ideamaps-models` Github repository. If you do not - contact the platform administrators using the contact details below.
3. Create a new branch in the `ideamaps-models` repository for the dataset that you are uploading using the branch convention outlined in the [CONTRIBUTING.md](/CONTRIBUTING.md) document.
4. Push the dataset and its resources to the new branch in the `ideamaps-models` repository.
5. Create a pull request to merge the new branch into the `dev` branch of the `ideamaps-models` repository.
6. Assign the pull request to the platform administrators for review.
7. Once the pull request has been reviewed and approved - the dataset will be ingested into the platform and will be available for validation.
8. The dataset owner will be notified of this and will be able to track the validation progress of the dataset on the platform.

## Folder Example
To upload a dataset to the IDEAMAPS Data Ecosystem platform, the following folder structure should be followed:

```
dataset-name
│   scripts
│   city
    │   dataset-outputs.csv
    │   dataset-metadata.json
    │   dataset-interpretability.md
    │   licensing.md
    │   image-examples
    │       │   example-model-high.png
    │       │   example-model-medium.png
    │       │   example-model-low.png
```

You can see an example of this folder structure in the [example-folder-structure](/models/example-folder-structure) directory.

- `dataset-name`: Top level folders should be named after the dataset they pertain to
- `scripts`: The scripts folder contains all source code used to generate the dataset
- `city`: The city folder should be named after the city in question. It contains all dataset related files (aside from those in the scripts folder).
- `dataset-outputs.csv`: The file that contains the dataset itself. Must be in `.csv` format.
- `dataset-metadata.json`: A file containing strict metadata information about the dataset. Must be in `.json` format
- `dataset-interpretability.md`: A non-technical document to be shown on the platform as a guide for users on how to intepret the results. An example is provided in this folder. Must be in `.md` format and can contain images and other linked content.
- `licensing.md`: A file that determines the dataset's terms of use. This must be in line with the terms of use set out by IDEAMAPS Data Ecosystem (see [dataset-licensing.md](dataset-licensing.md))
- `image-examples`: A folder containing square images that demonstrate or represent the dataset categories in some way. Must follow naming convention listed in folder example.


## Platform Administration
The IDEAMAPS Data Ecosystem platform administrators are responsible for the faciliatation of datasets that are uploaded to the platform. The administrators will also provide support to dataset owners who are looking to upload their datasets to the platform.

For help and support with uploading datasets to the IDEAMAPS Data Ecosystem platform - please contact the platform administrators at [andrew.c.clarke@glasgow.ac.uk](mailto:andrew.c.clarke@glasgow.ac.uk) or [diego.pajaritograjales@glasgow.ac.uk](mailto:diego.pajaritograjales@glasgow.ac.uk).