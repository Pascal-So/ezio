"""
The `generator` module contains code associated with generating the contents
of the output directory that make up the static website.

All of this could technically be wrapped behind a `port` but that seems like
more abstraction than what it's worth.
"""

import datetime as dt

from pydantic_geojson import FeatureCollectionModel, FeatureModel

from ezio.domain.geo import simplify_track
from ezio.domain.model import OutputDirectory, Track


def write_geojson_files(
    output_directory: OutputDirectory,
    tracks_by_date: dict[dt.date, list[Track]],
) -> None:
    for date, tracks in tracks_by_date.items():
        filename: str = date.strftime("%Y-%m-%d.geojson")

        collection = FeatureCollectionModel(
            type="FeatureCollection",
            features=[
                FeatureModel(
                    type="Feature",
                    # TODO: call track simplification before passing data
                    # into write_geojson_files
                    geometry=simplify_track(track).to_geojson(),
                    bbox=None,
                )
                for track in tracks
            ],
            bbox=None,
        )

        geojson: str = collection.model_dump_json(indent=None)

        with open(output_directory.tracks_dir / filename, "w") as f:
            f.write(geojson)
