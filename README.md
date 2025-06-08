# Overview
We share here a real heterogenous dataset for an urban incident prediction task. The goal of incident prediction is to estimate the latent ground truth for the hundreds of types of incidents that occur in a city (e.g., rodents, floods, etc.). We provide two sources of data for this prediction task.
 - First, we provide observations of the ground truth incident state via *government inspections* which generate *ratings* for neighborhoods. For example, New York City conducts street inspections for every street and rates them from 1-10. Importantly, these inspections are only conducted for some incident types and neighborhoods and are thus sparsely observed.
 - We also provide another source of data: frequently observed, biased proxies of the incident state, via crowdsourced *reports* of incidents. Unlike ratings, indicators of whether reports are made are observed across all incident types, all neighborhoods, and multiple points in time.

To our knowledge, prior urban prediction work has not considered the dual challenges and benefits of jointly learning from both types of available data---one reason is the lack of processed data, combining reports and ratings across types. To address this limitation, we provide here large-scale preprocessed data of reports and ratings from New York City. Our dataset is composed of 9,615,863 crowdsourced reports across 139 incident types and 1,041,415 government inspection ratings across 5 incident types. Beyond urban prediction, this data can also be used by other researchers to study data bias in urban applications, e.g. comparing the biased reporting data to the unbiased rating data can reveal the patterns of underreporting in an urban area.

# What tasks can this data be used for?
This data can be used to build urban incident prediction models and to investigate patterns of underreporting in crowdsourced reporting data. We also provide an [example](https://github.com/sidhikabalachandar/nyc_urban_incident_model) of such a model. More broadly, this dataset serves as an ideal setting in which to study distribution shifts over time. Moreover, raw rating and reporting data is continuously updated, so this setting has the additional benefit of having an automatic source of uncontaminated test sets.

# Preprocessed data
We provide our preprocessed data in `\data`. This folder contains two files:

## compressed_nyc_urban_incident_data.h5
This file contains rating and reporting data rom 2292 census tracts, from 139 complaint types, and from all weeks between 2021 and 2023. Each row of our dataset corresponds to a unique combination of a census tract, a complaint type, and a week. We note that for datapoints from the 5 types with real rating data, we provide data at a fine grained granularity smaller than each census tract (e.g. for streets we provide data for each individual street in a census tract). Thus for types with observed ratings, we may observe multiple data points for each census tract, complaint type, and week combination. Due to space limitations, we provide a sparse version of the dataset. For all types without real rating data, we only provide datapoints for which a report was made. We provide an explanation of each column below:
- node_idxs: 0-indexed identifier for each unique GEOID 
- type_idxs: 0-indexed identifier for each unique complaint type
- report_week: Week report was made
- finegrained_reported: Indicator of whether a report was made
- normalized_rating: Rating which is normalized/z-scored within each complaint type. Null if no rating is observed.
- real_rating_observed: Indicator of whether the rating is observed
- type_rating_observed: Indicator of whether any rating is observed for a give complaint type

## key.csv
This file contains mappings between each node_idx and the corresponding GEOID (census tract identifier) and each type_idx and the corresponding complaint type and New York City agency.

# Preprocessing code
We also provide our preprocessing code.

## Processing reports
Our code to process the reporting data is provided in `reports/`. We obtain raw [NYC 311 service request data](https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9/about_data) from the NYC OpenData platform. We transform reports into *indicators* of whether a report of a particular type was observed in a Census tract during a particular week. 

## Processing ratings
We provide ratings for five different incident types: (i) street conditions, (ii) park maintenance or facility conditions, (iii) rodents, (iv) food establishment/mobile food vendor/food poisoning, and (v) DCWP consumer complaints. The code to process data for these five types is provided in `ratings/`. We obtain raw rating data from the following NYC OpenData datasets:
- [Street ratings](https://data.cityofnewyork.us/Transportation/Street-Rating/mxi3-5xz5)
- [Park inspections](https://data.cityofnewyork.us/dataset/Parks-Inspection-Program-Inspections/yg3y-7juh)
- [Rodent inspections](https://data.cityofnewyork.us/Health/Rodent-Inspection/p937-wjvj)
- [Restaurant inspections](https://data.cityofnewyork.us/Health/DOHMH-New-York-City-Restaurant-Inspection-Results/43nn-pn8j)
- [DCWP inspections](https://data.cityofnewyork.us/Business/Department-of-Consumer-and-Worker-Protection-DCWP-/jzhd-m6uv)

## Processing demographic data
We use demographic data from the [Census](https://data.census.gov/). The code to process the demographic features we use is provided in `demographics.ipynb'.

## Combining ratings and reports
We provide code to combine ratings and reports in `combine_ratings_and_reports/` by matching ratings and reports across nodes, incident types, and weeks. 

## Getting updated data
One advantage of this dataset is that new reporting and rating data is available on OpenData daily. The second cell in each data processing notebook allows users to specify the paths of locally downloaded raw data files. Thus users can easily run the data processing pipeline with updated NYC data. 
