import argparse
import pandas as pd
import geopandas as gpd
from shapely import wkt
import sys
import os
sys.path.append(os.path.abspath(".."))
from utils import *

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--year', type=int)
    args = parser.parse_args()
    return args

def main():
    args = get_args()
    
    year = args.year
    rating_data_path = '/share/garg/311_data/sb2377_a_data/parks/Parks_Inspection_Program___Inspections_20240316.csv'
    report_data_path = '/share/garg/311_data/sb2377/clean_codebase/data_{}.csv'.format(year)
    preprocessed_report_data_path = '/share/garg/311_data/sb2377/clean_codebase/processed_maintenance_or_facility_{}.csv'.format(year)
    all_parks_path = '/share/garg/311_data/sb2377_a_data/parks/Parks_Inspection_Program___All_Sites__MAPPED__20240316.csv'
    
    complaint_type = 'Maintenance or Facility'
    rename_map = {'Date': 'date', 
                  'Multipolygon': 'finegrained_geometry',
                  'Prop ID': 'finegrained_id'
                 }
    
    parks_df = pd.read_csv(all_parks_path)
    df = pd.read_csv(rating_data_path)
    df_311 = pd.read_csv(report_data_path)
    
    census_gdf, _, _ = generate_graph_census()
    census_gdf = census_gdf.to_crs('EPSG:2263')
    
    # process list of all parks
    # rename columns
    parks_df = parks_df.rename(columns=rename_map)
    parks_df['finegrained_geometry'] = parks_df['finegrained_geometry'].apply(wkt.loads)

    # get census tract information
    parks_df = gpd.GeoDataFrame(parks_df,
                                geometry=parks_df['finegrained_geometry'],
                                crs='EPSG:4326')
    parks_sjoin = gpd.sjoin(parks_df.to_crs('EPSG:2263').reset_index(drop=True),census_gdf.to_crs('EPSG:2263'), how='inner', op='intersects')
    parks_sjoin = parks_sjoin.drop(columns='geometry')
    parks_sjoin = pd.merge(parks_sjoin, census_gdf[['GEOID', 'geometry']], on='GEOID', how='left')
    parks_sjoin = parks_sjoin.drop(columns='index_right')
    parks_sjoin['intersection_area'] = parks_sjoin.apply(lambda row: row['geometry'].intersection(row['finegrained_geometry']).area, axis=1)
    parks_df = parks_sjoin.loc[parks_sjoin.groupby('finegrained_id')['intersection_area'].idxmax()]
    parks_df = gpd.GeoDataFrame(parks_df,
                                geometry=parks_df['finegrained_geometry'],
                                crs='EPSG:4326')
    parks_df['GEOID'] = parks_df['GEOID'].astype(int)
    parks_df = parks_df.to_crs('EPSG:2263')
    
    # process rating data
    # rename columns
    df = df.rename(columns=rename_map)

    # process date
    df['date'] = pd.to_datetime(df['date'], format='%m/%d/%Y %I:%M:%S %p')
    df['year'] = df['date'].dt.year
    df['week'] = df['date'].dt.isocalendar().week
    df['month'] = df['date'].dt.month
    df.loc[(df['month'] == 1) & (df['week'] > 50), 'week'] = 0 # start first week at 0 (instead of previous year's indexing)
    one_year_df = df[df['year'] == year]

    # add location information
    one_year_df = pd.merge(one_year_df, parks_df, on='finegrained_id', how='left')

    # subset to data with at least one score
    one_year_df = one_year_df[(one_year_df['Overall Condition'].isin(['U', 'A'])) & (one_year_df['Cleanliness'].isin(['U', 'A']))]

    # convert binary ratings to scores
    one_year_df['condition_score'] = 0
    one_year_df.loc[one_year_df['Overall Condition'] != 'U', 'condition_score'] = 1
    one_year_df['cleanliness_score'] = 0
    one_year_df.loc[one_year_df['Cleanliness'] != 'U', 'cleanliness_score'] = 1
    one_year_df['score'] = one_year_df['condition_score'] + one_year_df['cleanliness_score']
    one_year_df = one_year_df[['finegrained_id', 'date', 'week', 'GEOID', 'score']]
    one_year_df = one_year_df.dropna() # remove rows that did not match into any census tract
    one_year_df = one_year_df.groupby(['finegrained_id', 'week', 'GEOID', 'date'])['score'].mean().reset_index()
    
    # process reporting data
    # get data for type
    type_df = df_311[df_311['Complaint Type'] == complaint_type]
    type_df['Created Date'] = pd.to_datetime(type_df['Created Date'])
    type_df['week'] = type_df['Created Date'].dt.isocalendar().week
    type_df['month'] = type_df['Created Date'].dt.month
    type_df.loc[(type_df['month'] == 1) & (type_df['week'] > 50), 'week'] = 0 # start first week at 0 (instead of previous year's indexing)

    # process location
    type_df = type_df[~(type_df.Latitude.isna()|type_df.Longitude.isna())]
    type_gdf = gpd.GeoDataFrame(type_df,
                                geometry=gpd.points_from_xy(type_df.Longitude, type_df.Latitude),
                                crs='EPSG:4326')

    # get census tract information
    type_gdf = gpd.sjoin(type_gdf.to_crs('EPSG:2263').reset_index(drop=True), census_gdf.to_crs('EPSG:2263'), how='inner', op='intersects')
    type_gdf['GEOID'] = type_gdf['GEOID'].astype(int)
    type_gdf = type_gdf.to_crs('EPSG:2263')

    reports_df = type_gdf
    
    # match each complaint with its associated street
    # loop through tract by tract and complete the matching within each tract to lower complexity
    all_distances = []
    for tract_geoid in reports_df['GEOID'].unique():
        # get all ratings and reports from this tract
        tract_park_df = parks_df[parks_df['GEOID'] == tract_geoid].copy()
        tract_reports_df = reports_df[reports_df['GEOID'] == tract_geoid].copy()

        finegrained_ids = tract_park_df[['finegrained_id', 'geometry']].copy()
        finegrained_ids = finegrained_ids.rename(columns={'geometry': 'finegrained_geometry'})
        report_locations = tract_reports_df[['Unique Key', 'geometry']].copy()

        if len(finegrained_ids) > 0:
            # Cross join street_ids and report_locations to create a DataFrame with all possible pairs of finegrained geometries and report points
            finegrained_ids['key'] = 1
            report_locations['key'] = 1
            cross_joined_df = pd.merge(finegrained_ids, report_locations, on='key').drop(labels='key', axis=1)

            # Calculate the distance for each pair
            cross_joined_df['distance'] = cross_joined_df.apply(lambda row: row['finegrained_geometry'].distance(row['geometry']), axis=1)

            # Finding the minimum distance for each point
            min_distances = cross_joined_df.loc[cross_joined_df.groupby('Unique Key')['distance'].idxmin()]
            all_distances.append(min_distances)
        else:
            # if there are no streets in this tract, search across all streets (across all census tracts)
            finegrained_ids = parks_df[['finegrained_id', 'finegrained_geometry']].copy()

            # Cross join street_ids and report_locations to create a DataFrame with all possible pairs of finegrained geometries and report points
            finegrained_ids['key'] = 1
            report_locations['key'] = 1
            cross_joined_df = pd.merge(finegrained_ids, report_locations, on='key').drop(labels='key', axis=1)

            # Calculate the distance for each pair
            cross_joined_df['distance'] = cross_joined_df.apply(lambda row: row['finegrained_geometry'].distance(row['geometry']), axis=1)

            # Finding the minimum distance for each point
            min_distances = cross_joined_df.loc[cross_joined_df.groupby('Unique Key')['distance'].idxmin()]
            all_distances.append(min_distances)

    # combine data across all census tracts
    all_min_distances = pd.concat(all_distances)

    # merge reports data with nearest inspection
    reports_df = pd.merge(reports_df, all_min_distances[['finegrained_id', 'finegrained_geometry', 'Unique Key', 'distance']], on='Unique Key')
    
    reports_df.to_csv(preprocessed_report_data_path)
    
if __name__ == "__main__":
    main()         