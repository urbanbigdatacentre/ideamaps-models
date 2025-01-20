import geopandas as gpd
from geopandas import GeoDataFrame
import momepy as mm
from libpysal import graph
from pathlib import Path
from shapely.geometry import Point, LineString
from parsers import morphometrics_parser as argument_parser


def pre_check(blg: GeoDataFrame, tess: GeoDataFrame):
    # This should be moved to the generation of the urban form elements
    blg_uids = set(blg['uID'])
    tess_uids = set(tess['uID'])
    common_uids = blg_uids.intersection(tess_uids)

    blg_only_uids = blg_uids - common_uids
    tess_only_uids = tess_uids - common_uids

    print(f"Unique uIDs in blg only: {len(blg_only_uids)}")
    print(f"Unique uIDs in tess only: {len(tess_only_uids)}")

    blg_cleaned = blg[blg['uID'] != 412867]
    tess_cleaned = tess[~tess['uID'].isin(tess_only_uids)]
    tess_cleaned = tess_cleaned.drop_duplicates(subset='uID', keep='first')

    blg_duplicates = blg_cleaned[blg_cleaned['uID'].duplicated()]['uID']
    tess_duplicates = tess_cleaned[tess_cleaned['uID'].duplicated()]['uID']

    print(f"Duplicate uIDs in blg: {blg_duplicates}")
    print(f"Duplicate uIDs in tess: {tess_duplicates}")

    common_uids = set(blg_cleaned['uID']).intersection(set(tess_cleaned['uID']))

    blg = blg_cleaned[blg_cleaned['uID'].isin(common_uids)].sort_values('uID')
    tess = tess_cleaned[tess_cleaned['uID'].isin(common_uids)].sort_values('uID')

    print(f"Aligned blg length: {len(blg)}")
    print(f"Aligned tess length: {len(tess)}")

    blg_uids_sorted = blg['uID'].tolist()
    tess_uids_sorted = tess['uID'].tolist()

    if blg_uids_sorted == tess_uids_sorted:
        print("uID match confirmed.")
    else:
        print("uID mismatch detected.")


# Function to check and clean invalid geometries
def check_and_clean_geometries(gdf):
    invalid_geometries = gdf[gdf.is_empty | gdf['geometry'].isnull()]
    print(f"Invalid geometries in {gdf.name if hasattr(gdf, 'name') else 'GeoDataFrame'}:")
    print(invalid_geometries)

    # Remove invalid geometries
    gdf_cleaned = gdf[~(gdf.is_empty | gdf['geometry'].isnull())]

    # Ensure all geometries are Shapely objects
    gdf_cleaned['geometry'] = gdf_cleaned['geometry'].apply(
        lambda geom: geom if isinstance(geom, (Point, LineString)) else None)

    return gdf_cleaned


if __name__ == '__main__':
    args = argument_parser().parse_known_args()[0]

    blg = gpd.read_parquet(args.building_file)
    tess = gpd.read_parquet(args.tessellation_file)

    pre_check(blg, tess)

    blg['sdbAre'] = blg.geometry.area  # Used for SDS (Sum & Mdn)
    blg[['uID', 'sdbAre']].to_parquet(Path(args.output_dir) / 'sdbAre.pq')

    blg['ssbElo'] = mm.elongation(blg)  # Used for SDS (Mdn)
    blg[['uID', 'ssbElo']].to_parquet(Path(args.output_dir) / 'ssbElo.pq')

    blg['stbOri'] = mm.orientation(blg)  # Used for ISL (SD)
    blg[['uID', 'stbOri']].to_parquet(Path(args.output_dir) / 'stbOri.pq')

    tess['stcOri'] = mm.orientation(tess)  # Used for ISL (SD)
    tess[['uID', 'stcOri']].to_parquet(Path(args.output_dir) / 'stcOri.pq')

    cencon = mm.centroid_corner_distance(blg)
    blg['ssbCCD'] = cencon['std']  # Used for ISL (Mdn)
    blg[['uID', 'ssbCCD']].to_parquet(Path(args.output_dir) / 'ssbCCD.pq')

    tess['sdcAre'] = tess.geometry.area  # Used for SDS (Mdn)
    tess[['uID', 'sdcAre']].to_parquet(Path(args.output_dir) / 'sdcAre.pq')

    tess['sscERI'] = mm.equivalent_rectangular_index(tess)  # Used for SDS (Mdn)
    tess[['uID', 'sscERI']].to_parquet(Path(args.output_dir) / 'sscERI.pq')

    tess = tess.merge(blg[['uID', 'sdbAre']], how='left', on='uID')
    tess['sicCAR'] = tess['sdbAre'] / tess['sdcAre']
    tess[['uID', 'sicCAR']].to_parquet(Path(args.output_dir) / 'sicCAR.pq')

    queen_1 = graph.Graph.build_contiguity(tess).higher_order(k=1)

    blg["mtbAli"] = mm.alignment(blg['stbOri'], queen_1)
    blg[['uID', 'mtbAli']].to_parquet(Path(args.output_dir) / 'mtbAli.pq')

    blg["mtbNDi"] = mm.neighbor_distance(blg, queen_1)  # Used for SDS (Mdn)
    blg[['uID', 'mtbNDi']].to_parquet(Path(args.output_dir) / 'mtbNDi.pq')

    tess["mtcWNe"] = mm.neighbors(tess, queen_1, weighted=True)  # Used for both (Mdn)
    tess[['uID', 'mtcWNe']].to_parquet(Path(args.output_dir) / 'mtcWNe.pq')

    # TODO: update API
    tess["mdcAre"] = mm.CoveredArea(tess, queen_1, "uID").series  # Used for SDS (Mdn)
    tess[['uID', 'mdcAre']].to_parquet(Path(args.output_dir) / 'mdcAre.pq')

    queen_3 = graph.Graph.build_contiguity(tess).higher_order(k=3)

    blg['ltbIBD'] = mm.mean_interbuilding_distance(blg, queen_1, queen_3)  # Used for SDS (Mdn)
    blg[['uID', 'ltbIBD']].to_parquet(Path(args.output_dir) / 'ltbIBD.pq')

    blg_q1 = graph.Graph.build_contiguity(blg).higher_order(k=1)

    blg['ltcBuA'] = mm.building_adjacency(queen_3, blg_q1)  # Used for both (Mdn)
    blg[['uID', 'ltcBuA']].to_parquet(Path(args.output_dir) / 'ltcBuA.pq')

    # TODO update to new API
    tess = tess.drop_duplicates(subset=['uID'])
    queen_3 = mm.sw_high(k=3, gdf=tess, ids='uID')
    # queen_3 = graph.Graph.build_contiguity(tess).higher_order(k=3)
    tess['ltcWRB'] = mm.BlocksCount(tess, 'bID', queen_3, 'uID', verbose=True).series
    tess[['uID', 'ltcWRB']].to_parquet(Path(args.output_dir) / 'ltcWRB.pq')

    # Clean and validate geometries
    blg = check_and_clean_geometries(blg)

    primary = tess.merge(blg, on='uID')
    primary.to_parquet(Path(args.output_dir) / 'primary.pq')
