import pytest

from core.pipeline_spec import PipelineSpec
from core.registry import clear_registry, get, register


@pytest.fixture(autouse=True)
def reset_registry():
    clear_registry()
    yield
    clear_registry()


def _dummy(*args, **kwargs):
    return {}


def test_register_and_get():
    spec = PipelineSpec(name="dummy", sources=["a.xlsx"], interpret=_dummy, calculate=_dummy, write=_dummy)
    register(spec)

    assert get("dummy") is spec


def test_get_unknown_raises_key_error():
    with pytest.raises(KeyError):
        get("does-not-exist")
