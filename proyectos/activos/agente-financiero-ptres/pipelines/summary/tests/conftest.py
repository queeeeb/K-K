import pytest

from pipelines.summary.tests.fixtures.make_fixtures import (
    make_facturacion_mayo,
    make_overview_consulting_mayo,
    make_provisiones_ds_mayo,
    make_provisiones_engineering_mayo,
    make_summary_abril,
)


@pytest.fixture(scope="session", autouse=True)
def generate_fixtures():
    make_summary_abril()
    make_facturacion_mayo()
    make_provisiones_ds_mayo()
    make_provisiones_engineering_mayo()
    make_overview_consulting_mayo()
