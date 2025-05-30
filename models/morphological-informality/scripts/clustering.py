import geopandas as gpd
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, RobustScaler
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
    output_dir = Path(args.output_dir)
    assert output_dir.exists()

    mm_file = Path(args.morphometrics_file)
    gdf = gpd.read_parquet(mm_file) if mm_file.suffix == '.parquet' else gpd.read_file(mm_file)
    print(gdf.isna().sum())
    gdf = gdf.fillna(0)

    morph_isl = ['kdes_stbOri', 'md_mtbAli', 'kdes_stcOri', 'kdes_strOri', 'md_strAli']
    morph_sds = ['sum_sdbAre', 'bcount', 'md_sdbAre', 'md_mtbNDi_log', 'md_sicCAR', 'md_mtcWNe']

    criterion = gdf['bcount'] >= 3
    gdf_train = gdf[criterion]
    gdf_isl = gdf_train[morph_isl]
    gdf_sds = gdf_train[morph_sds]

    # Initialize the StandardScaler object
    scaler = StandardScaler()

    # Scale the data
    data_isl = scaler.fit_transform(gdf_isl)
    data_sds = scaler.fit_transform(gdf_sds)

    # Define cluster values
    cluster_range = range(1, 16)
    cluster_selection = [6, 8, 10, 12, 14]

    # Storage for SSD
    ssd_isl = []
    ssd_sds = []

    # Loop through different cluster values
    for k in cluster_range:
        # Irregular Layout
        km_isl = KMeans(n_clusters=k, random_state=int(args.seed))
        km_isl = km_isl.fit(data_isl)
        ssd_isl.append(km_isl.inertia_)
        if k in cluster_selection:
            gdf[f'isl_c{k}'] = -1
            gdf.loc[criterion, f'isl_c{k}'] = km_isl.labels_
            # Save centroids as CSV
            centroids_isl = pd.DataFrame(km_isl.cluster_centers_, columns=gdf_isl.columns)
            centroids_isl.to_csv(output_dir / f'centroids_isl_k{k}.csv', index=False)

        # Small, Dense Structures
        km_sds = KMeans(n_clusters=k, random_state=int(args.seed))
        km_sds = km_sds.fit(data_sds)
        ssd_sds.append(km_sds.inertia_)
        if k in cluster_selection:
            gdf[f'sds_c{k}'] = -1
            gdf.loc[criterion, f'sds_c{k}'] = km_sds.labels_
            # Save centroids as CSV
            centroids_sds = pd.DataFrame(km_sds.cluster_centers_, columns=gdf_sds.columns)
            centroids_sds.to_csv(output_dir / f'centroids_sds_k{k}.csv', index=False)

    # Plot the elbow curves
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Irregular Layout
    axes[0].plot(cluster_range, ssd_isl, marker='o', linestyle='-')
    axes[0].set_title("Elbow Plot - Irregular Layout")
    axes[0].set_xlabel("Number of Clusters (k)")
    axes[0].set_ylabel("Sum of Squared Distances (SSD)")

    # Small, Dense Structures
    axes[1].plot(cluster_range, ssd_sds, marker='o', linestyle='-')
    axes[1].set_title("Elbow Plot - Small, Dense Structures")
    axes[1].set_xlabel("Number of Clusters (k)")
    axes[1].set_ylabel("Sum of Squared Distances (SSD)")
    plt.savefig(Path(args.output_dir) / 'elbow.png', dpi=300, bbox_inches='tight')

    gdf.to_parquet(Path(args.output_dir) / 'clusters.parquet')

