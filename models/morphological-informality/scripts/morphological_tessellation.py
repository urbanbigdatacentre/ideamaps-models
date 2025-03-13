import geopandas as gpd
from geopandas import GeoDataFrame
import momepy as mm
from pathlib import Path
import argparse
import utm


def get_utm_epsg(gdf: GeoDataFrame) -> int:
    gdf = gdf.to_crs(4326)

    bounds = gdf.total_bounds
    min_lng, min_lat, max_lng, max_lat = bounds

    # Calculate the centroid of the bounding box
    lng = (min_lng + max_lng) / 2
    lat = (min_lat + max_lat) / 2

    # Convert to UTM
    utm_coords = utm.from_latlon(lat, lng)

    # Extract UTM Zone information
    zone_number = utm_coords[2]
    zone_letter = utm_coords[3]

    # Determine the EPSG code
    if zone_letter >= 'N':  # Northern hemisphere
        epsg_code = 32600 + zone_number
    else:  # Southern hemisphere
        epsg_code = 32700 + zone_number

    return epsg_code


def argument_parser():
    # https://docs.python.org/3/library/argparse.html#the-add-argument-method
    parser = argparse.ArgumentParser(description="Experiment Args")
    parser.add_argument('-b', '--building-file', dest='building_file', required=True)
    parser.add_argument('-o', '--output-dir', dest='output_dir', default='outputs/', required=False,
                        help="path to output directory")

    parser.add_argument(
        "opts",
        help="Modify config options using the command-line",
        default=None,
        nargs=argparse.REMAINDER,
    )
    return parser


def get_morphological_tessellation(buildings: GeoDataFrame, identifier: str) -> GeoDataFrame:
    limit = mm.buffered_limit(buildings, 100)
    tess = mm.morphological_tessellation(buildings, clip=limit, segment=2)

    # Verification of tessellation
    excluded, multipolygons = mm.verify_tessellation(tess, buildings)
    print(excluded, multipolygons)

    tess = tess.join(buildings[[identifier]], how='left')

    return tess


if __name__ == '__main__':
    args = argument_parser().parse_known_args()[0]

    # Loading preprocessed buildings
    building_file = Path(args.building_file)
    buildings = gpd.read_parquet(building_file) if building_file.suffix == '.parquet' else gpd.read_file(building_file)

    # Morphological tessellation
    tess = get_morphological_tessellation(buildings, 'uID')

    # Ensure a 1:1 correspondence between buildings and tessellation
    building_ids = set(buildings['uID'])
    tess_ids = set(tess['uID'])
    common_ids = building_ids.intersection(tess_ids)
    print(f'Unique uIDs in blg only: {len(building_ids - common_ids)}')
    print(f'Unique uIDs in tess only: {len(tess_ids - common_ids)}')

    tess.index.name = None
    tess.to_parquet(Path(args.output_dir) / 'tessellation.parquet')





