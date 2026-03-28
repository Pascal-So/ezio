from abc import ABC, abstractmethod

from ezio.domain.types import Tile, Tilecoord


class Tilesource(ABC):
    @abstractmethod
    def get_tile(self, coord: Tilecoord) -> Tile:
        """Request a single map tile"""
        ...
