import datetime as dt
from pathlib import Path

from ezio.domain.model import load_existing_data


def test_load_old_data(data_dir: Path) -> None:
    existing_data = load_existing_data(data_dir / "old-data.json")
    assert existing_data is not None

    assert len(existing_data.segments) == 1
    segment = existing_data.segments[0]
    assert segment.date == dt.date(2022, 9, 3)
    assert segment.dist_km == 39.1
    assert segment.climb_m == 475
    assert segment.description == "Segment A"
    assert segment.featured_photo == "photo.webp"

    assert len(existing_data.background_segments) == 0
