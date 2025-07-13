from enum import Enum


# https://github.com/valhalla/valhalla/blob/master/docs/docs/api/turn-by-turn/api-reference.md#costing-models
class Costing(Enum):
    AUTO = "auto"
    BUS = "bus"
    TRUCK = "truck"

    @classmethod
    def from_string(cls, value: str) -> "Costing":
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"Invalid costing type: {value}")
