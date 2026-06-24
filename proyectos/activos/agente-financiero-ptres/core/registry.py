from core.pipeline_spec import PipelineSpec

_registry: dict[str, PipelineSpec] = {}


def register(spec: PipelineSpec) -> None:
    _registry[spec.name] = spec


def get(name: str) -> PipelineSpec:
    return _registry[name]


def clear_registry() -> None:
    _registry.clear()
