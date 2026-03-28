from dataclasses import dataclass


Tile = bytes


@dataclass
class Tilecoord:
    x: int
    y: int
    zoom: int
