import datetime as dt
from abc import ABC, abstractmethod
from pathlib import Path

from pydantic_geojson import LineStringModel


class Tracksource(ABC):
    @abstractmethod
    def get_tracks(self, directory: Path) -> list[tuple[dt.datetime, LineStringModel]]:
        pass
