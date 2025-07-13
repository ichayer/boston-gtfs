from dataclasses import dataclass


# https://github.com/valhalla/valhalla/blob/master/docs/docs/api/map-matching/api-reference.md#trace-route-action
@dataclass
class Measure:
    lat: str
    lon: str

    def __post_init__(self):
        if not (-90 <= float(self.lat) <= 90):
            raise ValueError("Latitude must be between -90 and 90 degrees.")
        if not (-180 <= float(self.lon) <= 180):
            raise ValueError("Longitude must be between -180 and 180 degrees.")

    def to_dict(self):
        return {"lat": self.lat, "lon": self.lon}
