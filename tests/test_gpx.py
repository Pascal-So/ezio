from pathlib import Path

from ezio.adapters.gpx import GpxTrackSource


def test_gpx_source() -> None:
    source = GpxTrackSource()
    linestrings = source.get_tracks(Path("tests/data"))

    assert len(linestrings) == 8
