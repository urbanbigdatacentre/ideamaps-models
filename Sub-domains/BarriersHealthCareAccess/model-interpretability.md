---
title: Barriers to Healthcare Access
author: Diego.Pajarito@glasgow.ac.uk
author: xingyi.du@glasgow.ac.uk
category: Our Data
tags: [deprivation, datasets]  
---

# Barriers to Healthcare Access

Barriers to Healthcare Access is a dataset that maps initial barriers communities in slums and other deprived areas face when accessing healthcare. It uses selected public facilities offering general healthcare services to estimate areas. "Barriers to healthcare access" are classfied in three levels **Low barriers, Medium barriers, or High barriers**.

The initial premise of the model is that either road distance or travel time to the nearest healthcare facility can work as a baseline for discussions about barriers to accessing healthcare. The idea is that the model can show a differentiation across urban areas regarding their connections to healthcare facilities. This can trigger discussion about whether the results match the community reality for perceived travel distance and the healthcare services they usually access. It will also allow discussion on other barriers beyond proximity to consider in the next model version. 

The model ultimately aims to describe the main barriers community members face when accessing healthcare with a gender-specific focus on maternal health as a population group highly impacted by a lack of or low-quality healthcare.

<aside>
💡 This page will help you understand more about how the classifications of Low - Medium - High are predicted in our data model.

</aside>

## Initial barriers considered to estimate healthcare access


Based on data about formal healthcare facilities, provided by [Grid3](https://data.grid3.org/), we used the concept of Isochrones to estimate the areas accessible within a given time/distrance; this is as an improvement to traditional methods that estimate direct distances that ignore other trip conditions. 

We considered two additional barriers to complement time/travel discance. Firstly, we selected healtcare facilities based on their ownership, either publc or from a non-government organisation since “Slum residents tend to seek government and non-governmental organisation facility and avoid private hospitals for healthcare services” (Park J, Kibe P, Yeboah G, et al; 2022). 

Secondly, we selected facilities based on the typology and categorisation of the services that were either closely link to maternal healthcare or more likely to be demmanded by the communities.

Together, these factors help estimate the barriers —> **Low, Medium, or High.**


### Three-level scale

*Low* 
<blockquote > You can reach a public healthcare facility in less than 15 minutes. You can consider walking.
</blockquote>
<img src="/docs/our-data/barriers-to-healthcare-access/barriers-health-care-low.png" alt="barriers-healtcare-low"/>


*Medium*
<blockquote> It would take you up to 30 minutes to reach a public healthcare facility. You would require a vehicle.
</blockquote>
<img src="/docs/our-data/barriers-to-healthcare-access/barriers-health-care-medium.png" alt="barriers-healtcare-medium"/>

*High*
<blockquote > It will take you more than 30 minutes to reach a public healthcare facility. You must use a vehicle.
</blockquote>
<img src="/docs/our-data/barriers-to-healthcare-access/barriers-health-care-high.png" alt="barriers-healtcare-high"/>


<aside>
💡 Together, these factors acount for some of the barriers communities in slums and other deprived areas experience when accessing healthcare and you see reflected in the grid cells on our map. 

To learn more about how you can help improve the accuracy of these classifications, visit our page on [How to Validate Our Data](/docs/using-the-map/how-to-validate-our-data).

</aside>