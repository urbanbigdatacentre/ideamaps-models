# Dataset Metadata

To allow the storage of datasets in our platform - the submission of datasets to a publicly accessible `csv` file is required. For more information on the format of the datasets - please refer to the [dataset-format.md](dataset-format.md) document.

Alongside the submission of datasets - the dataset must be accompanied by a `dataset-metadata.json` file. This file contains metadata about the dataset and the datasets. The metadata is used to describe the dataset and its outputs in the platform.

The requirements for the `dataset-metadata.json` file are as described here.

In addition to the `dataset-metadata.json` file - the dataset owners should create a non-technical document that helps users to understand the datasets. This document should be in the form of a `dataset-interpretability.md` file and should be stored in the same directory as the outputs file and the `dataset-metadata.json` file. This document should contain information about how the datasets should be interpreted by users - crucially including how the thresholds for output categories should be interpreted.

Finally, a series of images should be pushed to the dataset directory. These images serve to show the difference between the different categorisations of the dataset. These images should be pushed independently to the same directory as the `dataset-metadata.json` file and the datasets.

### Requirements

1. `dataset-metadata.json` file.
2. `dataset-interpretability.md` file.
3. Images to show the difference between the different categorisations of the dataset.

## File Format - `dataset-metadata.json`

The `dataset-metadata.json` file must be in a JSON format and contain the following fields:

- `name`: The name of the dataset.
- `notes`: A one sentence summary of the dataset.
- `city`: The city for which the datasets are generated.
- `subdomain`: The subdomain for which the datasets are generated.
- `output_keys`: A list of the output keys for the dataset. This should be in JSON format with the numeric value of the output as the key and the output name as the value.
- `features`: A list of the features used in the dataset.


## Example - `dataset-metadata.json`

Here is an example of a `dataset-metadata.json` file - also found in the [dataset-metadata.json](dataset-metadata.json) file in this directory:

```json
{
    "name": "Example dataset",
    "notes": "This is an example dataset.",
    "city": "Example City",
    "subdomain": "Example Subdomain",
    "output_keys": {
        "0": "Low",
        "1": "Medium",
        "2": "High"
    },
    "features": [
        "Population Density",
        "Roads",
        "Buildings"
    ]
}
```

## About the `dataset-interpretability.md` file

The `dataset-interpretability.md` file should contain information about how the datasets should be interpreted by users. This document should be written in a non-technical manner and should be easily understandable by non-experts. The document should include information about the thresholds for output categories and how they should be interpreted.

The document should begin with a summary paragraph that is able to capture the main features of the dataset in no more than 3 sentences.

This should also include information about the features that are described by the dataset.

The `dataset-interpretability.md` file should be stored in the same directory as the dataset itself and the `dataset-metadata.json` file.

Images and visualisations can be a good way to help non-technical users understand the difference between the different categorisations of the dataset - these should be pushed independently to the same directory as the `dataset-metadata.json` file and the datasets.

## About the Images

The images should be pushed to the dataset directory and should be used to show the difference between the different categorisations of the dataset.

The images should correspond directly to the `output_keys` in the `dataset-metadata.json` file. For example - if the `output_keys` are `Low`, `Medium`, and `High` - then there should be 3 images that correspond to these categories.

The naming convention of the images should be as follows:

- `dataset-name-low.png` for the image that corresponds to the `Low` category.
- `dataset-name-medium.png` for the image that corresponds to the `Medium` category.
- `dataset-name-high.png` for the image that corresponds to the `High` category.

If your dataset has only two categories - replace the `high`, `medium`, or `low` with `categoryA` and `categoryB` as appropriate.

> For guidance on the format of these images, their dimensions and the content that they should contain - please refer to the `/image-examples` directory in this folder. The three images here also contain the correct naming conventions to be used for your images.

These images can be of anything that the dataset owner chooses so long as they are able to show the difference between the different categorisations of the dataset.

The images should be provided in `.png` format and should be square in dimensions (400 x 400) would be preferable.