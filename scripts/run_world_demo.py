#!/usr/bin/env python3
"""
Run a coarse world simulation for a small set of major countries.

The goal is not forecasting accuracy. The goal is to make the design memo
concrete enough that we can compare:

- high automation / low adaptation
- high automation / high adaptation

using country-level state, cooperation, and structure-sustain metrics.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from copy import deepcopy
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

try:
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover - plotting is optional
    plt = None


State = Dict[str, float]


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def build_initial_states(config: dict) -> Dict[str, State]:
    states: Dict[str, State] = {}
    for country in config["countries"]:
        code = country["code"]
        state = deepcopy(country)
        state.setdefault("energy_exporter", False)
        states[code] = state
    return states


def metric_snapshot(state: State) -> Dict[str, float]:
    dependency_risk = clamp(state["import_dependency"] * (1.0 - state["supply_chain_resilience"]))
    displacement_gap = max(0.0, state["labor_displacement"] - state["distribution_capacity"])

    M = (
        0.16 * state["energy_security"]
        + 0.11 * state["food_security"]
        + 0.12 * state["compute_access"]
        + 0.15 * state["institutional_capacity"]
        + 0.10 * state["social_cohesion"]
        + 0.09 * state["alliance_support"]
        + 0.12 * state["distribution_capacity"]
        + 0.09 * state["supply_chain_resilience"]
        + 0.06 * state["capital_surplus"]
    )
    L = (
        0.20 * state["labor_displacement"]
        + 0.16 * state["inequality_pressure"]
        + 0.16 * state["conflict_risk"]
        + 0.12 * state["sanction_exposure"]
        + 0.12 * state["climate_stress"]
        + 0.14 * dependency_risk
        + 0.10 * max(0.0, 1.0 - state["cash_stability"])
    )
    S = M * math.exp(-L)
    horizon = max(
        0.0,
        2.0
        + 10.0 * S
        + 1.8 * state["distribution_capacity"]
        + 1.2 * state["alliance_support"]
        - 3.0 * displacement_gap
        - 2.0 * state["conflict_risk"],
    )
    support_needed = clamp(
        (0.72 - S) * 0.75
        + displacement_gap * 0.55
        + state["conflict_risk"] * 0.25
        + dependency_risk * 0.20,
        0.0,
        1.0,
    )

    return {
        "M": round(M, 4),
        "L": round(L, 4),
        "S": round(S, 4),
        "dependency_risk": round(dependency_risk, 4),
        "displacement_gap": round(displacement_gap, 4),
        "horizon_turns": round(horizon, 2),
        "support_needed": round(support_needed, 4),
    }


def apply_country_effects(states: Dict[str, State], effects: dict) -> None:
    for code, deltas in effects.items():
        if code not in states:
            continue
        for key, delta in deltas.items():
            states[code][key] = clamp(states[code][key] + delta)


def self_update(state: State, scenario: dict, modifiers: dict) -> Dict[str, float]:
    automation_push = (
        scenario["automation_velocity"]
        * state["automation_exposure"]
        * (0.55 + 0.45 * state["compute_access"])
    )
    physical_push = (
        scenario["physical_automation_velocity"]
        * state["physical_exposure"]
        * (0.55 + 0.45 * state["energy_security"])
    )
    displacement_bump = (
        0.62 * automation_push
        + 0.38 * physical_push
        + modifiers.get("labor_displacement_bonus", 0.0)
    )
    state["labor_displacement"] = clamp(state["labor_displacement"] + displacement_bump)

    adaptation_absorption = scenario["adaptation_velocity"] * (
        0.34 * state["distribution_capacity"]
        + 0.24 * state["institutional_capacity"]
        + 0.22 * state["social_cohesion"]
        + 0.20 * state["capital_surplus"]
    )
    structure_credit_gain = (
        scenario["structure_credit_intensity"] + modifiers.get("structure_credit_bonus", 0.0)
    ) * (
        0.30 * state["institutional_capacity"]
        + 0.25 * state["distribution_capacity"]
        + 0.20 * state["social_cohesion"]
        + 0.15 * state["alliance_support"]
        + 0.10 * state["capital_surplus"]
    )
    capital_share_gain = scenario["winner_reinvestment"] * 0.35 * max(0.0, state["capital_surplus"] - 0.55)

    effective_buffer = adaptation_absorption + structure_credit_gain + capital_share_gain
    displacement_gap = max(0.0, state["labor_displacement"] - effective_buffer)

    state["distribution_capacity"] = clamp(
        state["distribution_capacity"]
        + 0.020 * scenario["adaptation_velocity"]
        + 0.055 * structure_credit_gain
    )
    state["social_cohesion"] = clamp(
        state["social_cohesion"]
        - 0.060 * displacement_gap
        + 0.050 * structure_credit_gain
        + 0.015 * scenario["adaptation_velocity"]
    )
    state["cash_stability"] = clamp(
        state["cash_stability"]
        - 0.080 * displacement_gap
        + 0.020 * capital_share_gain
        - 0.015 * state["sanction_exposure"]
        - 0.010 * state["conflict_risk"]
    )
    state["inequality_pressure"] = clamp(
        state["inequality_pressure"]
        + 0.070 * displacement_gap
        - 0.045 * structure_credit_gain
    )
    state["conflict_risk"] = clamp(
        state["conflict_risk"]
        + 0.055 * displacement_gap
        + 0.020 * state["sanction_exposure"]
        + 0.020 * state["climate_stress"]
        - 0.020 * state["alliance_support"]
    )
    state["supply_chain_resilience"] = clamp(
        state["supply_chain_resilience"]
        + 0.018 * scenario["winner_reinvestment"]
        + 0.010 * scenario["adaptation_velocity"]
        - 0.010 * state["import_dependency"] * (1.0 - state["alliance_support"])
    )
    state["capital_surplus"] = clamp(
        state["capital_surplus"]
        + 0.020 * state["cash_stability"]
        - 0.035 * structure_credit_gain
        - 0.025 * max(0.0, displacement_gap - 0.15)
    )
    state["alliance_support"] = clamp(
        state["alliance_support"] + 0.010 * scenario["cooperation_bias"] - 0.010 * state["conflict_risk"]
    )

    return {
        "adaptation_absorption": round(adaptation_absorption, 4),
        "structure_credit_gain": round(structure_credit_gain, 4),
        "capital_share_gain": round(capital_share_gain, 4),
        "displacement_bump": round(displacement_bump, 4),
        "displacement_gap_after_buffer": round(displacement_gap, 4),
    }


def apply_cooperation(
    states: Dict[str, State],
    links: List[dict],
    scenario: dict,
    modifiers: dict,
) -> List[dict]:
    cooperation_bias = scenario["cooperation_bias"] + modifiers.get("cooperation_bonus", 0.0)
    transfers: List[dict] = []

    for link in links:
        donor = states[link["donor"]]
        target = states[link["target"]]
        donor_excess = max(0.0, donor["capital_surplus"] - 0.58)
        if donor_excess <= 0.0 or cooperation_bias <= 0.0:
            continue

        amount = donor_excess * link["weight"] * cooperation_bias * 0.45
        if amount <= 0.004:
            continue

        donor["capital_surplus"] = clamp(donor["capital_surplus"] - amount * 0.40)
        donor["cash_stability"] = clamp(donor["cash_stability"] + amount * 0.015)
        donor["supply_chain_resilience"] = clamp(donor["supply_chain_resilience"] + amount * 0.020)

        target["distribution_capacity"] = clamp(target["distribution_capacity"] + amount * 0.28)
        target["supply_chain_resilience"] = clamp(target["supply_chain_resilience"] + amount * 0.24)
        target["alliance_support"] = clamp(target["alliance_support"] + amount * 0.22)
        target["social_cohesion"] = clamp(target["social_cohesion"] + amount * 0.16)
        if donor.get("energy_exporter"):
            target["energy_security"] = clamp(target["energy_security"] + amount * 0.14)

        transfers.append(
            {
                "donor": link["donor"],
                "target": link["target"],
                "amount": round(amount, 4),
            }
        )

    return transfers


def weighted_average(rows: List[dict], key: str) -> float:
    total_weight = sum(row["population_weight"] for row in rows)
    if total_weight == 0:
        return 0.0
    return sum(row[key] * row["population_weight"] for row in rows) / total_weight


def scenario_output_dir(base_dir: Path, scenario_key: str) -> Path:
    path = base_dir / scenario_key
    path.mkdir(parents=True, exist_ok=True)
    return path


def run_scenario(config: dict, scenario: dict, output_dir: Path) -> dict:
    states = build_initial_states(config)
    event_map = {event["turn"]: event for event in config.get("events", [])}
    rows: List[dict] = []
    event_log: List[dict] = []
    aggregate_rows: List[dict] = []

    for turn in range(1, config["meta"]["turns"] + 1):
        event = event_map.get(turn, {})
        modifiers = deepcopy(event.get("modifiers", {}))
        if event.get("country_effects"):
            apply_country_effects(states, event["country_effects"])

        turn_effects = {}
        for code, state in states.items():
            turn_effects[code] = self_update(state, scenario, modifiers)

        transfers = apply_cooperation(states, config.get("cooperation_links", []), scenario, modifiers)

        turn_rows: List[dict] = []
        for code, state in states.items():
            metrics = metric_snapshot(state)
            row = {
                "scenario_key": scenario["key"],
                "scenario_name": scenario["name"],
                "turn": turn,
                "code": code,
                "name": state["name"],
                "population_weight": state["population_weight"],
                "energy_security": round(state["energy_security"], 4),
                "food_security": round(state["food_security"], 4),
                "compute_access": round(state["compute_access"], 4),
                "distribution_capacity": round(state["distribution_capacity"], 4),
                "social_cohesion": round(state["social_cohesion"], 4),
                "cash_stability": round(state["cash_stability"], 4),
                "capital_surplus": round(state["capital_surplus"], 4),
                "labor_displacement": round(state["labor_displacement"], 4),
                "inequality_pressure": round(state["inequality_pressure"], 4),
                "sanction_exposure": round(state["sanction_exposure"], 4),
                "conflict_risk": round(state["conflict_risk"], 4),
                "climate_stress": round(state["climate_stress"], 4),
                "alliance_support": round(state["alliance_support"], 4),
            }
            row.update(turn_effects[code])
            row.update(metrics)
            rows.append(row)
            turn_rows.append(row)

        aggregate_rows.append(
            {
                "scenario_key": scenario["key"],
                "turn": turn,
                "avg_S": round(weighted_average(turn_rows, "S"), 4),
                "avg_horizon_turns": round(weighted_average(turn_rows, "horizon_turns"), 4),
                "avg_cash_stability": round(weighted_average(turn_rows, "cash_stability"), 4),
                "avg_labor_displacement": round(weighted_average(turn_rows, "labor_displacement"), 4),
            }
        )

        event_log.append(
            {
                "scenario_key": scenario["key"],
                "turn": turn,
                "name": event.get("name", "Baseline dynamics"),
                "description": event.get("description", "No exogenous event."),
                "modifiers": modifiers,
                "cooperation_transfers": transfers,
            }
        )

    write_csv(output_dir / "turns.csv", rows)
    write_csv(output_dir / "aggregate.csv", aggregate_rows)
    write_jsonl(output_dir / "events.jsonl", event_log)

    final_rows = [row for row in rows if row["turn"] == config["meta"]["turns"]]
    final_rows.sort(key=lambda item: item["S"], reverse=True)
    summary = {
        "scenario_key": scenario["key"],
        "scenario_name": scenario["name"],
        "turns": config["meta"]["turns"],
        "global_avg_S_final": aggregate_rows[-1]["avg_S"],
        "global_avg_horizon_final": aggregate_rows[-1]["avg_horizon_turns"],
        "global_avg_cash_final": aggregate_rows[-1]["avg_cash_stability"],
        "top_resilient": [row["code"] for row in final_rows[:3]],
        "most_fragile": [row["code"] for row in final_rows[-3:]],
    }
    write_json(output_dir / "summary.json", summary)
    write_markdown_summary(output_dir / "summary.md", summary, final_rows, event_log)

    return {
        "rows": rows,
        "aggregate_rows": aggregate_rows,
        "event_log": event_log,
        "summary": summary,
        "final_rows": final_rows,
    }


def write_csv(path: Path, rows: List[dict]) -> None:
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


def write_jsonl(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_markdown_summary(path: Path, summary: dict, final_rows: List[dict], event_log: List[dict]) -> None:
    lines = [
        f"# {summary['scenario_name']}",
        "",
        f"- Final global average `S`: `{summary['global_avg_S_final']}`",
        f"- Final global average horizon: `{summary['global_avg_horizon_final']}` turns",
        f"- Final global average cash stability: `{summary['global_avg_cash_final']}`",
        f"- Top resilient: `{', '.join(summary['top_resilient'])}`",
        f"- Most fragile: `{', '.join(summary['most_fragile'])}`",
        "",
        "## Final Country Snapshot",
        "",
        "| Code | S | Horizon | Support Needed | Cash | Displacement | Conflict |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in final_rows:
        lines.append(
            f"| {row['code']} | {row['S']} | {row['horizon_turns']} | {row['support_needed']} | "
            f"{row['cash_stability']} | {row['labor_displacement']} | {row['conflict_risk']} |"
        )

    lines.extend(
        [
            "",
            "## Event Timeline",
            "",
        ]
    )
    for entry in event_log:
        transfer_text = ", ".join(
            f"{item['donor']}->{item['target']}:{item['amount']}" for item in entry["cooperation_transfers"][:5]
        )
        if not transfer_text:
            transfer_text = "none"
        lines.append(
            f"- Turn {entry['turn']}: {entry['name']} | transfers: {transfer_text}"
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_comparison_report(base_dir: Path, scenario_results: Dict[str, dict]) -> None:
    scenario_keys = list(scenario_results.keys())
    if len(scenario_keys) < 2:
        return

    first = scenario_results[scenario_keys[0]]
    second = scenario_results[scenario_keys[1]]

    final_a = {row["code"]: row for row in first["final_rows"]}
    final_b = {row["code"]: row for row in second["final_rows"]}

    lines = [
        "# Major Powers 10-Turn Comparison",
        "",
        f"- `{first['summary']['scenario_name']}` final avg `S`: `{first['summary']['global_avg_S_final']}`",
        f"- `{second['summary']['scenario_name']}` final avg `S`: `{second['summary']['global_avg_S_final']}`",
        f"- Delta avg `S`: `{round(second['summary']['global_avg_S_final'] - first['summary']['global_avg_S_final'], 4)}`",
        "",
        "## Final Country Delta",
        "",
        "| Code | S low-adaptation | S high-adaptation | Delta S | Horizon delta | Support delta |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for code in sorted(final_a.keys()):
        row_a = final_a[code]
        row_b = final_b[code]
        lines.append(
            f"| {code} | {row_a['S']} | {row_b['S']} | {round(row_b['S'] - row_a['S'], 4)} | "
            f"{round(row_b['horizon_turns'] - row_a['horizon_turns'], 2)} | "
            f"{round(row_b['support_needed'] - row_a['support_needed'], 4)} |"
        )

    (base_dir / "comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    if plt is not None:
        plot_comparison(base_dir, scenario_results)


def plot_comparison(base_dir: Path, scenario_results: Dict[str, dict]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))

    for scenario_key, result in scenario_results.items():
        turns = [row["turn"] for row in result["aggregate_rows"]]
        avg_s = [row["avg_S"] for row in result["aggregate_rows"]]
        avg_h = [row["avg_horizon_turns"] for row in result["aggregate_rows"]]
        axes[0].plot(turns, avg_s, marker="o", label=scenario_key)
        axes[1].plot(turns, avg_h, marker="o", label=scenario_key)

    axes[0].set_title("Average S by Turn")
    axes[0].set_xlabel("Turn")
    axes[0].set_ylabel("Average S")
    axes[1].set_title("Average Horizon by Turn")
    axes[1].set_xlabel("Turn")
    axes[1].set_ylabel("Turns")

    for axis in axes:
        axis.grid(alpha=0.25)
        axis.legend()

    fig.tight_layout()
    fig.savefig(base_dir / "comparison.png", dpi=160)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a coarse world simulation demo.")
    parser.add_argument(
        "--config",
        default="scenarios/major_powers_world_demo.yaml",
        help="Path to the world demo YAML config.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = Path(args.config)
    config = load_yaml(config_path)
    base_dir = Path(config["meta"]["output_dir"])
    base_dir.mkdir(parents=True, exist_ok=True)

    scenario_results = {}
    for scenario in config["scenarios"]:
        out_dir = scenario_output_dir(base_dir, scenario["key"])
        scenario_results[scenario["key"]] = run_scenario(config, scenario, out_dir)

    write_comparison_report(base_dir, scenario_results)

    manifest = {
        "config": str(config_path),
        "output_dir": str(base_dir),
        "scenarios": list(scenario_results.keys()),
    }
    write_json(base_dir / "manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
