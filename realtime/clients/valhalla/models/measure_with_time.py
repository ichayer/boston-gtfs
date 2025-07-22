from dataclasses import dataclass
from realtime.clients.valhalla.models.measure import Measure


# https://github.com/valhalla/valhalla/blob/master/docs/docs/api/map-matching/api-reference.md#get-better-results
@dataclass
class MeasureWithTime(Measure):
    time: str

    def __post_init__(self):
        super().__post_init__()

    def to_dict(self):
        data = super().to_dict()
        data["time"] = self.time
        return data
