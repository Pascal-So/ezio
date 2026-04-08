from collections.abc import Generator
from pathlib import Path
from tempfile import TemporaryDirectory

from pytest import fixture


@fixture
def tempdir() -> Generator[Path, None, None]:
    """
    Temporary directory that will be deleted after the test has run
    """

    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@fixture
def data_dir() -> Path:
    return Path("tests/data/")
