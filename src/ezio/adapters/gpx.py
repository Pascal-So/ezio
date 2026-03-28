import datetime as dt
import logging
import re
from pathlib import Path
from typing import override

import gpxpy
from gpxpy.gpx import GPXTrackSegment
from pydantic_geojson import LineStringModel
from pydantic_geojson._base import Coordinates

from ezio.ports.tracksource import Tracksource

logger = logging.getLogger(__name__)


class GpxTrackSource(Tracksource):
    """Load track segments from a directory containing GPX files"""

    def __init__(self) -> None:
        pass

    @override
    def get_tracks(self, directory: Path) -> list[tuple[dt.datetime, LineStringModel]]:
        gpx_files = list(directory.glob("*.gpx"))

        if len(gpx_files) == 0:
            logger.warning(f"No .gpx files found in the input directory {directory}")
            return []

        linestrings: list[tuple[dt.datetime, LineStringModel]] = []
        for gpx_path in gpx_files:
            try:
                with open(gpx_path, "r") as gpx_file:
                    gpx = gpxpy.parse(gpx_file)

            except Exception as e:
                logger.warning(f"Skipping file {gpx_path.name} due to error: {e}")
                continue

            logger.info(f"Reading {gpx_path.name}")

            filename_date = _get_date_from_filename(gpx_path.name)

            for track_idx, track in enumerate(gpx.tracks):
                for segment_idx, segment in enumerate(track.segments):
                    if len(segment.points) < 2:
                        continue

                    track_date = _get_date_from_gpx_segment(segment)

                    # if the GPX does not provide a date we fall back to filename
                    if not track_date:
                        if filename_date is not None:
                            logger.info(
                                f"  - GPX track {track_idx}, segment {segment_idx} does not contain time info. Using date from filename: {filename_date}"
                            )
                            track_date = dt.datetime.combine(
                                filename_date, dt.datetime.min.time()
                            )
                        else:
                            logger.warning(
                                f"Skipping track {track_idx}, segment {segment_idx} in file {gpx_path.name} because the date of the recording could not be determined"
                            )
                            continue

                    linestring = _segment_to_linestring(segment)
                    linestrings.append((track_date, linestring))

        return linestrings


def _segment_to_linestring(segment: GPXTrackSegment) -> LineStringModel:
    linestring = LineStringModel(
        coordinates=[
            Coordinates(lon=point.longitude, lat=point.latitude, alt=point.elevation)
            for point in segment.points
        ],
        type="LineString",
        bbox=None,
    )
    return linestring


def _get_date_from_gpx_segment(segment: GPXTrackSegment) -> dt.datetime | None:
    """
    Extract the date from the recorded GPX information.
    """

    if segment.points:
        first_point_time = segment.points[0].time
        if first_point_time:
            return first_point_time

    return None


def _get_date_from_filename(filename: str) -> dt.date | None:
    """
    Parses a date in the format YYYY-MM-DD or YYYY_MM_DD from a filename.
    """

    # Regex to find YYYY-MM-DD or YYYY_MM_DD
    match = re.search(r"(\d{4}[-_]\d{2}[-_]\d{2})", filename)
    if not match:
        return None

    date_str = match.group(1).replace("_", "-")
    try:
        return dt.date.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        # The matched string was not a valid date (e.g., '2023-13-40')
        return None
