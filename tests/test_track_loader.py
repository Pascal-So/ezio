from pathlib import Path

from ezio.adapters.geojson import GeoJsonTrackLoader
from ezio.adapters.gpx import GpxTrackLoader


def test_gpx_loader(data_dir: Path) -> None:
    loader = GpxTrackLoader()

    linestrings = loader.load_tracks(data_dir / "balkan-simplified.gpx")
    assert linestrings is not None
    assert len(linestrings) == 8

    assert loader.load_tracks(data_dir / "2022-10-10-12-29-16-_DSC0771.webp") is None


def test_geojson_loader(data_dir: Path) -> None:
    """
    Load a GeoJSON file containing LineString features
    """

    loader = GeoJsonTrackLoader()

    linestrings = loader.load_tracks(data_dir / "balkan-simplified.geojson")
    assert linestrings is not None
    assert len(linestrings) == 3

    assert loader.load_tracks(data_dir / "2022-10-10-12-29-16-_DSC0771.webp") is None


def test_geojson_loader_multilinestring(data_dir: Path) -> None:
    """
    Load a GeoJSON file containing MultiLineString features
    """

    loader = GeoJsonTrackLoader()

    linestrings = loader.load_tracks(data_dir / "three-test-lines-multiline.geojson")
    assert linestrings is not None
    assert len(linestrings) == 3
