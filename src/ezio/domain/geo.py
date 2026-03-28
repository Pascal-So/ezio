"""Coordinates calculations n stuff"""

import math
from typing import Literal


from pydantic_geojson import LineStringModel


def latitude_to_mercator_y(lat: float) -> float:
    """
    Mapping from latitude to the Mercator projection y-coordinate.

    y is 0 at the northern edge and increases towards the south up to 1
    """

    sin = math.sin(lat * math.pi / 180.0)
    return 0.5 - math.log((1 + sin) / (1 - sin)) / (4 * math.pi)


def degree_range_to_index_range(
    range: tuple[float, float],
    level: int,
    padding: float,
    direction: Literal["lat", "lng"],
) -> tuple[int, int]:
    """
    Convert a WGS84 coordinate range to a range of tile coordinates at a given
    zoom level.
    """

    frac_range = (
        (latitude_to_mercator_y(range[1]), latitude_to_mercator_y(range[0]))
        if direction == "lat"
        else (range[0] / 360.0 + 0.5, range[1] / 360.0 + 0.5)
    )

    level_size = nr_coords_on_zoom_level(level)

    lower: float = frac_range[0] * level_size - padding
    upper: float = frac_range[1] * level_size + padding

    lower_clamped = _clamp(math.floor(lower), 0, level_size - 1)
    upper_clamped = _clamp(math.ceil(upper), 0, level_size - 1)
    return lower_clamped, upper_clamped


def _clamp(val: int, lower: int, upper: int) -> int:
    return min(max(val, lower), upper)


def nr_coords_on_zoom_level(level: int) -> int:
    # The math.floor is required because of
    # https://github.com/python/mypy/issues/7765#issuecomment-544645704
    return math.floor(2 ** float(level))


def linestring_length_km(linestring: LineStringModel) -> float:
    """Calculates the total length of a LineString in kilometers."""

    coords = linestring.coordinates

    total_distance: float = 0.0
    for a, b in zip(coords, coords[1:]):
        segment_dist = earth_surface_distance_km(a.lat, a.lon, b.lat, b.lon)
        total_distance += segment_dist

    return total_distance


def earth_surface_distance_km(
    a_lat: float, a_lng: float, b_lat: float, b_lng: float
) -> float:
    # convert everything to radians first
    a_lat = math.radians(a_lat)
    a_lng = math.radians(a_lng)
    b_lat = math.radians(b_lat)
    b_lng = math.radians(b_lng)

    diff_lat: float = a_lat - b_lat
    diff_lng: float = a_lng - b_lng

    temp = (
        math.sin(diff_lat / 2) ** 2
        + math.cos(a_lat) * math.cos(b_lat) * math.sin(diff_lng / 2) ** 2
    )

    return 6378.137 * (2 * math.atan2(math.sqrt(temp), math.sqrt(1 - temp)))


def climb(linestring: LineStringModel) -> float | None:
    """
    Calculate the ascent that was climbed during the route, in metres.
    """

    elevations: list[float] = []

    for coord in linestring.coordinates:
        if coord.alt is None:
            # If any of the points does not have elevation set then we skip the
            # entire climb calculation
            return None
        elevations.append(coord.alt)

    smoothed = _smoothed_elevations(elevations, 10)

    total_climb: float = 0
    for a, b in zip(smoothed, smoothed[1:]):
        diff = max(b - a, 0)
        total_climb += diff

    return total_climb


def _smoothed_elevations(elevations: list[float], box_size: int) -> list[float]:
    """
    Average the elevations across a few points to reduce the influence of noise
    """

    smoothed: list[float] = []
    for i in range(0, len(elevations), box_size):
        chunk = elevations[i : i + box_size]
        smoothed.append(sum(chunk) / len(chunk))
    return smoothed
