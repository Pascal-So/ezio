import datetime as dt
from pathlib import Path

from pydantic_geojson import LineStringModel

from ezio.adapters.photo_source import list_photos  # todo: put this behind a port
from ezio.domain.generator import write_geojson_files
from ezio.domain.generator.photos import save_photo
from ezio.domain.geo import (
    bounding_box,
    climb,
    compute_required_map_tiles,
    track_length_km,
)
from ezio.domain.model import Data, OutputDirectory, SegmentInfo
from ezio.ports.tilesource import Tilesource
from ezio.ports.tracksource import Tracksource


def run_wizard(
    output_directory: OutputDirectory,
    track_source: Tracksource,
    tile_source: Tilesource,
    source_directory: Path,
) -> None:
    """
    The wizard guides the user through the steps to generate the static website
    """

    output_directory.create_directory_structure()

    photos = list_photos(source_directory)
    tracks_with_dt = track_source.get_tracks(source_directory)

    # TODO: if data already exists then we load it from disk and skip to the
    # data input section
    data = Data(segments=[], photos=[], background_segments=[])

    # group tracks by date
    tracks_by_date: dict[dt.date, list[LineStringModel]] = {}
    for taken_at, track in tracks_with_dt:
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

        data.segments.append(
            SegmentInfo(
                date=date,
                description="",
                dist_km=distance_km,
                climb_m=climb_m,
                featured_photo="",
            )
        )

    write_geojson_files(output_directory, tracks_by_date)

    # convert and resize images
    for taken_at, photo in photos:
        # TODO: progress bar
        photo_info = save_photo(output_directory, photo, taken_at)
        data.photos.append(photo_info)

    # download map tiles
    bbox = bounding_box([track for _, track in tracks_with_dt])
    tile_coords = compute_required_map_tiles(bbox)
    print(f"total: {len(tile_coords)} tiles")
    for tile_coord in tile_coords:
        # TODO: progress bar
        path = output_directory.tiles_dir / tile_coord.filename

        # skip tiles that we've already got
        if path.is_file():
            continue

        tile = tile_source.get_tile(tile_coord)
        with open(path, "wb") as f:
            _ = f.write(tile)

    # TODO: data input section where we ask the user for segment names
    # and segment featured photos

    # save data.json
    with open(output_directory.json_path, "w") as f:
        _ = f.write(data.model_dump_json(indent=2))
