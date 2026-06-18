import datetime as dt

from pydantic import BaseModel, Field


class OldPhotoInfo(BaseModel):
    n: str
    w: int
    h: int
    tw: int
    th: int


class OldSegmentInfo(BaseModel):
    date: dt.date
    desc: str
    dist: float
    climb: float | None
    feat: str


class OldData(BaseModel):
    """
    Model of the pre-0.1.0 data format
    """

    segments: list[OldSegmentInfo]
    photos: list[OldPhotoInfo]
    background_segments: list[str] = Field(default=[])
