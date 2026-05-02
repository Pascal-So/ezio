"""
The tests in this file don't directly assert anything, they are just here to
test some things manually. You can run them by for example running
`MANUAL_TESTS=1 uv run pytest -k testname`.

To see the stdout of the tests add the `-s` flag.
"""

import datetime as dt
import os
import time

import pytest
from rich.pretty import pprint

from ezio.adapters.rich_progress import RichProgress
from ezio.adapters.textual_segment_info_source import TextualSegmentInfoSource
from ezio.domain.generator.frontend import copy_frontend
from ezio.domain.model import OutputDirectory

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
