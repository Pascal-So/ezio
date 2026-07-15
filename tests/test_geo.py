import datetime as dt
import math
import random
from pathlib import Path

import numpy as np
from pydantic_geojson import FeatureCollectionModel, FeatureModel
from pytest import fixture

from ezio.adapters.geojson import GeoJsonTrackLoader
from ezio.domain.geo import (
    anonymize_point,
    earth_surface_distance_km,
    latitude_to_mercator_y,
    merge_bounding_boxes,
    simplify_track,
    track_length_km,
)
from ezio.domain.model import BoundingBox, Coord, Track


@fixture
def balkan_tracks(data_dir: Path) -> list[tuple[dt.datetime, Track]]:
    loader = GeoJsonTrackLoader()
    tracks = loader.load_tracks(data_dir / "balkan-simplified.geojson")
    assert tracks is not None
    return tracks


@fixture
def lancashire_track(data_dir: Path) -> Track:
    loader = GeoJsonTrackLoader()
    tracks = loader.load_tracks(data_dir / "lancashire.geojson")
    assert tracks is not None
    assert len(tracks) == 1
    return tracks[0][1]


def test_linestring_length(balkan_tracks: list[tuple[dt.datetime, Track]]) -> None:
    length_from_qgis: float = 200416.41252514403 / 1000

    total_length: float = 0
    for _, track in balkan_tracks:
        total_length += track_length_km(track)

    # check if the difference to the value computed in QGIS is below 1%
    assert abs(length_from_qgis - total_length) / length_from_qgis < 0.01


def test_latitude_to_fraction() -> None:
    eps = 0.0001

    assert latitude_to_mercator_y(0) == 0.5

    # check northernmost and southernmost limit of mercator
    max_mercator_lat = 85.05113
    assert abs(latitude_to_mercator_y(max_mercator_lat)) < eps
    assert abs(1 - latitude_to_mercator_y(-max_mercator_lat)) < eps

    d = -max_mercator_lat + eps
    while d < max_mercator_lat - eps:
        assert 0 < latitude_to_mercator_y(d) < 1
        d += 0.001


def test_bounding_box_merging() -> None:
    bbox1 = BoundingBox(min_lat=5, max_lat=15, min_lng=22, max_lng=25)
    bbox2 = BoundingBox(min_lat=6, max_lat=16, min_lng=20, max_lng=21)

    # merge of one single bounding box is just that bounding box itself
    merged1 = merge_bounding_boxes([bbox1])
    assert bbox1 == merged1

    merged = merge_bounding_boxes([bbox1, bbox2])
    assert merged == BoundingBox(min_lat=5, max_lat=16, min_lng=20, max_lng=25)


def test_point_anonymization() -> None:
    resolution_m = 100

    random.seed(0)

    for _ in range(100):
        # TODO: test near 180 deg boundary
        input = Coord(
            lat=(random.random() - 0.5) * 179, lng=(random.random() - 0.5) * 359
        )

        anon = anonymize_point(input, resolution_m)

        # Ensure that the anonymized point is close to the input
        dist_m = earth_surface_distance_km(input, anon) * 1000
        assert dist_m < resolution_m * math.sqrt(2)

        # ensure that the function is piecewise constant
        nr_equal_points = 0
        for _ in range(50):
            other = Coord(
                input.lat + (random.random() - 0.5) * 0.002,
                input.lng + (random.random() - 0.5) * 0.002,
            )

            dist_m = earth_surface_distance_km(input, other) * 1000
            if dist_m < resolution_m * 0.1 or dist_m > resolution_m * 2:
                # Only look at points that are close to, but not too close to
                # our original point
                continue

            other_anon = anonymize_point(other, resolution_m)

            if np.allclose([anon.lat, anon.lng], [other_anon.lat, other_anon.lng]):
                nr_equal_points += 1

        # We must have at least some points in the neighbourhood that map to
        # the same anonymized point.
        assert nr_equal_points > 1


def test_simplification(lancashire_track: Track) -> None:
    simplified: Track = simplify_track(lancashire_track)
    collection = FeatureCollectionModel(
        type="FeatureCollection",
        bbox=None,
        features=[
            FeatureModel(type="Feature", geometry=simplified.to_geojson(), bbox=None)
        ],
    )

    geojson: str = collection.model_dump_json(indent=None)

    with open("/tmp/eee.geojson", "w") as f:
        f.write(geojson)


def points_with_1m_spacing(amount: int) -> Track:
    """
    Generate a track with points that are 1 metre apart each.
    """

    return Track(coords=[Coord(lat=d * 90 / 1e7, lng=0.0) for d in range(amount)])


def test_simplify_short_track() -> None:
    """
    Simplifying short tracks (shorter than endpoint resolution) should return
    just a randomized start and end point.

    Simplifying tracks with just a single point should return one single point.
    """

    track = points_with_1m_spacing(5)
    simplified = simplify_track(track)
    assert len(simplified.coords) == 2

    track = points_with_1m_spacing(2)
    simplified = simplify_track(track)
    assert len(simplified.coords) == 2

    track = points_with_1m_spacing(1)
    simplified = simplify_track(track)
    assert len(simplified.coords) == 1


def test_simplification_resolution() -> None:
    nr_points = 1500
    endpoint_resolution_m = 100
    resolution_m = 9.2

    track = points_with_1m_spacing(nr_points)
    simplified = simplify_track(track, endpoint_resolution_m, resolution_m)

    expected_nr_points = (nr_points - endpoint_resolution_m * 2) / resolution_m

    assert abs(len(simplified.coords) - expected_nr_points) < 4


# def test_resolution() -> None:
#     loader = GpxTrackLoader()
#     tracks = loader.load_tracks(Path(""))

#     assert tracks is not None
#     assert len(tracks) == 1

#     track = tracks[0][1]

#     coords = track.coords

#     total_distance: float = 0.0
#     distances = []
#     for a, b in zip(coords, coords[1:]):
#         segment_dist = earth_surface_distance_km(a, b)
#         # print(segment_dist)
#         distances.append(segment_dist)
#         total_distance += segment_dist

#     print(total_distance)
#     # plt.hist(distances)
#     # plt.show()
