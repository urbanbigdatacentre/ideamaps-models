---
title: Flood Hazard
author: lorraine.otieno@itc.nl
category: Our Data
tags: [hazard, flood, datasets]
---

# Flood Hazard (Version 1)

Flood Hazard is a dataset that maps the potential risk of flooding across urban areas in cities such as Nairobi and Lagos. It is derived using the **FastFlood** hydrodynamic model, which simulates water accumulation from intense rainfall events. Flood risk is classified into **Low**, **Medium**, or **High** hazard levels, and reflects predicted water depth based on high-resolution topographic and rainfall data.

<aside>
💡 This page will help you understand more about how the classifications of Low - Medium - High are predicted in our flood hazard model.
</aside>

## Definitions of Hazard Levels

The dataset predicts flood hazard levels using simulations based on rainfall intensity, elevation, and surface flow accumulation. These levels — **Low, Medium, or High** — indicate the expected severity of flooding in each area.

Below, we define the flood hazard levels:

### Low
<blockquote>Areas that experience floods below 10 cm (ankle-height) or no floods at all. Water does not stagnate during rainy seasons and only causes minor access disruptions.</blockquote>

<img src="image-examples/example-low-flood-hazard.png" alt="example-low">

### Medium
<blockquote>Think of frequent yearly floods in the city. These areas experience floods between 10 and 100cm (waist-height). When flooded, the population can face severe disruptions.</blockquote>

<img src="image-examples/example-medium-flood-hazard.png" alt="example-medium">

### High
<blockquote>Think of the most severe floods in the city. These areas experience floods above 100cm (above waist line). When flooded, the population face life-threatening impacts.</blockquote>

<img src="image-examples/example-high-flood-hazard.png" alt="example-high">

Together, rainfall simulation, topography, and drainage conditions contribute to the flood hazard level for each grid cell on our map.

To learn more about how you can help improve the accuracy of these classifications, visit our page on [How to Validate Our Data](/docs/using-the-map/how-to-validate-our-data).

## Additional Insights into Flood Hazard Modelling

This section provides additional information on how flood risk is modeled using FastFlood.

**FastFlood** is a low-complexity 2D flood model designed to predict areas likely to accumulate water during extreme rainfall events. It integrates:

- Digital Elevation Models (DEMs)
- Surface runoff and flow direction estimation
- Rainfall data from both global datasets and local gauges

The model uses hydrodynamic flow-routing to estimate where water will likely pool on the ground surface after heavy rains. Water depth in each grid cell is calculated, and thresholds are applied to classify flood hazard.

The following criteria are used for classification:

- **Low**: Predicted water depth is negligible or within tolerable levels
- **Medium**: Moderate predicted water depth; localised flooding possible
- **High**: Severe predicted water depth; high flood risk

These simulations are aggregated to our 100 m × 100 m grid cells, and each grid cell is assigned a classification accordingly.

## Data Used for Modelling

The model relies on the following datasets:

- **Digital Elevation Models (DEM)** (SRTM)
- **Rainfall data** (e.g., CHIRPS, local meteorological gauge stations)
- **Land surface data** (including soil and permeability estimates)

Flood hazard modelling and simulations were conducted by [ITC](https://www.itc.nl/) as part of the [Space4All](https://www.itc.nl/research/projects/space4all/) project.

The satellite images used in the classification examples were obtained from [Google Maps](https://www.google.com/maps) (Google, Maxar Technologies).

