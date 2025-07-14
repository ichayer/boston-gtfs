from numpy import array, linalg
from typing import List
from folium import Map, PolyLine
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

    m = Map(location=[42.3601, -71.0589], tiles="CartoDB positron", zoom_start=12)

    # Query to get all trips with route_type = bus
    points: DataFrame = postgres_client.query(
        sql="""
        SELECT
            trip_id AS trip_id,
            vehicle_id AS vehicle_id,
            longitude AS lon,
            latitude AS lat,
            timestamp AS time
        FROM cleaned_vehicle_positions_filtered cvpf
        WHERE route_type = '3'
    """
    )

    grouped_points = points.groupby("trip_id")
    total_trips = len(grouped_points)

    max_distance_between_points = 100  # meters
    for i, (trip_id, group) in enumerate(grouped_points):
        vehicle_id = group["vehicle_id"].iloc[0]

        print(
            f"Processing trip {i + 1}/{total_trips}: {trip_id} for vehicle {vehicle_id}"
        )
        gdf = GeoDataFrame(
            geometry=[Point(lon, lat) for lon, lat in zip(group["lon"], group["lat"])],
            crs="EPSG:4326",
        ).to_crs(
            epsg=26986
        )  # feet projection

        if gdf.empty or not gdf.is_valid.all():
            print(f"Skipped trip {trip_id} (invalid geometry)\n")
            continue

        # Calculate the maximum distance between points
        coords = array([(geom.x, geom.y) for geom in gdf.geometry])
        dist_matrix = linalg.norm(coords[:, None, :] - coords[None, :, :], axis=-1)
        max_distance_feet = dist_matrix.max()
        max_distance_meters = max_distance_feet * 0.3048

        if max_distance_meters < max_distance_between_points:
            print(
                f"Skipped trip {trip_id} (too short {max_distance_meters:.2f} meters)\n"
            )
            continue

        measures: List[MeasureWithTime] = [
            MeasureWithTime(lon=row["lon"], lat=row["lat"], time=row["time"])
            for _, row in group.iterrows()
        ]

        if len(measures) < 2:
            print(
                f"Skipped trip {trip_id} (not enough points to process with Valhalla)\n"
            )
            continue

        try:
            output: OSRMResponse = valhalla_client.trace_route(
                measures=measures,
                costing=Costing.BUS,
                shape_match=ShapeMatch.MAP_SNAP,
                directions=Directions().set_format("osrm"),
                options=Options()
                .set_search_radius(max_distance_between_points)
                .set_use_timestamps(True),
            )
        except Exception as e:
            print(f"Error processing trip {trip_id}: {e}\n")
            continue

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

        print(f"Processed trip {trip_id} successfully\n")

    m.save("bus_map_matched_geometries.html")
