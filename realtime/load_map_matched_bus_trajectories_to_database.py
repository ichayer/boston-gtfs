from numpy import array, linalg
from typing import List
from geopandas import GeoDataFrame
from pandas import DataFrame
from shapely import LineString, Point
from clients.postgres.postgres_client import PostgresClient
from clients.valhalla.valhalla_client import ValhallaClient
from clients.valhalla.models.measure_with_time import MeasureWithTime
from clients.valhalla.models.costing import Costing
from clients.valhalla.models.shape_match import ShapeMatch
from clients.valhalla.models.directions import Directions
from clients.valhalla.models.options import Options
from clients.valhalla.models.osrm_response import OSRMResponse
from clients.valhalla.interpolation import assign_timestamps_to_linestring
from clients.valhalla.models.tgeompoint import TGeomPoint

if __name__ == "__main__":

    postgres_client = PostgresClient(
        db_user="postgres",
        db_pass="postgres",
        db_host="localhost",
        db_port="5432",
        db_name="mbtagtfs",
    )

    valhalla_client = ValhallaClient(base_url="http://valhalla1.openstreetmap.de")

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
    successfully_processed = 0
    for i, (trip_id, group) in enumerate(grouped_points):
        vehicle_id = group["vehicle_id"].iloc[0]

        print(
            f"Processing trip {i + 1}/{total_trips}: {trip_id} for vehicle {vehicle_id}"
        )
        gdf = GeoDataFrame(
            geometry=[Point(lon, lat) for lon, lat in zip(group["lon"], group["lat"])],
            crs="EPSG:4326",
        ).to_crs(epsg=26986)

        if gdf.empty or not gdf.is_valid.all():
            print(f"Skipped trip {trip_id} (invalid geometry)\n")
            continue

        # Calculate the maximum distance between points
        coords = array([(geom.x, geom.y) for geom in gdf.geometry])
        dist_matrix = linalg.norm(coords[:, None, :] - coords[None, :, :], axis=-1)
        max_distance_meters = dist_matrix.max()

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
                .set_search_radius(100)
                .set_turn_penalty_factor(10000)
                .set_use_timestamps(True),
                parse_tracepoint=True,
            )
        except Exception as e:
            print(f"Error processing trip {trip_id}: {e}\n")
            continue

        adjusted_points: List[Point] = output.tracepoints
        adjusted_geometry: LineString = output.geometry
        if len(adjusted_points) != len(measures):
            print(f"Skipped trip {trip_id} (tracepoints count mismatch)\n")
            continue

        # Fix topology and remove noise using DP
        try:
            cleaned_geom = adjusted_geometry.buffer(0)
            simplified_geom = cleaned_geom.simplify(1e-6, preserve_topology=True)
            if not isinstance(simplified_geom, LineString):
                raise ValueError("Geometry still invalid after cleaning.")
        except Exception as e:
            print(f"Cleaning failed for trip {trip_id}: {e}")
            continue

        try:
            interpolated: List[TGeomPoint] = assign_timestamps_to_linestring(
                anchor_points=adjusted_points,
                anchor_times=group["time"].astype(int).tolist(),
                geometry=simplified_geom,
            )
        except Exception as e:
            print(f"Interpolation failed for trip {trip_id}: {e}\n")
            continue

        try:
            postgres_client.execute(
                sql="""
                INSERT INTO map_matched_bus_trips_2 (trip_id, vehicle_id, trip)
                VALUES (:trip_id, :vehicle_id, tgeompoint :trip)
                """,
                params={
                    "trip_id": trip_id,
                    "vehicle_id": vehicle_id,
                    "trip": f"SRID=4326; [{','.join([str(tgp) for tgp in interpolated])}]",
                },
            )
        except Exception as e:
            print(f"Failed to insert trip {trip_id}: {e}\n")
            continue

        successfully_processed += 1
        print(
            f"Successfully processed trip {trip_id} ({successfully_processed}/{total_trips})\n"
        )

    print(f"Successfully processed {successfully_processed}/{total_trips} trips")
