import geopandas as gpd
grid_isocarfoot_gdf = gpd.read_file('joined_gdf.shp')

# add a new column to the GeoDataFrame and set it to 2
grid_isocarfoot_gdf['values'] = 2
grid_isocarfoot_gdf = grid_isocarfoot_gdf.assign(values=2)


# for values in the 'joined' column that are not nan set them to 1
grid_isocarfoot_gdf = grid_isocarfoot_gdf

# for values in the 'joined' column that are coming from the isochones by foot set them to 0
grid_isocarfoot_gdf.loc[grid_isocarfoot_gdf['index_right'] == 0, 'values'] = 0

# change column names of 'column1' and 'column2' to 'new_column1' and 'new_column2'
joined_gdf.rename(columns={'column1': 'new_column1', 'column2': 'new_column2'}, inplace=True)

# Save the GeoDataFrame to a CSV file with the follwoing columns latitude,longitude,lat_min,lat_max,lon_min,lon_max,result
grid_isocarfoot_gdf.to_csv('grid_isocarfoot_gdf.csv', columns=['latitude', 'longitude', 'lat_min', 'lat_max', 'lon_min', 'lon_max', 'result'])