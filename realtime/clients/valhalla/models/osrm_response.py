from dataclasses import dataclass
from polyline import decode
from shapely import LineString


@dataclass
class OSRMResponse:
    best_matching_index: int
    geometry: LineString
    confidence: float
    duration_in_seconds: float  # in seconds
    distance_in_meters: float  # in meters

    @classmethod
    def from_valhalla_response(cls, response: dict) -> "OSRMResponse":
        matchings = response.get("matchings", None)
        tracepoints = response.get("tracepoints", None)

        if not matchings or not tracepoints:
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

        return cls(
            geometry=geometry,
            confidence=selected_matching.get("confidence", 0.0),
            duration_in_seconds=selected_matching.get("duration", 0.0),
            distance_in_meters=selected_matching.get("distance", 0.0),
            best_matching_index=selected_index,
        )
