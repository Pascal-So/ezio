import datetime as dt
import logging
import re
from pathlib import Path
from typing import override

import pydantic_geojson._base as geojson_base
from pydantic_geojson import FeatureCollectionModel, FeatureModel
from pydantic_geojson.multi_line_string import LineStringCoordinates

from ezio.domain.model import Coord, Track
from ezio.ports.tracksource import TrackLoader

logger = logging.getLogger(__name__)


class GeoJsonTrackLoader(TrackLoader):
    """Load track segments from a GeoJson file"""

    @override
    def load_tracks(self, file_path: Path) -> list[tuple[dt.datetime, Track]] | None:
        if not file_path.is_file() or file_path.suffix != ".geojson":
            return None

        try:
            with open(file_path, "r") as file:
                text = file.read()
                feature_collection = FeatureCollectionModel.model_validate_json(text)

        except Exception as e:
            logger.warning(f"Skipping GPX file {file_path.name} due to error: {e}")
            return None

        logger.info(f"Reading {file_path.name}")

        filename_date = _get_date_from_filename(file_path.name)

        linestrings: list[tuple[dt.datetime, Track]] = []
        for feature_idx, feature in enumerate(feature_collection.features):
            geometry = feature.geometry
            if geometry is None:
                logger.warning(
                    f"Skipping feature {feature_idx} in file {file_path.name} because it contains no geometry"
                )
                continue

            if geometry.type != "LineString" and geometry.type != "MultiLineString":
                logger.warning(
                    f"Skipping feature {feature_idx} in file {file_path.name} because its geometry type is {geometry.type}"
                )
                continue

            datetime: dt.datetime | None = None
            if filename_date is not None:
                datetime = dt.datetime.combine(filename_date, dt.datetime.min.time())
            else:
                # If we don't have a date from the filename then let's try the feature name. Recordings from Locus that
                # were converted to GeoJSON should have this set.
                datetime = _get_date_from_feature_props(feature)

            if datetime is None:
                logger.warning(
                    f"Skipping feature {feature_idx} in file {file_path.name} because the date of the recording could not be determined"
                )
                continue

            if geometry.type == "LineString":
                linestrings.append((datetime, track_from_geojson(geometry.coordinates)))
            else:
                for linestring in geometry.coordinates:
                    linestrings.append((datetime, track_from_geojson(linestring)))

        logger.info(f"Read {len(linestrings)} LineString features")
        return linestrings


def _get_date_from_feature_props(feature: FeatureModel) -> dt.datetime | None:
    """
    Extract the date from the properties of a GeoJSON feature.
    """

    if feature.properties is None:
        return None

    feature_name: str | None = feature.properties.get("name")
    # TODO: try to get the full datetime instead of just the date
    feature_name_date = (
        _get_date_from_filename(feature_name) if feature_name is not None else None
    )
    if feature_name_date is None:
        return None

    feature_name_datetime = dt.datetime.combine(
        feature_name_date, dt.datetime.min.time()
    )

    return feature_name_datetime


# TODO: move to utility module
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


def coord_from_geojson(coord: geojson_base.Coordinates) -> Coord:
    return Coord(coord.lat, coord.lon, coord.alt)


def track_from_geojson(coords: LineStringCoordinates) -> Track:
    return Track(coords=[coord_from_geojson(coord) for coord in coords])
