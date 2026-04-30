import argparse
import datetime as dt
import logging
from dataclasses import dataclass
from pathlib import Path

from rich.logging import RichHandler

from ezio.adapters.gpx import GpxTrackLoader
from ezio.adapters.jawg import Jawg
from ezio.adapters.rich_progress import RichProgress
from ezio.adapters.textual_segment_info_source import TextualSegmentInfoSource
from ezio.domain.model import OutputDirectory
from ezio.domain.wizard import run_wizard

logger = logging.getLogger(__name__)


def main() -> None:
    try:
        args = _parse_args()
    except Exception as e:
        logger.error("Could not parse arguments")
        logger.error(str(e))
        exit(2)

    FORMAT = "%(message)s"
    logging.basicConfig(
        level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
    )

    # todo: logging config with level=os.environ.get('LOGLEVEL', 'INFO').upper()

    tile_source = Jawg()
    # tile_source = FakeTiles()
    track_loaders = [GpxTrackLoader()]
    segment_info_source = TextualSegmentInfoSource()
    progress = RichProgress()

    try:
        run_wizard(
            args.input_dir,
            args.output_directory,
            track_loaders,
            tile_source,
            progress,
            segment_info_source,
            start_date=args.start_date,
            end_date=args.end_date,
        )

    finally:
        progress.stop()


@dataclass
class Args:
    input_dir: Path
    output_directory: OutputDirectory
    start_date: dt.date | None
    end_date: dt.date | None


def _parse_args() -> Args:
    parser = argparse.ArgumentParser(
        prog="Ezio", description="Display a recorded route as a static website"
    )

    parser.add_argument("-i", "--input", required=True, type=str)
    parser.add_argument("-o", "--output", required=True, type=str)
    parser.add_argument("--start-date", required=False, type=str)
    parser.add_argument("--end-date", required=False, type=str)

    args = parser.parse_args()

    def parse_date(date: str | None, which: str) -> dt.date | None:
        if date is None:
            return None

        try:
            return dt.date.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise Exception(f"Date {which} is not in format YYYY-MM-DD: {date}")

    start_date = parse_date(args.start_date, "start-date")
    end_date = parse_date(args.end_date, "end-date")

    if start_date is not None and end_date is not None and start_date > end_date:
        raise Exception(f"Start date {start_date} is after end date {end_date}")

    return Args(
        input_dir=Path(args.input),
        output_directory=OutputDirectory(args.output),
        start_date=start_date,
        end_date=end_date,
    )
