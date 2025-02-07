from geopandas import GeoDataFrame
import osmnx as ox

# Download road network from OpenStreetMap
def get_edges(extent: GeoDataFrame) -> GeoDataFrame:
    extent = extent.to_crs(4326)
    extent = extent.unary_union

    # Get OSM roads for pilot site
    G = ox.graph_from_polygon(extent, network_type='all')
    edges = ox.graph_to_gdfs(G, nodes=False, edges=True, node_geometry=False, fill_edge_geometry=True)

    edges = edges[['highway', 'geometry']]
    edges['highway'] = edges['highway'].astype(str)

    return edges