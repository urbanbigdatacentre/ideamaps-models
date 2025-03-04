import time
from pathlib import Path
import pandas as pd
import geopandas as gpd
from shapely.ops import nearest_points
from shapely.geometry import LineString
import matplotlib.pyplot as plt
from tqdm.notebook import tqdm
import momepy as mm
import dask.dataframe as dd
import dask_geopandas


if __name__ == '__main__':

    data_path = Path('../data/')
    pilot = 'kano'
    if pilot == 'nairobi':
        utm_epsg = 'EPSG:32737'
    elif pilot == 'lagos':
        utm_epsg = 'EPSG:32631'
    elif pilot == 'kano':
        utm_epsg = 'EPSG:32632'

    # roads = gpd.read_file(data_path / 'road_connectivity' / f'roads_{pilot}.gpkg').to_crs(utm_epsg)
    roads = gpd.read_parquet(data_path / 'road_connectivity' / f'roads_{pilot}.parquet').to_crs(utm_epsg)
    if pilot == 'lagos' or pilot == 'kano':
        roads = roads[['geometry', 'RSC']]
        roads['nID'] = range(len(roads))
        roads['paved'] = roads['RSC'].apply(lambda x: 0 if x == 'Unpaved' else 1)
    elif pilot == 'nairobi':
        roads = roads[['geometry', 'surface']]
        roads['nID'] = range(len(roads))
        roads['paved'] = roads['surface'].apply(lambda x: 0 if x == 'unpaved' else 1)

    print(roads['paved'].value_counts())

    # buildings = gpd.read_file(data_path / 'road_connectivity' / f'buildings_{pilot}.gpkg').to_crs(utm_epsg)
    buildings = gpd.read_parquet(data_path / 'overture' / f'{pilot}_buildings_overture.parquet').to_crs(utm_epsg)
    buildings = buildings[['geometry']]
    buildings['uID'] = range(len(buildings))
    buildings['centroid'] = buildings.geometry.centroid

    buildings['nearest_road'] = mm.get_nearest_street(buildings, roads)
    buildings = buildings.merge(roads[['nID', 'paved']], how='left', left_on='nearest_road', right_index=True)

    out_file = data_path / 'road_connectivity' / f'buildings_{pilot}.parquet'
    buildings[['uID', 'nID', 'paved', 'geometry']].to_parquet(out_file)
    buildings.head()

    buildings = gpd.read_parquet(data_path / 'road_connectivity' / f'buildings_{pilot}.parquet')
    buildings['centroid'] = buildings.geometry.centroid
    buildings.head()

    progress_steps = 100_000
    start_index = None
    if start_index is not None:
        load_file = data_path / 'road_connectivity' / f'nearest_road_progress_{pilot}_{start_index}.parquet'
        nearest_road_points = gpd.read_parquet(load_file)
        nearest_road_points = list(nearest_road_points['nearest_road_point'])
    else:
        # Initialize an empty list to store the counts
        nearest_road_points = []


    # Find the nearest road point for each building
    def get_nearest_road_point(building_centroid, road):
        nearest_point = nearest_points(building_centroid, road.geometry)[1]  # Get nearest point on the road
        return nearest_point


    # Iterate over the 'centroid' column with tqdm for progress tracking
    for i in tqdm(range(len(buildings)), desc="Finding nearest roads"):
        if start_index is not None:
            if i < start_index:
                continue
        building = buildings.iloc[i]
        road = roads.iloc[building['nID']]

        nearest_road_points.append(get_nearest_road_point(building['centroid'], road))

        # Save progress every 10,000 iterations
        if (i + 1) % progress_steps == 0:
            progress = buildings.iloc[:i + 1].copy()
            progress['nearest_road_point'] = nearest_road_points
            progress_file = data_path / 'road_connectivity' / f'nearest_road_progress_{pilot}_{i + 1}.parquet'
            progress.set_geometry('nearest_road_point')[['uID', 'nearest_road_point']].to_parquet(progress_file)
            print(f'Saved progress at iteration {i + 1}')
            prev_progress_file = data_path / 'road_connectivity' / f'nearest_road_progress_{pilot}_{i + 1 - progress_steps}.parquet'
            if prev_progress_file.exists():
                prev_progress_file.unlink()

    # Assign the results back to the DataFrame
    buildings['nearest_road_point'] = nearest_road_points

    # Create a straight line from each building centroid to the closest road point
    buildings['nearest_road_line'] = buildings.apply(
        lambda row: LineString([row['centroid'], row['nearest_road_point']]), axis=1)

    nearest_road = buildings[['uID', 'nearest_road_point']].set_geometry('nearest_road_point').set_crs(utm_epsg)
    nearest_road.to_parquet(data_path / 'road_connectivity' / f'nearest_motorableroad_{pilot}.parquet')

    nearest_road_line = buildings[['uID', 'nearest_road_line']].set_geometry('nearest_road_line').set_crs(utm_epsg)
    nearest_road_line.to_parquet(data_path / 'road_connectivity' / f'line_to_nearest_motorableroad_{pilot}.parquet')

    buildings.head()

    nearest_road_file = data_path / 'road_connectivity' / f'nearest_motorableroad_{pilot}.parquet'
    nearest_road = gpd.read_parquet(nearest_road_file)

    nearest_road_line_file = data_path / 'road_connectivity' / f'line_to_nearest_motorableroad_{pilot}.parquet'
    nearest_road_line = gpd.read_parquet(nearest_road_line_file)

    buildings = buildings.merge(nearest_road, how='left', on='uID').merge(nearest_road_line, how='left', on='uID')
    buildings.head()

    start_index = None
    progress_steps = 10_000
    if start_index is not None:
        load_file = data_path / 'road_connectivity' / f'buildings_in_between_progress_{pilot}_{start_index}.parquet'
        buildings_in_between = gpd.read_parquet(load_file)
        buildings_in_between = list(buildings_in_between['buildings_in_between'])
    else:
        # Initialize an empty list to store the counts
        buildings_in_between = []


    # Count the number of buildings intersecting each line
    def count_intersecting_buildings(line, buildings):
        return buildings[buildings.geometry.intersects(line)].shape[0] - 1  # Exclude itself


    start_time = time.time()
    # Iterate over the 'line_to_road' column with tqdm for progress tracking
    for i, line in enumerate(tqdm(buildings['nearest_road_line'], desc='Counting intersecting buildings')):
        if start_index is not None:
            if i < start_index:
                continue
        buildings_in_between.append(count_intersecting_buildings(line, buildings))

        # Save progress every 10,000 iterations
        if (i + 1) % progress_steps == 0:
            buildings_progress = buildings.iloc[:i + 1].copy()
            buildings_progress['buildings_in_between'] = buildings_in_between
            out_file = data_path / 'road_connectivity' / f'buildings_in_between_progress_{pilot}_{i + 1}.parquet'
            buildings_progress.set_geometry('geometry')[['uID', 'buildings_in_between', 'geometry']].to_parquet(
                out_file)
            print(f'Saved progress at iteration {i + 1}')
            prev_progress_file = data_path / 'road_connectivity' / f'buildings_in_between_progress_{pilot}_{i + 1 - progress_steps}.parquet'
            if prev_progress_file.exists():
                prev_progress_file.unlink()

    end_time = time.time()
    print(f'Execution Time: {end_time - start_time:.2f} seconds')

    # Assign the results back to the DataFrame
    buildings['buildings_in_between'] = buildings_in_between


    # Count the number of buildings intersecting each line
    def count_buildings_dask(row, buildings):
        return buildings[buildings.geometry.intersects(row.nearest_road_line)].shape[0] - 1


    batch_size = 10_000
    start_index = 1_740_000  # add batch size to number in file name

    start_time = time.perf_counter()
    for i_batch in tqdm(range(start_index, len(buildings), batch_size)):

        # ddf = dd.from_pandas(buildings.iloc[i_batch:i_batch + batch_size], npartitions=4)
        ddf = dask_geopandas.from_geopandas(buildings.iloc[i_batch:i_batch + batch_size], npartitions=8)

        ddf['buildings_in_between'] = ddf.map_partitions(
            lambda df: df.apply(lambda row: count_buildings_dask(row, buildings), axis=1))

        # Compute results
        buildings_batch = ddf.compute()
        buildings_batch = buildings_batch[['uID', 'buildings_in_between', 'geometry']]

        out_file = data_path / 'road_connectivity' / f'buildings_in_between_progress_{pilot}_{i_batch}.parquet'
        if i_batch == 0:
            buildings_batch.set_geometry('geometry').to_parquet(out_file)
        else:
            file = data_path / 'road_connectivity' / f'buildings_in_between_progress_{pilot}_{i_batch - batch_size}.parquet'
            buildings_progress = gpd.read_parquet(file)
            buildings_progress = pd.concat([buildings_progress, buildings_batch])
            buildings_progress.set_geometry('geometry').to_parquet(out_file)
            file.unlink()
        # print(f'Saved batch {i_batch}-{i_batch + batch_size}.')

    end_time = time.perf_counter()
    print(f'Execution Time: {end_time - start_time:.2f} seconds')

    buildings['nearest_road_distance'] = buildings['nearest_road_line'].length
    buildings.head()

    # Display the results
    out_file = data_path / 'road_connectivity' / f'rcbi_motorableroads_{pilot}.parquet'
    buildings.set_geometry('geometry')[
    ['uID', 'nID', 'buildings_in_between', 'nearest_road_distance', 'paved', 'geometry']].to_parquet(out_file)

    # Aggregation
    buildings = gpd.read_parquet(data_path / 'road_connectivity' / 'in_between_buildings_nairobi.parquet')
    grid_file = data_path / 'grid' / '100mGrid_Nairobi_Mollweide.gpkg'
    grid = gpd.read_file(grid_file)
    grid['grid_id'] = range(len(grid))

    buildings = buildings.to_crs(grid.crs)

    grid.head()

    grid = gpd.sjoin(grid, buildings, how='inner', predicate='intersects')

    # handle missing data
    has_missing_values = grid.isnull().values.any()
    print(has_missing_values)
    grid = grid.dropna()

    merge_stats = grid.groupby('grid_id')[['buildings_in_between']].median().add_prefix('md_')

    # Perform Spatial Join
    df_stats = pd.merge(grid, merge_stats, on='grid_id', how='inner')
    gdf_stats = gpd.GeoDataFrame(df_stats, geometry='geometry', crs=grid.crs)
    gdf_stats.head()

    gdf_stats.set_geometry('geometry')[['grid_id', 'md_buildings_in_between', 'geometry']].to_parquet(out_file)