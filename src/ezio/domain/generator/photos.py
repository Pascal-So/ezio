import datetime as dt
from pathlib import Path

from PIL import Image

from ezio.domain.model import OutputDirectory, PhotoInfo, Resolution


def save_photo(
    output_directory: OutputDirectory, photo_path: Path, taken_at: dt.datetime
) -> PhotoInfo:
    """Save the photo in large and thumbnail resolutions in the output directory"""

    new_filename: str = taken_at.strftime("%Y-%m-%d-%H-%M-%S") + ".webp"

    photo = Image.open(photo_path)
    orig_res = Resolution(x=photo.width, y=photo.height)

    # save the large version of the image
    large_res = _fit_resolution(orig_res, 1920)
    large = _resize_to(photo, large_res)
    large.save(output_directory.photos_dir / new_filename, method=6)

    # save the thumbnail image
    thumb_res = _fit_resolution(orig_res, 250)
    thumb = _resize_to(photo, thumb_res)
    thumb.save(output_directory.thumbs_dir / new_filename, quality=78, method=6)

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
