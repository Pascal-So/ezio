import argparse
import datetime as dt
import logging
import textwrap
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

    logging.basicConfig(
        level="DEBUG" if args.verbose else "INFO",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler()],
    )

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
            title=args.title,
        )

        progress.stop()

    except Exception as e:
        progress.stop()
        logger.error(str(e))


@dataclass
class Args:
    title: str | None
    input_dir: Path
    output_directory: OutputDirectory
    start_date: dt.date | None
    end_date: dt.date | None
    verbose: bool


def _parse_args() -> Args:
    parser = argparse.ArgumentParser(
        prog="Ezio",
        formatter_class=argparse.RawDescriptionHelpFormatter,  # allow for newlines in description
        description=textwrap.dedent("""\
            Display a recorded route as a static website.

            Place recorded tracks and photos in the input directory. Subdirectoies
            are allowed. After running the generator, copy the contents of the
            output directory to your static file host.
        """),
        epilog="For more detailed usage information check the README at https://github.com/Pascal-So/ezio#usage",
    )

    parser.add_argument(
        "--title",
        required=False,
        type=str,
        help="Title of the generated HTML page that will be shown in the browser",
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        type=str,
        help="Directory where input files (photos and .gpx) are located",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=str,
        help="Output directory where the static website should be generated",
    )
    parser.add_argument(
        "--start-date",
        required=False,
        type=str,
        help="Only consider tracks in the input that were recorded on or after this day",
    )
    parser.add_argument(
        "--end-date",
        required=False,
        type=str,
        help="Only consider tracks in the input that were recorded on or before this day",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show more detailed logs",
    )

    args = parser.parse_args()

    def parse_date(date: str | None, which: str) -> dt.date | None:
        if date is None:
            return None

        try:
            return dt.date.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise Exception(f"Date {which} is not in format YYYY-MM-DD: {date}")

    start_date = parse_date(args.start_date, "start-date")  # pyright:ignore[reportAny]
    end_date = parse_date(args.end_date, "end-date")  # pyright:ignore[reportAny]

    if start_date is not None and end_date is not None and start_date > end_date:
        raise Exception(f"Start date {start_date} is after end date {end_date}")

    return Args(
        title=args.title,  # pyright:ignore[reportAny]
        input_dir=Path(args.input),  # pyright:ignore[reportAny]
        output_directory=OutputDirectory(args.output),  # pyright:ignore[reportAny]
        start_date=start_date,
        end_date=end_date,
        verbose=args.verbose,  # pyright:ignore[reportAny]
    )
