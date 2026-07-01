"""Coordinates calculations n stuff"""

import math
from typing import Literal

import gpxpy.geo

from ezio.domain.model import BoundingBox, Coord, Tilecoord, Track

EARTH_RADIUS_M = gpxpy.geo.EARTH_RADIUS


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


def bounding_box(track: Track) -> BoundingBox:
    bbox: BoundingBox | None = None

    for coord in track.coords:
        if bbox is None:
            bbox = BoundingBox(
                min_lat=coord.lat,
                max_lat=coord.lat,
                min_lng=coord.lng,
                max_lng=coord.lng,
            )
        else:
            bbox.min_lat = min(bbox.min_lat, coord.lat)
            bbox.max_lat = max(bbox.max_lat, coord.lat)
            bbox.min_lng = min(bbox.min_lng, coord.lng)
            bbox.max_lng = max(bbox.max_lng, coord.lng)

    if bbox is None:
        raise Exception("Track doesn't contain any coordinates!")

    return bbox


def merge_bounding_boxes(bounding_boxes: list[BoundingBox]) -> BoundingBox:
    total_bbox: BoundingBox | None = None

    for bbox in bounding_boxes:
        if total_bbox is None:
            total_bbox = bbox
        else:
            total_bbox.min_lat = min(total_bbox.min_lat, bbox.min_lat)
            total_bbox.max_lat = max(total_bbox.max_lat, bbox.max_lat)
            total_bbox.min_lng = min(total_bbox.min_lng, bbox.min_lng)
            total_bbox.max_lng = max(total_bbox.max_lng, bbox.max_lng)

    if total_bbox is None:
        raise Exception("Empty list of bounding boxes provided!")

    return total_bbox


def compute_required_map_tiles(
    bbox: BoundingBox,
    max_zoom_level: int,
) -> list[Tilecoord]:
    """
    The set of map tiles that we need to cover the area, across multiple zoom levels
    """

    min_zoom_level = 1
    padding = 2.5

    tiles: list[Tilecoord] = []

    for zoom_level in range(min_zoom_level, max_zoom_level + 1):
        x_range = degree_range_to_index_range(
            (bbox.min_lng, bbox.max_lng), zoom_level, padding, "lng"
        )
        y_range = degree_range_to_index_range(
            (bbox.min_lat, bbox.max_lat), zoom_level, padding, "lat"
        )

        for x in range(*x_range):
            for y in range(*y_range):
                tiles.append(Tilecoord(x, y, zoom=zoom_level))

    return tiles


def nr_coords_on_zoom_level(level: int) -> int:
    # The math.floor is required because of
    # https://github.com/python/mypy/issues/7765#issuecomment-544645704
    return math.floor(2 ** float(level))


def track_length_km(track: Track) -> float:
    """Calculates the total length of a LineString in kilometers."""

    coords = track.coords

    total_distance: float = 0.0
    for a, b in zip(coords, coords[1:]):
        segment_dist = earth_surface_distance_km(a, b)
        total_distance += segment_dist

    return total_distance


def earth_surface_distance_km(a: Coord, b: Coord) -> float:
    # convert everything to radians first
    a_lat = math.radians(a.lat)
    a_lng = math.radians(a.lng)
    b_lat = math.radians(b.lat)
    b_lng = math.radians(b.lng)

    diff_lat: float = a_lat - b_lat
    diff_lng: float = a_lng - b_lng

    temp = (
        math.sin(diff_lat / 2) ** 2
        + math.cos(a_lat) * math.cos(b_lat) * math.sin(diff_lng / 2) ** 2
    )

    return (
        EARTH_RADIUS_M / 1000 * (2 * math.atan2(math.sqrt(temp), math.sqrt(1 - temp)))
    )


def get_elevations(track: Track) -> list[float] | None:
    elevations: list[float] = []

    for coord in track.coords:
        if coord.alt is None:
            # If any of the points does not have elevation set then we skip the
            # entire climb calculation
            return None
        elevations.append(coord.alt)

    return elevations


def climb(track: Track) -> float | None:
    """
    Calculate the ascent that was climbed during the route, in metres.
    """

    elevations = get_elevations(track)
    if elevations is None:
        # If any of the points does not have elevation set then we skip the
        # entire climb calculation
        return None

    smoothed = smoothed_elevations(elevations, 10)

    total_climb: float = 0
    for a, b in zip(smoothed, smoothed[1:]):
        diff = max(b - a, 0)
        total_climb += diff

    return total_climb


def smoothed_elevations(elevations: list[float], box_size: int) -> list[float]:
    """
    Average the elevations across a few points to reduce the influence of noise
    """

    smoothed: list[float] = []
    for i in range(0, len(elevations), box_size):
        chunk = elevations[i : i + box_size]
        smoothed.append(sum(chunk) / len(chunk))
    return smoothed


def anonymize_point(point: Coord, resolution_m: float) -> Coord:
    """
    Get a deterministic point within a given distance of the input point. This
    function is piecewise constant to avoid leaking information even if the
    implementation is known.
    """

    # The idea is we create an orthographic map projection centered around the
    # rounded coordinates, and then round the position to the resolution grid
    # in that projected space.
    #
    # Rounding in the projected space ensures that the rounding resolution does
    # not vary by latitude. Rounding the coordinates that we use as the
    # projection origin ensures that we don't leak the original coordinates from
    # the way that the rounding grid shifts around.
    #
    # https://en.wikipedia.org/wiki/Orthographic_map_projection#Mathematics

    rounded_lat_deg = round(point.lat)
    rounded_lng_deg = round(point.lng)

    lat = math.radians(point.lat)
    lng = math.radians(point.lng)
    rounded_lat = math.radians(rounded_lat_deg)
    rounded_lng = math.radians(rounded_lng_deg)

    x = EARTH_RADIUS_M * math.cos(lat) * math.sin(lng - rounded_lng)
    y = EARTH_RADIUS_M * (
        math.cos(rounded_lat) * math.sin(lat)
        - math.sin(rounded_lat) * math.cos(lat) * math.cos(lng - rounded_lng)
    )

    # snap to the resolution grid
    rounded_x = round(x / resolution_m) * resolution_m
    rounded_y = round(y / resolution_m) * resolution_m

    # inverse projection
    rho = math.hypot(x, y)
    c = math.asin(rho / EARTH_RADIUS_M)
    sc = math.sin(c)
    cc = math.cos(c)
    new_lat = math.asin(
        cc * math.sin(rounded_lat) + (rounded_y * sc * math.cos(rounded_lat)) / rho
    )
    new_lng = rounded_lng + math.atan2(
        rounded_x * sc,
        rho * cc * math.cos(rounded_lat) - rounded_y * sc * math.sin(rounded_lat),
    )

    return Coord(lat=math.degrees(new_lat), lng=math.degrees(new_lng))


def simplify_track(
    track: Track, endpoint_resolution_m: float = 500, resolution_m: float = 200
) -> Track:
    if len(track.coords) == 0:
        return track

    simplified: list[Coord] = []

    coords = track.coords

    total_distance: float = 0
    # We run a stronger simplification right at the start to anonymize the
    # start location.
    simplified.append(anonymize_point(coords[0], endpoint_resolution_m))
    last_point_added_distance: float = endpoint_resolution_m

    for a, b in zip(coords, coords[1:]):
        segment_dist_m = earth_surface_distance_km(a, b) * 1000
        total_distance += segment_dist_m

        if total_distance > last_point_added_distance + resolution_m:
            simplified.append(b)

            last_point_added_distance = total_distance

    # TODO: anonymize endpoint

    return Track(simplified)
