import json
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


def fetch_gtfs_realtime_data(url: str):
    feed = gtfs_realtime_pb2.FeedMessage()

    try:
        response = requests.get(
            url,
            verify=True,
        )

        response.raise_for_status()

        feed.ParseFromString(response.content)

    except requests.exceptions.RequestException as e:
        raise ReferenceError(f"Error fetching GTFS-RT data: {e}")

    if not feed or not feed.entity:
        raise ReferenceError(f"No data received from GTFS-RT feed. URL: {url}.")

    return feed


if __name__ == "__main__":

    feed = fetch_gtfs_realtime_data(
        url="https://api.entur.io/realtime/v1/gtfs-rt/vehicle-positions"
    )

    vehicle_positions = extract_vehicle_positions(feed)

    with open("vehicle_positions.json", "w") as f:
        json.dump(vehicle_positions, f, indent=4)

    print(f"Extracted {len(vehicle_positions)} vehicle positions.")
