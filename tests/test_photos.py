import datetime as dt
from pathlib import Path

from ezio.adapters.photo_source import list_photos


def test_list_photos() -> None:
    photos = list_photos(Path("tests/data/"))
    photos.sort()

    assert len(photos) == 2
    assert photos[0][0] == dt.datetime(2022, 10, 10, 12, 29, 16)
    assert photos[1][0] == dt.datetime(2022, 10, 11, 15, 3, 22)
