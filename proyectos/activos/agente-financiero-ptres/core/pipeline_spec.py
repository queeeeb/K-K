from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class PipelineSpec:
    name: str
    sources: list[str]
    interpret: Callable[..., Any]
    calculate: Callable[..., Any]
    write: Callable[..., Any]


@dataclass
class Plan:
    token: str
    pipeline: str
    mes: str
    resumen: dict
    detalle: dict
