import random
import time
from typing import override

import requests

from ezio.domain.types import Tile, Tilecoord
from ezio.ports.tilesource import Tilesource


class Jawg(Tilesource):
    """Request map tiles from jawg.io"""

    def __init__(self) -> None:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0",
                "Accept": "image/avif,image/webp,*/*",
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "en-GB,en;q=0.5",
                "Sec-Fetch-Dest": "image",
                "Sec-Fetch-Mode": "no-cors",
                "Sec-Fetch-Site": "cross-site",
                "Referer": "https://umap.openstreetmap.fr/",
            }
        )

        self._session: requests.Session = session
        self._api_key: str = "community"

    @override
    def get_tile(self, coord: Tilecoord) -> Tile:
        url = f"https://tile.jawg.io/dark/{coord.zoom}/{coord.x}/{coord.y}.png?api-key={self._api_key}"

        response = self._session.get(url)

        # Let's not spam the server too much, we're getting all those pretty map
        # tiles for free after all...
        time.sleep(random.random() * 0.4)

        if response.status_code >= 300:
            raise Exception(
                f"Request to {url} failed with {response.status_code} {response.content.decode('utf-8', errors='replace')}"
            )
        else:
            return response.content
