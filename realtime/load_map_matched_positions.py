from typing import List
from pandas import DataFrame
from clients.postgres.postgres_client import PostgresClient
from clients.valhalla.valhalla_client import ValhallaClient
from clients.valhalla.models.measure_with_time import MeasureWithTime
from clients.valhalla.models.costing import Costing
from clients.valhalla.models.shape_match import ShapeMatch
from clients.valhalla.models.directions import Directions
from clients.valhalla.models.options import Options


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
            longitude AS lon,
            latitude AS lat,
            timestamp AS time
        FROM cleaned_vehicle_positions_filtered
        WHERE trip_id = '69980293'
          AND vehicle_id = 'y3303'
    """
    )

    measures: List[MeasureWithTime] = [
        MeasureWithTime(lon=row["lon"], lat=row["lat"], time=row["time"])
        for _, row in points.iterrows()
    ]

    output: dict = valhalla_client.trace_route(
        measures=measures,
        costing=Costing.BUS,
        shape_match=ShapeMatch.MAP_SNAP,
        directions=Directions().set_format("osrm"),
        options=Options().set_search_radius(10).set_use_timestamps(True),
    )

    print("Response from Valhalla trace_route:", output)
