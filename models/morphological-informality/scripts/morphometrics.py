import geopandas as gpd
from geopandas import GeoDataFrame
import momepy as mm
from libpysal import graph
from pathlib import Path
from shapely.geometry import Point, LineString
import argparse


def argument_parser():
    # https://docs.python.org/3/library/argparse.html#the-add-argument-method
    parser = argparse.ArgumentParser(description="Experiment Args")
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


if __name__ == '__main__':
    args = argument_parser().parse_known_args()[0]

    blg = gpd.read_parquet(args.building_file)
    tess = gpd.read_parquet(args.tessellation_file)
    tess.index = tess['uID']
    tess['geometry'] = tess['geometry'].buffer(0)  # Fix invalid geometries
    invalid_geometries = tess[~tess.is_valid]
    print(f'Invalid geometries: {len(invalid_geometries)}')

    indices = [335307, 336555, 842121]
    for index in indices:
        tess = tess.drop(index=index)
        blg = blg.drop(index=index)

    # Reassign primary keys (indices) after dropping rows
    blg.index.name = None
    tess.index.name = None
    assert blg['uID'].is_unique and tess['uID'].is_unique
    blg = blg.sort_values(by='uID').reset_index(drop=True)
    tess = tess.sort_values(by='uID').reset_index(drop=True)

    blg.to_parquet(Path(args.output_dir) / 'buildings_clean.parquet')

    blg['sdbAre'] = blg.geometry.area  # Used for SDS (Sum & Mdn)
    blg[['uID', 'sdbAre']].to_parquet(Path(args.output_dir) / 'sdbAre.parquet')

    blg['ssbElo'] = mm.elongation(blg)  # Used for SDS (Mdn)
    blg[['uID', 'ssbElo']].to_parquet(Path(args.output_dir) / 'ssbElo.parquet')

    blg['stbOri'] = mm.orientation(blg)  # Used for ISL (SD)
    blg[['uID', 'stbOri']].to_parquet(Path(args.output_dir) / 'stbOri.parquet')

    tess['stcOri'] = mm.orientation(tess)  # Used for ISL (SD)
    tess[['uID', 'stcOri']].to_parquet(Path(args.output_dir) / 'stcOri.parquet')

    cencon = mm.centroid_corner_distance(blg)
    blg['ssbCCD'] = cencon['std']  # Used for ISL (Mdn)
    blg[['uID', 'ssbCCD']].to_parquet(Path(args.output_dir) / 'ssbCCD.parquet')

    tess['sdcAre'] = tess.geometry.area  # Used for SDS (Mdn)
    tess[['uID', 'sdcAre']].to_parquet(Path(args.output_dir) / 'sdcAre.parquet')

    tess['sscERI'] = mm.equivalent_rectangular_index(tess)  # Used for SDS (Mdn)
    tess[['uID', 'sscERI']].to_parquet(Path(args.output_dir) / 'sscERI.parquet')

    tess = tess.merge(blg[['uID', 'sdbAre']], how='left', on='uID')
    tess['sicCAR'] = tess['sdbAre'] / tess['sdcAre']
    tess[['uID', 'sicCAR']].to_parquet(Path(args.output_dir) / 'sicCAR.parquet')

    queen_1 = graph.Graph.build_contiguity(tess).higher_order(k=1)

    blg["mtbAli"] = mm.alignment(blg['stbOri'], queen_1)
    blg[['uID', 'mtbAli']].to_parquet(Path(args.output_dir) / 'mtbAli.parquet')

    blg["mtbNDi"] = mm.neighbor_distance(blg, queen_1)  # Used for SDS (Mdn)
    blg[['uID', 'mtbNDi']].to_parquet(Path(args.output_dir) / 'mtbNDi.parquet')

    tess["mtcWNe"] = mm.neighbors(tess, queen_1, weighted=True)  # Used for both (Mdn)
    tess[['uID', 'mtcWNe']].to_parquet(Path(args.output_dir) / 'mtcWNe.parquet')

    # Compute CoveredArea using the .describe() method
    tess["mdcAre"] = queen_1.describe(tess['sdcAre'], statistics=['sum']) # Used for SDS (Mdn)
    tess[['uID', 'mdcAre']].to_parquet(Path(args.output_dir) / 'mdcAre.parquet')

    queen_3 = graph.Graph.build_contiguity(tess).higher_order(k=3)

    blg['ltbIBD'] = mm.mean_interbuilding_distance(blg, queen_1, queen_3)  # Used for SDS (Mdn)
    blg[['uID', 'ltbIBD']].to_parquet(Path(args.output_dir) / 'ltbIBD.parquet')

    blg_q1 = graph.Graph.build_contiguity(blg).higher_order(k=1)

    blg['ltcBuA'] = mm.building_adjacency(queen_3, blg_q1)  # Used for both (Mdn)
    blg[['uID', 'ltcBuA']].to_parquet(Path(args.output_dir) / 'ltcBuA.parquet')

    # Compute BlocksCount using the .describe() method
    block_count = queen_3.describe(tess['bID'], statistics=['count']).squeeze()
    neighborhood_area = queen_3.describe(tess['sdcAre'], statistics=['sum']).squeeze()
    tess['ltcWRB'] = block_count / neighborhood_area
    tess[['uID', 'ltcWRB']].to_parquet(Path(args.output_dir) / 'ltcWRB.parquet')

    primary = blg.merge(tess.drop(columns='geometry'), on='uID')
    primary.to_parquet(Path(args.output_dir) / 'primary.parquet')
