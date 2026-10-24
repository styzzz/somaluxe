"""Tool registry shared by the five modules and the assistant."""
from dataclasses import dataclass
from typing import Any, Callable

READ = "read"
WRITE = "write"  # never executes directly; produces a pending action


@dataclass
class Tool:
    name: str
    module: str
    description: str
    input_schema: dict
    fn: Callable[..., Any]
    kind: str = READ

    def api_schema(self) -> dict:
        return {
            "name": self.name,
            "description": f"[{self.module}] {self.description}",
            "input_schema": self.input_schema,
        }


def schema(props: dict, required: list[str] | None = None) -> dict:
    return {"type": "object", "properties": props, "required": required or [],
            "additionalProperties": False}


INT = {"type": "integer"}
NUM = {"type": "number"}
STR = {"type": "string"}
