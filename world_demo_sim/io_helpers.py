from __future__ import annotations

import json
import math
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def deep_merge(base: dict, override: dict) -> dict:
    merged = deepcopy(base)
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    extends = payload.pop("extends", None)
    if not extends:
        return payload
    base_path = (path.parent / extends).resolve()
    base_payload = load_yaml(base_path)
    return deep_merge(base_payload, payload)


def load_country_library(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def merge_numeric_effects(base: dict, delta: dict) -> dict:
    merged = deepcopy(base)
    for key, value in delta.items():
        if isinstance(value, (int, float)) and isinstance(merged.get(key), (int, float)):
            merged[key] = merged.get(key, 0.0) + value
        else:
            merged[key] = value
    return merged


def scenario_output_dir(base_dir: Path, scenario_key: str) -> Path:
    path = base_dir / scenario_key
    path.mkdir(parents=True, exist_ok=True)
    return path


def scenario_seed(config: dict, scenario: dict) -> int:
    base_seed = int(config.get("meta", {}).get("seed", 20260416))
    scenario_offset = sum((index + 1) * ord(char) for index, char in enumerate(scenario["key"]))
    return (base_seed + scenario_offset) % (2**32 - 1)


def weighted_average(rows: list[dict], key: str) -> float:
    total_weight = sum(row["population_weight"] for row in rows)
    if total_weight == 0:
        return 0.0
    return sum(row[key] * row["population_weight"] for row in rows) / total_weight


def write_csv(path: Path, rows: list[dict]) -> None:
    import csv

    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
