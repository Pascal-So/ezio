"""
The `generator` module contains code associated with generating the contents
of the output directory that make up the static website.

All of this could technically be wrapped behind a `port` but that seems like
more abstraction than what it's worth.
"""

import datetime as dt
import logging
import subprocess
from collections.abc import Iterable
from pathlib import Path

from pydantic_geojson import FeatureCollectionModel, FeatureModel, MultiLineStringModel

from ezio.domain.model import (
    OutputDirectory,
    Track,
)

logger = logging.getLogger(__name__)


def write_geojson(
    output_directory: OutputDirectory,
    tracks_by_date: dict[dt.date, list[Track]],
) -> None:
    sorted_segments = sorted(tracks_by_date.items())

    sorted_segments_with_bbox = [
        (date, tracks, compute_geojson_bounding_box(tracks))
        for date, tracks in sorted_segments
    ]

    bounding_boxes = [
        bbox for _, _, bbox in sorted_segments_with_bbox if bbox is not None
    ]

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
                bbox=bbox,
            )
            for date, tracks, bbox in sorted_segments_with_bbox
        ],
        bbox=merge_geojson_bounding_boxes(bounding_boxes),
    )

    geojson: str = collection.model_dump_json(indent=None)

    with open(output_directory.segments_path, "w") as f:
        f.write(geojson)


def precompress_file(path: Path) -> None:
    """
    If brotli is available on this machine, compress the file so that a compressed
    version can be served from the web server.
    """

    compressed_suffix = path.suffix + ".br"
    compressed_path = path.with_suffix(compressed_suffix)

    if compressed_path.is_file():
        original_time = path.stat().st_ctime
        compressed_time = compressed_path.stat().st_ctime

        if original_time < compressed_time:
            logger.debug(
                f"Skipping compression of {path} because compressed file exists and is newer than original file ({original_time} < {compressed_time}"
            )
            return None

    try:
        subprocess.run(
            [
                "brotli",
                "-k",  # keep source file
                "-Z",  # use best compression level (11)
                "-f",  # overwrite existing compressed file
                path,
            ],
            shell=False,
            check=False,
            timeout=10.0,
        )
    except FileNotFoundError:
        # ignore error if brotli is not available
        logger.debug(f"Could not precompress {path} because brotli is not available")

    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout error for brotli compression of {path}")

        # Remove the generated file if it exists since we don't want
        # half-finished files.
        compressed_path.unlink(missing_ok=True)


def compute_geojson_bounding_box(tracks: list[Track]) -> list[float] | None:
    """
    Compute the bounding box as required by the geojson spec.

    The dimensionality of the bounding box must match that of the coordinates,
    i.e. if the data contains elevations then we must return 6 numbers rather
    than just 3.

    Returns None for empty data

    https://datatracker.ietf.org/doc/html/rfc7946#section-5
    """

    if len(tracks) == 0 or len(tracks[0].coords) == 0:
        return None

    first_coord = tracks[0].coords[0]
    bbox: list[float] = [first_coord.lng, first_coord.lat]
    if first_coord.alt is not None:
        bbox.append(first_coord.alt)

    dimensionality = len(bbox)

    bbox *= 2

    for track in tracks:
        for coord in track.coords:
            bbox[0] = min(bbox[0], coord.lng)
            bbox[1] = min(bbox[1], coord.lat)
            bbox[dimensionality] = max(bbox[dimensionality], coord.lng)
            bbox[dimensionality + 1] = max(bbox[dimensionality + 1], coord.lat)

            if coord.alt is not None:
                assert dimensionality == 3
                bbox[2] = min(bbox[2], coord.alt)
                bbox[5] = max(bbox[5], coord.alt)
            else:
                assert dimensionality == 2

    return bbox


def merge_geojson_bounding_boxes(
    bounding_boxes: Iterable[list[float]],
) -> list[float] | None:
    combined: list[float] | None = None

    for bbox in bounding_boxes:
        if combined is None:
            combined = bbox
        else:
            dimensionality: int = len(combined) // 2
            for i in range(0, dimensionality):
                combined[i] = min(combined[i], bbox[i])
            for i in range(dimensionality, dimensionality * 2):
                combined[i] = max(combined[i], bbox[i])

    return combined
