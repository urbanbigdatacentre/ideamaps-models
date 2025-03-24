import geopandas as gpd
from geopandas import GeoDataFrame
import pandas as pd
from shapely.geometry import LineString
import utm
import numpy as np
from pathlib import Path
import argparse


def argument_parser():
    # https://docs.python.org/3/library/argparse.html#the-add-argument-method
    parser = argparse.ArgumentParser(description="Experiment Args")
    parser.add_argument('-m', "--metric", dest='metric', required=True)
    parser.add_argument('-r', "--road-file", dest='road_file', required=True)
    parser.add_argument('-o', "--output-dir", dest='output_dir', default='outputs/', required=False,
                        help="path to output directory")

    parser.add_argument(
        "opts",
        help="Modify config options using the command-line",
        default=None,
        nargs=argparse.REMAINDER,
    )
    return parser

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

# Subset for OSM road attributes
def preprocess(roads: GeoDataFrame) -> GeoDataFrame:
    if 'subtype' in roads.columns:
        roads = roads[roads['subtype'] == 'road']

    if 'class' in roads.columns:
        road_classes = ['living_street', 'motorway', 'primary', 'residential', 'secondary', 'service', 'tertiary',
                        'trunk', 'unclassified', 'unknown',]
        roads = roads[roads['class'].isin(road_classes)]

    return roads

def interpolate_points(line, interval=1):
    """Generate points along a LineString at a fixed interval."""
    points = []
    for distance in np.arange(0, line.length, interval):
        point = line.interpolate(distance)
        points.append(point)
    return points

def calculate_orientation(point1, point2):
    """Calculate road orientation in degrees between two consecutive points."""
    dx = point2.x - point1.x
    dy = point2.y - point1.y
    angle = np.arctan2(dy, dx) * 180 / np.pi  # Convert radians to degrees
    return angle % 180  # Keep within [0, 180] degrees

def orientation_deviation(angle):
    """Convert orientation to deviation from cardinal directions (0, 90, 180)."""
    return min(angle % 90, 90 - (angle % 90))

def dissolve_roads_into_points(gdf, interval=10):
    """Dissolve road segments into points and compute orientation."""
    points = []
    orientations = []

    for line in gdf.geometry:
        if isinstance(line, LineString):
            road_points = interpolate_points(line, interval)
            points.extend(road_points)

            # Compute orientations between consecutive points
            for i in range(len(road_points) - 1):
                angle = calculate_orientation(road_points[i], road_points[i + 1])
                orientations.append(angle)

            # Ensure lists have equal length by appending a None orientation for the last point
            orientations.append(None)

    print(len(points), len(orientations))

    return gpd.GeoDataFrame({"geometry": points, "orientation": orientations}, crs=gdf.crs)


def compute_metric(metric: str, roads: GeoDataFrame, out_path: Path) -> GeoDataFrame:

    # Load from file if already exists
    out_file = out_path / f'{metric}.parquet'
    # if out_file.exists():
    #     print(f'{metric} has already been computed. Loading data from {out_file}.')
    #     values = pd.read_parquet(out_file)
    #     return values

    if metric == 'strOri':
        # Convert roads into points with orientation
        values = dissolve_roads_into_points(roads, interval=10)

        values['strOri'] = values['orientation'].apply(
            lambda x: orientation_deviation(x) if pd.notnull(x) else None)
        values = values[['strOri', 'geometry']]
        values.to_parquet(out_file)
        return values


if __name__ == '__main__':
    args = argument_parser().parse_known_args()[0]
    assert Path(args.output_dir).exists()

    roads = gpd.read_parquet(args.road_file)
    utm_epsg = get_utm_epsg(roads)
    roads = roads.to_crs(utm_epsg)
    roads = preprocess(roads)
    out_road_file = Path(args.output_dir) / 'roads.parquet'
    if not out_road_file.exists():
        roads[['geometry']].to_parquet(out_road_file)

    _ = compute_metric(args.metric, roads, Path(args.output_dir))