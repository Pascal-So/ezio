import math
import random
from pathlib import Path

import numpy as np
from pydantic_geojson import FeatureCollectionModel, FeatureModel, LineStringModel
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
from ezio.domain.model import BoundingBox


@fixture
def balkan_featurecollection() -> FeatureCollectionModel:
    with open("tests/data/balkan-simplified.geojson") as f:
        collection = FeatureCollectionModel.model_validate_json(f.read())
    return collection


@fixture
def lancashire_track(data_dir: Path) -> LineStringModel:
    loader = GeoJsonTrackLoader()
    tracks = loader.load_tracks(data_dir / "lancashire.geojson")
    assert tracks is not None
    assert len(tracks) == 1
    return tracks[0][1]


def test_linestring_length(balkan_featurecollection: FeatureCollectionModel) -> None:
    length_from_qgis: float = 200416.41252514403 / 1000

    total_length: float = 0
    for feature in balkan_featurecollection.features:
        if feature.geometry is None:
            continue
        if feature.geometry.type == "LineString":
            total_length += track_length_km(feature.geometry)

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
        lat = (random.random() - 0.5) * 179
        lng = (random.random() - 0.5) * 359

        alat, alng = anonymize_point(lat, lng, resolution_m)

        # Ensure that the anonymized point is close to the input
        dist_m = earth_surface_distance_km(lat, lng, alat, alng) * 1000
        assert dist_m < resolution_m * math.sqrt(2)

        # ensure that the function is piecewise constant
        nr_equal_points = 0
        for _ in range(50):
            other_lat = lat + (random.random() - 0.5) * 0.002
            other_lng = lng + (random.random() - 0.5) * 0.002

            dist_m = earth_surface_distance_km(lat, lng, other_lat, other_lng) * 1000
            if dist_m < resolution_m * 0.1 or dist_m > resolution_m * 2:
                # Only look at points that are close to, but not too close to
                # our original point
                continue

            other_alat, other_alng = anonymize_point(other_lat, other_lng, resolution_m)

            if np.allclose([alat, alng], [other_alat, other_alng]):
                nr_equal_points += 1

        # We must have at least some points in the neighbourhood that map to
        # the same anonymized point.
        assert nr_equal_points > 1
