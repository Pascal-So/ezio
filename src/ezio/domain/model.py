import datetime as dt
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

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


class Data(BaseModel):
    segments: list[SegmentInfo]
    photos: list[PhotoInfo]
    background_segments: list[str]
    total_bounding_box: BoundingBox


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
        self.tracks_dir.mkdir(parents=True, exist_ok=True)
        self.background_segments_dir.mkdir(parents=True, exist_ok=True)
