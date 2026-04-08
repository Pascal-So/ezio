from pathlib import Path

from ezio.adapters.gpx import GpxTrackLoader


def test_gpx_source(data_dir: Path) -> None:
    loader = GpxTrackLoader()

    linestrings = loader.load_tracks(data_dir / "balkan-simplified.gpx")
    assert linestrings is not None
    assert len(linestrings) == 8

    assert loader.load_tracks(data_dir / "2022-10-10-12-29-16-_DSC0771.webp") is None
