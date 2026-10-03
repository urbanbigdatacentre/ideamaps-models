import geopandas as gpd
from geopandas import GeoDataFrame
import momepy as mm
from pathlib import Path
import argparse
import shapely
import utm


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
    tess = mm.morphological_tessellation(buildings, clip=limit, segment=2, shrink=1)

    # Verification of tessellation
    excluded, multipolygons = mm.verify_tessellation(tess, buildings)
    print(excluded, multipolygons)

    tess = tess.join(buildings[[identifier]], how='left')

    return tess


def clean_geometries(buildings: GeoDataFrame) -> GeoDataFrame:
    # Keep only the polygonal parts of GeometryCollections (e.g., artefacts from GEE exports)
    is_gc = buildings.geom_type == 'GeometryCollection'
    if is_gc.any():
        print(f'Extracting polygons from {is_gc.sum()} GeometryCollection(s).')
        buildings.loc[is_gc, 'geometry'] = [
            shapely.unary_union([g for g in geom.geoms if g.geom_type in ('Polygon', 'MultiPolygon')])
            for geom in buildings.geometry[is_gc]
        ]
    return buildings


if __name__ == '__main__':
    args = argument_parser().parse_known_args()[0]

    # Loading preprocessed buildings
    building_file = Path(args.building_file)
    buildings = gpd.read_parquet(building_file) if building_file.suffix == '.parquet' else gpd.read_file(building_file)
    buildings = clean_geometries(buildings)
    buildings = buildings.sort_values(by='uID').reset_index(drop=True)

    # Morphological tessellation
    tess = get_morphological_tessellation(buildings, 'uID')

    # Ensure a 1:1 correspondence between buildings and tessellation
    building_ids = set(buildings['uID'])
    tess_ids = set(tess['uID'])
    missing_ids = list(set(building_ids) - set(tess_ids))
    if len(missing_ids) > 0:
        print(f'Removing {len(missing_ids)} buildings without tessellation cell.')
        # Remove ids of missing tessellation cells from buildings
        buildings = buildings[~buildings['uID'].isin(missing_ids)]
        assert len(buildings) == len(tess)

        # reindex
        buildings = buildings.sort_values(by='uID').reset_index(drop=True)
        tess = tess.sort_values(by='uID').reset_index(drop=True)
        buildings['uID'] = range(len(buildings))
        tess['uID'] = range(len(tess))

    # Write buildings and tessellation with aligned, contiguous indices (keeping all building attributes)
    buildings.index.name = None
    buildings.to_parquet(Path(args.output_dir) / 'buildings.parquet')
    tess.index.name = None
    tess.to_parquet(Path(args.output_dir) / 'tessellation.parquet')
