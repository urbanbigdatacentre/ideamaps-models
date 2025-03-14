import geopandas as gpd
from geopandas import GeoDataFrame
import pandas as pd
from pandas import DataFrame
import momepy as mm
from libpysal import graph
from pathlib import Path
import argparse
import pickle


def argument_parser():
    # https://docs.python.org/3/library/argparse.html#the-add-argument-method
    parser = argparse.ArgumentParser(description="Experiment Args")
    parser.add_argument('-m', "--metric", dest='metric', required=True)
    parser.add_argument('-b', "--building-file", dest='building_file', required=True)
    parser.add_argument('-t', "--tessellation-file", dest='tessellation_file', required=True)
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
    building_metrics = ['sdbAre', 'ssbElo', 'stbOri', 'ssbCCD', 'mtbAli', 'mtbNDi', 'ltbIBD', 'ltcBuA']
    tessellation_metrics = ['sdcAre', 'stcOri', 'sscERI', 'sicCAR', 'mtcWNe', 'mdcAre', 'ltcWRB']
    assert metric in building_metrics or metric in tessellation_metrics
    building_metric = True if metric in building_metrics else False

    # Load from file if already exists
    out_file = out_path / f'{metric}.parquet'
    if out_file.exists():
        print(f'{metric} has already been computed. Loading data from {out_file}.')
        values = pd.read_parquet(out_file)
        return values
        # return buildings.merge(values, on='uID') if building_metric else tessellation.merge(values, on='uID')

    if metric == 'sdbAre':
        values = buildings.geometry.area  # Used for SDS (Sum & Mdn)
    elif metric == 'sdcAre':
        values = tessellation.geometry.area  # Used for SDS (Mdn)
    elif metric == 'ssbElo':
        values = mm.elongation(buildings)  # Used for SDS (Mdn)
    elif metric == 'stbOri':
        values = mm.orientation(buildings)  # Used for ISL (SD)
    elif metric == 'stcOri':
        values = mm.orientation(tessellation)  # Used for ISL (SD)
    elif metric == 'ssbCCD':
        cencon = mm.centroid_corner_distance(buildings)
        values = cencon['std']  # Used for ISL (Mdn)
    elif metric == 'sscERI':
        values = mm.equivalent_rectangular_index(tessellation)  # Used for SDS (Mdn)
    elif metric == 'sicCAR':
        sdbAre = compute_metric('sdbAre', buildings, tessellation, out_path)
        sdcAre = compute_metric('sdcAre', buildings, tessellation, out_path)
        values = pd.merge(sdbAre, sdcAre, on='uID')
        values = values['sdbAre'] / values['sdcAre']
    elif metric == 'mtbAli':  # TODO: fix
        queen_1 = compute_queen_graph(tessellation, 1, out_path)
        stbOri = compute_metric('stbOri', buildings, tessellation, out_path)
        buildings = buildings.merge(stbOri, on='uID')
        values = mm.alignment(buildings['stbOri'], queen_1)
    elif metric == 'mtbNDi':
        # TODO: UserWarning: The indices of the two GeoSeries are different. (geoms.distance(geometry.geometry, align=True)).groupby(level=0).mean()
        queen_1 = compute_queen_graph(tessellation, 1, out_path)
        values = mm.neighbor_distance(buildings, queen_1)  # Used for SDS (Mdn)
    elif metric == 'mtcWNe':
        queen_1 = compute_queen_graph(tessellation, 1, out_path)
        values = mm.neighbors(tessellation, queen_1, weighted=True)  # Used for both (Mdn)
    elif metric == 'mdcAre':
        queen_1 = compute_queen_graph(tessellation, 1, out_path)
        tessellation['sdcAre'] = tessellation.geometry.area
        values = queen_1.describe(tessellation['sdcAre'], statistics=['sum'])  # Used for SDS (Mdn)
    elif metric == 'ltbIBD':
        # TODO: RuntimeWarning: invalid value encountered in scalar divide mean_distances[i] = sub_matrix.sum() / sub_matrix.nnz
        queen_1 = compute_queen_graph(tessellation, 1, out_path)
        queen_3 = compute_queen_graph(tessellation, 3, out_path)
        values = mm.mean_interbuilding_distance(buildings, queen_1, queen_3)  # Used for SDS (Mdn)
    elif metric == 'ltcBuA':
        buildings_q1 = graph.Graph.build_contiguity(buildings).higher_order(k=1)
        queen_3 = compute_queen_graph(tessellation, 3, out_path)
        values = mm.building_adjacency(queen_3, buildings_q1)  # Used for both (Mdn)
    elif metric == 'ltcWRB':
        queen_3 = compute_queen_graph(tessellation, 3, out_path)
        block_count = queen_3.describe(tessellation['bID'], statistics=['count']).squeeze()
        sdcAre = compute_metric('sdcAre', buildings, tessellation, out_path)
        neighborhood_area = queen_3.describe(sdcAre['sdcAre'], statistics=['sum']).squeeze()
        values = block_count / neighborhood_area
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

    metrics = ['sdbAre', 'ssbElo', 'stbOri', 'ssbCCD', 'mtbAli', 'mtbNDi', 'ltbIBD', 'ltcBuA', 'sdcAre', 'stcOri',
               'sscERI', 'sicCAR', 'mtcWNe', 'mdcAre', 'ltcWRB']

    if args.metric == 'all':
        for metric in metrics:
            print(metric)
            compute_metric(metric, blg, tess, Path(args.output_dir))
    elif args.metric == 'combine':
        for metric in metrics:
            values = compute_metric(metric, blg, tess, Path(args.output_dir))
            blg = blg.merge(values, on='uID')
        blg[metrics + ['geometry']].to_parquet(Path(args.output_dir) / 'primary.parquet')
    else:
        compute_metric(args.metric, blg, tess, Path(args.output_dir))