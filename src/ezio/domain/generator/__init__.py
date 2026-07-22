"""
The `generator` module contains code associated with generating the contents
of the output directory that make up the static website.

All of this could technically be wrapped behind a `port` but that seems like
more abstraction than what it's worth.
"""

import datetime as dt


import pydantic_geojson._base as geojson_base
from pydantic_geojson import FeatureCollectionModel, FeatureModel, MultiLineStringModel

from ezio.domain.model import (
    BoundingBox,
    OutputDirectory,
    Track,
)


def write_geojson_files(
    output_directory: OutputDirectory,
    tracks_by_date: dict[dt.date, list[Track]],
    bounding_boxes: dict[dt.date, BoundingBox],
    total_bounding_box: BoundingBox,
) -> None:
    sorted_segments = sorted(tracks_by_date.items())

    def get_bbox(date: dt.date) -> geojson_base.BoundingBox | None:
        bbox = bounding_boxes.get(date)
        if bbox is None:
            return None

        return bbox.to_geojson()

    collection = FeatureCollectionModel(
        type="FeatureCollection",
        features=[
            FeatureModel(
                type="Feature",
                id=date.strftime("%Y-%m-%d"),
                geometry=MultiLineStringModel(
                    coordinates=[
                        [coord.to_geojson() for coord in track.coords]
                        for track in tracks
                    ],
                    type="MultiLineString",
                    bbox=None,
                ),
                bbox=get_bbox(date),
            )
            for date, tracks in sorted_segments
        ],
        bbox=total_bounding_box.to_geojson(),
    )

    geojson: str = collection.model_dump_json(indent=None)

    with open(output_directory.segments_path, "w") as f:
        f.write(geojson)
