# https://github.com/valhalla/valhalla/blob/master/docs/docs/api/map-matching/api-reference.md#costing-models-and-other-options
class Options:
    def __init__(self):
        self._options = {}
        self._trace_options = {}

    def set_begin_time(self, begin_time: int):
        if not isinstance(begin_time, (int, float)):
            raise ValueError("begin_time must be a numeric UNIX timestamp.")
        self._options["begin_time"] = begin_time
        return self

    def set_durations(self, durations: list):
        if not all(isinstance(d, (int, float)) and d >= 0 for d in durations):
            raise ValueError("All durations must be non-negative numbers.")
        self._options["durations"] = durations
        return self

    def enable_use_timestamps(self, enabled: bool = True):
        self._options["use_timestamps"] = bool(enabled)
        return self

    def enable_linear_references(self, enabled: bool = True):
        self._options["linear_references"] = bool(enabled)
        return self

    def set_search_radius(self, meters: float):
        if meters < 0:
            raise ValueError("search_radius must be non-negative.")
        self._trace_options["search_radius"] = meters
        return self

    def set_gps_accuracy(self, meters: float):
        if meters < 0:
            raise ValueError("gps_accuracy must be non-negative.")
        self._trace_options["gps_accuracy"] = meters
        return self

    def set_breakage_distance(self, meters: float):
        if meters < 0:
            raise ValueError("breakage_distance must be non-negative.")
        self._trace_options["breakage_distance"] = meters
        return self

    def set_interpolation_distance(self, meters: float):
        if meters < 0:
            raise ValueError("interpolation_distance must be non-negative.")
        self._trace_options["interpolation_distance"] = meters
        return self

    def set_turn_penalty_factor(self, factor: float):
        if factor < 0:
            raise ValueError("turn_penalty_factor must be non-negative.")
        self._trace_options["turn_penalty_factor"] = factor
        return self

    def set_use_timestamps(self, enabled: bool = True):
        self._options["use_timestamps"] = bool(enabled)
        return self

    def to_dict(self) -> dict:
        data = self._options.copy()
        if self._trace_options:
            data["trace_options"] = self._trace_options.copy()
        return data
