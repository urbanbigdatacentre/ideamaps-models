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

    gdf[['isl', 'sds', 'mi', 'geometry']].to_parquet(Path(args.output_dir) / 'model.parquet')
