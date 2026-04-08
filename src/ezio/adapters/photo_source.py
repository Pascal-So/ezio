import datetime as dt
import logging
from pathlib import Path

import exifread
from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)


def load_photo(file_path: Path) -> tuple[dt.datetime, Path] | None:
    if not file_path.is_file():
        return None

    try:
        _ = Image.open(file_path)
    except UnidentifiedImageError:
        return None
    except Exception:
        logger.exception(f"Cannot load photo {file_path}")
        return None

    taken_at = _get_date_taken(file_path)
    if taken_at is None:
        logger.info(
            f"skipping photo {file_path} because the capture date could not be determined"
        )
        return None

    return (taken_at, file_path)


# TODO: drop dependency on exifread and just use exif info in Pillow instead?
# https://stackoverflow.com/a/75357594/5817996
def _get_date_taken(photo_file_path: Path) -> dt.datetime | None:
    with open(photo_file_path, "rb") as fh:
        tags = exifread.process_file(fh)
        date_time_original = tags.get("EXIF DateTimeOriginal")
        date_time = tags.get("EXIF DateTime")
        taken_at = date_time_original if date_time_original is not None else date_time

    if taken_at is None:
        return None

    try:
        return dt.datetime.strptime(taken_at.values, "%Y:%m:%d %H:%M:%S")
    except ValueError:
        logger.warning(
            f"photo {photo_file_path} contains invalid datetime {taken_at.values}"
        )
        return None
