from typing import List
from shapely import LineString, Point
from math import inf
from clients.valhalla.models.tgeompoint import TGeomPoint


# https://spin.atomicobject.com/interpolate-along-linestring/
def assign_timestamps_to_linestring(
    anchor_points: List[Point],
    anchor_times: List[int],
    geometry: LineString,
) -> List[TGeomPoint]:
    """
    Assigns interpolated timestamps to each vertex of a matched polyline using known anchor points as time references.
    For each vertex in the geometry, the function locates the anchor segment it falls into and linearly interpolates its timestamp.
    """

    # Ensure the geometry has no self-intersections.
    # If not linear geometries, projection distances along the Linestring may become ambiguous.
    # https://shapely.readthedocs.io/en/2.1.1/reference/shapely.LineString.html#shapely.LineString.interpolate
    # https://shapely.readthedocs.io/en/2.1.1/reference/shapely.LineString.html#shapely.LineString.project
    if not geometry.is_simple:
        raise ValueError(
            "Geometry is not simple. It contains self-intersections. This can lead to incorrect projections or interpolations results"
        )

    if len(anchor_points) < 2 or len(anchor_times) < 2:
        raise ValueError("At least two anchors with timestamps are required.")

    # Project anchor points onto the Linestring and pair with timestamp
    # Sort by distance along the Linestring
    anchors = [
        (point, geometry.project(point), timestamp)
        for point, timestamp in zip(anchor_points, anchor_times)
    ]
    anchors.sort(key=lambda x: x[1])

    # Results
    result = []

    # Variables to help in the algorithm
    previous_interpolated_time, previous_interpolated_point = -inf, None

    # Start with the first segment
    start_point, start_dist, start_time = anchors.pop(0)
    end_point, end_dist, end_time = anchors.pop(0)

    for coord in geometry.coords:
        current_point = Point(coord)
        current_dist = geometry.project(current_point)

        # Advance segment if current point is beyond it or if it's invalid
        while len(anchors) > 0 and (
            start_point.equals_exact(end_point) or current_dist > end_dist
        ):
            # Store p2 to maitain consistency with retrieved data in protobuf
            if (
                not end_point.equals_exact(previous_interpolated_point)
                and end_time > previous_interpolated_time
            ):
                result.append(TGeomPoint(end_point, end_time))
                previous_interpolated_time = end_time
                previous_interpolated_point = end_point
            start_point, start_dist, start_time = end_point, end_dist, end_time
            end_point, end_dist, end_time = anchors.pop(0)

        # Interpolate only if the current point is within a valid segment
        if not start_point.equals_exact(end_point) and current_dist <= end_dist:
            if end_dist == start_dist:
                interpolated_time = start_time  # avoid dividing by 0
            else:
                # Interpolation formula
                interpolated_time = start_time + (
                    (current_dist - start_dist) / (end_dist - start_dist)
                ) * (end_time - start_time)

            if interpolated_time < previous_interpolated_time:
                raise ValueError(
                    f"Non-increasing timestamp at distance {current_dist:.2f}."
                )
            elif interpolated_time == previous_interpolated_time:
                continue

            result.append(TGeomPoint(current_point, interpolated_time))
            previous_interpolated_time = interpolated_time
            previous_interpolated_point = current_point

    return result
