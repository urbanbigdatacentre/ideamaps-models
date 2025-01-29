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
