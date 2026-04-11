from collections.abc import Iterable
import datetime as dt
from pathlib import Path
from typing import override

from ezio.adapters.fake_tiles import FakeTiles
from ezio.domain.model import BoundingBox, SegmentInfo, Tilecoord
from ezio.domain.wizard import download_tiles, merge_existing_segments
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


def test_merge_existing_segments() -> None:
    days = [
        dt.date(2026, 4, 10),
        dt.date(2026, 4, 11),
        dt.date(2026, 4, 12),
        dt.date(2026, 4, 13),
    ]

    def make_segment(
        date: dt.date, description: str = "", featured_photo: str | None = None
    ) -> SegmentInfo:
        return SegmentInfo(
            date=date,
            description=description,
            dist_km=1,
            climb_m=1,
            featured_photo=featured_photo,
            bounding_box=BoundingBox(min_lat=0, min_lng=0, max_lat=0, max_lng=0),
        )

    existing_segments = [
        make_segment(days[0], "day 0", "1.jpg"),
        make_segment(days[1], "day 1", "2.jpg"),
        make_segment(days[2], "day 2", "asdf.jpg"),
    ]

    new_segments = [
        make_segment(days[1]),
        make_segment(days[2]),
        make_segment(days[3]),
    ]

    photos = ["1.jpg", "2.jpg", "3.jpg"]

    merge_existing_segments(existing_segments, new_segments, photos)

    assert new_segments[0] == make_segment(days[1], "day 1", "2.jpg")
    assert new_segments[1] == make_segment(days[2], "day 2")
    assert new_segments[2] == make_segment(days[3])
