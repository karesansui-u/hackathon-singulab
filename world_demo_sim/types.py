from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class CountryMeta:
    code: str
    name: str
    name_ja: str
    tier: str = ""
    region_id: str = ""
    role_tags: tuple[str, ...] = ()
    primary_axes: tuple[str, ...] = ()
    secondary_axes: tuple[str, ...] = ()
    reason_short: str = ""
    lon: float = 0.0
    lat: float = 0.0


@dataclass(slots=True)
class CountrySelectionResult:
    config: dict[str, Any]
    preset: str
    library_path: Path
    countries: dict[str, CountryMeta]

    def as_config(self) -> dict[str, Any]:
        return self.config


@dataclass(slots=True)
class ScenarioRunResult:
    rows: list[dict[str, Any]]
    aggregate_rows: list[dict[str, Any]]
    event_log: list[dict[str, Any]]
    summary: dict[str, Any]
    final_rows: list[dict[str, Any]]
    conflict_rows: list[dict[str, Any]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "rows": self.rows,
            "aggregate_rows": self.aggregate_rows,
            "event_log": self.event_log,
            "summary": self.summary,
            "final_rows": self.final_rows,
            "conflict_rows": self.conflict_rows,
        }
