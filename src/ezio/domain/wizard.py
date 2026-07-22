import datetime as dt
import logging
from collections.abc import Collection, Iterable
from dataclasses import dataclass
from pathlib import Path

from ezio.adapters.photo_source import load_photo  # todo: put this behind a port
from ezio.domain.generator import write_geojson_files
from ezio.domain.generator.frontend import copy_frontend
from ezio.domain.generator.photos import save_photo
from ezio.domain.generator.plot import plot_segment
from ezio.domain.geo import (
    bounding_box,
    climb,
    compute_required_map_tiles,
    merge_bounding_boxes,
    simplify_track,
    track_length_km,
)
from ezio.domain.model import (
    BoundingBox,
    Data,
    OutputDirectory,
    PhotoInfo,
    SegmentInfo,
    Tilecoord,
    Track,
    load_existing_data,
)
from ezio.ports.progress import Progress
from ezio.ports.segment_info_source import SegmentInfoSource
from ezio.ports.tilesource import Tilesource
from ezio.ports.tracksource import TrackLoader

logger = logging.getLogger(__name__)


@dataclass
class Statistics:
    segments: dict[dt.date, SegmentInfo]
    total_distance_km: float
    total_bounding_box: BoundingBox


def compute_statistics(
    tracks_by_date: dict[dt.date, list[Track]],
) -> Statistics:
    segments: dict[dt.date, SegmentInfo] = {}
    total_distance_km: float = 0

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

        total_distance_km += distance_km

        bbox = merge_bounding_boxes([bounding_box(track) for track in tracks])

        segments[date] = SegmentInfo(
            date=date,
            description="",
            dist_km=distance_km,
            climb_m=climb_m,
            featured_photo=None,
            bounding_box=bbox,
        )

    total_bbox = merge_bounding_boxes([seg.bounding_box for seg in segments.values()])
    return Statistics(segments, total_distance_km, total_bbox)


def run_wizard(
    source_directories: list[Path],
    output_directory: OutputDirectory,
    track_loaders: Collection[TrackLoader],
    tile_source: Tilesource,
    progress: Progress,
    segment_info_source: SegmentInfoSource,
    start_date: dt.date | None,
    end_date: dt.date | None,
    title: str | None,
) -> None:
    """
    The wizard guides the user through the steps to generate the static website
    """

    output_directory.create_directory_structure()

    inputs = load_input_files(
        source_directories, track_loaders, progress, start_date, end_date
    )
    if len(inputs.tracks) == 0:
        raise Exception(
            f"No tracks were found in the input directory {source_directories}"
        )
    sort_photos(inputs.photos)

    tracks_by_date = group_tracks_by_date(inputs.tracks)
    statistics = compute_statistics(tracks_by_date)
    anonymized_tracks: dict[dt.date, list[Track]] = {
        date: [simplify_track(track) for track in tracks]
        for date, tracks in tracks_by_date.items()
    }
    bounding_boxes = {
        date: seg.bounding_box for date, seg in statistics.segments.items()
    }

    write_geojson_files(
        output_directory,
        anonymized_tracks,
        bounding_boxes,
        statistics.total_bounding_box,
    )

    photos: list[PhotoInfo] = []

    # convert and resize photos
    for taken_at, photo in progress.track(
        inputs.photos, "Converting and resizing photos"
    ):
        photo_info = save_photo(output_directory, photo, taken_at)
        photos.append(photo_info)

    background_segments: list[str] = []
    segments: list[SegmentInfo] = list(statistics.segments.values())

    if output_directory.json_path.is_file():
        logger.info(
            f"Existing data found in {output_directory.json_path}, merging with new data"
        )

        existing_data = load_existing_data(output_directory.json_path)

        background_segments = existing_data.background_segments

        available_photos = {photo.filename for photo in photos}
        merge_existing_segments(
            existing_segments=existing_data.segments,
            new_segments=segments,
            photos=available_photos,
        )

    max_zoom_level = 10
    data = Data(
        segments=segments,
        photos=photos,
        background_segments=background_segments,
        total_bounding_box=statistics.total_bounding_box,
        max_zoom_level=max_zoom_level,
    )

    # download map tiles
    tile_coords = compute_required_map_tiles(
        statistics.total_bounding_box, max_zoom_level
    )

    try:
        download_tiles(tile_coords, tile_source, output_directory.tiles_dir, progress)
    except Exception:
        logger.warning(
            "Error while downloading map tiles, some tiles might be missing",
            exc_info=True,
        )

    # generate plots
    for date, tracks in tracks_by_date.items():
        filename = output_directory.plots_dir / date.strftime("%Y-%m-%d.svg")
        plot_segment(tracks, filename)

    count_photos_per_segment(photos, segments)
    segment_info_source.add_descriptions(data.segments)

    # save data.json
    with open(output_directory.json_path, "w") as f:
        f.write(data.model_dump_json(indent=2))

    # add the frontend to the output directory
    copy_frontend(output_directory, title)

    logger.info(f"Total track distance: {statistics.total_distance_km:.2f} km")


