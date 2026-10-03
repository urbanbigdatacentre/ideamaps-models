from geopandas import GeoDataFrame
from shapely.geometry import box
import osmnx as ox
from pathlib import Path
import argparse

# Vehicular road classes used by the model (OSM highway tags); link roads are mapped to their parent class
ROAD_CLASSES = ['motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'residential', 'living_street', 'service',
                'unclassified']


def argument_parser():
    # https://docs.python.org/3/library/argparse.html#the-add-argument-method
    parser = argparse.ArgumentParser(description="Experiment Args")
    parser.add_argument('-e', '--east', dest='east', required=True)
    parser.add_argument('-w', '--west', dest='west', required=True)
    parser.add_argument('-n', '--north', dest='north', required=True)
    parser.add_argument('-s', '--south', dest='south', required=True)
    parser.add_argument('-o', '--output-dir', dest='output_dir', default='outputs/', required=False,
                        help="path to output directory")

    parser.add_argument(
        "opts",
        help="Modify config options using the command-line",
        default=None,
        nargs=argparse.REMAINDER,
    )
    return parser


def road_class(highway) -> str:
    # Simplified OSM edges can carry several highway tags; use the first vehicular one
    tags = highway if isinstance(highway, list) else [highway]
    for tag in tags:
        tag = str(tag).removesuffix('_link')
        if tag in ROAD_CLASSES:
            return tag
    return None


# Download road network from OpenStreetMap
def get_osm_roads(east: float, west: float, north: float, south: float) -> GeoDataFrame:
    # Create bounding box (shapely box)
    bbox = box(west, south, east, north)

    # Get OSM roads for pilot site; undirected so that two-way roads are represented by a single edge
    G = ox.graph_from_polygon(bbox, network_type='all')
    G = ox.convert.to_undirected(G)
    edges = ox.graph_to_gdfs(G, nodes=False, edges=True, node_geometry=False, fill_edge_geometry=True)

    # Keep vehicular roads only (excludes footways, paths, tracks, etc.)
    edges['class'] = edges['highway'].apply(road_class)
    edges = edges[edges['class'].notna()]

    edges = edges[['highway', 'class', 'geometry']].reset_index(drop=True)
    edges['highway'] = edges['highway'].astype(str)

    return edges


if __name__ == '__main__':
    args = argument_parser().parse_known_args()[0]
    assert Path(args.output_dir).exists()
    roads = get_osm_roads(float(args.east), float(args.west), float(args.north), float(args.south))
    roads.to_parquet(Path(args.output_dir) / 'roads.parquet')
