from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from .io_helpers import deep_merge, load_country_library, merge_numeric_effects
from .types import CountryMeta, CountrySelectionResult


def resolve_country_selection(
    config: dict,
    config_path: Path,
    country_set_override: str | None = None,
) -> CountrySelectionResult:
    selection = config.get("country_selection")
    if not selection:
        return CountrySelectionResult(
            config=deepcopy(config),
            preset="",
            library_path=config_path,
            countries={},
        )

    library_path = (config_path.parent / selection["library"]).resolve()
    library = load_country_library(library_path)
    preset_name = country_set_override or selection.get("preset", "core_30")
    preset = library["presets"][preset_name]
    profiles = library["profiles"]
    tier_order = {"T1": 1, "T2": 2, "T3": 3}
    include_codes = set(preset.get("include_codes", []))
    exclude_codes = set(preset.get("exclude_codes", []))
    by_code = {entry["code"]: entry for entry in library["countries"]}

    missing_codes = sorted(code for code in include_codes | exclude_codes if code not in by_code)
    if missing_codes:
        raise ValueError(f"Unknown country codes in preset '{preset_name}': {', '.join(missing_codes)}")

    selected_map = {
        entry["code"]: deepcopy(entry)
        for entry in library["countries"]
        if entry["tier"] in preset["tiers"] and entry["code"] not in exclude_codes
    }
    for code in include_codes:
        if code in exclude_codes:
            continue
        selected_map[code] = deepcopy(by_code[code])

    selected_entries = list(selected_map.values())
    selected_entries.sort(
        key=lambda entry: (
            0 if entry["code"] in include_codes else 1,
            tier_order.get(entry["tier"], 99),
            entry.get("phase1_priority", 999),
            entry["code"],
        )
    )
    selected_entries = selected_entries[: preset["max_countries"]]
    selected_codes = {entry["code"] for entry in selected_entries}

    resolved = deepcopy(config)
    resolved_countries: list[dict[str, Any]] = []
    layout: dict[str, dict[str, float]] = {}
    selected_metadata: dict[str, CountryMeta] = {}

    for entry in selected_entries:
        state = deepcopy(profiles[entry["profile"]])
        state = deep_merge(state, entry.get("overrides", {}))
        state["code"] = entry["code"]
        state["name"] = entry["name"]
        state["name_ja"] = entry.get("name_ja", entry["name"])
        state["population_weight"] = entry["population_weight"]
        state["lon"] = entry["lon"]
        state["lat"] = entry["lat"]
        state["tier"] = entry["tier"]
        state["region_id"] = entry["region_id"]
        state["role_tags"] = deepcopy(entry.get("role_tags", []))
        resolved_countries.append(state)
        layout[entry["code"]] = {"lon": entry["lon"], "lat": entry["lat"]}
        selected_metadata[entry["code"]] = CountryMeta(
            code=entry["code"],
            name=entry["name"],
            name_ja=entry.get("name_ja", entry["name"]),
            tier=entry["tier"],
            region_id=entry["region_id"],
            role_tags=tuple(entry.get("role_tags", [])),
            primary_axes=tuple(entry.get("primary_axes", [])),
            secondary_axes=tuple(entry.get("secondary_axes", [])),
            reason_short=entry.get("reason_short", ""),
            lon=float(entry["lon"]),
            lat=float(entry["lat"]),
        )

    resolved["countries"] = resolved_countries
    resolved["layout"] = layout
    resolved["cooperation_links"] = [
        edge for edge in library.get("cooperation_links", [])
        if edge["donor"] in selected_codes and edge["target"] in selected_codes
    ]
    resolved["rivalries"] = [
        edge for edge in library.get("rivalries", [])
        if edge["actor"] in selected_codes and edge["target"] in selected_codes
    ]
    resolved.setdefault("meta", {})
    resolved["meta"]["country_set"] = preset_name
    resolved["meta"]["country_count"] = len(resolved_countries)
    resolved["_selection_metadata"] = {
        "preset": preset_name,
        "library_path": str(library_path),
        "countries": {
            code: {
                "code": meta.code,
                "name": meta.name,
                "name_ja": meta.name_ja,
                "tier": meta.tier,
                "region_id": meta.region_id,
                "role_tags": list(meta.role_tags),
                "primary_axes": list(meta.primary_axes),
                "secondary_axes": list(meta.secondary_axes),
                "reason_short": meta.reason_short,
                "lon": meta.lon,
                "lat": meta.lat,
            }
            for code, meta in selected_metadata.items()
        },
    }
    return CountrySelectionResult(
        config=resolved,
        preset=preset_name,
        library_path=library_path,
        countries=selected_metadata,
    )


def validate_config_links(config: dict) -> None:
    codes = {country["code"] for country in config.get("countries", [])}
    missing_layout = sorted(code for code in codes if code not in config.get("layout", {}))
    if missing_layout:
        raise ValueError(f"Missing layout entries for: {', '.join(missing_layout)}")

    bad_rivalries = [
        edge for edge in config.get("rivalries", [])
        if edge["actor"] not in codes or edge["target"] not in codes
    ]
    if bad_rivalries:
        pairs = ", ".join(f"{edge['actor']}->{edge['target']}" for edge in bad_rivalries[:8])
        raise ValueError(f"Rivalries reference missing countries: {pairs}")

    bad_cooperation = [
        edge for edge in config.get("cooperation_links", [])
        if edge["donor"] not in codes or edge["target"] not in codes
    ]
    if bad_cooperation:
        pairs = ", ".join(f"{edge['donor']}->{edge['target']}" for edge in bad_cooperation[:8])
        raise ValueError(f"Cooperation links reference missing countries: {pairs}")


def expand_event_country_effects(event: dict, selection_metadata: dict) -> dict:
    effects = deepcopy(event.get("country_effects", {}))
    countries = selection_metadata.get("countries", {})
    if not countries:
        return effects

    for code, meta in countries.items():
        merged = deepcopy(effects.get(code, {}))
        for tag, deltas in event.get("tag_effects", {}).items():
            if tag in meta.get("role_tags", []):
                merged = merge_numeric_effects(merged, deltas)
        for region_id, deltas in event.get("region_effects", {}).items():
            if region_id == meta.get("region_id"):
                merged = merge_numeric_effects(merged, deltas)
        for tier, deltas in event.get("tier_effects", {}).items():
            if tier == meta.get("tier"):
                merged = merge_numeric_effects(merged, deltas)
        if merged:
            effects[code] = merged
    return effects
