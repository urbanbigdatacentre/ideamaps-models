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
    parser.add_argument('-e', '--edge-file', dest='edge_file', required=True)
    parser.add_argument('-o', '--output-dir', dest='output_dir', default='outputs/', required=False,
                        help="path to output directory")

    parser.add_argument(
        "opts",
        help="Modify config options using the command-line",
        default=None,
        nargs=argparse.REMAINDER,
    )
    return parser


def preprocess_edges(edges: GeoDataFrame, extent: GeoDataFrame) -> GeoDataFrame:
    extent = extent.to_crs(4326)
    utm_epsg = get_utm_epsg(extent)
    edges = edges.to_crs(utm_epsg)
    extent_utm = extent.to_crs(utm_epsg)

    if 'subtype' in edges.columns:
        edges = edges[edges['subtype'] == 'road']

    if 'class' in edges.columns:
        road_classes = ['living_street', 'motorway', 'primary', 'residential', 'secondary', 'service', 'tertiary',
                        'trunk', 'unclassified', 'unknown', ]
        edges = edges[edges['class'].isin(road_classes)]

    # Subset roads to only roads that intersect with region of interest
    edges = edges[edges.geometry.intersects(extent_utm.unary_union)]

    edges = mm.remove_false_nodes(edges.explode(index_parts=False).reset_index(drop=True))

    # Generate ids for the edges and assign them to the closest building
    edges = edges.reset_index()
    edges['nID'] = range(len(edges))

    return edges


if __name__ == '__main__':
    args = argument_parser().parse_known_args()[0]
    assert Path(args.output_dir).exists()

    # Region of interest
    roi = gpd.read_file(args.roi_file)

    # Buildings
    building_file = Path(args.building_file)
    buildings = gpd.read_parquet(building_file) if building_file.suffix == '.parquet' else gpd.read_file(building_file)

    # Roads
    edge_file = Path(args.edge_file)
    edges = gpd.read_parquet(edge_file) if edge_file.suffix == '.parquet' else gpd.read_file(edge_file)
    edges = preprocess_edges(edges, roi)
    edges = edges[['nID', 'geometry']]
    edges.to_parquet(Path(args.output_dir) / 'edges.parquet')

    # Add network ID of closest road (within 500 m) to buildings
    buildings['nID'] = mm.get_nearest_street(buildings, edges, max_distance=500)

    buildings[['uID', 'nID', 'geometry']].to_parquet(Path(args.output_dir) / 'buildings.parquet')
