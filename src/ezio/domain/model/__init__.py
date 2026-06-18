import datetime as dt
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field

from ezio.domain.model.old_model import OldData, OldSegmentInfo

Tile = bytes


@dataclass
class Tilecoord:
    x: int
    y: int
    zoom: int

    @property
    def filename(self) -> str:
        return f"{self.zoom}-{self.x}-{self.y}.png"


class Resolution(BaseModel):
    """Photo resolution"""

    x: int
    y: int


class PhotoInfo(BaseModel):
    filename: str
    date: dt.date
    res: Resolution
    thumb_res: Resolution


class BoundingBox(BaseModel):
    min_lat: float
    min_lng: float
    max_lat: float
    max_lng: float


class SegmentInfo(BaseModel):
    date: dt.date
    description: str
    dist_km: float
    climb_m: float | None
    featured_photo: str | None
    bounding_box: BoundingBox
    nr_photos: int | None = Field(default=None)


class Data(BaseModel):
    segments: list[SegmentInfo]
    photos: list[PhotoInfo]
    background_segments: list[str]
    total_bounding_box: BoundingBox
    max_zoom_level: int


class OutputDirectory(Path):
    """Directory where the generated static website is written to"""

    @property
    def photos_dir(self) -> Path:
        return self / "img" / "photos" / "large"

    @property
    def thumbs_dir(self) -> Path:
        return self / "img" / "photos" / "thumb"

    @property
    def tiles_dir(self) -> Path:
        return self / "img" / "tiles"

    @property
    def plots_dir(self) -> Path:
        return self / "img" / "plots"

    @property
    def tracks_dir(self) -> Path:
        return self / "tracks"

    @property
    def background_segments_dir(self) -> Path:
        return self / "background-segments"

    @property
    def json_path(self) -> Path:
        return self / "data.json"

    def create_directory_structure(self) -> None:
        """Create all the required subdirectories"""
        self.mkdir(exist_ok=True)

        self.photos_dir.mkdir(parents=True, exist_ok=True)
        self.thumbs_dir.mkdir(parents=True, exist_ok=True)
        self.tiles_dir.mkdir(parents=True, exist_ok=True)
        self.plots_dir.mkdir(parents=True, exist_ok=True)
        self.tracks_dir.mkdir(parents=True, exist_ok=True)
        self.background_segments_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class ExistingData:
    background_segments: list[str]
    segments: list[SegmentInfo]


def load_existing_data(json_path: Path) -> ExistingData:
    """
    Try to load the contents of the existing data.json with fallbacks to older
    data formats.
    """

    with open(json_path) as f:
        json = f.read()

    try:
        existing_data = Data.model_validate_json(json)

        return ExistingData(
            background_segments=existing_data.background_segments,
            segments=existing_data.segments,
        )
    except Exception as e:
        # Format doesn't match, let's try the old format

        try:
            existing_old_data = OldData.model_validate_json(json)
        except Exception:
            # The old format doesn't match either. Let's re-raise the original
            # error message for the new format because that's probably more
            # instructive.
            raise e

        def convert_old_segment(old_segment: OldSegmentInfo) -> SegmentInfo:
            return SegmentInfo(
                date=old_segment.date,
                description=old_segment.desc,
                dist_km=old_segment.dist,
                climb_m=old_segment.climb,
                featured_photo=old_segment.feat,
                bounding_box=BoundingBox(min_lat=0, max_lat=0, min_lng=0, max_lng=0),
                nr_photos=None,
            )

        return ExistingData(
            background_segments=existing_old_data.background_segments,
            segments=list(map(convert_old_segment, existing_old_data.segments)),
        )
