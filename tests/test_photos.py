import datetime as dt
from pathlib import Path

from ezio.adapters.photo_source import load_photo


def test_load_photo(data_dir: Path) -> None:
    photo = load_photo(data_dir / "2022-10-10-12-29-16-_DSC0771.webp")
    assert photo is not None

    expected = dt.datetime(
        2022, 10, 10, 12, 29, 16, tzinfo=dt.timezone(dt.timedelta(hours=2))
    )
    assert photo[0] == expected

    assert load_photo(data_dir / "balkan-simplified.gpx") is None
