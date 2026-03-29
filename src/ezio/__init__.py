import argparse
from dataclasses import dataclass
from pathlib import Path

from ezio.adapters.gpx import GpxTrackSource
from ezio.adapters.jawg import Jawg
from ezio.domain.model import OutputDirectory
from ezio.domain.wizard import run_wizard
from ezio.ports.tilesource import Tilesource
from ezio.ports.tracksource import Tracksource


def main() -> None:
    args = _parse_args()

    tile_source: Tilesource = Jawg()
    track_source: Tracksource = GpxTrackSource()

    run_wizard(args.output_directory, track_source, tile_source, args.input_dir)


@dataclass
class Args:
    input_dir: Path
    output_directory: OutputDirectory


def _parse_args() -> Args:
    parser = argparse.ArgumentParser(
        prog="Ezio", description="Display a recorded route as a static website"
    )

    _ = parser.add_argument("-i", "--input", required=True, type=str)
    _ = parser.add_argument("-o", "--output", required=True, type=str)

    args = parser.parse_args()

    if not isinstance(args.input, str) or not isinstance(args.output, str):
        raise TypeError()

    return Args(
        input_dir=Path(args.input), output_directory=OutputDirectory(args.output)
    )
