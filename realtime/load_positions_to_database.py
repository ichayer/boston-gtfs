from sqlalchemy import create_engine
from clients.mbta.mbta_client import MBTAClient


if __name__ == "__main__":

    # Initialize the client with the GTFS-RT protobuf URL
    client = MBTAClient(
        vehicle_protobuf_url="https://cdn.mbta.com/realtime/VehiclePositions.pb"
    )
    df = client.collect_by_duration(duration_minutes=190, interval_seconds=15)

    # Save retrieved data to CSV
    df.to_csv("vehicle_positions.csv", index=False)

    # Load data into PostgreSQL database
    engine = create_engine("postgresql://postgres:postgres@localhost:5432/mbtagtfs")
    df.to_sql("vehicle_positions", engine, if_exists="replace", index=False)
