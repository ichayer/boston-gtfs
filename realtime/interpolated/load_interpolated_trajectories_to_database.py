from typing import List
from pandas import DataFrame
from realtime.clients.postgres.postgres_client import PostgresClient
from realtime.clients.valhalla.valhalla_client import ValhallaClient
from realtime.clients.valhalla.models.measure_with_time import MeasureWithTime
from realtime.clients.valhalla.models.costing import Costing
from realtime.clients.valhalla.models.shape_match import ShapeMatch
from realtime.clients.valhalla.models.directions import Directions
from realtime.clients.valhalla.models.options import Options
from realtime.clients.valhalla.models.osrm_response import OSRMResponse
from realtime.clients.valhalla.interpolation import assign_timestamps_to_linestring
from realtime.clients.valhalla.models.tgeompoint import TGeomPoint
from realtime.clients.valhalla.utils import is_trip_long_enough

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
          AND trip_id NOT IN (
              SELECT trip_id FROM map_matched_bus_trips
          )
        """
    )

    grouped_points = points.groupby("trip_id")
    total_trips = len(grouped_points)
    successfully_processed = 0
    for i, (trip_id, group) in enumerate(grouped_points):
        vehicle_id = group["vehicle_id"].iloc[0]

        print(
            f"Processing trip {i + 1}/{total_trips}: {trip_id} for vehicle {vehicle_id}"
        )

        if not is_trip_long_enough(group, min_distance_meters=100.0):
            print(f"Skipped trip {trip_id} (too short)\n")
            continue

        measures: List[MeasureWithTime] = [
            MeasureWithTime(lon=row["lon"], lat=row["lat"], time=row["time"])
            for _, row in group.iterrows()
        ]

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

        if len(output.tracepoints) != len(measures):
            print(f"Skipped trip {trip_id} (tracepoints count mismatch)\n")
            continue

        try:
            interpolated: List[TGeomPoint] = assign_timestamps_to_linestring(
                anchor_points=output.tracepoints,
                anchor_times=group["time"].astype(int).tolist(),
                linestring=output.geometry,
            )
        except Exception as e:
            print(f"Interpolation failed for trip {trip_id}: {e}\n")
            continue

        try:
            postgres_client.execute(
                sql="""
                INSERT INTO map_matched_bus_trips (trip_id, vehicle_id, trip)
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
