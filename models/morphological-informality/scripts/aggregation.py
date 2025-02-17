import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path

from parsers import aggregation_parser as argument_parser


if __name__ == '__main__':
    args = argument_parser().parse_known_args()[0]
    # TODO: add ltcWRB

    umm = gpd.read_parquet(args.building_file)
    umm = umm[['uID', 'geometry']]
    assert np.all(umm.is_valid)

    # Loading Urban Morphometrics (UMM)
    metrics = ['sdbAre', 'ssbElo', 'stbOri', 'stcOri', 'ssbCCD', 'sdcAre', 'sscERI', 'sicCAR', 'mtbAli', 'mtbNDi',
               'mtcWNe', 'mdcAre', 'ltcBuA', 'ltbIBD', 'ltcWRB']

    for metric in metrics:
        metric_values = pd.read_parquet(Path(args.morphometrics_dir) / f'{metric}.pq')
        umm = pd.merge(umm, metric_values, on='uID', how='inner')

    umm = gpd.GeoDataFrame(umm, geometry='geometry')
    umm = umm.to_crs("EPSG:4326")
    umm['centroid'] = umm.geometry.centroid
    umm = gpd.GeoDataFrame(umm, geometry='centroid').drop(columns='geometry')

    #Aggregation to the grid
    grid = gpd.read_file(args.grid_file)
    grid = grid[['geometry']]
    grid['grid_id'] = range(1, len(grid) + 1)  # create column containing an unique raw numbering for each grid
    grid = grid.to_crs("EPSG:4326")
    assert np.all(grid.is_valid)

    # Perform Spatial Join
    umm_grid = gpd.sjoin(grid, umm, how='inner', predicate='intersects')

    # handle missing data
    has_missing_values = umm_grid.isnull().values.any()

    umm_grid = umm_grid.dropna()

    # Assuming 'joined' is your GeoDataFrame
    # 'geometry' is the column name of the grid geometry
    # 'grid_id' is the identifier for each grid cell

    # 'variables' is a list of the variable names you want to aggregate by mean and median
    median = ['sdcAre', 'ssbElo', 'ssbCCD', 'mtbAli', 'mtbNDi', 'ltcBuA', 'sdbAre', 'sscERI', 'sicCAR', 'mtcWNe',
              'mdcAre', 'ltbIBD', 'ltcWRB']
    sd = ['stbOri', 'stcOri']
    sum = ['sdcAre']

    # Set the grid geometry as the active geometry
    print(umm_grid.columns)
    umm_grid = umm_grid.set_geometry('geometry')

    # Group by 'grid_id' and calculate median and std
    median_values = umm_grid.groupby('grid_id')[median].median().add_prefix('md_')
    sd_values = umm_grid.groupby('grid_id')[sd].std().fillna(0).add_prefix('sd_')
    sum_values = umm_grid.groupby('grid_id')[sum].sum().add_prefix('sum_')

    building_counts = umm_grid.groupby('grid_id').size().rename('bcount')
    single_building_grids = building_counts[building_counts == 1]

    # the NaN values are because there is only 1 building per grid
    sd_values.isnull().sum()

    # Assuming df_shp and join_df are your DataFrames and 'uID' is the common column
    merge_stats = pd.merge(median_values, sd_values, on='grid_id', how='inner')
    merge_stats = pd.merge(merge_stats, sum_values, on='grid_id', how='inner')
    merge_stats = pd.merge(merge_stats, building_counts, on='grid_id', how='inner')

    merge_stats.isnull().sum()

    if grid.index.name != 'grid_id':
        grid = grid.set_index('grid_id')

    if merge_stats.index.name != 'grid_id':
        merge_stats = merge_stats.set_index('grid_id')

    # Perform Spatial Join
    df_stats = pd.merge(grid, merge_stats, on='grid_id', how='inner')
    gdf_stats = gpd.GeoDataFrame(df_stats, geometry='geometry', crs='EPSG:4326')

    # if any column is duplicated
    duplicate_columns = gdf_stats.columns[gdf_stats.columns.duplicated()]
    print(duplicate_columns)

    gdf_stats = gdf_stats.loc[:, ~gdf_stats.columns.duplicated()]

    # Export to a new gpkg
    gdf_stats.to_parquet(Path(args.output_dir) / 'morphometrics_grid.pq')