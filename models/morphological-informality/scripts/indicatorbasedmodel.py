import geopandas as gpd
import numpy as np
from pathlib import Path
import argparse


def argument_parser():
    # https://docs.python.org/3/library/argparse.html#the-add-argument-method
    parser = argparse.ArgumentParser(description="Experiment Args")
    parser.add_argument('-c', "--cluster-file", dest='cluster_file', required=True)
    parser.add_argument('--isl-clusters', dest='isl_clusters', required=True, metavar='N', type=int, nargs='+')
    parser.add_argument('--sds-clusters', dest='sds_clusters', required=True, metavar='N', type=int, nargs='+')
    parser.add_argument('-o', "--output-dir", dest='output_dir', default='outputs/', required=False,
                        help="path to output directory")
    parser.add_argument('--isl-n-clusters', dest='isl_n_clusters', required=False, default=10, type=int)
    parser.add_argument('--sds-n-clusters', dest='sds_n_clusters', required=False, default=10, type=int)
    parser.add_argument('-g', '--grid-file', dest='grid_file', required=False, default=None,
                        help='optional grid; cells without clusters (no buildings) are added as low (0)')

    parser.add_argument(
        "opts",
        help="Modify config options using the command-line",
        default=None,
        nargs=argparse.REMAINDER,
    )
    return parser


if __name__ == '__main__':
    args = argument_parser().parse_known_args()[0]

    cluster_file = Path(args.cluster_file)
    gdf = gpd.read_parquet(cluster_file) if cluster_file.suffix == '.parquet' else gpd.read_file(cluster_file)

    n_isl_clusters = int(args.isl_n_clusters)
    gdf['isl'] = gdf[f'isl_c{n_isl_clusters}'].isin(args.isl_clusters)
    gdf['isl'] = gdf['isl'].astype(int)
    n_sds_clusters = int(args.sds_n_clusters)
    gdf['sds'] = gdf[f'sds_c{n_sds_clusters}'].isin(args.sds_clusters)
    gdf['sds'] = gdf['sds'].astype(int)

    def model_logic(row):
        isl, sds = row['isl'], row['sds']
        if isl == 0 and sds == 0:
            return 0
        elif isl == 0 and sds == 1 or isl == 1 and sds == 0:
            return 1
        else:
            return 2

    gdf['mi'] = gdf.apply(model_logic, axis=1)

    gdf = gdf[['isl', 'sds', 'mi', 'geometry']]

    if args.grid_file is not None:
        grid_file = Path(args.grid_file)
        grid = gpd.read_parquet(grid_file) if grid_file.suffix == '.parquet' else gpd.read_file(grid_file)
        grid = grid[['geometry']].reset_index(drop=True)
        # Match grid cells to cluster cells via their representative points
        pts = gpd.GeoDataFrame(geometry=gdf.to_crs(grid.crs).representative_point(), index=gdf.index)
        joined = gpd.sjoin(pts, grid, how='inner', predicate='within')
        grid[['isl', 'sds', 'mi']] = 0
        grid.loc[joined['index_right'].values, ['isl', 'sds', 'mi']] = gdf.loc[joined.index, ['isl', 'sds', 'mi']].values
        gdf = grid[['isl', 'sds', 'mi', 'geometry']]

    gdf.to_parquet(Path(args.output_dir) / 'model.parquet')
