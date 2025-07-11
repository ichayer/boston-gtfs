from dataclasses import asdict, dataclass
from typing import Optional, List
from google.transit.gtfs_realtime_pb2 import FeedMessage


@dataclass
class Vehicle:
    id: str
    trip_id: Optional[str]
    schedule_relationship: Optional[int]
    latitude: float
    longitude: float
    bearing: Optional[float]
    speed_kmh: Optional[float]
    current_status: Optional[int]
    timestamp: Optional[int]
    stop_id: Optional[str]
    vehicle_id: Optional[str]
    vehicle_label: Optional[str]
    vehicle_license_plate: Optional[str]
    congestion_level: Optional[int] = None
    occupancy_status: Optional[int] = None

    @classmethod
    def from_feed(cls, feed: FeedMessage) -> List["Vehicle"]:
        vehicles = []
        for entity in feed.entity:
            if entity.HasField("vehicle"):
                vehicle = entity.vehicle
                vehicle = cls(
                    id=entity.id,
                    trip_id=vehicle.trip.trip_id,
                    schedule_relationship=vehicle.trip.schedule_relationship,
                    latitude=vehicle.position.latitude,
                    longitude=vehicle.position.longitude,
                    bearing=vehicle.position.bearing,
                    speed_kmh=vehicle.position.speed * 3.6,
                    current_status=vehicle.current_status,
                    timestamp=vehicle.timestamp,
                    stop_id=vehicle.stop_id,
                    vehicle_id=vehicle.vehicle.id,
                    vehicle_label=vehicle.vehicle.label,
                    vehicle_license_plate=vehicle.vehicle.license_plate,
                )
                vehicles.append(vehicle)
        return vehicles

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}
