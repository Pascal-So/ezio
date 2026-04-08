from collections.abc import Iterable
from pathlib import Path
from typing import override

from ezio.adapters.fake_tiles import FakeTiles
from ezio.domain.model import Tilecoord
from ezio.domain.wizard import download_tiles
from ezio.ports.progress import Progress


def test_tile_downloading_shows_up_in_progress_bar(tempdir: Path) -> None:
    nr_tiles = 16

    coords = [Tilecoord(x=x, y=10, zoom=10) for x in range(nr_tiles)]

    progress = MockProgress()

    download_tiles(coords, FakeTiles(), tempdir, progress)
    assert len(list(tempdir.iterdir())) == nr_tiles

    assert progress.nr_items == nr_tiles
    assert progress.finished


class MockProgress(Progress):
    def __init__(self) -> None:
        self.nr_items: int = 0
        self.finished: bool = False

    @override
    def track[T](self, iter: Iterable[T], description: str) -> Iterable[T]:
        for item in iter:
            self.nr_items += 1
            yield item

        self.finished = True
