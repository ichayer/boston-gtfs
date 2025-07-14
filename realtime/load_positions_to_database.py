from clients.mbta.mbta_client import MBTAClient
from clients.postgres.postgres_client import PostgresClient


if __name__ == "__main__":

    # Initialize the client with the GTFS-RT protobuf URL
    client = MBTAClient(
        vehicle_protobuf_url="https://cdn.mbta.com/realtime/VehiclePositions.pb"
    )
    df = client.collect_by_duration(duration_minutes=190, interval_seconds=15)

    # Save retrieved data to CSV
    df.to_csv("vehicle_positions.csv", index=False)

    postgres_client = PostgresClient(
        db_user="postgres",
        db_pass="postgres",
        db_host="localhost",
        db_port="5432",
        db_name="mbtagtfs",
    )

    # Load data into PostgreSQL database
    df.to_sql(
        "vehicle_positions", postgres_client.engine, if_exists="replace", index=False
    )
