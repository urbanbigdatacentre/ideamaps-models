import geopandas as gpd
import numpy as np
from pathlib import Path
import argparse


def argument_parser():
    # https://docs.python.org/3/library/argparse.html#the-add-argument-method
    parser = argparse.ArgumentParser(description="Experiment Args")
    parser.add_argument('-p', "--param-file", dest='param_file', required=True)
    parser.add_argument('-t', dest='thresh', required=True, type=float)
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

    param_file = Path(args.param_file)
    gdf = gpd.read_parquet(param_file) if param_file.suffix == '.parquet' else gpd.read_file(param_file)
    thresh = float(args.thresh)

    def model_logic(row):
        road_type = row['mode_paved']
        building_between = row['mean_buildings_in_between']
        if building_between < thresh:
            return 0 if road_type == 1 else 1
        else:
            return 2

    gdf['ra'] = gdf.apply(model_logic, axis=1)

    gdf[['ra', 'geometry']].to_parquet(Path(args.output_dir) / 'output.parquet')
