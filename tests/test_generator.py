from ezio.domain.generator import (
    merge_geojson_bounding_boxes,
    compute_geojson_bounding_box,
)
from ezio.domain.model import Coord, Track


def _tracks(with_altitude: bool) -> list[Track]:
    tracks = [
        Track(coords=[Coord(lat=1, lng=101), Coord(lat=2, lng=105)]),
        Track(coords=[Coord(lat=3, lng=101), Coord(lat=2, lng=102)]),
    ]

    if with_altitude:
        return tracks
    else:
        return [
            Track(coords=[Coord(lat=c.lat, lng=c.lng) for c in track.coords])
            for track in tracks
        ]


def test_bounding_boxes_2d() -> None:
    tracks = _tracks(with_altitude=False)

    bbox = compute_geojson_bounding_box(tracks)
    assert bbox == [101, 1, 105, 3]

    bboxes = [
        compute_geojson_bounding_box(tracks[:1]),
        compute_geojson_bounding_box(tracks[1:]),
    ]

    assert bboxes[0] is not None
    assert bboxes[1] is not None
    combined = merge_geojson_bounding_boxes(
        # the None filtering is just to make mypy happy
        [b for b in bboxes if b is not None]
    )

    assert combined == bbox
