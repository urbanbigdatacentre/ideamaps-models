import geopandas as gpd
from geopandas import GeoDataFrame
import pandas as pd
from pandas import DataFrame
import momepy as mm
from libpysal import graph
from pathlib import Path
import argparse
import pickle
import numpy as np


def argument_parser():
    # https://docs.python.org/3/library/argparse.html#the-add-argument-method
    parser = argparse.ArgumentParser(description="Experiment Args")
    parser.add_argument('-m', "--metric", dest='metric', required=True)
    parser.add_argument('-b', "--building-file", dest='building_file', required=True)
    parser.add_argument('-t', "--tessellation-file", dest='tessellation_file', required=True)
    parser.add_argument('-e', "--edge-file", dest='edge_file', required=False, default=None)
    parser.add_argument('-o', "--output-dir", dest='output_dir', default='outputs/', required=False,
                        help="path to output directory")

    parser.add_argument(
        "opts",
        help="Modify config options using the command-line",
        default=None,
        nargs=argparse.REMAINDER,
    )
    return parser


def compute_queen_graph(tessellation: GeoDataFrame, order: int, out_path: Path):
    out_file = out_path / f'queen_{order}_graph.pkl'
    if out_file.exists():
        with open(str(out_file), 'rb') as f:
            queen_graph = pickle.load(f)
    else:
        queen_graph = graph.Graph.build_contiguity(tessellation).higher_order(k=order)
        with open(str(out_file), 'wb') as f:
            pickle.dump(queen_graph, f)
    return queen_graph


def compute_metric(metric: str, buildings: GeoDataFrame, tessellation: GeoDataFrame, out_path: Path) -> DataFrame:
    building_metrics = ['sdbAre', 'stbOri', 'mtbAli', 'mtbNDi', 'ltbIBD', 'mtbNDi_log', 'strAli']
    tessellation_metrics = ['sdcAre', 'stcOri', 'sicCAR', 'mtcWNe']
    assert metric in building_metrics or metric in tessellation_metrics
    building_metric = True if metric in building_metrics else False

    # Load from file if already exists
    out_file = out_path / f'{metric}.parquet'
    if out_file.exists():
        print(f'{metric} has already been computed. Loading data from {out_file}.')
        values = pd.read_parquet(out_file)
        return values

    if metric == 'sdbAre':
        values = buildings.geometry.area
    elif metric == 'sdcAre':
        values = tessellation.geometry.area
    elif metric == 'stbOri':
        values = mm.orientation(buildings)
    elif metric == 'stcOri':
        values = mm.orientation(tessellation)
    elif metric == 'sicCAR':
        sdbAre = compute_metric('sdbAre', buildings, tessellation, out_path)
        sdcAre = compute_metric('sdcAre', buildings, tessellation, out_path)
        values = pd.merge(sdbAre, sdcAre, on='uID')
        values = values['sdbAre'] / values['sdcAre']
    elif metric == 'mtbAli':
        queen_1 = compute_queen_graph(tessellation, 1, out_path)
        # TODO: Key error with 'all' when running it for the first time
        stbOri = compute_metric('stbOri', buildings, tessellation, out_path)
        buildings = buildings.merge(stbOri[['stbOri', 'uID']], on='uID')
        values = mm.alignment(buildings['stbOri'], queen_1)
    elif metric == 'mtbNDi':
        # TODO: UserWarning: The indices of the two GeoSeries are different. (geoms.distance(geometry.geometry, align=True)).groupby(level=0).mean()
        queen_1 = compute_queen_graph(tessellation, 1, out_path)
        values = mm.neighbor_distance(buildings, queen_1)
    elif metric == 'mtbNDi_log':
        mtbNDi = compute_metric('mtbNDi', buildings, tessellation, out_path)
        values = np.where(mtbNDi['mtbNDi'] <= 0, 0, np.log(mtbNDi['mtbNDi']))
        values[values < -5] = -5
    elif metric == 'mtcWNe':
        queen_1 = compute_queen_graph(tessellation, 1, out_path)
        values = mm.neighbors(tessellation, queen_1, weighted=True)
    elif metric == 'strAli':
        assert args.edge_file is not None
        roads = gpd.read_parquet(args.edge_file)
        roads_orient = mm.orientation(roads)
        blg_orient = compute_metric('stbOri', buildings, tessellation, out_path)
        buildings = buildings.merge(blg_orient[['uID', 'stbOri']], on='uID', how='left')
        notna = buildings['nID'].notna()
        buildings['strAli'] = 45.
        buildings.loc[notna, 'strAli'] = mm.street_alignment(buildings.loc[notna, 'stbOri'], roads_orient,
                                                             buildings.loc[notna, 'nID']).astype(float)
        values = buildings['strAli']
    else:
        raise Exception('Unkown metric.')

    if building_metric:
        buildings[metric] = values
        buildings[['uID', metric]].to_parquet(out_file)
        return buildings[['uID', metric]]
    else:
        tessellation[metric] = values
        tessellation[['uID', metric]].to_parquet(out_file)
        return tessellation[['uID', metric]]


if __name__ == '__main__':
    args = argument_parser().parse_known_args()[0]
    assert Path(args.output_dir).exists()

    blg = gpd.read_parquet(args.building_file)
    tess = gpd.read_parquet(args.tessellation_file)

    assert blg['uID'].is_unique
    blg = blg.sort_values(by='uID')
    assert tess['uID'].is_unique
    tess = tess.sort_values(by='uID')

    metrics = ['sdbAre', 'stbOri', 'mtbNDi_log', 'sdcAre', 'stcOri', 'sicCAR', 'mtcWNe', 'strAli', 'mtbAli']

    if args.metric == 'all':
        for metric in metrics:
            print(metric)
            compute_metric(metric, blg, tess, Path(args.output_dir))
    elif args.metric == 'combine':
        for metric in metrics:
            values = compute_metric(metric, blg, tess, Path(args.output_dir))
            blg = blg.merge(values, on='uID')
        blg[metrics + ['geometry']].to_parquet(Path(args.output_dir) / 'buildings_primary.parquet')
    else:
        compute_metric(args.metric, blg, tess, Path(args.output_dir))