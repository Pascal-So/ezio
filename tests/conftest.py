from collections.abc import Generator
from pathlib import Path
from tempfile import TemporaryDirectory

from pydantic_geojson import FeatureCollectionModel
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


@fixture
def balkan_featurecollection(data_dir: Path) -> FeatureCollectionModel:
    with open(data_dir / "balkan-simplified.geojson") as f:
        collection = FeatureCollectionModel.model_validate_json(f.read())
    return collection
