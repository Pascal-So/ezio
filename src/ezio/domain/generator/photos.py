import datetime as dt
import logging
from pathlib import Path

from PIL import Image, ImageOps

from ezio.domain.model import OutputDirectory, PhotoInfo, Resolution

logger = logging.getLogger(__name__)


def save_photo(
    output_directory: OutputDirectory, photo_path: Path, taken_at: dt.datetime
) -> PhotoInfo:
    """Save the photo in large and thumbnail resolutions in the output directory"""

    new_filename: str = taken_at.strftime("%Y-%m-%d-%H-%M-%S") + ".webp"

    large_output_path: Path = output_directory.photos_dir / new_filename
    thumb_output_path: Path = output_directory.thumbs_dir / new_filename

    if large_output_path.is_file() and thumb_output_path.is_file():
        logger.info(
            f"Skipping photo {photo_path} because output file {new_filename} already exists"
        )

    photo = Image.open(photo_path)

    # apply exif orientation
    ImageOps.exif_transpose(photo, in_place=True)

    orig_res = Resolution(x=photo.width, y=photo.height)

    # save the large version of the image
    large_res = _fit_resolution(orig_res, 1920)
    large = _resize_to(photo, large_res)
    large.save(large_output_path, method=6)

    # save the thumbnail image
    thumb_res = _fit_resolution(orig_res, 250)
    thumb = _resize_to(photo, thumb_res)
    thumb.save(thumb_output_path, quality=78, method=6)

    return PhotoInfo(
        filename=new_filename,
        date=taken_at.date(),
        res=large_res,
        thumb_res=thumb_res,
    )


def _resize_to(photo: Image.Image, res: Resolution) -> Image.Image:
    return photo.resize(size=(res.x, res.y), resample=Image.Resampling.LANCZOS)


def _fit_resolution(res: Resolution, max_sidelength: int) -> Resolution:
    """Compute the new resolution for the photo"""

    ratio: float = max_sidelength / max(res.x, res.y)

    # ensure that we don't grow the image resolution
    ratio = min(ratio, 1)

    return Resolution(x=int(res.x * ratio), y=int(res.y * ratio))
