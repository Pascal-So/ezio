import argparse
from dataclasses import dataclass
from pathlib import Path

from ezio.adapters.gpx import GpxTrackLoader
from ezio.adapters.jawg import Jawg
from ezio.adapters.rich_progress import RichProgress
from ezio.domain.model import OutputDirectory
from ezio.domain.wizard import run_wizard


def main() -> None:
    args = _parse_args()

    # todo: logging config with level=os.environ.get('LOGLEVEL', 'INFO').upper()

    tile_source = Jawg()
    # tile_source = FakeTiles()
    track_loaders = [GpxTrackLoader()]
    progress = RichProgress()

    run_wizard(
        args.input_dir, args.output_directory, track_loaders, tile_source, progress
    )

    progress.stop()


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
