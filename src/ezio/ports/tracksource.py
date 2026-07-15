import datetime as dt
from abc import ABC, abstractmethod
from pathlib import Path

from ezio.domain.model import Track


class TrackLoader(ABC):
    @abstractmethod
    def load_tracks(self, file_path: Path) -> list[tuple[dt.datetime, Track]] | None:
        pass
