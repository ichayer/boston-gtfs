# https://github.com/valhalla/valhalla/blob/master/docs/docs/api/turn-by-turn/api-reference.md#directions-options
class Directions:
    def __init__(self):
        self._options = {}

    def set_units(self, units: str):
        allowed = {"kilometers", "km", "miles", "mi"}
        if units not in allowed:
            raise ValueError(f"Invalid units: {units}. Must be one of {allowed}.")
        self._options["units"] = units
        return self

    def set_language(self, language: str):
        # No strict validation because it depends on tag BCP 47
        self._options["language"] = language
        return self

    def set_directions_type(self, directions_type: str):
        allowed = {"none", "maneuvers", "instructions"}
        if directions_type not in allowed:
            raise ValueError(
                f"Invalid directions_type: {directions_type}. Must be one of {allowed}."
            )
        self._options["directions_type"] = directions_type
        return self

    def set_format(self, fmt: str):
        allowed = {"json", "gpx", "osrm", "pbf"}
        if fmt not in allowed:
            raise ValueError(f"Invalid format: {fmt}. Must be one of {allowed}.")
        self._options["format"] = fmt
        return self

    def set_shape_format(self, shape_format: str):
        allowed = {"polyline6", "polyline5", "geojson", "no_shape"}
        if shape_format not in allowed:
            raise ValueError(
                f"Invalid shape_format: {shape_format}. Must be one of {allowed}."
            )
        self._options["shape_format"] = shape_format
        return self

    def enable_banner_instructions(self, enabled: bool = True):
        self._options["banner_instructions"] = bool(enabled)
        return self

    def enable_voice_instructions(self, enabled: bool = True):
        self._options["voice_instructions"] = bool(enabled)
        return self

    def set_alternates(self, count: int):
        if not isinstance(count, int) or count < 0:
            raise ValueError("Alternates must be a non-negative integer.")
        self._options["alternates"] = count
        return self

    def to_dict(self) -> dict:
        return self._options.copy()
