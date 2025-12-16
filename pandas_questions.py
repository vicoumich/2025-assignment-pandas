"""Plotting referendum results in pandas.

In short, we want to make beautiful map to report results of a referendum. In
some way, we would like to depict results with something similar to the maps
that you can find here:
https://github.com/x-datascience-datacamp/datacamp-assignment-pandas/blob/main/example_map.png

To do that, you will load the data as pandas.DataFrame, merge the info and
aggregate them by regions and finally plot them on a map using `geopandas`.
"""
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt


def load_data():
    """Load data from the CSV files referundum/regions/departments."""
    import os
    current_dir = os.getcwd()
    data_dir = os.path.join(current_dir, 'data')
    referendum_path = os.path.join(data_dir, "referendum.csv")
    regions_path = os.path.join(data_dir, "regions.csv")
    departments_path = os.path.join(data_dir, "departments.csv")

    referendum = pd.read_csv(
        referendum_path, sep=';',
        dtype={"Department code": str, "Town code": str})
    regions = pd.read_csv(regions_path, sep=",", dtype={"code": str})
    departments = pd.read_csv(
        departments_path, sep=",",
        dtype={"code": str, "region_code": str})

    return referendum, regions, departments


def merge_regions_and_departments(
        regions: pd.DataFrame,
        departments: pd.DataFrame):
    """Merge regions and departments in one DataFrame.

    The columns in the final DataFrame should be:
    ['code_reg', 'name_reg', 'code_dep', 'name_dep']
    """
    merged = pd.merge(
        departments, regions,
        left_on='region_code', right_on='code',
        how='inner')

    return merged.rename(columns={
        "code_x": "code_dep",
        "name_x": "name_dep",
        "code_y": "code_reg",
        "name_y": "name_reg",
    })[["code_reg", "name_reg", "code_dep", "name_dep"]]


def merge_referendum_and_areas(
        referendum: pd.DataFrame,
        regions_and_departments: pd.DataFrame):
    """Merge referendum and regions_and_departments in one DataFrame.

    You can drop the lines relative to DOM-TOM-COM departments, and the
    french living abroad, which all have a code that contains `Z`.

    DOM-TOM-COM departments are departements that are remote from metropolitan
    France, like Guadaloupe, Reunion, or Tahiti.
    """
    ref = referendum[~referendum["Department code"].str.contains("Z")].copy()

    def normalize_dep_code(code):
        s = str(code)
        if s in ["2A", "2B"]:
            return s
        if s.isdigit():
            return f"{int(s):02d}"
        return s

    ref["code_dep"] = ref["Department code"].map(normalize_dep_code)

    merged = regions_and_departments.merge(ref, on="code_dep", how="inner")

    return merged


def compute_referendum_result_by_regions(referendum_and_areas: pd.DataFrame):
    """Return a table with the absolute count for each region.

    The return DataFrame should be indexed by `code_reg` and have columns:
    ['name_reg', 'Registered', 'Abstentions', 'Null', 'Choice A', 'Choice B']
    """
    result = (
        referendum_and_areas
        .groupby("code_reg", as_index=True)
        .agg({
            "name_reg": "first",
            "Registered": "sum",
            "Abstentions": "sum",
            "Null": "sum",
            "Choice A": "sum",
            "Choice B": "sum",
        })
    )
    return result


def plot_referendum_map(referendum_result_by_regions):
    """Plot a map with the results from the referendum.

    * Load the geographic data with geopandas from `regions.geojson`.
    * Merge these info into `referendum_result_by_regions`.
    * Use the method `GeoDataFrame.plot` to display the result map. The results
      should display the rate of 'Choice A' over all expressed ballots.
    * Return a gpd.GeoDataFrame with a column 'ratio' containing the results.
    """

    import os

    current_dir = os.getcwd()
    data_dir = os.path.join(current_dir, "data")
    regions_geo_path = os.path.join(data_dir, "regions.geojson")

    regions_geo = gpd.read_file(regions_geo_path)

    df = referendum_result_by_regions.reset_index()

    gdf = regions_geo.merge(
        df, left_on="code",
        right_on="code_reg", how="left")

    expressed = gdf["Choice A"] + gdf["Choice B"]
    gdf["ratio"] = gdf["Choice A"] / expressed

    gdf.plot(column="ratio", legend=True)
    plt.tight_layout()

    return gdf


if __name__ == "__main__":

    referendum, df_reg, df_dep = load_data()
    regions_and_departments = merge_regions_and_departments(
        df_reg, df_dep
    )
    referendum_and_areas = merge_referendum_and_areas(
        referendum, regions_and_departments
    )
    print(referendum_and_areas.shape)
    referendum_results = compute_referendum_result_by_regions(
        referendum_and_areas
    )
    print(referendum_results)

    plot_referendum_map(referendum_results)
    plt.show()
