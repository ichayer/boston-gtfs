import time
import requests
import pandas as pd
from models.vehicle import Vehicle
from google.transit.gtfs_realtime_pb2 import FeedMessage
from email.utils import format_datetime, parsedate_to_datetime


class VehicleDataCollector:

    def __init__(self, vehicle_protobuf_url: str):
        self.url = vehicle_protobuf_url
        self.last_modified = None

    def collect_by_duration(
        self, duration_minutes: int, interval_seconds: int
    ) -> pd.DataFrame:
        collected_data = []
        start_time = time.time()
        end_time = time.time() + duration_minutes * 60
        iteration = 0

        while time.time() < end_time:
            feed = self._fetch_feed()

            if feed:
                vehicles = Vehicle.from_feed(feed)
                collected_data.extend([v.to_dict() for v in vehicles])

            now = time.time()
            elapsed = now - start_time
            remaining = max(0, end_time - now)
            iteration += 1
            print(
                f"[Iteration {iteration}] Collected {len(collected_data)} vehicle positions "
                f"| Elapsed: {elapsed:.1f}s | Remaining: {remaining:.1f}s"
            )

            time.sleep(interval_seconds)

        return pd.DataFrame(collected_data)

    def _fetch_feed(self) -> FeedMessage | None:
        headers = {}
        if self.last_modified:
            headers["If-Modified-Since"] = format_datetime(self.last_modified)

        try:
            response = requests.get(url=self.url, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            raise ReferenceError(f"Error fetching GTFS-RT feed: {e}")

        if response.status_code == 304:
            print(
                f"Feed not modified since last fetch {self.last_modified}. Skipping fetch."
            )
            return None

        print("Feed updated. Parsing protobuf data.")
        feed = FeedMessage()
        feed.ParseFromString(response.content)

        if not feed or not feed.entity:
            raise ReferenceError("No entities found in GTFS-RT feed")

        if "Last-Modified" in response.headers:
            self.last_modified = parsedate_to_datetime(
                response.headers["Last-Modified"]
            )

        return feed
