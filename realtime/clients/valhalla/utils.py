from geopandas import GeoDataFrame
from shapely.geometry import Point
from numpy import array, linalg
import pandas as pd


def is_trip_long_enough(
    group: pd.DataFrame,
    min_distance_meters: float = 100.0,
    crs_in: str = "EPSG:4326",
    crs_metric: str = "EPSG:26986",
) -> bool:
    """
    Checks whether the given group of GPS points spans at least `min_distance_meters`
    by computing pairwise distances after reprojecting to a metric CRS.
    """

    # Create GeoDataFrame in WGS84 and reproject to meters
    gdf = GeoDataFrame(
        geometry=[Point(lon, lat) for lon, lat in zip(group["lon"], group["lat"])],
        crs=crs_in,
    ).to_crs(crs_metric)

    if gdf.empty or not gdf.is_valid.all():
        return False

    coords = array([(geom.x, geom.y) for geom in gdf.geometry])
    dist_matrix = linalg.norm(coords[:, None, :] - coords[None, :, :], axis=-1)
    max_distance = dist_matrix.max()

    return max_distance >= min_distance_meters
