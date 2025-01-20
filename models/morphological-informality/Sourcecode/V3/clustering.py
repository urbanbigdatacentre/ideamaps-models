import geopandas as gpd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from pathlib import Path

from parsers import clustering_parser as argument_parser

SEED = 7

if __name__ == '__main__':
    args = argument_parser().parse_known_args()[0]

    gdf = gpd.read_parquet(args.morphometrics_file)
    print(gdf.columns)
    gdf.head()
    #TODO: only cluster cells with buildings

    #TODO: add md_ltcWRB
    morph_isl = ['md_ssbCCD', 'md_mtbAli', 'md_ltcBuA', 'md_mtcWNe', 'md_ltcWRB', 'sd_stbOri', 'sd_stcOri']

    #TODO add md_ltcWRB and md_ltbIBD
    morph_sds = ['md_sdcAre', 'md_ssbElo', 'md_mtbNDi', 'md_ltbIBD', 'md_ltcBuA', 'md_sdbAre', 'md_sscERI', 'md_sicCAR',
                 'md_mtcWNe', 'md_mdcAre', 'md_ltcWRB', 'sum_sdcAre']

    gdf_isl = gdf[morph_isl]
    gdf_sds = gdf[morph_sds]

    # Initialize the StandardScaler object
    scaler = StandardScaler()

    # Scale the data by standardizing features
    # by removing the mean and scaling to unit variance
    data_isl = scaler.fit_transform(gdf_isl)
    data_sds = scaler.fit_transform(gdf_sds)

    # elbo Irregular Layout
    # Calculating sum of squared distances for k in range 1 to 20
    ssd = []
    for k in [6, 8, 10]:
        km = KMeans(n_clusters=k, random_state=SEED)
        km = km.fit(data_isl)
        ssd.append(km.inertia_)
        gdf[f'isl_c{k}'] = km.labels_



    # elbo Small, Dense Structures
    # Calculating sum of squared distances for k in range 1 to 20
    ssd = []
    for k in [6, 8, 10]:
        km = KMeans(n_clusters=k, random_state=SEED)
        km = km.fit(data_sds)
        ssd.append(km.inertia_)
        gdf[f'sds_c{k}'] = km.labels_

    gdf.to_parquet(Path(args.output_dir) / 'clustering.pq')

