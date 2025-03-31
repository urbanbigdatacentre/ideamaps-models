import geopandas as gpd
from geopandas import GeoDataFrame
import pandas as pd
import numpy as np
from scipy.stats import entropy, gaussian_kde
import utm
from pathlib import Path
import argparse
from tqdm import tqdm


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

def compute_entropy(series, areas=None):
    if areas is not None:
        relevant_buildings = areas >= 50
        if relevant_buildings.sum() < 2:
            return 0
        series = series[areas >= 50]
    probs = series.value_counts(normalize=True)  # Get probability distribution
    return entropy(probs, base=2)  # Compute Shannon entropy (bits)


def kde_entropy(series, areas=None, bandwidth='scott', num_bins=100):
    """
    Compute entropy of building orientation deviations using Kernel Density Estimation (KDE).

    Parameters:
    - series: Pandas Series, angles in degrees within [0, 45]
    - bandwidth: str or float, KDE bandwidth (default 'scott' adapts to sample size)
    - num_bins: int, number of evaluation points for entropy computation

    Returns:
    - Shannon entropy (higher = more irregular orientation distribution)
    """
    if series.isna().sum() == len(series) or series.nunique() < 2:
        return 0  # Return 0 if there's not enough unique data

    if areas is not None:
        relevant_buildings = areas >= 50
        if relevant_buildings.sum() < 2:
            return 0
        series = series[areas >= 50]

        if series.isna().sum() == len(series) or series.nunique() < 2:
            return 0  # Return 0 if there's not enough unique data

    # Convert to NumPy array
    angles_deg = series.dropna().to_numpy()

    # Fit Kernel Density Estimation (KDE)
    kde = gaussian_kde(angles_deg, bw_method=bandwidth)

    # Define evaluation range (to cover [0, 45] space)
    x_vals = np.linspace(0, 45, num_bins)

    # Compute estimated density
    pdf_vals = kde(x_vals)

    # Normalize PDF to ensure it's a proper probability distribution
    pdf_vals /= pdf_vals.sum()

    # Compute entropy using SciPy's built-in function
    return entropy(pdf_vals, base=np.e)  # Natural log base


