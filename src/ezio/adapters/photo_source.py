import datetime as dt
import logging
from pathlib import Path

from PIL import ExifTags, Image, UnidentifiedImageError

logger = logging.getLogger(__name__)


def load_photo(file_path: Path) -> tuple[dt.datetime, Path] | None:
    if not file_path.is_file():
        return None

    try:
        image = Image.open(file_path)
        # TODO: check if we need to register additional openers
        # for HEIF and AVIF, or if this just works out of the box.
    except UnidentifiedImageError:
        return None
    except Exception:
        logger.exception(f"Cannot load photo {file_path}")
        return None

    taken_at = _get_date_taken(image, file_path)
    if taken_at is None:
        logger.info(
            f"skipping photo {file_path} because the capture date could not be determined"
        )
        return None

    return (taken_at, file_path)


def _get_date_taken(image: Image.Image, photo_file_path: Path) -> dt.datetime | None:
    exif = image.getexif()

    ifd_exif = exif.get_ifd(ExifTags.IFD.Exif)

    # On a photo that I tested I only had DateTimeOriginal and OffsetTime set,
    # so it seems that these values don't necessarily come in corresponding
    # pairs. We thus go through the fallback list separately for the datetime
    # and the offset.
    taken_at = _get_with_fallback(
        ifd_exif,
        ExifTags.Base.DateTimeOriginal,
        ExifTags.Base.DateTimeDigitized,
        ExifTags.Base.DateTime,
    )
    offset = _get_with_fallback(
        ifd_exif,
        ExifTags.Base.OffsetTimeOriginal,
        ExifTags.Base.OffsetTimeDigitized,
        ExifTags.Base.OffsetTime,
    )

    if taken_at is None:
        return None

    taken_at_str = f"{taken_at}{offset or ''}"
    try:
        return dt.datetime.strptime(taken_at_str, "%Y:%m:%d %H:%M:%S%z")
    except ValueError:
        logger.warning(
            f"photo {photo_file_path} contains invalid datetime {taken_at} with offset {offset}"
        )
        return None


def _get_with_fallback[T](exif: dict[int, T], *key: int) -> T | None:
    for k in key:
        val = exif.get(k)
        if val is not None:
            return val
    return None
