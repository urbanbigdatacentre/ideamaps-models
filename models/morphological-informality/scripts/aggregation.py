import geopandas as gpd
from geopandas import GeoDataFrame
import pandas as pd
import numpy as np
from scipy.stats import entropy
import utm
from pathlib import Path
import argparse

def get_utm_epsg(gdf: GeoDataFrame) -> int:
    gdf = gdf.to_crs(4326)

    # Calculate the centroid of the bounding box
    bounds = gdf.total_bounds
    min_lng, min_lat, max_lng, max_lat = bounds
    lng, lat = (min_lng + max_lng) / 2, (min_lat + max_lat) / 2

    # Convert to UTM and create EPSG code
    utm_coords = utm.from_latlon(lat, lng)
    zone_number, zone_letter = utm_coords[2], utm_coords[3]
    epsg_code = 32600 + zone_number if zone_letter >= 'N' else 32700 + zone_number

    return epsg_code

def argument_parser():
    # https://docs.python.org/3/library/argparse.html#the-add-argument-method
    parser = argparse.ArgumentParser(description="Experiment Args")
    parser.add_argument('-m', "--morphometrics-dir", dest='morphometrics_dir', required=True)
    parser.add_argument('-b', "--building-file", dest='building_file', required=True)
    parser.add_argument('-g', "--grid-file", dest='grid_file', required=True)
    parser.add_argument('-o', "--output-dir", dest='output_dir', default='outputs/', required=False,
                        help="path to output directory")

    parser.add_argument(
        "opts",
        help="Modify config options using the command-line",
        default=None,
        nargs=argparse.REMAINDER,
    )
    return parser


if __name__ == '__main__':
    args = argument_parser().parse_known_args()[0]
    assert Path(args.output_dir).exists()

    building_file = Path(args.building_file)
    umm = gpd.read_parquet(building_file) if building_file.suffix == '.parquet' else gpd.read_file(building_file)
    umm = umm[['uID', 'geometry']]
    assert np.all(umm.is_valid)

    # Loading Urban Morphometrics (UMM)
    metrics = ['sdbAre', 'ssbElo', 'ssbCCD', 'stbOri', 'mtbAli', 'mtbNDi', 'ltbIBD', 'ltcBuA', 'sdcAre', 'sscERI',
               'sicCAR', 'mtcWNe', 'mdcAre', 'stcOri',  'ltcWRB']

    for metric in metrics:
        metric_values = pd.read_parquet(Path(args.morphometrics_dir) / f'{metric}.parquet')
        umm = pd.merge(umm, metric_values, on='uID', how='inner')
    umm = gpd.GeoDataFrame(umm, geometry='geometry')

    # Loading grid
    grid_file = Path(args.grid_file)
    grid = gpd.read_parquet(grid_file) if grid_file.suffix == '.parquet' else gpd.read_file(grid_file)
    grid = grid[['geometry']]
    grid['grid_id'] = range(1, len(grid) + 1)  # create column containing an unique raw numbering for each grid

    # Reprojecting buildings and grid to local UTM zone
    grid_crs = grid.crs
    utm_epsg = get_utm_epsg(grid)
    grid, umm = grid.to_crs(utm_epsg), umm.to_crs(utm_epsg)

    # Perform spatial join based on building centroids and drop grid cells with no buildings
    umm['centroid'] = umm.geometry.centroid
    umm_grid = gpd.sjoin(grid, umm.set_geometry('centroid').drop(columns='geometry'), how='inner',
                         predicate='intersects')
    umm_grid = umm_grid.dropna()

    # 'variables' is a list of the variable names you want to aggregate by median and standard deviation
    median = ['sdbAre', 'ssbElo', 'ssbCCD', 'mtbAli', 'mtbNDi', 'ltbIBD', 'ltcBuA', 'sdcAre', 'sscERI', 'sicCAR',
              'mtcWNe', 'mdcAre', 'ltcWRB']
    mean = ['sdbAre']
    maximum = ['sdbAre']
    variation = ['stbOri', 'stcOri']

    # Set the grid geometry as the active geometry
    umm_grid = umm_grid.set_geometry('geometry')

    # Group by 'grid_id' and calculate median and std
    median_values = umm_grid.groupby('grid_id')[median].median().add_prefix('md_')
    sd_values = umm_grid.groupby('grid_id')[variation].std().fillna(0).add_prefix('sd_')
    def compute_entropy(series):
        probs = series.value_counts(normalize=True)  # Get probability distribution
        return entropy(probs, base=2)  # Compute Shannon entropy (bits)
    entropy_values = umm_grid.groupby('grid_id')[variation].apply(
        lambda x: x.apply(compute_entropy)).fillna(0).add_prefix('entropy_')
    building_counts = umm_grid.groupby('grid_id').size().rename('bcount')

    # Merge all statistics
    merge_stats = pd.merge(median_values, sd_values, on='grid_id', how='inner')
    merge_stats = pd.merge(merge_stats, entropy_values, on='grid_id', how='inner')
    merge_stats = pd.merge(merge_stats, building_counts, on='grid_id', how='inner')
    print(f'NaN values: {merge_stats.isnull().sum()}')

    # Compute sum of built-up area 'sum_sdbAre'
    # Get intersecting building footprints for each grid cell and sum the intersected areas
    intersections = gpd.overlay(umm, grid, how='intersection')
    intersections['intersected_area'] = intersections.geometry.area
    grid_building_area = intersections.groupby('grid_id')['intersected_area'].sum().reset_index()
    merge_stats = pd.merge(merge_stats, grid_building_area, on='grid_id', how='left')
    merge_stats = merge_stats.rename(columns={'intersected_area': 'sum_sdbAre'})
    # Fill NaN values with 0 (cells with no buildings)
    merge_stats['sum_sdbAre'] = merge_stats['sum_sdbAre'].fillna(0)

    # Maximum area covered by single building within grid cell
    grid_max_building_area = intersections.groupby('grid_id')['intersected_area'].max().reset_index()
    merge_stats = pd.merge(merge_stats, grid_max_building_area, on='grid_id', how='left')
    merge_stats = merge_stats.rename(columns={'intersected_area': 'max_sdbAre'})
    # Fill NaN values with 0 (cells with no buildings)
    merge_stats['max_sdbAre'] = merge_stats['max_sdbAre'].fillna(0)

    for metric in variation:
        merge_stats[f'nentropy_{metric}'] = merge_stats[f'entropy_{metric}'] / np.log1p(merge_stats['bcount'])

    if grid.index.name != 'grid_id':
        grid = grid.set_index('grid_id')

    if merge_stats.index.name != 'grid_id':
        merge_stats = merge_stats.set_index('grid_id')

    # Perform Spatial Join
    df_stats = pd.merge(grid, merge_stats, on='grid_id', how='inner')
    gdf_stats = gpd.GeoDataFrame(df_stats, geometry='geometry', crs=utm_epsg)

    gdf_stats = gdf_stats.loc[:, ~gdf_stats.columns.duplicated()]
    gdf_stats = gdf_stats.to_crs(grid_crs)

    # Export to a new gpkg
    gdf_stats.to_parquet(Path(args.output_dir) / 'morphometrics_grid_v2.parquet')