if __name__ == '__main__':
    args = argument_parser().parse_known_args()[0]
    assert Path(args.output_dir).exists()

    building_file = Path(args.building_file)
    bmm = gpd.read_parquet(building_file) if building_file.suffix == '.parquet' else gpd.read_file(building_file)
    bmm = bmm[['uID', 'geometry']]

    # Loading Urban Morphometrics (UMM)
    building_metrics = ['sdbAre', 'ssbElo', 'ssbCCD', 'stbOri', 'mtbAli', 'mtbNDi', 'mtbNDi3', 'mtbNDi_log', 'ltbIBD', 'ltcBuA', 'sdcAre',
                        'sscERI', 'sicCAR', 'mtcWNe', 'mdcAre', 'stcOri', 'ltcWRB', 'strAli']

    for metric in building_metrics:
        metric_values = pd.read_parquet(Path(args.morphometrics_dir) / f'{metric}.parquet')
        bmm = pd.merge(bmm, metric_values, on='uID', how='inner')
    bmm = gpd.GeoDataFrame(bmm, geometry='geometry')

    # Loading grid
    grid_file = Path(args.grid_file)
    grid = gpd.read_parquet(grid_file) if grid_file.suffix == '.parquet' else gpd.read_file(grid_file)
    grid = grid[['geometry']]
    grid['grid_id'] = range(1, len(grid) + 1)  # create column containing an unique raw numbering for each grid

    # Reprojecting buildings and grid to local UTM zone
    grid_crs = grid.crs
    utm_epsg = get_utm_epsg(grid)
    grid, bmm = grid.to_crs(utm_epsg), bmm.to_crs(utm_epsg)

    # Perform spatial join based on building centroids and drop grid cells with no buildings
    bmm['centroid'] = bmm.geometry.centroid
    bmm_grid = gpd.sjoin(grid, bmm.set_geometry('centroid').drop(columns='geometry'), how='inner',
                         predicate='intersects')
    bmm_grid = bmm_grid.dropna()

    # 'variables' is a list of the variable names you want to aggregate by median and standard deviation
    median = ['sdbAre', 'ssbElo', 'ssbCCD', 'mtbAli', 'mtbNDi', 'ltbIBD', 'ltcBuA', 'sdcAre', 'sscERI', 'sicCAR',
              'mtcWNe', 'mdcAre', 'ltcWRB', 'mtbNDi_log', 'mtbNDi3', 'strAli']
    mean = ['sicCAR', 'mtbNDi', 'strAli']
    variation = ['stbOri', 'stcOri']

    # Set the grid geometry as the active geometry
    bmm_grid = bmm_grid.set_geometry('geometry')
    grouped_bmm_grid = bmm_grid.groupby('grid_id')

    # Group by 'grid_id' and calculate median and std
    median_values = grouped_bmm_grid[median].median().add_prefix('md_')
    mean_values = grouped_bmm_grid[mean].mean().add_prefix('mn_')
    sd_values = grouped_bmm_grid[variation].std().fillna(0).add_prefix('sd_')

    variation_measures = ['kdes', 'kdesr']
    # variation_measures = ['kdes']
    variation_dict = {f'{measure}_{metric}': [] for metric in variation for measure in variation_measures}
    variation_dict['grid_id'] = []
    for grid_id, values in tqdm(grouped_bmm_grid):
        variation_dict['grid_id'].append(grid_id)
        for metric in variation:
            skde_value = kde_entropy(values[metric])
            variation_dict[f'kdes_{metric}'].append(skde_value)
            skder_value = kde_entropy(values[metric], areas=values['sdbAre'])
            variation_dict[f'kdesr_{metric}'].append(skder_value)

    variation_values = pd.DataFrame(variation_dict)
    building_counts = grouped_bmm_grid.size().rename('bcount')

    # Merge all statistics
    merge_stats = pd.merge(median_values, sd_values, on='grid_id', how='inner')
    merge_stats = pd.merge(merge_stats, mean_values, on='grid_id', how='inner')
    merge_stats = pd.merge(merge_stats, variation_values, on='grid_id', how='inner')
    merge_stats = pd.merge(merge_stats, building_counts, on='grid_id', how='inner')

    # Compute sum of built-up area 'sum_sdbAre'
    # Get intersecting building footprints for each grid cell and sum the intersected areas
    intersections = gpd.overlay(bmm, grid, how='intersection')
    intersections['intersected_area'] = intersections.geometry.area
    grid_building_area = intersections.groupby('grid_id')['intersected_area'].sum().reset_index()
    merge_stats = pd.merge(merge_stats, grid_building_area, on='grid_id', how='left')
    merge_stats = merge_stats.rename(columns={'intersected_area': 'sum_sdbAre'})
    # Fill NaN values with 0 (cells with no buildings)
    merge_stats['sum_sdbAre'] = merge_stats['sum_sdbAre'].fillna(0)

    if grid.index.name != 'grid_id':
        grid = grid.set_index('grid_id')

    if merge_stats.index.name != 'grid_id':
        merge_stats = merge_stats.set_index('grid_id')

    # Perform Spatial Join
    building_stats = pd.merge(grid, merge_stats, on='grid_id', how='inner')

    # Roads
    road_metrics = ['strOri']
    var_measures_road = ['kdes']
    rmm = gpd.read_parquet(Path(args.morphometrics_dir) / 'strOri.parquet')
    rmm = rmm.to_crs(utm_epsg)
    rmm_grid = gpd.sjoin(grid, rmm, how='left', predicate='intersects')
    grouped_rmm_grid = rmm_grid.groupby('grid_id')

    var_dict_road = {f'{measure}_{metric}': [] for metric in road_metrics for measure in var_measures_road}
    var_dict_road['grid_id'] = []
    for grid_id, values in tqdm(grouped_rmm_grid):
        var_dict_road['grid_id'].append(grid_id)
        for metric in road_metrics:
            skde_value = kde_entropy(values[metric])
            var_dict_road[f'kdes_{metric}'].append(skde_value)

    var_values_road = pd.DataFrame(var_dict_road)
    road_point_counts = grouped_rmm_grid.size().rename('rcount')
    road_stats = pd.merge(var_values_road, road_point_counts, on='grid_id', how='inner')

    df_stats = pd.merge(building_stats, road_stats, on='grid_id', how='left')
    gdf_stats = gpd.GeoDataFrame(df_stats, geometry='geometry', crs=utm_epsg)

    # Combine Roads and Buildings
    bmm = bmm[['stbOri', 'centroid']].rename(columns={'stbOri': 'objOri', 'centroid': 'geometry'})
    bmm = bmm.set_geometry('geometry')
    rmm = rmm[['strOri', 'geometry']].rename(columns={'strOri': 'objOri'})
    cmm = pd.concat([bmm, rmm])
    cmm_grid = gpd.sjoin(grid, cmm, how='inner', predicate='intersects')
    cmm_grid = cmm_grid.dropna()
    grouped_cmm_grid = cmm_grid.groupby('grid_id')
    grid_ids, skde_values = [], []
    for grid_id, values in tqdm(grouped_cmm_grid):
        grid_ids.append(grid_id)
        skde_values.append(kde_entropy(values['objOri']))
    var_values_combined = pd.DataFrame({'kdes_objOri': skde_values, 'grid_id': grid_ids})

    gdf_stats = gdf_stats.merge(var_values_combined, on='grid_id', how='left')

    gdf_stats = gdf_stats.loc[:, ~gdf_stats.columns.duplicated()]
    gdf_stats = gdf_stats.to_crs(grid_crs)

    # Export to a new gpkg
    gdf_stats.to_parquet(Path(args.output_dir) / 'morphometrics_grid.parquet')