import requests
from typing import List
from clients.valhalla.models.measure_with_time import Measure
from clients.valhalla.models.costing import Costing
from clients.valhalla.models.shape_match import ShapeMatch
from clients.valhalla.models.directions import Directions
from clients.valhalla.models.options import Options
from clients.valhalla.models.osrm_response import OSRMResponse


class ValhallaClient:
    def __init__(self, base_url: str):
        if not base_url:
            raise ValueError("Base URL must be provided.")
        self.base_url = base_url.rstrip("/")

    def trace_route(
        self,
        measures: List[Measure],
        costing: Costing,
        shape_match: ShapeMatch,
        directions: Directions,
        options: Options,
    ) -> dict:

        if not measures:
            raise ValueError("At least one measure must be provided.")

        if not costing:
            raise ValueError("Costing must be specified")

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
        return OSRMResponse.from_valhalla_response(response.json())
