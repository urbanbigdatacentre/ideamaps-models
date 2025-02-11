import geopandas as gpd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from pathlib import Path
import argparse


def argument_parser():
    # https://docs.python.org/3/library/argparse.html#the-add-argument-method
    parser = argparse.ArgumentParser(description="Experiment Args")
    parser.add_argument('-m', "--morphometrics-file", dest='morphometrics_file', required=True)
    parser.add_argument('-o', "--output-dir", dest='output_dir', default='outputs/', required=False,
                        help="path to output directory")
    parser.add_argument('-s', "--seed", dest='seed', default=7, required=False, help="seed for clustering")

    parser.add_argument(
        "opts",
        help="Modify config options using the command-line",
        default=None,
        nargs=argparse.REMAINDER,
    )
    return parser


if __name__ == '__main__':
    args = argument_parser().parse_known_args()[0]

    mm_file = Path(args.morphometrics_file)
    gdf = gpd.read_parquet(mm_file) if mm_file.suffix == '.parquet' else gpd.read_file(mm_file)
    print(gdf.columns)
    gdf.head()
    #TODO: only cluster cells with buildings

    morph_isl = ['md_ssbCCD', 'md_mtbAli', 'md_ltcBuA', 'md_mtcWNe', 'md_ltcWRB', 'sd_stbOri', 'sd_stcOri']

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
        km = KMeans(n_clusters=k, random_state=int(args.seed))
        km = km.fit(data_isl)
        ssd.append(km.inertia_)
        gdf[f'isl_c{k}'] = km.labels_


    # elbo Small, Dense Structures
    # Calculating sum of squared distances for k in range 1 to 20
    ssd = []
    for k in [6, 8, 10]:
        km = KMeans(n_clusters=k, random_state=int(args.seed))
        km = km.fit(data_sds)
        ssd.append(km.inertia_)
        gdf[f'sds_c{k}'] = km.labels_

    gdf.to_parquet(Path(args.output_dir) / 'clustering.parquet')

