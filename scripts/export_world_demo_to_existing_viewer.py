#!/usr/bin/env python3
"""
Export world demo outputs into the legacy viewer format.

The existing visualization/viewer.html expects:
- messages.jsonl
- optional memory_reasoning.jsonl
- frame_XXXX.png files in the same directory

This script converts the world demo outputs into that layout so the same
viewer can be reused without changing its code.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path
from typing import Dict, List

import yaml


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_csv(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_jsonl(path: Path) -> List[dict]:
    rows: List[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def rows_by_turn(rows: List[dict]) -> Dict[int, List[dict]]:
    result: Dict[int, List[dict]] = {}
    for row in rows:
        turn = int(row["turn"])
        result.setdefault(turn, []).append(row)
    return result


def aggregate_map(rows: List[dict]) -> Dict[int, dict]:
    return {int(row["turn"]): row for row in rows}


def event_map(rows: List[dict]) -> Dict[int, dict]:
    return {int(row["turn"]): row for row in rows}


def top_changes(current_rows: List[dict], previous_rows: List[dict] | None) -> tuple[list[tuple[str, float]], list[tuple[str, float]]]:
    if not previous_rows:
        return [], []
    prev = {row["code"]: row for row in previous_rows}
    deltas = []
    for row in current_rows:
        code = row["code"]
        if code not in prev:
            continue
        delta = float(row["S"]) - float(prev[code]["S"])
        deltas.append((code, delta))
    deltas.sort(key=lambda item: item[1], reverse=True)
    return deltas[:3], deltas[-3:]


def make_system_message(turn: int, scenario_name: str, aggregate: dict, event: dict, current_rows: List[dict], previous_rows: List[dict] | None) -> dict:
    rising, falling = top_changes(current_rows, previous_rows)
    rising_text = ", ".join(f"{code} {delta:+.02f}" for code, delta in rising) or "none"
    falling_text = ", ".join(f"{code} {delta:+.02f}" for code, delta in falling) or "none"
    conflicts = event.get("conflict_events", [])
    transfers = event.get("cooperation_transfers", [])
    conflict_text = ", ".join(
        f"{item['actor']}->{item['target']} {item['mode']} {float(item['intensity']):.2f}"
        for item in conflicts[:3]
    ) or "none"

    message = (
        f"[{scenario_name}] Turn {turn}. Event: {event.get('name', 'Baseline dynamics')}. "
        f"Avg S={float(aggregate['avg_S']):.3f}, cash={float(aggregate['avg_cash_stability']):.3f}, "
        f"war burden={float(aggregate['avg_war_burden']):.3f}, conflict risk={float(aggregate['avg_conflict_risk']):.3f}. "
        f"Top gains: {rising_text}. Top drops: {falling_text}. "
        f"Cooperation links: {len(transfers)}. Conflict events: {conflict_text}."
    )
    reasoning = (
        "Macro narration for the world demo. "
        "This synthetic message lets the legacy viewer show the step event, the aggregate state, "
        "and the biggest winners/losers even though the underlying simulation is country-level."
    )
    return {
        "step": turn,
        "from": "WORLD",
        "to": "ALL",
        "message": message,
        "reasoning": reasoning,
    }


def make_transfer_messages(turn: int, transfers: List[dict]) -> List[dict]:
    messages = []
    for item in transfers:
        amount = float(item["amount"])
        messages.append(
            {
                "step": turn,
                "from": item["donor"],
                "to": item["target"],
                "message": (
                    f"Resilience support corridor opened. Transfer amount {amount:.4f}. "
                    "Expected effect: better distribution capacity, alliance support, and supply-chain resilience."
                ),
                "reasoning": (
                    "This is a synthetic cooperation message for the legacy viewer. "
                    "It represents a cross-border resilience investment rather than a conversational utterance."
                ),
            }
        )
    return messages


def make_conflict_messages(turn: int, conflicts: List[dict]) -> List[dict]:
    messages = []
    for item in conflicts:
        intensity = float(item["intensity"])
        messages.append(
            {
                "step": turn,
                "from": item["actor"],
                "to": item["target"],
                "message": (
                    f"{item['mode']} pressure activated in {item['domain']}. "
                    f"Intensity {intensity:.2f}. This raises war burden and destabilizes the target's structure sustain path."
                ),
                "reasoning": (
                    "Synthetic conflict notice for the legacy viewer. "
                    "In this demo, conflict is modeled as survival-driven coercion that often begins in the gray zone."
                ),
            }
        )
    return messages


def summarize_row(row: dict) -> tuple[str, str]:
    mode = row["likely_mode"]
    war_pressure = float(row["war_pressure"])
    war_pressure_text = f"{war_pressure:.2f}"
    summary = (
        f"S={float(row['S']):.2f}, horizon={float(row['horizon_turns']):.1f}, "
        f"cash={float(row['cash_stability']):.2f}, support={float(row['support_needed']):.2f}, "
        f"war pressure={war_pressure_text}, mode={mode}."
    )

    if mode == "gray_zone":
        reasoning = "Survival pressure and rivalry have crossed the gray-zone threshold, but deterrence still suppresses direct war."
    elif mode == "proxy":
        reasoning = "Conflict pressure is strong enough for coercive or proxy escalation while direct war remains constrained."
    elif mode == "limited_war":
        reasoning = "Direct limited war pressure is now high relative to deterrence and internal survival pressure."
    elif mode == "pressure_only":
        reasoning = "This country has elevated coercive pressure, but not enough to trigger an event this turn."
    else:
        reasoning = "This country remains inside the simulation without active conflict escalation this turn."

    memory = (
        f"{summary} Inequality={float(row['inequality_pressure']):.2f}, labor displacement={float(row['labor_displacement']):.2f}, "
        f"conflict risk={float(row['conflict_risk']):.2f}, war burden={float(row['war_burden']):.2f}."
    )
    return reasoning, memory


def export_scenario(base_output: Path, scenario: str, scenario_name: str) -> Path:
    source_dir = base_output / scenario
    output_dir = source_dir / "legacy_viewer"
    output_dir.mkdir(parents=True, exist_ok=True)

    turn_rows = load_csv(source_dir / "turns.csv")
    aggregate_rows = load_csv(source_dir / "aggregate.csv")
    event_rows = load_jsonl(source_dir / "events.jsonl")

    by_turn = rows_by_turn(turn_rows)
    agg_by_turn = aggregate_map(aggregate_rows)
    events = event_map(event_rows)

    messages: List[dict] = []
    reasonings: List[dict] = []
    previous_rows: List[dict] | None = None

    for turn in sorted(by_turn.keys()):
        current_rows = sorted(by_turn[turn], key=lambda row: float(row["population_weight"]), reverse=True)
        event = events[turn]
        aggregate = agg_by_turn[turn]

        messages.append(make_system_message(turn, scenario_name, aggregate, event, current_rows, previous_rows))
        messages.extend(make_transfer_messages(turn, event.get("cooperation_transfers", [])))
        messages.extend(make_conflict_messages(turn, event.get("conflict_events", [])))

        for row in current_rows:
            reasoning, memory = summarize_row(row)
            reasonings.append(
                {
                    "step": turn,
                    "id": row["code"],
                    "memory": memory,
                    "reasoning": reasoning,
                }
            )

        previous_rows = current_rows

    with (output_dir / "messages.jsonl").open("w", encoding="utf-8") as handle:
        for item in messages:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")

    with (output_dir / "memory_reasoning.jsonl").open("w", encoding="utf-8") as handle:
        for item in reasonings:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")

    frame_dir = source_dir / "frames"
    for frame in sorted(frame_dir.glob("frame_*.png")):
        shutil.copyfile(frame, output_dir / frame.name)

    shutil.copyfile(source_dir / "summary.md", output_dir / "summary.md")
    return output_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export world demo to legacy viewer format.")
    parser.add_argument(
        "--config",
        default="scenarios/major_powers_world_demo.yaml",
        help="Path to the world demo config.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_yaml(Path(args.config))
    base_output = Path(config["meta"]["output_dir"])

    exported = {}
    for scenario in config["scenarios"]:
        scenario_key = scenario["key"]
        exported[scenario_key] = str(export_scenario(base_output, scenario_key, scenario["name"]))

    print(json.dumps({"exported": exported}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
