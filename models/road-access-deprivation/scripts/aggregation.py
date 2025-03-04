from pathlib import Path
import pandas as pd
import geopandas as gpd
import argparse


def argument_parser():
    # https://docs.python.org/3/library/argparse.html#the-add-argument-method
    parser = argparse.ArgumentParser(description="Experiment Args")
    parser.add_argument('-b', "--buildings-file", dest='buildings_file', required=True,
                        help='Building footprint file (.parquet) with attributes buildings_in_between and paved')
    parser.add_argument('-g', "--grid-file", dest='grid_file', required=True,
                        help='IDEAMAPS 100 x 100 m grid file')
    parser.add_argument('-o', "--out-file", dest='out_file', required=True,
                        help='output file (.parquet)')
    parser.add_argument(
        "opts",
        help="Modify config options using the command-line",
        default=None,
        nargs=argparse.REMAINDER,
    )
    return parser


def aggregate_parameters(buildings_file: str, grid_file: str, out_file: str):
    # Loading building footprints with attributions 'buildings_in_between' and 'paved'
    buildings = gpd.read_parquet(buildings_file)
    if not 'centroid' in buildings.columns:
        buildings['centroid'] = buildings.centroid
    buildings = buildings.set_geometry('centroid').drop(columns='geometry')

    # Loading IDEAMAPS 100 x 100 m grid
    grid = gpd.read_file(grid_file)
    grid['grid_id'] = range(len(grid))
    buildings = buildings.to_crs(grid.crs)

    # Join grid id to each building
    buildings = gpd.sjoin(buildings, grid, how='left', predicate='within')

    # Drop buildings with no grid id
    buildings = buildings[buildings['grid_id'].notna()]

    # Compute grid cell mean for number of buildings between a building and its nearest road
    mean_buildings_in_between = buildings.groupby('grid_id')[['buildings_in_between']].mean().add_prefix('mean_')
    # Compute grid cell mode for road type (paved/unpaved)
    mode_surface_type = buildings.groupby('grid_id')[['paved']].agg(lambda x: x.mode().iloc[0]).add_prefix('mode_')

    # Combine grid-level parameters
    merge_stats = pd.merge(mean_buildings_in_between, mode_surface_type, on='grid_id', how='inner')

    # Join parameters to reference grid
    df_stats = pd.merge(merge_stats, grid[['grid_id', 'geometry']], on='grid_id', how='left')
    gdf_stats = gpd.GeoDataFrame(df_stats, geometry='geometry', crs=grid.crs)

    # Save grid-level parameters
    out_file = Path(out_file)
    assert out_file.suffix == '.parquet'
    gdf_stats.to_parquet(str(out_file))


if __name__ == '__main__':
    args = argument_parser().parse_known_args()[0]
    aggregate_parameters(args.buildings_file, args.grid_file, args.out_file)
