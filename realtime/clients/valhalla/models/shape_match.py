from enum import Enum


# https://github.com/valhalla/valhalla/blob/master/docs/docs/api/map-matching/api-reference.md#shape-matching-parameters
class ShapeMatch(Enum):
    MAP_SNAP = "map_snap"
    WALK_OR_SNAP = "walk_or_snap"
    EDGE_WALK = "edge_walk"

    @classmethod
    def from_string(cls, value: str) -> "ShapeMatch":
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"Invalid shape match type: {value}")
