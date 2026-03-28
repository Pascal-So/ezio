from pathlib import Path

from ezio.adapters.jawg import Jawg
from ezio.domain.geo import degree_range_to_index_range
from ezio.domain.types import Tilecoord
from ezio.ports.tilesource import Tilesource


def main() -> None:
    tilesource: Tilesource = Jawg()

    lat_range = (46.5, 47.7)
    lng_range = (7.1, 8.66)
    zoom_range = (0, 13)

    for zoom in range(*zoom_range):
        x_range = degree_range_to_index_range(lng_range, zoom, 1.5, "lng")
        y_range = degree_range_to_index_range(lat_range, zoom, 1.5, "lat")

        print(f"zoom = {zoom}, x_range = {x_range}, y_range = {y_range}")

        for x in range(*x_range):
            for y in range(*y_range):
                file_path = Path(f"public/img/tiles/{zoom}-{x}-{y}.png")

                if not file_path.exists():
                    print(f"getting {zoom} {x} {y}")

                    tile = tilesource.get_tile(Tilecoord(x=x, y=y, zoom=zoom))
                    with open(file_path, "wb") as f:
                        _ = f.write(tile)
