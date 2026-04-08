"""
The tests in this file don't directly assert anything, they are just here to
test some things manually. You can run them by for example running
`MANUAL_TESTS=1 uv run pytest -k testname`.

To see the stdout of the tests add the `-s` flag.
"""

import os
import time

import pytest

from ezio.adapters.rich_progress import RichProgress

# Disable this entire test file if the env var is not set.
pytestmark = pytest.mark.skipif(
    "MANUAL_TESTS" not in os.environ, reason="MANUAL_TESTS env variable not set"
)


def test_progress_bar() -> None:
    progress = RichProgress()

    for _ in progress.track(range(8), description="Testing some things"):
        time.sleep(0.3)

    progress.stop()
