import json
from typing import Any


def to_json(data: Any) -> str:
    return json.dumps(data, indent=2, default=str)


def print_mapping(data: dict[str, Any], indent: int = 0) -> None:
    width = max((len(str(key)) for key in data), default=0)
    for key, value in data.items():
        if isinstance(value, dict):
            print(f"{' ' * indent}{key}:")
            print_mapping(value, indent + 2)
        else:
            print(f"{' ' * indent}{str(key).ljust(width)}  {value}")
