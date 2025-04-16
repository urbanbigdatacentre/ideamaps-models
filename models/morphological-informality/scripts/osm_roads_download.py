from geopandas import GeoDataFrame
from shapely.geometry import box
import osmnx as ox
import argparse


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


# Download road network from OpenStreetMap
def get_osm_roads(east: float, west: float, north: float, south: float) -> GeoDataFrame:
    # Create bounding box (shapely box)
    bbox = box(west, south, east, north)

    # Get OSM roads for pilot site
    G = ox.graph_from_polygon(bbox, network_type='all')
    edges = ox.graph_to_gdfs(G, nodes=False, edges=True, node_geometry=False, fill_edge_geometry=True)

    edges = edges[['highway', 'geometry']]
    edges['highway'] = edges['highway'].astype(str)

    return edges


if __name__ == '__main__':
    args = argument_parser().parse_known_args()[0]
    roads = get_osm_roads(float(args.east), float(args.west), float(args.north), float(args.south))
    roads.to_parquet(args.output_dir)



