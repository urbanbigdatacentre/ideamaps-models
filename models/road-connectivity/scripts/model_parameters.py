from pathlib import Path
import pandas as pd
import geopandas as gpd
from shapely.ops import nearest_points
from shapely.geometry import LineString
import momepy as mm
import dask_geopandas
import utm
import argparse


def argument_parser():
    # https://docs.python.org/3/library/argparse.html#the-add-argument-method
    parser = argparse.ArgumentParser(description="Experiment Args")
    parser.add_argument('-r', "--roads-file", dest='roads_file', required=True,
                        help='Road network data with a surface type attribute')
    parser.add_argument('-t', "--road-type-attribute", dest='road_type_attribute', required=True,
                        help='Name of the field containing the road type information (paved/unpaved)')
    parser.add_argument('-p', "--road-type-key", dest='road_type_key', required=True,
                        help='Road type key corresponding to paved roads')
    parser.add_argument('-b', "--buildings-file", dest='buildings_file', required=True,
                        help='Building footprint file (.parquet) with attributes buildings_in_between and paved')
    parser.add_argument('-o', "--out-file", dest='out_file', required=True,
                        help='output file (.parquet)')
    parser.add_argument(
        "opts",
        help="Modify config options using the command-line",
        default=None,
        nargs=argparse.REMAINDER,
    )
    return parser


def compute_model_parameters(roads_file: str, road_type_attribute: str, road_type_key: str, buildings_file: str,
                             out_file: str):

    # Load roads data
    roads_file = Path(roads_file)
    roads = gpd.read_parquet(str(roads_file)) if roads_file.suffix == '.parquet' else gpd.read_file(str(roads_file))
    roads = roads[['geometry', args.road_type_attribute]]
    roads['nID'] = range(len(roads))
    roads['paved'] = roads[args.road_type_attribute].apply(lambda x: 0 if x == args.road_type_key else 1)

    # Reproject to UTM zone
    roads = roads.to_crs(epsg=4326)
    centroid = roads.unary_union.centroid
    lon, lat = centroid.x, centroid.y
    _, _, zone_number, zone_letter = utm.from_latlon(lat, lon)
    utm_epsg = 32600 + zone_number if zone_letter >= 'N' else 32700 + zone_number
    roads = roads.to_crs(epsg=utm_epsg)

    # Load buildings data
    build_file = Path(buildings_file)
    buildings = gpd.read_parquet(str(build_file)) if build_file.suffix == '.parquet' else gpd.read_file(str(build_file))
    buildings = buildings[['geometry']].to_crs(epsg=utm_epsg)
    buildings['uID'] = range(len(buildings))
    buildings['centroid'] = buildings.geometry.centroid

    # Compute nearest road
    buildings['nearest_road'] = mm.get_nearest_street(buildings, roads)
    buildings = buildings.merge(roads[['nID', 'paved']], how='left', left_on='nearest_road', right_index=True)

    # Find the nearest point on road w.r.t for a building centroid
    def get_nearest_road_point(building_centroid, road):
        nearest_point = nearest_points(building_centroid, road.geometry)[1]  # Get nearest point on the road
        return nearest_point

    # Iterate over buildings and compute nearest road points
    nearest_road_points = []
    for i in range(len(buildings)):
        building = buildings.iloc[i]
        road = roads.iloc[building['nID']]
        nearest_road_points.append(get_nearest_road_point(building['centroid'], road))
    buildings['nearest_road_point'] = nearest_road_points

    # Create a straight line from each building centroid to the closest road point
    buildings['nearest_road_line'] = buildings.apply(
        lambda row: LineString([row['centroid'], row['nearest_road_point']]), axis=1)

    # Intermediate save of nearest road points and nearest road lines
    out_file = Path(out_file)
    nearest_road = buildings[['uID', 'nearest_road_point']].set_geometry('nearest_road_point').set_crs(utm_epsg)
    nearest_road.to_parquet(out_file.parent / f'{out_file.stem}_nearest_road_point.parquet')
    nearest_road_line = buildings[['uID', 'nearest_road_line']].set_geometry('nearest_road_line').set_crs(utm_epsg)
    nearest_road_line.to_parquet(out_file.parent / f'{out_file.stem}_nearest_road_line.parquet')

    # Count the number of buildings intersecting a line
    def count_buildings_dask(row, buildings):
        return buildings[buildings.geometry.intersects(row.nearest_road_line)].shape[0] - 1

    # Loop over buildings in batches to compute number of buildings in between each building and its nearest road
    batches = []
    batch_size = 10_000
    for i_batch in range(0, len(buildings), batch_size):
        ddf = dask_geopandas.from_geopandas(buildings.iloc[i_batch:i_batch + batch_size], npartitions=8)

        ddf['buildings_in_between'] = ddf.map_partitions(
            lambda df: df.apply(lambda row: count_buildings_dask(row, buildings), axis=1))

        buildings_batch = ddf.compute()
        buildings_batch = buildings_batch[['uID', 'buildings_in_between', 'paved', 'geometry']]
        batches.append(buildings_batch)
        print(f'Processed batch: {i_batch} - {i_batch + batch_size} ({len(buildings)}.')
    buildings = pd.concat(batches)

    # Save the parameters
    buildings.set_geometry('geometry')[
    buildings['uID', 'buildings_in_between', 'paved', 'geometry']].to_parquet(out_file)


if __name__ == '__main__':
    args = argument_parser().parse_known_args()[0]
    compute_model_parameters(args.roads_file, args.road_type_attribute, args.road_type_key, args.buildings_file,
                             args.out_file)
