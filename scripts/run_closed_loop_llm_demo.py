#!/usr/bin/env python3
"""Run a stepwise closed-loop LLM demo.

The presentation viewer should replay generated rows. This runner is for
offline row-data generation: country state -> Japan state -> agents -> feedback
-> next step.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "outputs" / "runs" / "closed_loop_llm_71steps_40years"
DEFAULT_COUNTRY_CODES = "USA,CHN,JPN,TWN,KOR,PRK,RUS,UKR,IRN,ISR,SAU,EU"
DEFAULT_AGENT_IDS = (
    "A01,A02,A03,A04,A05,A06,A07,A08,A09,A10,A11,A14,"
    "A12,A13,A15,A17,A18,A27,W02,W22"
)
DEFAULT_ORGANIZATION_IDS = "O02,O04,O07,O10,O11,O12,O14,O15"
DEFAULT_AGENT_PANEL = ROOT / "domain_packs" / "agi_youth_japan" / "data" / "demo_panel_48.tsv"
DEFAULT_GENERATION_INFLOW_TEMPLATES = (
    ROOT / "domain_packs" / "agi_youth_japan" / "data" / "generation_inflow_templates.tsv"
)


LOG_FIELDNAMES = [
    "step",
    "phase",
    "status",
    "return_code",
    "start_time",
    "end_time",
    "duration_seconds",
    "command",
]


def append_log_row(path: Path, row: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=LOG_FIELDNAMES)
        if not exists:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in LOG_FIELDNAMES})


def run_command(
    cmd: List[str],
    dry_run: bool = False,
    log_path: Path | None = None,
    step: int | str = "",
    phase: str = "",
) -> None:
    print("$ " + " ".join(cmd), flush=True)
    start_time = datetime.now()
    start_monotonic = time.monotonic()
    status = "dry_run" if dry_run else "ok"
    return_code: int | str = ""
    if dry_run:
        if log_path:
            append_log_row(log_path, {
                "step": step,
                "phase": phase,
                "status": status,
                "return_code": return_code,
                "start_time": start_time.isoformat(timespec="seconds"),
                "end_time": datetime.now().isoformat(timespec="seconds"),
                "duration_seconds": 0.0,
                "command": json.dumps(cmd, ensure_ascii=False),
            })
        return
    try:
        completed = subprocess.run(cmd, cwd=ROOT, check=True)
        return_code = completed.returncode
    except subprocess.CalledProcessError as exc:
        status = "failed"
        return_code = exc.returncode
        raise
    finally:
        if log_path:
            end_time = datetime.now()
            append_log_row(log_path, {
                "step": step,
                "phase": phase,
                "status": status,
                "return_code": return_code,
                "start_time": start_time.isoformat(timespec="seconds"),
                "end_time": end_time.isoformat(timespec="seconds"),
                "duration_seconds": round(time.monotonic() - start_monotonic, 3),
                "command": json.dumps(cmd, ensure_ascii=False),
            })


def append_tsv(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("r", encoding="utf-8", newline="") as source_handle:
        reader = csv.reader(source_handle, delimiter="\t")
        rows = list(reader)
    if not rows:
        return
    if not destination.exists():
        with destination.open("w", encoding="utf-8", newline="") as dest_handle:
            writer = csv.writer(dest_handle, delimiter="\t")
            writer.writerows(rows)
        return
    with destination.open("a", encoding="utf-8", newline="") as dest_handle:
        writer = csv.writer(dest_handle, delimiter="\t")
        writer.writerows(rows[1:])


def ids_completed_for_step(path: Path, step: int, id_field: str) -> set[str]:
    if not path.exists():
        return set()
    completed: set[str] = set()
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            try:
                row_step = int(float(row.get("step", "")))
            except ValueError:
                continue
            if row_step == step and row.get(id_field):
                completed.add(row[id_field])
    return completed


def step_complete(path: Path, step: int, id_field: str, expected_ids: Iterable[str]) -> bool:
    expected = {item for item in expected_ids if item}
    if not expected:
        return False
    return expected.issubset(ids_completed_for_step(path, step, id_field))


def log_skipped_step(log_path: Path, step: int, phase: str, reason: str) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    append_log_row(log_path, {
        "step": step,
        "phase": phase,
        "status": "skipped",
        "return_code": "",
        "start_time": now,
        "end_time": now,
        "duration_seconds": 0.0,
        "command": reason,
    })


def copy_if_exists(source: Path, destination: Path) -> None:
    if not source.exists():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def read_optional_tsv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def generation_agent_ids_for_step(step: int) -> List[str]:
    ids: List[str] = []
    for row in read_optional_tsv(DEFAULT_GENERATION_INFLOW_TEMPLATES):
        try:
            trigger_step = int(float(row.get("発火ステップ", "")))
        except ValueError:
            continue
        agent_id = row.get("生成ID接頭辞", "")
        if agent_id and step >= trigger_step:
            ids.append(agent_id)
    return ids


def feedback_ready(agent_turns: Path) -> bool:
    if not agent_turns.exists():
        return False
    with agent_turns.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle) > 1


def build_world_to_japan(output_dir: Path, dry_run: bool, log_path: Path, step: int) -> None:
    world_dir = output_dir / "world_to_japan"
    run_command(
        [
            sys.executable,
            "scripts/build_world_to_japan_state.py",
            "--country-turns",
            str(output_dir / "country_turns.tsv"),
            "--output-dir",
            str(world_dir),
        ],
        dry_run,
        log_path,
        step,
        "world_to_japan",
    )
    if not dry_run:
        copy_if_exists(world_dir / "japan_state.tsv", output_dir / "japan_state.tsv")
        copy_if_exists(world_dir / "auto_events.tsv", output_dir / "auto_events.tsv")


def current_auto_events_input(output_dir: Path) -> Path:
    for name in [
        "auto_events_with_organization.tsv",
        "auto_events.tsv",
    ]:
        path = output_dir / name
        if path.exists():
            return path
    return output_dir / "auto_events.tsv"


def build_organization_to_agent_events(output_dir: Path, dry_run: bool, log_path: Path, step: int) -> None:
    run_command(
        [
            sys.executable,
            "scripts/build_organization_to_agent_events.py",
            "--organization-turns",
            str(output_dir / "organization_turns.tsv"),
            "--auto-events-tsv",
            str(output_dir / "auto_events.tsv"),
            "--output-dir",
            str(output_dir),
        ],
        dry_run,
        log_path,
        step,
        "organization_to_agent_events",
    )


def build_agent_feedback(
    output_dir: Path,
    dry_run: bool,
    log_path: Path,
    step: int,
    phase: str,
    agent_panel_tsv: Path = DEFAULT_AGENT_PANEL,
) -> None:
    feedback_dir = output_dir / "feedback"
    run_command(
        [
            sys.executable,
            "scripts/build_agent_feedback_loop.py",
            "--agent-turns",
            str(output_dir / "agent_turns.tsv"),
            "--japan-state-tsv",
            str(output_dir / "japan_state.tsv"),
            "--auto-events-tsv",
            str(current_auto_events_input(output_dir)),
            "--agent-panel-tsv",
            str(agent_panel_tsv),
            "--output-dir",
            str(feedback_dir),
        ],
        dry_run,
        log_path,
        step,
        phase,
    )
    if not dry_run:
        copy_if_exists(feedback_dir / "agent_feedback.tsv", output_dir / "agent_feedback.tsv")
        copy_if_exists(feedback_dir / "japan_state_feedback.tsv", output_dir / "japan_state_feedback.tsv")
        copy_if_exists(feedback_dir / "auto_events_with_feedback.tsv", output_dir / "auto_events_with_feedback.tsv")


def maybe_feedback_input(output_dir: Path, name: str) -> Path:
    feedback_path = output_dir / name
    if feedback_path.exists():
        return feedback_path
    if name == "auto_events_with_feedback.tsv":
        organization_path = output_dir / "auto_events_with_organization.tsv"
        if organization_path.exists():
            return organization_path
    return output_dir / {
        "japan_state_feedback.tsv": "japan_state.tsv",
        "auto_events_with_feedback.tsv": "auto_events.tsv",
    }[name]


def write_manifest(output_dir: Path, args: argparse.Namespace) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "kind": "closed_loop_llm_demo",
        "start_step": args.start_step,
        "steps": args.steps,
        "model": args.model,
        "scenario_mode": args.scenario_mode,
        "country_codes": args.country_codes,
        "agent_ids": args.agent_ids,
        "organization_ids": args.organization_ids,
        "country_budget": args.country_budget,
        "organization_budget": args.organization_budget,
        "agent_budget": args.agent_budget,
        "agent_panel_tsv": str(args.agent_panel_tsv),
        "outputs": [
            "country_turns.tsv",
            "organization_turns.tsv",
            "japan_state.tsv",
            "auto_events.tsv",
            "organization_events.tsv",
            "auto_events_with_organization.tsv",
            "japan_state_feedback.tsv",
            "auto_events_with_feedback.tsv",
            "agent_turns.tsv",
            "scheduled_events_used.tsv",
            "agent_feedback.tsv",
        ],
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run closed-loop LLM row generation.")
    parser.add_argument("--start-step", type=int, default=1)
    parser.add_argument("--steps", type=int, default=71)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--country-codes", default=DEFAULT_COUNTRY_CODES)
    parser.add_argument("--agent-ids", default=DEFAULT_AGENT_IDS)
    parser.add_argument("--organization-ids", default=DEFAULT_ORGANIZATION_IDS)
    parser.add_argument("--agent-panel-tsv", type=Path, default=DEFAULT_AGENT_PANEL)
    parser.add_argument("--country-budget", type=float, default=0.75)
    parser.add_argument("--organization-budget", type=float, default=0.45)
    parser.add_argument("--agent-budget", type=float, default=0.50)
    parser.add_argument("--timeout", type=int, default=420)
    parser.add_argument(
        "--scenario-mode",
        choices=[
            "no_intervention",
            "birth_grant_only",
            "structure_intervention",
            "structure_birth_grant_package",
            "structure_hope_family_package",
            "all",
        ],
        default="structure_intervention",
        help="Run comparison branch: no policies or structure-sustain interventions.",
    )
    parser.add_argument("--parallel-by-country", action="store_true")
    parser.add_argument("--parallel-by-organization", action="store_true")
    parser.add_argument("--parallel-by-agent", action="store_true")
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    raw_dir = output_dir / "raw"
    log_path = output_dir / "run_log.tsv"
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    write_manifest(output_dir, args)

    country_turns = output_dir / "country_turns.tsv"
    organization_turns = output_dir / "organization_turns.tsv"
    agent_turns = output_dir / "agent_turns.tsv"
    scheduled_events_used = output_dir / "scheduled_events_used.tsv"
    country_ids = [item.strip() for item in args.country_codes.split(",") if item.strip()]
    organization_ids = [item.strip() for item in args.organization_ids.split(",") if item.strip()]
    agent_ids = [item.strip() for item in args.agent_ids.split(",") if item.strip()]

    for step in range(args.start_step, args.start_step + args.steps):
        step_label = f"{step:03d}"
        country_step_dir = raw_dir / f"country_step_{step_label}"
        country_done = step_complete(country_turns, step, "country_code", country_ids)
        if country_done and not args.dry_run:
            print(f"Skip country step {step}: already completed", flush=True)
            log_skipped_step(log_path, step, "country_llm", "already completed")
        else:
            country_cmd = [
                sys.executable,
                "scripts/run_country_llm_demo.py",
                "--stateful",
                "--start-step",
                str(step),
                "--steps",
                "1",
                "--country-codes",
                args.country_codes,
                "--model",
                args.model,
                "--budget",
                str(args.country_budget),
                "--timeout",
                str(args.timeout),
                "--output-dir",
                str(country_step_dir),
            ]
            if country_turns.exists():
                country_cmd.extend(["--previous-country-turns-tsv", str(country_turns)])
            if args.parallel_by_country:
                country_cmd.extend(["--parallel-by-country", "--workers", str(args.workers)])
            run_command(country_cmd, args.dry_run, log_path, step, "country_llm")
            if not args.dry_run:
                append_tsv(country_step_dir / "turns.tsv", country_turns)

        build_world_to_japan(output_dir, args.dry_run, log_path, step)

        organization_step_dir = raw_dir / f"organization_step_{step_label}"
        organization_done = step_complete(
            organization_turns,
            step,
            "organization_id",
            organization_ids,
        )
        if organization_done and not args.dry_run:
            print(f"Skip organization step {step}: already completed", flush=True)
            log_skipped_step(log_path, step, "organization_llm", "already completed")
        else:
            organization_cmd = [
                sys.executable,
                "scripts/run_organization_llm_demo.py",
                "--stateful",
                "--start-step",
                str(step),
                "--steps",
                "1",
                "--organization-ids",
                args.organization_ids,
                "--model",
                args.model,
                "--budget",
                str(args.organization_budget),
                "--timeout",
                str(args.timeout),
                "--japan-state-tsv",
                str(output_dir / "japan_state.tsv"),
                "--auto-events-tsv",
                str(output_dir / "auto_events.tsv"),
                "--output-dir",
                str(organization_step_dir),
            ]
            if organization_turns.exists():
                organization_cmd.extend(["--previous-organization-turns-tsv", str(organization_turns)])
            if args.parallel_by_organization:
                organization_cmd.extend(["--parallel-by-organization", "--workers", str(args.workers)])
            run_command(organization_cmd, args.dry_run, log_path, step, "organization_llm")
            if not args.dry_run:
                append_tsv(organization_step_dir / "turns.tsv", organization_turns)

        if args.dry_run or organization_turns.exists():
            build_organization_to_agent_events(output_dir, args.dry_run, log_path, step)

        if feedback_ready(agent_turns):
            build_agent_feedback(
                output_dir,
                args.dry_run,
                log_path,
                step,
                "agent_feedback_pre",
                args.agent_panel_tsv,
            )

        agent_step_dir = raw_dir / f"agent_step_{step_label}"
        agent_cmd = [
            sys.executable,
            "scripts/run_civilization_os_llm_demo.py",
            "--stateful",
            "--start-step",
            str(step),
            "--steps",
            "1",
            "--agent-ids",
            args.agent_ids,
            "--model",
            args.model,
            "--budget",
            str(args.agent_budget),
            "--timeout",
            str(args.timeout),
            "--japan-state-tsv",
            str(maybe_feedback_input(output_dir, "japan_state_feedback.tsv")),
            "--auto-events-tsv",
            str(maybe_feedback_input(output_dir, "auto_events_with_feedback.tsv")),
            "--agent-panel-tsv",
            str(args.agent_panel_tsv),
            "--scenario-mode",
            args.scenario_mode,
            "--output-dir",
            str(agent_step_dir),
        ]
        expected_agent_ids = [*agent_ids, *generation_agent_ids_for_step(step)]
        agent_done = step_complete(agent_turns, step, "agent_id", expected_agent_ids)
        if agent_done and not args.dry_run:
            print(f"Skip agent step {step}: already completed", flush=True)
            log_skipped_step(log_path, step, "agent_llm", "already completed")
        else:
            if agent_turns.exists():
                agent_cmd.extend(["--previous-agent-turns-tsv", str(agent_turns)])
            if args.parallel_by_agent:
                agent_cmd.extend(["--parallel-by-agent", "--workers", str(args.workers)])
            run_command(agent_cmd, args.dry_run, log_path, step, "agent_llm")
            if not args.dry_run:
                append_tsv(agent_step_dir / "turns.tsv", agent_turns)
                append_tsv(agent_step_dir / "scheduled_events_used.tsv", scheduled_events_used)

        if args.dry_run or feedback_ready(agent_turns):
            build_agent_feedback(
                output_dir,
                args.dry_run,
                log_path,
                step,
                "agent_feedback_post",
                args.agent_panel_tsv,
            )
        print(f"Closed-loop step {step} finished", flush=True)


if __name__ == "__main__":
    main()
