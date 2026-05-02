import logging
import os
from importlib.resources import path as rpath
from pathlib import Path
from shutil import rmtree

from ezio.domain.model import OutputDirectory

logger = logging.getLogger(__name__)


def copy_frontend(output_directory: OutputDirectory, title: str | None) -> None:
    """
    Copy the compiled frontend (html / js / etc.) into the output directory.

    This assumes that a directory called `dist` has been placed alongside
    this __init__.py file. That should be done in packaging.
    """

    copied_frontend = False

    # copy the bundled frontend files from the python package
    with rpath(__name__, "dist") as fspath:
        if _copy_dist_contents_if_exists(fspath, output_directory):
            copied_frontend = True

    if not copied_frontend:
        # fallback to frontend dev path in dev mode
        dev_dist_dir = _find_frontend_dev_dir()
        if _copy_dist_contents_if_exists(dev_dist_dir, output_directory):
            logger.info("Accessed compiled frontend via frontend dev path fallback")
            copied_frontend = True

    if copied_frontend:
        if title is not None:
            replace_html_title(output_directory / "index.html", title)
    else:
        logger.error(
            "Could not find compiled frontend. This might be a packaging error, or you might have to run `just build-frontend` in the project source directory."
        )


def _find_frontend_dev_dir() -> Path:
    current_dir = Path(__file__).parent

    while current_dir.name != "src":
        current_dir = current_dir.parent

    return current_dir.parent / "frontend" / "dist"


def _copy_dist_contents_if_exists(
    dist_dir: Path, output_directory: OutputDirectory
) -> bool:
    if not dist_dir.is_dir():
        return False

    asset_target_dir = output_directory / "assets"
    index_target_path = output_directory / "index.html"
    if asset_target_dir.is_dir() or index_target_path.is_file():
        logger.info("removing existing frontend files from output directory")

        if asset_target_dir.is_dir():
            rmtree(asset_target_dir)
        if index_target_path.is_file():
            os.remove(index_target_path)

    (dist_dir / "assets").copy_into(output_directory)
    (dist_dir / "index.html").copy_into(output_directory)

    return True


def replace_html_title(html_path: Path, title: str) -> None:
    """Replace the title of the index.html file. Modifies the file in place."""

    with open(html_path) as f:
        html = f.read()

    new_html = html.replace("Ezio Track Viewer", title)

    with open(html_path, "w") as f:
        f.write(new_html)
