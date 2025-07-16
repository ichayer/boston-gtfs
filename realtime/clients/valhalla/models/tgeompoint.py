from pandas import to_datetime
from shapely import Point


class TGeomPoint:

    def __init__(self, point: Point, unix_timestamp: float):
        self.point = point
        self.unix_timestamp = unix_timestamp

    def __str__(self):
        return f"Point({self.point.x} {self.point.y})@{to_datetime(self.unix_timestamp, unit='s', utc=True)}"

    def __eq__(self, other):
        if self is other:
            return True

        if not isinstance(other, TGeomPoint):
            return False

        return (
            self.point.equals_exact(other.point)
            and self.unix_timestamp == other.unix_timestamp
        )

    def __hash__(self):
        x = round(self.point.x, 8)
        y = round(self.point.y, 8)
        t = round(self.unix_timestamp, 6)
        return hash((x, y, t))

    def __lt__(self, other):
        return self.unix_timestamp < other.unix_timestamp

    def __gt__(self, other):
        return self.unix_timestamp > other.unix_timestamp
