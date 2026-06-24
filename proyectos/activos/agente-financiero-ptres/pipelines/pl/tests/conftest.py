import pytest

from pipelines.pl.tests.fixtures.make_fixtures import make_contpaqi_marzo


@pytest.fixture(scope="session", autouse=True)
def generate_fixtures():
    make_contpaqi_marzo()
