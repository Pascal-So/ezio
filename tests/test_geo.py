from pydantic_geojson import FeatureCollectionModel
from pytest import fixture

from ezio.domain.geo import latitude_to_mercator_y, linestring_length_km


@fixture
def balkan_featurecollection() -> FeatureCollectionModel:
    with open("tests/data/balkan-simplified.geojson") as f:
        collection = FeatureCollectionModel.model_validate_json(f.read())
    return collection


def test_linestring_length(balkan_featurecollection: FeatureCollectionModel) -> None:
    length_from_qgis: float = 200416.41252514403 / 1000

    total_length: float = 0
    for feature in balkan_featurecollection.features:
        if feature.geometry is None:
            continue
        if feature.geometry.type == "LineString":
            total_length += linestring_length_km(feature.geometry)

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
