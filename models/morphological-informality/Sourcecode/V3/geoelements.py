import geopandas as gpd
from geopandas import GeoDataFrame
import momepy as mm
from pathlib import Path
import osmnx as ox

from parsers import geomelements_parser as argument_parser
from utils import get_utm_epsg


def preprocess_gobv3_buildings(buildings: GeoDataFrame, extent: GeoDataFrame) -> GeoDataFrame:
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

    # TODO: Not sure what this does
    buildings = buildings.reset_index(drop=True).explode(index_parts=False).reset_index(drop=True)

    # Check morphological tessellation
    check = mm.CheckTessellationInput(buildings)

    # Drop problematic buildings
    buildings = buildings.drop(check.collapse.index.union(check.overlap.index).union(check.split.index))

    # Assign building ID and network ID
    buildings.index = range(len(buildings))
    buildings = buildings.rename_axis('ID')
    buildings['uID'] = buildings.index

    return buildings


def get_edges(extent: GeoDataFrame) -> GeoDataFrame:

    extent = extent.to_crs(4326)
    utm_epsg = get_utm_epsg(extent)
    extent = extent.unary_union

    # Get OSM roads for pilot site
    G = ox.graph_from_polygon(extent, network_type='all')
    edges = ox.graph_to_gdfs(G, nodes=False, edges=True, node_geometry=False, fill_edge_geometry=True)

    # Reproject to UTM zone
    edges = edges.to_crs(utm_epsg)

    edges = mm.remove_false_nodes(edges.explode(index_parts=False).reset_index(drop=True))

    edges = edges[['highway', 'geometry']]
    edges['highway'] = edges['highway'].astype(str)

    # Generate ids for the edges and assign them to the closest building
    edges.index = range(len(edges))
    edges = edges.rename_axis('ID')
    edges['nID'] = edges.index

    return edges


def get_morphological_tessellation(buildings: GeoDataFrame) -> GeoDataFrame:
    limit = mm.buffered_limit(buildings, 100)
    tess = mm.morphological_tessellation(buildings, clip=limit, segment=2)

    # Verification of tessellation
    excluded, multipolygons = mm.verify_tessellation(tess, buildings)
    print(excluded, multipolygons)
    tess = tess.join(buildings[['uID', 'nID']], how='left')

    return tess


def get_blocks(buildings: GeoDataFrame, tess: GeoDataFrame, edges: GeoDataFrame) -> GeoDataFrame:
    # Extend the edges if necessary to avoid issues
    snapped = mm.extend_lines(edges, tolerance=40, target=tess, barrier=buildings)

    # Generate blocks
    blocks, _ = mm.generate_blocks(tess, snapped, buildings)

    # Assign block ID
    blocks.index = range(len(blocks))
    blocks = blocks.rename_axis('ID')
    blocks['bID'] = blocks.index

    return blocks


if __name__ == '__main__':
    args = argument_parser().parse_known_args()[0]

    # Extent
    extent = gpd.read_file(args.extent_file)

    # Edges
    edges = get_edges(extent)
    edges.to_parquet(Path(args.output_dir) / 'edges.pq')

    # Buildings
    buildings = gpd.read_file(args.building_file)
    buildings = preprocess_gobv3_buildings(buildings, extent)

    # Add network ID of closest road to buildings
    buildings['nID'] = mm.get_nearest_street(buildings, edges, max_distance=500)

    buildings.to_parquet(Path(args.output_dir) / 'buildings.pq')

    # Morphological Tessellation
    tess = get_morphological_tessellation(buildings)
    tess.to_parquet(Path(args.output_dir) / 'tessellation.pq')

    # Blocks
    blocks = get_blocks(buildings, tess, edges)
    blocks.to_parquet(Path(args.output_dir) / 'blocks.pq')

    # Add IDs
    buildings = buildings[['uID', 'nID', 'geometry']]
    buildings_with_block_id = gpd.sjoin(buildings, blocks[['bID', 'geometry']], how='left', predicate='within')
    buildings_with_block_id = buildings_with_block_id.drop(columns='index_right')
    buildings_with_block_id.to_parquet(Path(args.output_dir) / 'buildings.pq')

    tess_with_block_id = tess.merge(buildings_with_block_id[['uID', 'bID']], how='left', on='uID')
    tess_with_block_id.to_parquet(Path(args.output_dir) / 'tessellation.pq')