import datetime as dt
from collections.abc import Iterable
from pathlib import Path
from typing import override

from ezio.adapters.fake_tiles import FakeTiles
from ezio.adapters.gpx import GpxTrackLoader
from ezio.domain.model import Data, OutputDirectory, SegmentInfo, Tilecoord
from ezio.domain.wizard import (
    download_tiles,
    load_input_files,
    merge_existing_segments,
    run_wizard,
)
from ezio.ports.progress import Progress
from ezio.ports.segment_info_source import SegmentInfoSource

from .utils import make_segment


def test_wizard_end_to_end(data_dir: Path, tempdir: Path) -> None:
    descriptions = {"2022-10-07": "Description for the first day"}

    output_dir = OutputDirectory(tempdir)
    run_wizard(
        data_dir,
        output_dir,
        [GpxTrackLoader()],
        FakeTiles(),
        MockProgress(),
        MockSegmentInfoSource(descriptions),
        None,
        None,
    )

    # Check data.json
    assert output_dir.json_path.is_file()
    with open(output_dir.json_path) as f:
        data = Data.model_validate_json(f.read())

        assert len(data.segments) == 3

        # Check that all segments actually exist as files
        for seg in data.segments:
            assert (output_dir.tracks_dir / f"{seg.date}.geojson").is_file()

        assert data.segments[0].description == "Description for the first day"

        # Check that all photos exist as files
        for photo in data.photos:
            assert (output_dir.thumbs_dir / photo.filename).is_file()
            assert (output_dir.photos_dir / photo.filename).is_file()


def test_tracks_outside_date_range_are_ignored(data_dir: Path) -> None:
    # expected number of track segments:
    # 5 on 2022-10-07
    # 1 on 2022-10-10
    # 2 on 2022-10-11

    inputs = load_input_files(
        data_dir,
        [GpxTrackLoader()],
        MockProgress(),
        start_date=dt.date(2022, 10, 11),
        end_date=None,
    )
    assert len(inputs.tracks) == 2

    inputs = load_input_files(
        data_dir,
        [GpxTrackLoader()],
        MockProgress(),
        start_date=dt.date(2022, 10, 7),
        end_date=dt.date(2022, 10, 10),
    )
    assert len(inputs.tracks) == 6

    inputs = load_input_files(
        data_dir,
        [GpxTrackLoader()],
        MockProgress(),
        start_date=None,
        end_date=dt.date(2022, 10, 6),
    )
    assert len(inputs.tracks) == 0


def test_tile_downloading_shows_up_in_progress_bar(tempdir: Path) -> None:
    nr_tiles = 16

    coords = [Tilecoord(x=x, y=10, zoom=10) for x in range(nr_tiles)]

    progress = MockProgress()

    download_tiles(coords, FakeTiles(), tempdir, progress)
    assert len(list(tempdir.iterdir())) == nr_tiles

    assert progress.nr_items == nr_tiles
    assert progress.finished


class MockSegmentInfoSource(SegmentInfoSource):
    def __init__(self, descriptions: dict[str, str]) -> None:
        self._descriptions: dict[str, str] = descriptions

    @override
    def add_descriptions(self, segments: list[SegmentInfo]) -> None:
        for seg in segments:
            desc = self._descriptions.get(seg.date.strftime("%Y-%m-%d"))

            if desc is not None:
                seg.description = desc


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
