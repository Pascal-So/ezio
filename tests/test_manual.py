"""
The tests in this file don't directly assert anything, they are just here to
test some things manually. You can run them by for example running
`MANUAL_TESTS=1 uv run pytest -k testname`.

To see the stdout of the tests add the `-s` flag.
"""

import datetime as dt
import os
import random
import time
from pathlib import Path

from pydantic_geojson import FeatureCollectionModel, FeatureModel
import pytest
from rich.pretty import pprint

from ezio.adapters.gpx import GpxTrackLoader
from ezio.adapters.noop_progress import NoopProgress
from ezio.adapters.rich_progress import RichProgress
from ezio.adapters.textual_segment_info_source import TextualSegmentInfoSource
from ezio.domain.generator.frontend import copy_frontend
from ezio.domain.generator.plot import plot_segment
from ezio.domain.geo import anonymize_point
from ezio.domain.model import Coord, OutputDirectory, Track
from ezio.domain.wizard import group_tracks_by_date, load_input_files

from .utils import make_segment

# Disable this entire test file if the env var is not set.
pytestmark = pytest.mark.skipif(
    "MANUAL_TESTS" not in os.environ, reason="MANUAL_TESTS env variable not set"
)


def test_progress_bar() -> None:
    progress = RichProgress()

    for _ in progress.track(range(8), description="Testing some things"):
        time.sleep(0.3)

    progress.stop()


def test_resource_path() -> None:
    copy_frontend(OutputDirectory("/tmp"), None)


def test_textual_segment_info() -> None:
    source = TextualSegmentInfoSource()

    dates = [dt.date(2026, 4, 10), dt.date(2026, 4, 11)]
    segments = [
        make_segment(dates[0], description="First Day"),
        make_segment(dates[1]),
        make_segment(dates[1]),
        make_segment(dates[1]),
        make_segment(dates[1]),
    ]

    source.add_descriptions(segments)

    pprint(segments)


def test_plotting() -> None:
    path = Path("./additional-test-data")

    inputs = load_input_files([path], [GpxTrackLoader()], NoopProgress(), None, None)
    tracks_by_date = group_tracks_by_date(inputs.tracks)

    for date, segment in tracks_by_date.items():
        plot_segment(segment, Path(date.strftime("%Y-%m-%d.svg")))


def test_plot_anonymization() -> None:
    """
    Visualize the effect of point anonymization
    """

    random.seed(4)

    lines: list[Track] = []
    for _ in range(100000):
        c = Coord(lng=random.random() * 0.05 - 5, lat=random.random() * 0.03 + 53.9)

        lines.append(Track([c, anonymize_point(c, 100)]))

    collection = FeatureCollectionModel(
        type="FeatureCollection",
        bbox=None,
        features=[
            FeatureModel(type="Feature", geometry=line.to_geojson(), bbox=None)
            for line in lines
        ],
    )
    geojson: str = collection.model_dump_json(indent=None)

    with open("/tmp/anon.geojson", "w") as f:
        f.write(geojson)
