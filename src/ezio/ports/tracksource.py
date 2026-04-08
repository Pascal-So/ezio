import datetime as dt
from abc import ABC, abstractmethod
from pathlib import Path

from pydantic_geojson import LineStringModel


class TrackLoader(ABC):
    @abstractmethod
    def load_tracks(
        self, file_path: Path
    ) -> list[tuple[dt.datetime, LineStringModel]] | None:
        pass
