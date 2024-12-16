# Overview
We create a real heterogenous dataset for an urban incident prediction task. The goal of incident prediction is to estimate the latent ground truth for the hundreds of types of incidents that occur in a city (e.g., rodents, floods, etc.). We provide two sources of data for this prediction task. First, we provide observations of the ground truth state via *government inspections* which generate *ratings* for neighborhoods. For example, New York City conducts street inspections for every street and rates them from 1-10, but each street is only rated once every year. Importantly, these inspections are only conducted for some incident types and neighborhoods and are thus sparsely observed. We also provide another source of data: frequently observed, biased proxies of the latent state, e.g., via crowdsourced *reports* of incidents. Unlike ratings, indicators of whether reports are made are observed across all incident types, all neighborhoods, and multiple points in time. 

For our dataset, we source reports from New York City 311 complaints (crowdsourced reports), leveraging 55 million reports across 141 types over two years. We combine this with a carefully curated dataset of ground truth ratings which are sourced from 300k government inspections across 5 types in the same time frame. In this codebase we provide a preprocessed dataset (available in `data/`) and code to reproduce our preprocessing steps.

# Data components
## Reporting data
Our code to process the reporting data is provided in `reports/`. We obtain raw [NYC 311 service request data](https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9/about_data) from the NYC OpenData platform. We locally save the raw 311 data in separate csv files by year for faster processing. 

## Rating data
We provide ratings for five different incident types: (i) street conditions, (ii) park maintenance or facility conditions, (iii) rodents, (iv) food establishment/mobile food vendor/food poisoning, and (v) DCWP consumer complaints. The code to process data for these five types is provided in `ratings/`. We obtain raw rating data from the following NYC OpenData datasets:
- [Street ratings](https://data.cityofnewyork.us/Transportation/Street-Rating/mxi3-5xz5)
- [Park inspections](https://data.cityofnewyork.us/dataset/Parks-Inspection-Program-Inspections/yg3y-7juh)
- [Rodent inspections](https://data.cityofnewyork.us/Health/Rodent-Inspection/p937-wjvj)
- [Restaurant inspections](https://data.cityofnewyork.us/Health/DOHMH-New-York-City-Restaurant-Inspection-Results/43nn-pn8j)
- [DCWP inspections](https://data.cityofnewyork.us/Business/Department-of-Consumer-and-Worker-Protection-DCWP-/jzhd-m6uv)

## Demographic data
We use demographic data from the [Census](https://data.census.gov/). The code to process the demographic features we use is provided in `demographics.ipynb'.

# Detailed data description
Our final dataset contains rating and reporting data from 2292 census tracts, from 141 complaint types, and from all weeks in 2022 and 2023. Each row of our dataset corresponds to a unique combination of a census tract, a complaint type, and a week. We note that for datapoints from the 5 types with real rating data, we provide data at a fine grained granularity smaller than each census tract (e.g. for streets we provide data for each individual street in a census tract). Thus for types with observed ratings, we may observe multiple data points for each census tract, complaint type, and week combination. We provide an explanation of each column below:
- GEOID: Unique numeric string used by the U.S. Census Bureau to identify census tracts
- node_idxs: 0-indexed identifier for each unique GEOID (a mapping of GEOIDs to node_idxs is provided in `data/two_year_base.csv`)
- typeagency: Complaint type and agency
- type_idxs: 0-indexed identifier for each unique typeagency (a mapping of typeagencys to type_idxs is provided in `data/two_year_base.csv`)
- finegrained_id: Unique identifier for each finegrained entitiy (e.g. for streets, the id identifies each unique street segment)
- report_week: Week report was made
- finegrained_reported: Indicator of whether a report was made
- normalized_rating: Rating which is normalized/z-scored within each complaint type. Null if no rating is observed.
- real_rating_observed: Indicator of whether the rating is observed
- rating_week: Week rating was made (We assume that once an inspection produces a rating, the finegrained entity remains at that rating until another inspection is conducted)
