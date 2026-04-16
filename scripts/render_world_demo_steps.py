#!/usr/bin/env python3
"""
Render step-by-step frames for the coarse world simulation demo.

Outputs:
- per-scenario PNG frame sequences
- per-scenario animated GIFs

Design goals:
- keep a geographic intuition without requiring a true world map
- make per-turn changes readable at a glance
- show structure sustain, cash, support need, and war pressure together
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, Rectangle
from PIL import Image
import yaml


MODE_COLORS = {
    "none": "#cfd8dc",
    "pressure_only": "#607d8b",
    "gray_zone": "#7b1fa2",
    "proxy": "#d32f2f",
    "limited_war": "#111111",
}

COOP_COLOR = "#1976d2"
BAR_COLORS = {
    "cash": "#1e88e5",
    "support": "#fb8c00",
    "war": "#d32f2f",
}


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


def scenario_positions(config: dict) -> Dict[str, Tuple[float, float]]:
    return {
        code: (coords["x"], coords["y"])
        for code, coords in config.get("layout", {}).items()
    }


def rows_by_turn(rows: List[dict]) -> Dict[int, Dict[str, dict]]:
    result: Dict[int, Dict[str, dict]] = {}
    for row in rows:
        turn = int(row["turn"])
        result.setdefault(turn, {})
        result[turn][row["code"]] = row
    return result


def aggregate_by_turn(rows: List[dict]) -> Dict[int, dict]:
    return {int(row["turn"]): row for row in rows}


def events_by_turn(rows: List[dict]) -> Dict[int, dict]:
    return {int(row["turn"]): row for row in rows}


def draw_background(ax: plt.Axes) -> None:
    ax.set_facecolor("#f4f7fb")
    continents = [
        Ellipse((-0.74, 0.44), 0.45, 0.27, facecolor="#dfe8d8", edgecolor="none", alpha=0.65),
        Ellipse((-0.47, -0.28), 0.30, 0.25, facecolor="#dfe8d8", edgecolor="none", alpha=0.65),
        Ellipse((0.05, 0.40), 0.95, 0.42, facecolor="#e7e2d0", edgecolor="none", alpha=0.55),
        Ellipse((0.10, 0.02), 0.34, 0.23, facecolor="#eadfca", edgecolor="none", alpha=0.60),
    ]
    for patch in continents:
        ax.add_patch(patch)

    ax.text(-0.84, 0.67, "Americas", fontsize=11, color="#607d8b")
    ax.text(-0.02, 0.78, "Eurasia", fontsize=11, color="#607d8b")
    ax.text(-0.02, 0.19, "Middle East / Indian Ocean", fontsize=10, color="#607d8b")

    ax.set_xlim(-1.00, 1.00)
    ax.set_ylim(-0.55, 0.95)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def node_radius(pop_weight: float) -> float:
    return 0.062 + 0.10 * float(pop_weight)


def as_float(row: dict, key: str) -> float:
    return float(row[key])


def curved_arrow(ax: plt.Axes, start: Tuple[float, float], end: Tuple[float, float], color: str, width: float, alpha: float, rad: float) -> None:
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=14,
        linewidth=width,
        color=color,
        alpha=alpha,
        connectionstyle=f"arc3,rad={rad}",
    )
    ax.add_patch(arrow)


def draw_node(ax: plt.Axes, code: str, row: dict, pos: Tuple[float, float], cmap, norm) -> None:
    x, y = pos
    radius = node_radius(as_float(row, "population_weight"))
    fill = cmap(norm(as_float(row, "S")))
    pressure = as_float(row, "war_pressure")
    mode = row["likely_mode"]
    ring_color = MODE_COLORS.get(mode, MODE_COLORS["pressure_only"])
    ring_width = 1.1 + 7.0 * pressure

    ax.add_patch(Circle((x, y), radius, facecolor=fill, edgecolor="#263238", linewidth=1.3, zorder=3))
    if pressure > 0.01:
        ax.add_patch(
            Circle(
                (x, y),
                radius + 0.015,
                facecolor="none",
                edgecolor=ring_color,
                linewidth=ring_width,
                alpha=0.85,
                zorder=4,
            )
        )

    label = f"{code}\nS {as_float(row, 'S'):.2f} | H {as_float(row, 'horizon_turns'):.1f}"
    ax.text(x, y + radius + 0.03, label, ha="center", va="bottom", fontsize=9.5, color="#1f2937", zorder=5)

    bar_x = x - radius
    bar_y = y - radius - 0.055
    bar_w = radius * 2.0
    bar_h = 0.014
    metrics = [
        ("cash", as_float(row, "cash_stability")),
        ("support", as_float(row, "support_needed")),
        ("war", as_float(row, "war_burden")),
    ]
    for index, (key, value) in enumerate(metrics):
        y0 = bar_y - index * (bar_h + 0.007)
        ax.add_patch(Rectangle((bar_x, y0), bar_w, bar_h, facecolor="#eceff1", edgecolor="none", zorder=2))
        ax.add_patch(Rectangle((bar_x, y0), bar_w * value, bar_h, facecolor=BAR_COLORS[key], edgecolor="none", zorder=3))

    ax.text(
        x,
        bar_y - 3 * (bar_h + 0.007) - 0.006,
        f"W {pressure:.2f} | {mode}",
        ha="center",
        va="top",
        fontsize=8.3,
        color=ring_color if mode != "none" else "#607d8b",
        zorder=5,
    )


def draw_links(ax: plt.Axes, positions: Dict[str, Tuple[float, float]], event_row: dict) -> None:
    for transfer in event_row.get("cooperation_transfers", []):
        start = positions[transfer["donor"]]
        end = positions[transfer["target"]]
        width = 1.0 + 16.0 * float(transfer["amount"])
        curved_arrow(ax, start, end, COOP_COLOR, width, 0.45, 0.18)

    for conflict in event_row.get("conflict_events", []):
        start = positions[conflict["actor"]]
        end = positions[conflict["target"]]
        mode = conflict["mode"]
        intensity = float(conflict["intensity"])
        color = MODE_COLORS.get(mode, "#000000")
        width = 1.6 + 11.0 * intensity
        curved_arrow(ax, start, end, color, width, 0.85, -0.22)


def top_changes(current_rows: Dict[str, dict], prev_rows: Dict[str, dict] | None) -> List[Tuple[str, float]]:
    if not prev_rows:
        return []
    deltas: List[Tuple[str, float]] = []
    for code, row in current_rows.items():
        if code not in prev_rows:
            continue
        delta = as_float(row, "S") - as_float(prev_rows[code], "S")
        deltas.append((code, delta))
    return sorted(deltas, key=lambda item: item[1], reverse=True)


def draw_info_panel(
    ax: plt.Axes,
    scenario_name: str,
    turn: int,
    total_turns: int,
    current_rows: Dict[str, dict],
    prev_rows: Dict[str, dict] | None,
    event_row: dict,
    aggregate_row: dict,
) -> None:
    ax.axis("off")
    changes = top_changes(current_rows, prev_rows)
    top_up = ", ".join(f"{code} {delta:+.02f}" for code, delta in changes[:3]) or "none"
    top_down = ", ".join(f"{code} {delta:+.02f}" for code, delta in changes[-3:]) if changes else "none"
    conflicts = event_row.get("conflict_events", [])
    transfers = event_row.get("cooperation_transfers", [])

    lines = [
        f"{scenario_name}",
        "",
        f"Turn {turn}/{total_turns}",
        f"Event: {event_row.get('name', 'Baseline dynamics')}",
        "",
        event_row.get("description", "No exogenous event."),
        "",
        f"Avg S: {float(aggregate_row['avg_S']):.3f}",
        f"Avg cash: {float(aggregate_row['avg_cash_stability']):.3f}",
        f"Avg war burden: {float(aggregate_row['avg_war_burden']):.3f}",
        f"Avg conflict risk: {float(aggregate_row['avg_conflict_risk']):.3f}",
        "",
        f"Top S gains: {top_up}",
        f"Top S drops: {top_down}",
        "",
        f"Cooperation links this turn: {len(transfers)}",
        f"Conflict events this turn: {len(conflicts)}",
    ]

    if conflicts:
        lines.append("")
        lines.append("Active conflict:")
        for item in conflicts[:3]:
            lines.append(
                f"- {item['actor']} -> {item['target']} | {item['mode']} | I {float(item['intensity']):.2f}"
            )

    ax.text(
        0.0,
        1.0,
        "\n".join(lines),
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=10.3,
        color="#17212b",
        linespacing=1.35,
    )

    legend_y = 0.02
    legend_items = [
        ("cash", BAR_COLORS["cash"]),
        ("support need", BAR_COLORS["support"]),
        ("war burden", BAR_COLORS["war"]),
        ("cooperation", COOP_COLOR),
        ("gray-zone", MODE_COLORS["gray_zone"]),
        ("proxy", MODE_COLORS["proxy"]),
    ]
    for idx, (label, color) in enumerate(legend_items):
        x = 0.0 if idx < 3 else 0.50
        y = legend_y + 0.07 * (2 - (idx % 3))
        ax.add_patch(Rectangle((x, y), 0.04, 0.03, transform=ax.transAxes, facecolor=color, edgecolor="none"))
        ax.text(x + 0.05, y + 0.015, label, transform=ax.transAxes, va="center", fontsize=9.2, color="#37474f")


def draw_timeline(ax: plt.Axes, aggregate_rows: List[dict], current_turn: int) -> None:
    turns = [int(row["turn"]) for row in aggregate_rows]
    avg_s = [float(row["avg_S"]) for row in aggregate_rows]
    avg_cash = [float(row["avg_cash_stability"]) for row in aggregate_rows]
    avg_war = [float(row["avg_war_burden"]) for row in aggregate_rows]
    event_counts = [float(row["war_events_count"]) for row in aggregate_rows]

    ax.plot(turns, avg_s, marker="o", color="#2e7d32", label="avg S")
    ax.plot(turns, avg_cash, marker="o", color="#1e88e5", label="avg cash")
    ax.plot(turns, avg_war, marker="o", color="#d32f2f", label="avg war burden")
    ax.bar(turns, [count / 4.0 for count in event_counts], width=0.55, alpha=0.18, color="#7b1fa2", label="war events / 4")
    ax.axvline(current_turn, color="#212121", linestyle="--", linewidth=1.2)
    ax.set_xlim(min(turns) - 0.5, max(turns) + 0.5)
    ax.set_ylim(0.0, max(max(avg_s), max(avg_cash), max(avg_war), 0.6))
    ax.set_xlabel("Turn")
    ax.set_ylabel("0-1 scale")
    ax.set_title("Global trajectory")
    ax.grid(alpha=0.25)
    ax.legend(loc="upper right", ncol=4, fontsize=8.8)


def create_frame(
    output_path: Path,
    config: dict,
    scenario_name: str,
    turn: int,
    total_turns: int,
    current_rows: Dict[str, dict],
    prev_rows: Dict[str, dict] | None,
    event_row: dict,
    aggregate_rows: List[dict],
) -> None:
    positions = scenario_positions(config)
    cmap = plt.get_cmap("RdYlGn")
    norm = colors.Normalize(vmin=0.25, vmax=0.58)

    fig = plt.figure(figsize=(15.5, 8.8))
    gs = fig.add_gridspec(2, 3, height_ratios=[0.82, 0.18], width_ratios=[1.1, 1.1, 0.85], hspace=0.16, wspace=0.10)
    ax_map = fig.add_subplot(gs[0, 0:2])
    ax_info = fig.add_subplot(gs[0, 2])
    ax_timeline = fig.add_subplot(gs[1, :])

    draw_background(ax_map)
    draw_links(ax_map, positions, event_row)
    for code, row in current_rows.items():
        draw_node(ax_map, code, row, positions[code], cmap, norm)

    agg_map = aggregate_by_turn(aggregate_rows)
    draw_info_panel(ax_info, scenario_name, turn, total_turns, current_rows, prev_rows, event_row, agg_map[turn])
    draw_timeline(ax_timeline, aggregate_rows, turn)

    fig.suptitle("Major Powers World Demo: step-by-step state change", fontsize=16, y=0.98)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def create_gif(frame_paths: List[Path], output_path: Path, duration_ms: int = 850) -> None:
    if not frame_paths:
        return
    images = [Image.open(path) for path in frame_paths]
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=duration_ms,
        loop=0,
    )
    for image in images:
        image.close()


def render_scenario(config: dict, base_output: Path, scenario_key: str) -> None:
    scenario_dir = base_output / scenario_key
    rows = load_csv(scenario_dir / "turns.csv")
    aggregate_rows = load_csv(scenario_dir / "aggregate.csv")
    event_rows = load_jsonl(scenario_dir / "events.jsonl")
    by_turn = rows_by_turn(rows)
    event_map = events_by_turn(event_rows)
    total_turns = max(by_turn.keys())

    scenario_name = rows[0]["scenario_name"]
    frame_dir = scenario_dir / "frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    frame_paths: List[Path] = []

    prev_rows = None
    for turn in range(1, total_turns + 1):
        frame_path = frame_dir / f"frame_{turn:04d}.png"
        create_frame(
            frame_path,
            config,
            scenario_name,
            turn,
            total_turns,
            by_turn[turn],
            prev_rows,
            event_map[turn],
            aggregate_rows,
        )
        frame_paths.append(frame_path)
        prev_rows = by_turn[turn]

    create_gif(frame_paths, scenario_dir / "animation.gif")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render step-by-step world demo frames.")
    parser.add_argument(
        "--config",
        default="scenarios/major_powers_world_demo.yaml",
        help="Path to the world demo scenario config.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = Path(args.config)
    config = load_yaml(config_path)
    base_output = Path(config["meta"]["output_dir"])

    for scenario in config["scenarios"]:
        render_scenario(config, base_output, scenario["key"])

    print(json.dumps({"output_dir": str(base_output), "rendered": [s["key"] for s in config["scenarios"]]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
