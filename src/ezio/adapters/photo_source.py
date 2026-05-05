import datetime as dt
import logging
from pathlib import Path

from PIL import ExifTags, Image, UnidentifiedImageError

from ezio.domain.model import PhotoDetails

logger = logging.getLogger(__name__)


def load_photo(file_path: Path) -> PhotoDetails | None:
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

    exif = image.getexif()
    make_model = _get_make_model(exif)
    name = str(file_path)
    if make_model is not None:
        name += f" ({make_model})"
    taken_at = _get_date_taken(exif, name)

    if taken_at is None:
        logger.info(
            f"skipping photo {file_path} because the capture date could not be determined"
        )
        return None

    return PhotoDetails(taken_at, file_path, make_model)


def _get_make_model(exif: Image.Exif) -> str | None:
    make = exif.get(ExifTags.Base.Make)
    model = exif.get(ExifTags.Base.Model)

    make_model = f"{make or ''} {model or ''}".strip()
    if make_model == "":
        return None
    else:
        return make_model


def _get_date_taken(exif: Image.Exif, name: str) -> dt.datetime | None:
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

    if offset is None:
        try:
            # parsing without timezone
            datetime = dt.datetime.strptime(taken_at_str, "%Y:%m:%d %H:%M:%S")
            logger.info(
                f"found photo {name} with capture time {taken_at_str} (no time zone specified)"
            )
            return datetime
        except ValueError:
            logger.warning(f"photo {name} contains invalid datetime {taken_at}")
            return None
    else:
        try:
            # parsing with timezone
            datetime = dt.datetime.strptime(taken_at_str, "%Y:%m:%d %H:%M:%S%z")
            logger.info(f"found photo {name} with capture time {taken_at_str}")
            return datetime
        except ValueError:
            logger.warning(
                f"photo {name} contains invalid datetime {taken_at} with offset {offset}"
            )
            return None


def _get_with_fallback[T](exif: dict[int, T], *key: int) -> T | None:
    for k in key:
        val = exif.get(k)
        if val is not None:
            return val
    return None
