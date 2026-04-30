import logging
import os
from importlib.resources import path as rpath
from pathlib import Path
from shutil import rmtree

from ezio.domain.model import OutputDirectory

logger = logging.getLogger(__name__)


def copy_frontend(output_directory: OutputDirectory) -> None:
    """
    Copy the compiled frontend (html / js / etc.) into the output directory.

    This assumes that a directory called `dist` has been placed alongside
    this __init__.py file. That should be done in packaging.
    """

    # copy the bundled frontend files from the python package
    with rpath(__name__, "dist") as fspath:
        if _copy_dist_contents_if_exists(fspath, output_directory):
            return

    # fallback to frontend dev path in dev mode
    dev_dist_dir = _find_frontend_dev_dir()
    if _copy_dist_contents_if_exists(dev_dist_dir, output_directory):
        logger.info("Accessed compiled frontend via frontend dev path fallback")
        return

    raise Exception("Could not find compiled frontend")


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

    # TODO: replace title in the head of index.html with user provided title

    return True
