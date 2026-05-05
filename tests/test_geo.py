from pydantic_geojson import FeatureCollectionModel

from ezio.domain.geo import (
    latitude_to_mercator_y,
    merge_bounding_boxes,
    track_length_km,
)
from ezio.domain.model import BoundingBox


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
