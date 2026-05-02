from abc import ABC, abstractmethod

from ezio.domain.model import Tile, Tilecoord


class Tilesource(ABC):
    @abstractmethod
    def get_tile(self, coord: Tilecoord) -> Tile:
        """Request a single map tile"""
        ...


# TODO: stadiamaps, mapbox, carto, etc. client?
# TODO: generic client which just takes a config string in https://tile.openstreetmap.org/{z}/{x}/{y}.png format?
