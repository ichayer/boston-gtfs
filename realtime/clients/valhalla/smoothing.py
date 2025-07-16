from shapely import LineString


def smooth_linestring(linestring: LineString):

    # Remove line noise using DP
    # https://shapely.readthedocs.io/en/stable/reference/shapely.LineString.html#shapely.LineString.simplify
    smoothed_linestring = linestring.simplify(1e-6, preserve_topology=True)

    # Ensure the geometry has no self-intersections.
    # If not linear geometries, projection distances along the Linestring may become ambiguous.
    # https://shapely.readthedocs.io/en/2.1.1/reference/shapely.LineString.html#shapely.LineString.interpolate
    # https://shapely.readthedocs.io/en/2.1.1/reference/shapely.LineString.html#shapely.LineString.project
    if not smoothed_linestring.is_simple:

        # Attempt to fix topology (forcing the geometry)
        smoothed_linestring = smoothed_linestring.buffer(0)
        if (
            smoothed_linestring.geom_type != "LineString"
            or not smoothed_linestring.is_simple
        ):
            raise ValueError(
                "Linestring still invalid after attemping a forced cleaning"
            )

    return smoothed_linestring
