from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class PipelineSpec:
    name: str
    sources: list[str]
    interpret: Callable[..., Any]
    calculate: Callable[..., Any]
    write: Callable[..., Any]
    nombrar: Callable[..., Any] | None = None


@dataclass
class Plan:
    token: str
    pipeline: str
    mes: str
    resumen: dict
    detalle: dict
