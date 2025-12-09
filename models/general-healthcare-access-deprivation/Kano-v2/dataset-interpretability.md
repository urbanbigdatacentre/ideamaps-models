---
title: General Healthcare Access Deprivation 
authors: [Diego Pajarito Grajales - Diego.PajaritoGrajales@glasgow.ac.uk, Xingyi Du - xingyi.du@glasgow.ac.uk]
category: Our Data
tags: [General Healthcare, Accessibility]  
---

# General Healthcare Access Deprivation

Limited access to primary health negatively impacts the Nigerian population, especially on issues like infant and maternal mortality Rates [(Ogah, P., Uguru, N., Okeke, C. et al., 2024)](https://doi.org/10.1186/s12913-024-11406-0). Also, it has consequences on the way preventable diseases spread and increased healthcare costs, making it impactful for livelihoods in general and socio economic development in the country. With 190 million Nigerians struggling to access health care [(WHO, 2024)](https://www.who.int/about/accountability/results/who-results-report-2024-2025), the understanding of such deprivation becomes crucial, especially in slums and other deprived areas.

<aside>
💡 This page will help you understand more about how the classifications of Low - Medium - High are assessed in our data model.
</aside>

<br>
This model shows how people living in slums and other deprived areas have trouble getting basic healthcare. Because of the many negative effects of not having proper healthcare, the communities have decided that this is a key topic for them to work on together in the IDEAMAPS project. The model focuses on two main factors: the availability of healthcare services and how easy it is to access them.
Healthcare availability refers to the options community members have for conveniently receiving basic healthcare. Ideally, healthcare facilities should provide services at very low costs so that serious illnesses can be detected early and common issues can be treated on time.
Healthcare accessibility looks at the time and resources needed to choose and get to a healthcare facility. When there are many facilities to choose from, it reduces the chances of not being seen by a professional due to a lack of space or full agendas. Ideally, having access to various (five or more) facilities makes it easier to receive timely care. If walking to a facility is not an option, being able to get there by vehicle should not require a long trip (no more than 30 minutes); longer trips mean higher costs and complicated transfers between different transport systems. With these points in mind, the team examined the following two factors.

1. Healthcare Offer: The offer is represented by public and primary healthcare facilities registered in different databases. In most cities, the local IDEAMAPS team complemented the dataset with their knowledge about ownership and service levels. Detailed documentation of data sources and compilation procedures can be found in the city-specific README files or Jupyter notebooks (ipynb). General health in slums and deprived areas is usually linked to public facilities, which are conveniently located to reduce travel times. This ensures low costs for arriving and receiving care.

2. Healthcare Accessibility: The team considered travel times by walking and by vehicle to estimate physical accessibility [(ORS, 2025; Florio et al., 2023)](https://doi.org/10.1016/j.apgeog.2023.103118). The team estimated travel times for each gridcell in the study areas and counted the number accessible of health facilities. With counts of cero or one health facilities, the areas were labeled as being in high access deprivation. Medium or high labels were assigned when counts increased.

## Definitions of Deprivation Levels

This dataset relates to the general healthcare services offered by public facilities and the conditions in which communities can choose and access them. In every city, counts of the healthcare facilities that can be reached by walking or by short trips by vehicle were used to estimate the three deprivation levels as —>  **Low, Medium, or High.**

### Low
<blockquote> My neighbourhood has multiple options for accessing primary healthcare. There are enough public facilities to choose from within walking distance, or if using a vehicle.

<img src="image-examples/primary-healthcare-access-deprivation-low.png" alt="example-low">

### Medium
<blockquote> There are some options to access primary healthcare in my neighbourhood. A few facilities are accessible on foot, but it is better to consider using a vehicle to have alternatives.

<img src="image-examples/primary-healthcare-access-deprivation-medium.png" alt="example-medium">

### High
<blockquote> My neighbourhood has limited options for accessing primary healthcare. There is only few or no public healthcare facility nearby. Therefore, a vehicle is required to access public facilities.

<img src="image-examples/primary-healthcare-access-deprivation-high.png" alt="example-high">

## City-Specific thresholds for general healthcare access deprivation

Thresholds for primary healthcare accessibility differ across cities due to variations in urban scale, spatial distribution of facilities, and local mobility conditions. The deprivation levels defined above should be interpreted relative to each city’s context. The table below summarises the thresholds applied in each city for classification.

### **Pilot City**

- ### Kano, Nigeria

Functional Urban Area (FUA): ~ 1409 km², FUA population: approximately 4,821,779 (2015)

| Deprivation level | Walking access (1 km)                  | Vehicle access (3.3 km)       |
|-------------------|----------------------------------------|-------------------------------|
| High (2)          | 1 or fewer facilities                  | not used for classification   |
| Medium (1)        | less than 4 facilities                 | or less than 15 facilities    |
| Low (0)           | 4 or more facilities                   | and 15 or more facilities     |

- ### Lagos, Nigeria

Functional Urban Area (FUA): ~ 2284 km², FUA population: approximately 12,337,227 (2015)

| Deprivation level | Walking access (1 km)                  | Vehicle access (3.3 km)       |
|-------------------|----------------------------------------|-------------------------------|
| High (2)          | 1 or fewer facilities                  | not used for classification   |
| Medium (1)        | less than 4 facilities                 | or less than 15 facilities    |
| Low (0)           | 4 or more facilities                   | and 15 or more facilities     |

- ### Nairobi, Kenya

Functional Urban Area (FUA): ~ 859 km², FUA population: approximately 4,712,494 (2015)

| Deprivation level | Walking access (1 km)                  | Vehicle access (3.3 km)       |
|-------------------|----------------------------------------|-------------------------------|
| High (2)          | no facilities                          | 1 or fewer facilities         |
| Medium (1)        | fewer than 2 facilities                | and fewer than 4 facilities   |
| Low (0)           | 2 or more facilities                   | or 4 or more facilities       |

### **2. Expansion City**

- ### Kisumu, Kenya

Functional Urban Area (FUA): ~ 134 km², FUA population: approximately 369,934 (2015)

| Deprivation level | Walking access (1 km)                  | Vehicle access (3.3 km)       |
|-------------------|----------------------------------------|-------------------------------|
| High (2)          | no facilities                          | no more than 2 facilities     |
| Medium (1)        | fewer than 2 facilities                | and no more than 8 facilities |
| Low (0)           | 2 or more facilities                   | or more than 8 facilities     |

- ### Accra, Ghana

Functional Urban Area (FUA): ~ 1934 km², FUA population: approximately 4,786,265 (2015)

| Deprivation level | Walking access (1 km)                  | Vehicle access (3.3 km)       |
|-------------------|----------------------------------------|-------------------------------|
| High (2)          | no facilities                          | no facilities                 |
| Medium (1)        | fewer than 1 facility                  | and fewer than 3 facilities   |
| Low (0)           | at least 1 facility                    | or at least 3 facilities      |

- ### Abuja, Nigeria

Functional Urban Area (FUA): ~ 1027 km², FUA population: approximately 2,578,150 (2015)

| Deprivation level | Walking access (1 km)                  | Vehicle access (3.3 km)       |
|-------------------|----------------------------------------|-------------------------------|
| High (2)          | no facilities                          | no more than 2 facilities     |
| Medium (1)        | fewer than 2 facilities                | and no more than 8 facilities |
| Low (0)           | 2 or more facilities                   | or more than 8 facilities     |

- ### Beira, Mozambique

Functional Urban Area (FUA): ~ 39 km², FUA population: approximately 340,492 (2015)

| Deprivation level | Walking access (1 km)                  | Vehicle access (3.3 km)       |
|-------------------|----------------------------------------|-------------------------------|
| High (2)          | no facilities                          | no facilities                 |
| Medium (1)        | fewer than 1 facility                  | and fewer than 3 facilities   |
| Low (0)           | at least 1 facility                    | or at least 3 facilities      |

- ### Pasto, Colombia

Functional Urban Area (FUA): ~ 58 km², FUA population: approximately 416,042 (2015)

| Deprivation level | Walking access (1 km)                  | Vehicle access (3.3 km)       |
|-------------------|----------------------------------------|-------------------------------|
| High (2)          | no facilities                          | fewer than 3 facilities       |
| Medium (1)        | 1. no facilities, <br> 2. **or** 1 facility | 1. between 3 and 12 facilities, <br> 2. **or** fewer than 2 facilities |
| Low (0)           | 1. no facilities, <br> 2. **or** at least 1 facility, <br> 3. **or** 2 or more facilities | 1. **and** more than 12 facilities, <br> 2. **and** 2 or more facilities |

- ### Pereira, Colombia

Functional Urban Area (FUA): ~ 138 km², FUA population: approximately 641,965 (2015)

| Deprivation level | Walking access (1 km)                  | Vehicle access (3.3 km)       |
|-------------------|----------------------------------------|-------------------------------|
| High (2)          | no facilities                          | no facilities                 |
| Medium (1)        | fewer than 1 facility                  | up to 14 facilities           |
| Low (0)           | at least 1 facility                    | or more than 14 facilities    |

---

<br>
To learn more about how you can help improve the accuracy of these classifications, visit our page on [How to Validate Our Data](/docs/using-the-map/how-to-validate-our-data).

## Limitations and assumptions

As with any model, some limitations emerge from the decisions and constraints imposed by the available datasets. The following are the main limitations identified by the team.

- Population was not considered in the model. Instead, considering that an area should have access to multiple healthcare facilities, aimed at considering the capacity and opening times.
- The healthcare facilities can be outdated, and, in some cases, public ownership cannot be validated.
- To estimate travel times, we used a standard routing service where the walking and vehicle speeds were not tested on the ground, which can lead to inaccuracies.
- Some roads are not captured in the dataset for calculating routes and travel times.
- We did not consider public transport when estimating travel times.
- Using synthetic indexes adds complexity, making explaining the process and providing feedback on the results difficult.


## Focus area for validation

The focus areas are related to the boundaries between the low and medium categories. The counts might overlook the perceived accessibility to healthcare facilities. By validating those areas, the team can adjust and improve the model thresholds used.

## Data used for Modelling

The model relies on the following datasets:

- Health care facilities dataset can be found in the city-specific README files

- [General population counts from WorldPop](https://hub.worldpop.org/geodata/summary?id=49705)

- [Road network data from OpenStreetMap via the Open Route Service API](https://openrouteservice.org/)