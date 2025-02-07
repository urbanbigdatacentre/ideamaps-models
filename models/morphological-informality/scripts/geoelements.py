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


def preprocess_buildings(buildings: GeoDataFrame, extent: GeoDataFrame, identifier: str) -> GeoDataFrame:
    # Reproject buildings to UTM Zone
    utm_epsg = get_utm_epsg(extent)
    buildings = buildings.to_crs(utm_epsg)

    # Generating simple extents for geographic and map coordinates
    extent_utm = extent.to_crs(utm_epsg).unary_union
    buildings = buildings[buildings.intersects(extent_utm)]

    # Clean geometries of buildings
    buildings.geometry = buildings.buffer(0)

    # Remove buildings with NaN geometries
    buildings = buildings[~buildings.geometry.isna()]

    # Simplify polygons
    buildings = buildings.explode(index_parts=False)

    # Reset indices
    # buildings = buildings.reset_index(drop=True).explode(index_parts=False).reset_index(drop=True)
    buildings = mm.preprocess(buildings.reset_index(), size=10, compactness=0.2, islands=True)

    # Check morphological tessellation
    check = mm.CheckTessellationInput(buildings)

    # Drop problematic buildings
    buildings = buildings.drop(check.collapse.index.union(check.overlap.index).union(check.split.index))

    # Assign building ID
    buildings = buildings.reset_index()
    buildings[identifier] = range(len(buildings))

    return buildings


def get_morphological_tessellation(buildings: GeoDataFrame, identifier: str) -> GeoDataFrame:
    limit = mm.buffered_limit(buildings, 100)
    tess = mm.morphological_tessellation(buildings, clip=limit, segment=2)

    # Verification of tessellation
    excluded, multipolygons = mm.verify_tessellation(tess, buildings)
    print(excluded, multipolygons)

    tess = tess.join(buildings[[identifier]], how='left')

    return tess


def preprocess_edges(edges: GeoDataFrame, extent: GeoDataFrame) -> GeoDataFrame:
    extent = extent.to_crs(4326)
    utm_epsg = get_utm_epsg(extent)
    edges = edges.to_crs(utm_epsg)
    extent_utm = extent.to_crs(utm_epsg)

    # Subset roads to only roads that intersect with region of interest
    edges = edges[edges.geometry.intersects(extent_utm.unary_union)]

    edges = mm.remove_false_nodes(edges.explode(index_parts=False).reset_index(drop=True))

    # Generate ids for the edges and assign them to the closest building
    edges = edges.reset_index()
    edges['nID'] = range(len(edges))

    return edges


def get_blocks(buildings: GeoDataFrame, tess: GeoDataFrame, edges: GeoDataFrame) -> GeoDataFrame:
    # Extend the edges if necessary to avoid issues
    snapped = mm.extend_lines(edges, tolerance=40, target=tess, barrier=buildings)

    # Generate blocks
    blocks, _ = mm.generate_blocks(tess, snapped, buildings)

    # Assign block ID
    blocks['bID'] = range(len(blocks))

    return blocks


if __name__ == '__main__':
    args = argument_parser().parse_known_args()[0]

    # Region of interest
    roi = gpd.read_file(args.roi_file)

    # Buildings
    building_file = Path(args.building_file)
    buildings = gpd.read_parquet(building_file) if building_file.suffix == '.parquet' else gpd.read_file(building_file)
    buildings = preprocess_buildings(buildings, roi, 'uID')

    # Morphological tessellation
    tess = get_morphological_tessellation(buildings, 'uID')

    # Establish a 1:1 correspondence between buildings and tessellation
    building_ids = set(buildings['uID'])
    tess_ids = set(tess['uID'])
    common_ids = building_ids.intersection(tess_ids)

    print(f'Unique uIDs in blg only: {len(building_ids - common_ids)}')
    print(f'Unique uIDs in tess only: {len(tess_ids - common_ids)}')

    # buildings = buildings[buildings['tempID'].isin(common_ids)].drop_duplicates(subset='tempID', keep='first')
    # tess = tess[tess['tempID'].isin(common_ids)].drop_duplicates(subset='tempID', keep='first')

    # Assigning IDs
    # buildings = buildings.reset_index()
    # buildings['uID'] = range(len(buildings))
    buildings = buildings[['uID', 'geometry']]
    # buildings = buildings.set_index('uID')
    # tess.index = tess.set_index('uID')

    # tess = tess.join(buildings[['uID']], on='tempID', how='left')

    # tess = tess.reset_index()
    # buildings = buildings.drop(columns='tempID')
    # tess = tess.drop(columns='tempID')

    buildings.to_parquet(Path(args.output_dir) / 'buildings.parquet')
    tess.to_parquet(Path(args.output_dir) / 'tessellation.parquet')

    # Roads
    edge_file = Path(args.edge_file)
    edges = gpd.read_parquet(edge_file) if edge_file.suffix == '.parquet' else gpd.read_file(edge_file)
    edges = preprocess_edges(edges, roi)
    edges = edges[['nID', 'geometry']]
    edges.to_parquet(Path(args.output_dir) / 'edges.parquet')

    # Add network ID of closest road to buildings
    buildings['nID'] = mm.get_nearest_street(buildings, edges, max_distance=500)

    # Blocks
    blocks = get_blocks(buildings, tess, edges)
    blocks.to_parquet(Path(args.output_dir) / 'blocks.parquet')

    # Add IDs
    buildings = buildings[['uID', 'nID', 'geometry']]
    buildings_with_block_id = gpd.sjoin(buildings, blocks[['bID', 'geometry']], how='left', predicate='within')
    buildings_with_block_id = buildings_with_block_id.drop(columns='index_right')
    buildings_with_block_id.to_parquet(Path(args.output_dir) / 'buildings.parquet')

    tess_with_block_id = tess.merge(buildings_with_block_id[['uID', 'bID']], how='left', on='uID')
    tess_with_block_id.to_parquet(Path(args.output_dir) / 'tessellation.parquet')




