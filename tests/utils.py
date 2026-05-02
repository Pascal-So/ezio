import datetime as dt

from ezio.domain.model import BoundingBox, SegmentInfo


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
