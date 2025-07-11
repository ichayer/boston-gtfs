import time
import requests
import pandas as pd
from google.transit.gtfs_realtime_pb2 import FeedMessage
from models.vehicle import Vehicle


class VehicleDataCollector:

    def __init__(self, vehicle_protobuf_url: str):
        self.url = vehicle_protobuf_url

    def collect_by_duration(
        self, duration_minutes: int, interval_seconds: int
    ) -> pd.DataFrame:
        collected_data = []
        end_time = time.time() + duration_minutes * 60

        while time.time() < end_time:
            feed = self._fetch_feed()
            vehicles = Vehicle.from_feed(feed)
            collected_data.extend([v.to_dict() for v in vehicles])
            time.sleep(interval_seconds)

        return pd.DataFrame(collected_data)

    def collect_by_changes(
        self, max_changes: int, interval_seconds: int
    ) -> pd.DataFrame:
        collected_data = []
        seen_timestamps = set()

        while len(seen_timestamps) < max_changes:
            feed = self._fetch_feed()
            ts = feed.header.timestamp

            if ts not in seen_timestamps:
                seen_timestamps.add(ts)
                vehicles = Vehicle.from_feed(feed)
                collected_data.extend([v.to_dict() for v in vehicles])
            time.sleep(interval_seconds)

        return pd.DataFrame(collected_data)

    def _fetch_feed(self) -> FeedMessage:
        feed = FeedMessage()
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            feed.ParseFromString(response.content)
        except requests.exceptions.RequestException as e:
            raise ReferenceError(f"Error fetching GTFS-RT data: {e}")

        if not feed or not feed.entity:
            raise ReferenceError("Empty or invalid GTFS-RT feed received.")
        return feed