@dataclass
class Inputs:
    photos: list[tuple[dt.datetime, Path]]
    tracks: list[tuple[dt.datetime, Track]]


def all_files(path: Path) -> Iterable[Path]:
    """
    Recursively list all files in the directory. The directories themselves
    are not listed.

    If the given path is a file, just return that file directly.
    """

    if path.is_file():
        yield path
    elif path.is_dir():
        for root, _dirs, files in path.walk():
            for file in files:
                file_path = root / file
                if not file_path.is_file():
                    continue
                yield file_path
    else:
        raise Exception(f"The given input path {path} does not exist")


def load_input_files(
    input_paths: list[Path],
    loaders: Collection[TrackLoader],
    progress: Progress,
    start_date: dt.date | None,
    end_date: dt.date | None,
) -> Inputs:
    inputs = Inputs(photos=[], tracks=[])

    loaded_tracks = 0
    skipped_tracks = 0
    track_files = 0

    files = [file for input_path in input_paths for file in all_files(input_path)]
    for file_path in progress.track(files, "Loading input files"):
        for loader in loaders:
            tracks = loader.load_tracks(file_path)
            if tracks is not None:
                for track in tracks:
                    date = track[0].date()

                    # Only keep tracks from dates in the selected range
                    if start_date is not None and date < start_date:
                        skipped_tracks += 1
                        continue
                    if end_date is not None and date > end_date:
                        skipped_tracks += 1
                        continue

                    loaded_tracks += 1

                    inputs.tracks.append(track)

                # The track loader was successful, skip the remaining loaders
                track_files += 1
                continue

        # if no track loader was successful, it might be a photo
        photo = load_photo(file_path)
        if photo is not None:
            inputs.photos.append(photo)
            continue

        logger.debug(f"No loader accepted file {file_path}, we thus ignore the file.")

    if start_date is not None or end_date is not None:
        logger.info(
            f"{skipped_tracks} tracks were skipped because they were outside the selected date range"
        )
    logger.info(f"Loaded {loaded_tracks} tracks from {track_files} files")

    return inputs


def download_tiles(
    tile_coords: list[Tilecoord],
    tile_source: Tilesource,
    tiles_dir: Path,
    progress: Progress,
) -> None:
    skipped_tiles: int = 0

    for tile_coord in progress.track(tile_coords, description="Downloading map tiles"):
        path = tiles_dir / tile_coord.filename

        # skip tiles that we've already got
        if path.is_file():
            skipped_tiles += 1
            continue

        tile = tile_source.get_tile(tile_coord)
        with open(path, "wb") as f:
            f.write(tile)

    if skipped_tiles > 0:
        logger.info(
            f"Skipped {skipped_tiles} already existing tiles out of {len(tile_coords)} tiles"
        )


def merge_existing_segments(
    existing_segments: Iterable[SegmentInfo],
    new_segments: Iterable[SegmentInfo],
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


def sort_photos(photos: list[tuple[dt.datetime, Path]]) -> None:
    """
    Best-effort sorting of photos by datetime, dealing with various
    time zone shennanigans.
    """

    timezones = {datetime.utcoffset() for (datetime, _) in photos}

    if len(timezones) <= 1:
        # All photos have the same time zone information, just sort directly.
        photos.sort()
        return

    if None in timezones:
        # Some photos don't have a time zone set, let's just use local time
        # for everything
        logger.warning(
            "sorting photos by directly comparing local times, ignoring time zone info"
        )
        photos.sort(key=lambda p: p[0].replace(tzinfo=None))
        return

    # Otherwise we have photos which all have time zone info, but not all photos
    # are from the same time zone
    logger.warning(f"Not all photos are from the same time zone: {timezones}")
    photos.sort()


def group_tracks_by_date(
    tracks: list[tuple[dt.datetime, Track]],
) -> dict[dt.date, list[Track]]:
    tracks_by_date: dict[dt.date, list[Track]] = {}

    # TODO: figure out time sorting stuff.
    #       Problem 1: track might not have tz info?
    #       Problem 2: track might just have a date without time
    for track_datetime, track in sorted(
        tracks, key=lambda val: (val[0].date(), val[0].hour)
    ):
        date = track_datetime.date()

        if date not in tracks_by_date:
            tracks_by_date[date] = []

        tracks_by_date[date].append(track)

    return tracks_by_date


def count_photos_per_segment(
    photos: list[PhotoInfo], segments: list[SegmentInfo]
) -> None:
    """
    Modify the `segments` list to fix the `nr_photos` field on every `SegmentInfo`.
    """

    by_date: dict[dt.date, int] = {}

    for photo in photos:
        if photo.date not in by_date:
            by_date[photo.date] = 0

        by_date[photo.date] += 1

    for segment in segments:
        segment.nr_photos = by_date.get(segment.date, 0)
