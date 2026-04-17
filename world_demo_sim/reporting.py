from __future__ import annotations

from pathlib import Path
from typing import Dict

import numpy as np

try:
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover - plotting is optional
    plt = None

from .io_helpers import write_csv, write_json, write_jsonl
from .types import ScenarioRunResult


def write_markdown_summary(path: Path, summary: dict, final_rows: list[dict], event_log: list[dict]) -> None:
    lines = [
        f"# {summary['scenario_name']}",
        "",
        f"- Final global average `S`: `{summary['global_avg_S_final']}`",
        f"- Final global average horizon: `{summary['global_avg_horizon_final']}` turns",
        f"- Final global average cash stability: `{summary['global_avg_cash_final']}`",
        f"- Final global average war burden: `{summary['global_avg_war_burden_final']}`",
        f"- Final global average domestic burden: `{summary['global_avg_domestic_burden_final']}`",
        f"- Final global average protest pressure: `{summary['global_avg_protest_pressure_final']}`",
        f"- Top resilient: `{', '.join(summary['top_resilient'])}`",
        f"- Most fragile: `{', '.join(summary['most_fragile'])}`",
        f"- Most domestically fragile: `{', '.join(summary['most_domestically_fragile'])}`",
        f"- Conflict mix: `gray={summary['gray_zone_events']}, proxy={summary['proxy_events']}, limited={summary['limited_war_events']}`",
        f"- Domestic mix: `grievance={summary['grievance_events']}, protest={summary['protest_events']}, mass={summary['mass_protest_events']}, riot={summary['riot_events']}, insurgency={summary['insurgency_events']}, civil={summary['civil_conflict_events']}`",
        "",
        "## Final Country Table",
        "",
        "| Code | S | Horizon | Support Needed | Cash | Domestic Stage | Domestic Burden | Protest Pressure | War Burden | War Pressure | Likely Mode |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in final_rows:
        lines.append(
            f"| {row['code']} | {row['S']} | {row['horizon_turns']} | {row['support_needed']} | "
            f"{row['cash_stability']} | {row['domestic_stage']} | {row['domestic_burden']} | {row['protest_pressure']} | "
            f"{row['war_burden']} | {row['war_pressure']} | {row['likely_mode']} |"
        )

    lines.extend(["", "## Event Timeline", ""])
    for entry in event_log:
        transfer_text = ", ".join(
            f"{item['donor']}->{item['target']}:{item['amount']}" for item in entry["cooperation_transfers"][:5]
        ) or "none"
        conflict_text = ", ".join(
            f"{item['actor']}->{item['target']}:{item['mode']}:{item['intensity']}" for item in entry["conflict_events"]
        ) or "none"
        domestic_text = ", ".join(
            f"{item['country']}:{item['from_stage']}->{item['to_stage']}" for item in entry.get("domestic_events", [])[:5]
        ) or "none"
        lines.append(
            f"- Turn {entry['turn']}: {entry['name']} | transfers: {transfer_text} | conflict: {conflict_text} | domestic: {domestic_text}"
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_comparison_report(base_dir: Path, scenario_results: Dict[str, ScenarioRunResult]) -> None:
    scenario_keys = list(scenario_results.keys())
    if len(scenario_keys) < 2:
        return

    first = scenario_results[scenario_keys[0]]
    second = scenario_results[scenario_keys[1]]

    final_a = {row["code"]: row for row in first.final_rows}
    final_b = {row["code"]: row for row in second.final_rows}

    comparison_rows: list[dict] = []
    lines = [
        "# Major Powers 10-Turn Comparison",
        "",
        f"- `{first.summary['scenario_name']}` final avg `S`: `{first.summary['global_avg_S_final']}`",
        f"- `{second.summary['scenario_name']}` final avg `S`: `{second.summary['global_avg_S_final']}`",
        f"- Delta avg `S`: `{round(second.summary['global_avg_S_final'] - first.summary['global_avg_S_final'], 4)}`",
        f"- Delta avg war burden: `{round(second.summary['global_avg_war_burden_final'] - first.summary['global_avg_war_burden_final'], 4)}`",
        f"- Delta avg domestic burden: `{round(second.summary['global_avg_domestic_burden_final'] - first.summary['global_avg_domestic_burden_final'], 4)}`",
        f"- Conflict mix `{first.summary['scenario_name']}`: "
        f"`gray={first.summary['gray_zone_events']}, proxy={first.summary['proxy_events']}, limited={first.summary['limited_war_events']}`",
        f"- Conflict mix `{second.summary['scenario_name']}`: "
        f"`gray={second.summary['gray_zone_events']}, proxy={second.summary['proxy_events']}, limited={second.summary['limited_war_events']}`",
        f"- Domestic mix `{first.summary['scenario_name']}`: "
        f"`riot={first.summary['riot_events']}, insurgency={first.summary['insurgency_events']}, civil={first.summary['civil_conflict_events']}`",
        f"- Domestic mix `{second.summary['scenario_name']}`: "
        f"`riot={second.summary['riot_events']}, insurgency={second.summary['insurgency_events']}, civil={second.summary['civil_conflict_events']}`",
        "",
        "## Final Country Delta",
        "",
        "| Code | S low-adaptation | S high-adaptation | Delta S | Horizon delta | Support delta | War burden delta | Domestic burden delta |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for code in sorted(final_a.keys()):
        row_a = final_a[code]
        row_b = final_b[code]
        delta_s = round(row_b["S"] - row_a["S"], 4)
        delta_h = round(row_b["horizon_turns"] - row_a["horizon_turns"], 2)
        delta_support = round(row_b["support_needed"] - row_a["support_needed"], 4)
        delta_war = round(row_b["war_burden"] - row_a["war_burden"], 4)
        delta_domestic = round(row_b["domestic_burden"] - row_a["domestic_burden"], 4)
        lines.append(
            f"| {code} | {row_a['S']} | {row_b['S']} | {delta_s} | {delta_h} | {delta_support} | {delta_war} | {delta_domestic} |"
        )
        comparison_rows.append(
            {
                "code": code,
                "s_low_adaptation": row_a["S"],
                "s_high_adaptation": row_b["S"],
                "delta_s": delta_s,
                "delta_horizon": delta_h,
                "delta_support_needed": delta_support,
                "delta_war_burden": delta_war,
                "delta_domestic_burden": delta_domestic,
            }
        )

    (base_dir / "comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_csv(base_dir / "comparison.csv", comparison_rows)

    if plt is not None:
        plot_comparison(base_dir, scenario_results)


def plot_scenario_dashboard(output_dir: Path, result: ScenarioRunResult) -> None:
    if plt is None:
        return

    turns = [row["turn"] for row in result.aggregate_rows]
    avg_s = [row["avg_S"] for row in result.aggregate_rows]
    avg_cash = [row["avg_cash_stability"] for row in result.aggregate_rows]
    avg_war = [row["avg_war_burden"] for row in result.aggregate_rows]
    avg_domestic = [row["avg_domestic_burden"] for row in result.aggregate_rows]
    avg_conflict = [row["avg_conflict_risk"] for row in result.aggregate_rows]
    avg_protest = [row["avg_protest_pressure"] for row in result.aggregate_rows]
    avg_riot = [row["avg_riot_pressure"] for row in result.aggregate_rows]
    avg_civil = [row["avg_civil_conflict_pressure"] for row in result.aggregate_rows]
    gray_counts = [row["gray_zone_events"] for row in result.aggregate_rows]
    proxy_counts = [row["proxy_events"] for row in result.aggregate_rows]
    limited_counts = [row["limited_war_events"] for row in result.aggregate_rows]
    grievance_counts = [row["grievance_stage_count"] for row in result.aggregate_rows]
    protest_counts = [row["protest_stage_count"] for row in result.aggregate_rows]
    mass_counts = [row["mass_protest_stage_count"] for row in result.aggregate_rows]
    riot_counts = [row["riot_stage_count"] for row in result.aggregate_rows]
    insurgency_counts = [row["insurgency_stage_count"] for row in result.aggregate_rows]
    civil_counts = [row["civil_conflict_stage_count"] for row in result.aggregate_rows]

    countries = [row["code"] for row in result.final_rows]
    rows_by_country = {code: [] for code in countries}
    for row in result.rows:
        rows_by_country[row["code"]].append(row)
    s_matrix = np.array([[entry["S"] for entry in rows_by_country[code]] for code in countries])

    fig = plt.figure(figsize=(18, 10))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.0, 1.0, 1.0], height_ratios=[1.0, 1.0])

    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(turns, avg_s, marker="o", label="avg S", color="#1b5e20")
    ax1.plot(turns, avg_cash, marker="o", label="avg cash stability", color="#1565c0")
    ax1.plot(turns, avg_domestic, marker="o", label="avg domestic burden", color="#8e24aa")
    ax1.plot(turns, avg_war, marker="o", label="avg war burden", color="#b71c1c")
    ax1.set_title(f"{result.summary['scenario_name']}: global trajectory")
    ax1.set_xlabel("Turn")
    ax1.set_ylabel("0-1 scale")
    ax1.grid(alpha=0.25)
    ax1.legend(loc="best")

    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(turns, avg_conflict, marker="o", label="avg conflict risk", color="#ef6c00")
    ax2.plot(turns, avg_protest, marker="o", label="avg protest pressure", color="#ffb300")
    ax2.plot(turns, avg_riot, marker="o", label="avg riot pressure", color="#fb8c00")
    ax2.plot(turns, avg_civil, marker="o", label="avg civil conflict pressure", color="#6d4c41")
    ax2.set_title("Conflict and domestic pressure")
    ax2.set_xlabel("Turn")
    ax2.set_ylabel("0-1 scale")
    ax2.grid(alpha=0.25)
    ax2.legend(loc="best")

    ax3 = fig.add_subplot(gs[0, 2])
    heat = ax3.imshow(s_matrix, aspect="auto", cmap="YlGnBu", vmin=0.20, vmax=0.55)
    ax3.set_title("Country S heatmap")
    ax3.set_xlabel("Turn")
    ax3.set_ylabel("Country")
    ax3.set_xticks(range(len(turns)))
    ax3.set_xticklabels(turns)
    ax3.set_yticks(range(len(countries)))
    ax3.set_yticklabels(countries)
    fig.colorbar(heat, ax=ax3, fraction=0.046, pad=0.04)

    ax4 = fig.add_subplot(gs[1, 0])
    final_s = [row["S"] for row in result.final_rows]
    final_support = [row["support_needed"] for row in result.final_rows]
    y = np.arange(len(countries))
    ax4.barh(y - 0.18, final_s, height=0.32, label="final S", color="#2e7d32")
    ax4.barh(y + 0.18, final_support, height=0.32, label="support needed", color="#ef6c00")
    ax4.set_yticks(y)
    ax4.set_yticklabels(countries)
    ax4.set_xlabel("Score")
    ax4.set_title("Final resilience vs support need")
    ax4.invert_yaxis()
    ax4.legend(loc="best")

    ax5 = fig.add_subplot(gs[1, 1])
    ax5.bar(turns, gray_counts, label="gray-zone", color="#6a1b9a")
    ax5.bar(turns, proxy_counts, bottom=gray_counts, label="proxy", color="#e53935")
    ax5.bar(
        turns,
        limited_counts,
        bottom=np.array(gray_counts) + np.array(proxy_counts),
        label="limited war",
        color="#212121",
    )
    ax5.set_title("Conflict events by turn")
    ax5.set_xlabel("Turn")
    ax5.set_ylabel("Event count")
    ax5.legend(loc="best")

    ax6 = fig.add_subplot(gs[1, 2])
    stage_bottom = np.zeros(len(turns))
    stage_series = [
        ("grievance", grievance_counts, "#5c6bc0"),
        ("protest", protest_counts, "#fdd835"),
        ("mass protest", mass_counts, "#fb8c00"),
        ("riot", riot_counts, "#e53935"),
        ("insurgency", insurgency_counts, "#8e24aa"),
        ("civil conflict", civil_counts, "#212121"),
    ]
    for label, values, color in stage_series:
        ax6.bar(turns, values, bottom=stage_bottom, label=label, color=color, alpha=0.92)
        stage_bottom = stage_bottom + np.array(values)
    ax6.set_title("Domestic stage counts by turn")
    ax6.set_xlabel("Turn")
    ax6.set_ylabel("Country count")
    ax6.legend(loc="best", fontsize=8)

    fig.tight_layout()
    fig.savefig(output_dir / "dashboard.png", dpi=180)
    plt.close(fig)


def plot_comparison(base_dir: Path, scenario_results: Dict[str, ScenarioRunResult]) -> None:
    if plt is None:
        return

    scenario_keys = list(scenario_results.keys())
    first = scenario_results[scenario_keys[0]]
    second = scenario_results[scenario_keys[1]]

    fig, axes = plt.subplots(2, 3, figsize=(18, 9))

    for scenario_key, result in scenario_results.items():
        label = result.summary["scenario_name"]
        turns = [row["turn"] for row in result.aggregate_rows]
        axes[0, 0].plot(turns, [row["avg_S"] for row in result.aggregate_rows], marker="o", label=label)
        axes[0, 1].plot(
            turns,
            [row["avg_war_burden"] for row in result.aggregate_rows],
            marker="o",
            label=f"{label} war",
        )
        axes[0, 1].plot(
            turns,
            [row["avg_domestic_burden"] for row in result.aggregate_rows],
            marker="o",
            linestyle="--",
            alpha=0.9,
            label=f"{label} domestic",
        )
        axes[0, 2].plot(
            turns,
            [row["avg_protest_pressure"] for row in result.aggregate_rows],
            marker="o",
            label=f"{label} protest",
        )
        axes[0, 2].plot(
            turns,
            [row["avg_riot_pressure"] for row in result.aggregate_rows],
            marker="o",
            linestyle="--",
            alpha=0.9,
            label=f"{label} riot",
        )

    axes[0, 0].set_title("Average S by turn")
    axes[0, 0].set_xlabel("Turn")
    axes[0, 0].set_ylabel("Average S")
    axes[0, 0].grid(alpha=0.25)
    axes[0, 0].legend(loc="best")

    axes[0, 1].set_title("War burden and domestic burden")
    axes[0, 1].set_xlabel("Turn")
    axes[0, 1].set_ylabel("Burden")
    axes[0, 1].grid(alpha=0.25)
    axes[0, 1].legend(loc="best", fontsize=8)

    axes[0, 2].set_title("Domestic instability pressure")
    axes[0, 2].set_xlabel("Turn")
    axes[0, 2].set_ylabel("Pressure")
    axes[0, 2].grid(alpha=0.25)
    axes[0, 2].legend(loc="best", fontsize=8)

    final_a = {row["code"]: row for row in first.final_rows}
    final_b = {row["code"]: row for row in second.final_rows}
    codes = sorted(final_a.keys())
    delta_s = [final_b[code]["S"] - final_a[code]["S"] for code in codes]
    delta_domestic = [final_b[code]["domestic_burden"] - final_a[code]["domestic_burden"] for code in codes]

    axes[1, 0].barh(codes, delta_s, color=["#2e7d32" if value >= 0 else "#c62828" for value in delta_s])
    axes[1, 0].set_title("Delta S: high adaptation minus low adaptation")
    axes[1, 0].set_xlabel("Delta S")
    axes[1, 0].axvline(0.0, color="black", linewidth=1)

    y = np.arange(len(codes))
    axes[1, 1].barh(y - 0.18, [final_a[code]["support_needed"] for code in codes], height=0.32, label="low adaptation", color="#ef9a9a")
    axes[1, 1].barh(y + 0.18, [final_b[code]["support_needed"] for code in codes], height=0.32, label="high adaptation", color="#90caf9")
    axes[1, 1].set_yticks(y)
    axes[1, 1].set_yticklabels(codes)
    axes[1, 1].set_xlabel("Support needed")
    axes[1, 1].set_title("Final support needed by country")
    axes[1, 1].legend(loc="best")

    axes[1, 2].barh(
        codes,
        delta_domestic,
        color=["#2e7d32" if value <= 0 else "#c62828" if value > 0 else "#9e9e9e" for value in delta_domestic],
    )
    axes[1, 2].set_title("Delta domestic burden: high minus low")
    axes[1, 2].set_xlabel("Delta domestic burden")
    axes[1, 2].axvline(0.0, color="black", linewidth=1)

    for axis in axes.flat:
        if axis not in (axes[1, 0], axes[1, 2]):
            axis.grid(alpha=0.20)

    fig.tight_layout()
    fig.savefig(base_dir / "comparison.png", dpi=180)
    plt.close(fig)


def persist_scenario_result(output_dir: Path, result: ScenarioRunResult) -> None:
    write_csv(output_dir / "turns.csv", result.rows)
    write_csv(output_dir / "aggregate.csv", result.aggregate_rows)
    write_csv(output_dir / "conflicts.csv", result.conflict_rows)
    write_jsonl(output_dir / "events.jsonl", result.event_log)
    write_json(output_dir / "summary.json", result.summary)
    write_markdown_summary(output_dir / "summary.md", result.summary, result.final_rows, result.event_log)
    plot_scenario_dashboard(output_dir, result)


def persist_comparison_report(base_dir: Path, scenario_results: Dict[str, ScenarioRunResult]) -> None:
    write_comparison_report(base_dir, scenario_results)
