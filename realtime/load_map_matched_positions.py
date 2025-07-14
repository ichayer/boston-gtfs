from typing import List
from folium import Map, PolyLine, FeatureGroup, LayerControl
from geopandas import GeoDataFrame
from pandas import DataFrame
from shapely import Point
from clients.postgres.postgres_client import PostgresClient
from clients.valhalla.valhalla_client import ValhallaClient
from clients.valhalla.models.measure_with_time import MeasureWithTime
from clients.valhalla.models.costing import Costing
from clients.valhalla.models.shape_match import ShapeMatch
from clients.valhalla.models.directions import Directions
from clients.valhalla.models.options import Options
from clients.valhalla.models.osrm_response import OSRMResponse

if __name__ == "__main__":

    postgres_client = PostgresClient(
        db_user="postgres",
        db_pass="postgres",
        db_host="localhost",
        db_port="5432",
        db_name="mbtagtfs",
    )

    valhalla_client = ValhallaClient(base_url="http://valhalla1.openstreetmap.de")

    vehicle_id = "y3303"
    trip_id = "69980293"

    points: DataFrame = postgres_client.query(
        sql=f"""
        SELECT
            longitude AS lon,
            latitude AS lat,
            timestamp AS time
        FROM cleaned_vehicle_positions_filtered
        WHERE trip_id = '{trip_id}'
          AND vehicle_id = '{vehicle_id}'
    """
    )

    measures: List[MeasureWithTime] = [
        MeasureWithTime(lon=row["lon"], lat=row["lat"], time=row["time"])
        for _, row in points.iterrows()
    ]

    output: OSRMResponse = valhalla_client.trace_route(
        measures=measures,
        costing=Costing.BUS,
        shape_match=ShapeMatch.MAP_SNAP,
        directions=Directions().set_format("osrm"),
        options=Options().set_search_radius(100).set_use_timestamps(True),
    )

    m = Map(location=[42.3601, -71.0589], tiles="CartoDB positron", zoom_start=12)

    query = f"""
    SELECT trip_id, trajectory
    FROM raw_actual_trips
    WHERE ST_GeometryType(trajectory) = 'ST_LineString' AND trip_id = '{trip_id}' AND vehicle_id = '{vehicle_id}'
    """
    gdf = postgres_client.query_geodataframe(query, geom_col="trajectory")
    gdf = gdf.to_crs(epsg=4326)
    for _, row in gdf.iterrows():
        coords = [(lat, lon) for lon, lat in row.trajectory.coords]
        PolyLine(coords, color="blue", weight=2, opacity=0.6, popup=row.trip_id).add_to(
            m
        )

    gdf_matched = GeoDataFrame(geometry=[output.geometry], crs="EPSG:4326")
    for _, row in gdf_matched.iterrows():
        coords = [(lat, lon) for lon, lat in row.geometry.coords]
        PolyLine(
            coords,
            color="red",
            weight=2,
            opacity=0.6,
            popup=f"Matched trajectory for {vehicle_id} on trip {trip_id}",
        ).add_to(m)

    m.save("map_matched_vs_original.html")
