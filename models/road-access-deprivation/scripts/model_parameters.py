from pathlib import Path
import geopandas as gpd
import shapely
import momepy as mm
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


def read_geodata(file: Path) -> gpd.GeoDataFrame:
    gdf = gpd.read_parquet(str(file)) if file.suffix == '.parquet' else gpd.read_file(str(file))
    # Data providers name the geometry column differently (e.g., 'geom'), so normalize it
    if gdf.geometry.name != 'geometry':
        gdf = gdf.rename_geometry('geometry')
    return gdf


def compute_model_parameters(roads_file: str, road_type_attribute: str, road_type_key: str, buildings_file: str,
                             out_file: str):

    # Load roads data
    roads_file = Path(roads_file)
    roads = read_geodata(roads_file)
    roads = roads[['geometry', road_type_attribute]]
    roads['nID'] = range(len(roads))
    roads['paved'] = roads[road_type_attribute].apply(lambda x: 1 if x == road_type_key else 0)

    # Reproject to UTM zone
    roads = roads.to_crs(epsg=4326)
    centroid = roads.unary_union.centroid
    lon, lat = centroid.x, centroid.y
    _, _, zone_number, zone_letter = utm.from_latlon(lat, lon)
    utm_epsg = 32600 + zone_number if zone_letter >= 'N' else 32700 + zone_number
    roads = roads.to_crs(epsg=utm_epsg)

    # Load buildings data
    build_file = Path(buildings_file)
    buildings = read_geodata(build_file)
    buildings = buildings[['geometry']].to_crs(epsg=utm_epsg)
    buildings['uID'] = range(len(buildings))
    buildings['centroid'] = buildings.geometry.centroid

    # Compute nearest road
    buildings['nearest_road'] = mm.get_nearest_street(buildings, roads)
    buildings = buildings.merge(roads[['nID', 'paved']], how='left', left_on='nearest_road', right_index=True)

    # Vectorized: shortest line from each building centroid to its nearest road geometry
    # (nID was assigned as range(len(roads)), so it doubles as a positional index into roads)
    nearest_road_geom = roads.geometry.to_numpy()[buildings['nID'].to_numpy()]
    nearest_road_line = shapely.shortest_line(buildings['centroid'].to_numpy(), nearest_road_geom)
    buildings['nearest_road_line'] = gpd.GeoSeries(nearest_road_line, index=buildings.index, crs=utm_epsg)
    nearest_road_point = shapely.get_point(nearest_road_line, -1)
    buildings['nearest_road_point'] = gpd.GeoSeries(nearest_road_point, index=buildings.index, crs=utm_epsg)
    buildings['nearest_road_distance'] = buildings['nearest_road_line'].length

    # Intermediate save of nearest road points and nearest road lines
    out_file = Path(out_file)
    nearest_road = buildings[['uID', 'nearest_road_point']].set_geometry('nearest_road_point').set_crs(utm_epsg)
    nearest_road.to_parquet(out_file.parent / f'{out_file.stem}_nearest_road_point.parquet')
    nearest_road_line = buildings[['uID', 'nearest_road_line']].set_geometry('nearest_road_line').set_crs(utm_epsg)
    nearest_road_line.to_parquet(out_file.parent / f'{out_file.stem}_nearest_road_line.parquet')

    # Count the number of buildings intersecting each building's nearest-road line, using a spatial
    # join so only nearby candidates (via the buildings' spatial index) are tested, instead of
    # testing every line against every building.
    lines = buildings[['uID', 'nearest_road_line']].set_geometry('nearest_road_line').set_crs(utm_epsg)
    hits = gpd.sjoin(lines, buildings[['uID', 'geometry']], predicate='intersects', how='inner',
                      lsuffix='line', rsuffix='building')
    hits = hits[hits['uID_line'] != hits['uID_building']]  # exclude a building intersecting its own line
    counts = hits.groupby('uID_line').size()
    buildings['buildings_in_between'] = buildings['uID'].map(counts).fillna(0).astype(int)

    # Save the parameters
    buildings.set_geometry('geometry')
    buildings[['uID', 'buildings_in_between', 'nearest_road_distance', 'paved', 'geometry']].to_parquet(out_file)


if __name__ == '__main__':
    args = argument_parser().parse_known_args()[0]
    compute_model_parameters(args.roads_file, args.road_type_attribute, args.road_type_key, args.buildings_file,
                             args.out_file)
