import utm
from geopandas import GeoDataFrame


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
