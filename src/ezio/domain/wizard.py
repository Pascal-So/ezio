import datetime as dt
import logging
from collections.abc import Collection, Iterable
from dataclasses import dataclass
from pathlib import Path

from pydantic_geojson import LineStringModel

from ezio.adapters.photo_source import load_photo  # todo: put this behind a port
from ezio.domain.generator import write_geojson_files
from ezio.domain.generator.photos import save_photo
from ezio.domain.geo import (
    bounding_box,
    climb,
    compute_required_map_tiles,
    merge_bounding_boxes,
    track_length_km,
)
from ezio.domain.model import Data, OutputDirectory, PhotoInfo, SegmentInfo, Tilecoord
from ezio.ports.progress import Progress
from ezio.ports.segment_info_source import SegmentInfoSource
from ezio.ports.tilesource import Tilesource
from ezio.ports.tracksource import TrackLoader

logger = logging.getLogger(__name__)


def run_wizard(
    source_directory: Path,
    output_directory: OutputDirectory,
    track_loaders: Collection[TrackLoader],
    tile_source: Tilesource,
    progress: Progress,
    segment_info_source: SegmentInfoSource,
) -> None:
    """
    The wizard guides the user through the steps to generate the static website
    """

    output_directory.create_directory_structure()

    inputs = load_input_files(source_directory, track_loaders, progress)

    segments: list[SegmentInfo] = []

    # group tracks by date
    tracks_by_date: dict[dt.date, list[LineStringModel]] = {}
    for taken_at, track in inputs.tracks:
        date = taken_at.date()
        if date not in tracks_by_date:
            tracks_by_date[date] = []

        tracks_by_date[date].append(track)

    # compute stats for tracks
    for date, tracks in tracks_by_date.items():
        distance_km: float = 0
        climb_m: float | None = 0

        for track in tracks:
            distance_km += track_length_km(track)

            if climb_m is None:
                continue

            c = climb(track)
            if c is None:
                climb_m = None
            else:
                climb_m += c

        bbox = merge_bounding_boxes([bounding_box(track) for track in tracks])

        segments.append(
            SegmentInfo(
                date=date,
                description="",
                dist_km=distance_km,
                climb_m=climb_m,
                featured_photo="",
                bounding_box=bbox,
            )
        )

    write_geojson_files(output_directory, tracks_by_date)

    total_bounding_box = merge_bounding_boxes([seg.bounding_box for seg in segments])

    photos: list[PhotoInfo] = []

    # convert and resize images
    for taken_at, photo in inputs.photos:
        # TODO: progress bar
        photo_info = save_photo(output_directory, photo, taken_at)
        photos.append(photo_info)

    if output_directory.json_path.is_file():
        logger.info(
            f"Existing data found in {output_directory.json_path}, merging with new data..."
        )

        with open(output_directory.json_path) as f:
            existing_data = Data.model_validate_json(f.read())

        available_photos = {photo.filename for photo in photos}
        merge_existing_segments(
            existing_segments=existing_data.segments,
            new_segments=segments,
            photos=available_photos,
        )

    data = Data(
        segments=segments,
        photos=photos,
        background_segments=[],
        total_bounding_box=total_bounding_box,
    )

    # download map tiles
    tile_coords = compute_required_map_tiles(total_bounding_box)
    download_tiles(tile_coords, tile_source, output_directory.tiles_dir, progress)

    segment_info_source.add_descriptions(data.segments)

    # save data.json
    with open(output_directory.json_path, "w") as f:
        _ = f.write(data.model_dump_json(indent=2))


@dataclass
class Inputs:
    photos: list[tuple[dt.datetime, Path]]
    tracks: list[tuple[dt.datetime, LineStringModel]]


def all_files(dir: Path) -> Iterable[Path]:
    """
    Recursively list all files in the directory. The directories themselves
    are not listed.
    """

    for root, _dirs, files in dir.walk():
        for file in files:
            file_path = root / file
            if not file_path.is_file():
                continue
            yield file_path


def load_input_files(
    input_dir: Path, loaders: Collection[TrackLoader], progress: Progress
) -> Inputs:
    inputs = Inputs(photos=[], tracks=[])

    files = list(all_files(input_dir))
    for file_path in progress.track(files, "Loading input files"):
        for loader in loaders:
            tracks = loader.load_tracks(file_path)
            if tracks is not None:
                # The track loader was successful, skip the remaining loaders
                inputs.tracks.extend(tracks)
                continue

        # if no track loader was successful, it might be a photo
        photo = load_photo(file_path)
        if photo is not None:
            inputs.photos.append(photo)
            continue

        logger.debug(f"No loader accepted file {file_path}, we thus ignore the file.")

    return inputs


def download_tiles(
    tile_coords: list[Tilecoord],
    tile_source: Tilesource,
    tiles_dir: Path,
    progress: Progress,
) -> None:
    for tile_coord in progress.track(tile_coords, description="Downloading map tiles"):
        path = tiles_dir / tile_coord.filename

        # skip tiles that we've already got
        if path.is_file():
            continue

        tile = tile_source.get_tile(tile_coord)
        with open(path, "wb") as f:
            _ = f.write(tile)


def merge_existing_segments(
    existing_segments: list[SegmentInfo],
    new_segments: list[SegmentInfo],
    photos: Collection[str],
) -> None:
    """
    Merge existing segment information from a previous generator run into the
    new list of segments from this run.

    This modifies the list `new_segments`
    """

    existing_segments_dict = {seg.date: seg for seg in existing_segments}

    for seg in new_segments:
        existing_seg = existing_segments_dict.get(seg.date)
        if existing_seg is None:
            continue

        seg.description = existing_seg.description
        if existing_seg.featured_photo in photos:
            seg.featured_photo = existing_seg.featured_photo
