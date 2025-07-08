import os
import json
from dotenv import find_dotenv, load_dotenv
from google.transit import gtfs_realtime_pb2
import requests


def extract_vehicle_positions(feed):
    vehicle_positions = []
    for entity in feed.entity:
        if entity.HasField("vehicle"):
            vehicle = entity.vehicle
            vehicle_positions.append(
                {
                    "id": entity.id,
                    "trip_id": vehicle.trip.trip_id,
                    "schedule_relationship": vehicle.trip.schedule_relationship,
                    "latitude": vehicle.position.latitude,
                    "longitude": vehicle.position.longitude,
                    "bearing": vehicle.position.bearing,
                    "speed": vehicle.position.speed * 3.6,  # Speed in km/h
                    "current_status": vehicle.current_status,
                    "timestamp": vehicle.timestamp,
                    "stop_id": vehicle.stop_id,
                    "vehicle_id": vehicle.vehicle.id,
                    "vehicle_label": vehicle.vehicle.label,
                    "vehicle_license_plate": vehicle.vehicle.license_plate,
                }
            )
    return vehicle_positions


def fetch_gtfs_realtime_data(url):
    feed = gtfs_realtime_pb2.FeedMessage()

    try:
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {os.getenv('OPEN_DATA_TOKEN')}"},
            verify=False,
        )

        response.raise_for_status()

        feed.ParseFromString(response.content)

    except requests.exceptions.RequestException as e:
        raise ReferenceError(f"Error fetching GTFS-RT data: {e}")
    return feed


if __name__ == "__main__":

    dotenv_path = find_dotenv()

    if not dotenv_path:
        print(
            "Error: .env file not found. Please create a .env file with the required configuration using env-sample as template."
        )
        exit(1)

    load_dotenv(dotenv_path)

    feed = fetch_gtfs_realtime_data(
        url="https://api.opentransportdata.swiss/la/gtfs-rt/vehiclepositions.pb"
    )
    if feed:
        print("GTFS-RT data fetched successfully.")
        vehicle_positions = extract_vehicle_positions(feed)
        print(f"Extracted {len(vehicle_positions)} vehicle positions.")
    else:
        print("Failed to fetch GTFS-RT data.")
