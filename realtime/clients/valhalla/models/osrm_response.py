from dataclasses import dataclass
from typing import List
from polyline import decode
from shapely import LineString, Point


@dataclass
class OSRMResponse:
    best_matching_index: int
    geometry: LineString
    confidence: float
    duration_in_seconds: float  # in seconds
    distance_in_meters: float  # in meters
    tracepoints: List[Point]

    @classmethod
    def from_valhalla_response(
        cls, response: dict, parse_tracepoints: bool = False
    ) -> "OSRMResponse":
        matchings = response.get("matchings", None)
        raw_tracepoints_data = response.get("tracepoints", None)

        if not matchings or not raw_tracepoints_data:
            raise ValueError(
                "Invalid Valhalla response: missing 'matchings' or 'tracepoints'"
            )

        selected_index, selected_matching = max(
            enumerate(matchings),
            key=lambda x: (x[1].get("confidence", 0.0), x[1].get("weight", 0.0)),
        )

        if selected_matching is None or selected_index is None:
            raise ValueError("No valid matching found in the response")

        decoded_coords = decode(
            expression=selected_matching["geometry"], precision=6, geojson=True
        )
        geometry = LineString(decoded_coords)

        if not geometry.is_valid:
            raise ValueError("Decoded geometry is not valid")

        tracepoints = []
        if parse_tracepoints:
            for tracepoint_data in raw_tracepoints_data:
                if tracepoint_data is None:
                    continue
                location = tracepoint_data.get("location", None)
                if location is None:
                    continue
                lon, lat = location  # Valhalla returns [lon, lat]
                tracepoints.append(Point(lon, lat))  # Shapely expects (x=lon, y=lat)

        return cls(
            geometry=geometry,
            confidence=selected_matching.get("confidence", 0.0),
            duration_in_seconds=selected_matching.get("duration", 0.0),
            distance_in_meters=selected_matching.get("distance", 0.0),
            best_matching_index=selected_index,
            tracepoints=tracepoints,
        )
