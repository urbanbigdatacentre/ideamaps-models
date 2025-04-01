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
    parser.add_argument('-r', '--roi-file', dest='roi_file', required=True)
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


def preprocess_buildings(buildings: GeoDataFrame, extent: GeoDataFrame, identifier: str) -> GeoDataFrame:
    # Reproject buildings to UTM Zone
    utm_epsg = get_utm_epsg(extent)
    buildings = buildings.to_crs(utm_epsg)

    # Generating simple extents for geographic and map coordinates
    extent_utm = extent.to_crs(utm_epsg).unary_union
    buildings = buildings[buildings.intersects(extent_utm)]
    print(f'Processing {len(buildings)} buildings.')

    # Dropping duplicates
    buildings['geometry'] = buildings.normalize()
    n_duplicate_geometries = len(buildings) - len(buildings.drop_duplicates('geometry'))
    print(f'Number of duplicate geometries in buildings: {n_duplicate_geometries}')
    buildings = buildings.drop_duplicates('geometry')

    # Clean geometries of buildings
    buildings.geometry = buildings.buffer(0)

    # Remove buildings with NaN geometries
    buildings = buildings[~buildings.geometry.isna()]

    # Simplify polygons
    buildings = buildings.explode(index_parts=False)

    # Reset indices
    # buildings = buildings.reset_index(drop=True).explode(index_parts=False).reset_index(drop=True)
    buildings = buildings.reset_index()
    buildings = mm.preprocess(buildings, size=10, compactness=0.2, islands=True)

    # Check morphological tessellation
    check = mm.CheckTessellationInput(buildings)

    # Drop problematic buildings
    buildings = buildings.drop(check.collapse.index.union(check.overlap.index).union(check.split.index))

    # Assign building ID
    buildings = buildings.reset_index()
    buildings[identifier] = range(len(buildings))

    return buildings


if __name__ == '__main__':
    args = argument_parser().parse_known_args()[0]
    assert Path(args.output_dir).exists()

    # Region of interest
    roi = gpd.read_file(args.roi_file)

    # Buildings
    building_file = Path(args.building_file)
    buildings = gpd.read_parquet(building_file) if building_file.suffix == '.parquet' else gpd.read_file(building_file)
    buildings = preprocess_buildings(buildings, roi, 'uID')

    buildings = buildings[['uID', 'geometry']]
    buildings.index.name = None
    buildings.to_parquet(Path(args.output_dir) / 'buildings.parquet')





