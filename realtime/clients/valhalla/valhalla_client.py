import requests
from typing import List
from realtime.clients.valhalla.models.measure_with_time import Measure
from realtime.clients.valhalla.models.costing import Costing
from realtime.clients.valhalla.models.shape_match import ShapeMatch
from realtime.clients.valhalla.models.directions import Directions
from realtime.clients.valhalla.models.options import Options
from realtime.clients.valhalla.models.osrm_response import OSRMResponse
from realtime.clients.valhalla.decorator import retry_on_failure


class ValhallaClient:
    def __init__(self, base_url: str):
        if not base_url:
            raise ValueError("Base URL must be provided.")
        self.base_url = base_url.rstrip("/")

    @retry_on_failure(max_attempts=3, backoff=2)
    def trace_route(
        self,
        measures: List[Measure],
        costing: Costing,
        shape_match: ShapeMatch,
        directions: Directions,
        options: Options,
        parse_tracepoint=False,
    ) -> dict:

        if not measures:
            raise ValueError("At least one measure must be provided.")

        if not costing:
            raise ValueError("Costing must be specified")

        if len(measures) < 2:
            raise ValueError(f"Not enough points to process with Valhalla\n")

        shape = [m.to_dict() for m in measures]

        payload = {
            "shape": shape,
            "shape_match": shape_match.value,
            "costing": costing.value,
            **directions.to_dict(),
            **options.to_dict(),
        }

        if payload.get("format") != "osrm":
            raise ValueError(
                "Unsupported payload. format: osrm is supported at the moment"
            )

        print(
            "Sending request to /trace_route with payload:",
            {k: v for k, v in payload.items() if k != "shape"},
        )

        response = requests.post(
            f"{self.base_url}/trace_route",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        return OSRMResponse.from_valhalla_response(
            response.json(), parse_tracepoints=parse_tracepoint
        )
