---
title: Morphological Informality
author: grace.gielink@glasgow.ac.uk
category: Our Data
tags: [deprivation, datasets]  
---

# Morphological Informality

Morphological Informality is a dataset focused on mapping the difference between formally planned and informally planned areas of cities as an indication of urban deprivation. The levels of “morphological informality” are classified as **Low morphological informality, Medium morphological informality, or High morphological informality**. Generally, higher levels of informality are related to more deprived areas.

<aside>
💡 This page will help you understand more about how the classifications of Low - Medium - High are predicted in our data model.

</aside>

## Main Indicators of Morphological Informality

The dataset combines three main indicators of morphological informality: Building Density and Arrangements, Road Arrangements, and Population Density.

Together, these indicators help predict the level of informality —> **Low, Medium, or High.**

For each indicator (Buildings, Roads, and Population), our modellers used a set of parameters to classify the data into the categories of Low, Medium, and High. Below, we describe those parameters.

### Buildings

*Low*
<blockquote > Buildings are large, detached from each other with formal arrangements and low density of at least 500 buildings per km2.</blockquote>
<img src="/docs/our-data/morphological-informality/buildings-low.png" alt="buildings-low"/>


*Medium*
<blockquote> Buildings are small and dense OR have variable building arrangements with moderate density of at least 1,500 buildings per km2.</blockquote>
<img src="/docs/our-data/morphological-informality/buildings-low.png" alt="buildings-medium"/>

*High*
<blockquote > Buildings are small and dense OR have variable building arrangements with moderate density of at least 1,500 buildings per km2.</blockquote>
<img src="/docs/our-data/morphological-informality/buildings-high.png" alt="buildings-high"/>


### Roads

*Low*
<blockquote> Roads are paved and wide with uniform paths. The paved road density is at least 1.25 km per km2.</blockquote>
<img  src="/docs/our-data/morphological-informality/roads-low.png" alt="roads-low"/>



*Medium*
<blockquote>There are both paved and unpaved roads, with a combination of planned and unplanned paths. The paved road density is at least 0.76 km per km2.</blockquote>
<img src="/docs/our-data/morphological-informality/roads-medium.png" alt="roads-medium"/>


*High*

<blockquote>Paths and roads are narrow and unpaved. The paved road density is at least 0.3 km per km2.</blockquote>
<img src="/docs/our-data/morphological-informality/roads-high.png" alt="roads-high" />


<aside>
💡 Together, these indicators combine to form the different classifications of morphological informality that you see reflected in the grid cells on our map. 

To learn more about how you can help improve the accuracy of these classifications, visit our page on [How to Validate Our Data](/docs/using-the-map/how-to-validate-our-data).

</aside>
