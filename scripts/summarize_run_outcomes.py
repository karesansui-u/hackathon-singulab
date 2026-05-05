#!/usr/bin/env python3
"""Summarize demo outcome metrics from generated agent_turns.tsv."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize hope and child-intent proxy metrics.")
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    path = args.run_dir / "agent_turns.tsv"
    if not path.exists():
        raise SystemExit(f"Missing {path}")

    rows_by_step: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in read_rows(path):
        try:
            step = int(float(row.get("step", "")))
        except ValueError:
            continue
        rows_by_step[step].append(row)

    best_hope_step = 0
    best_hope_count = -1
    best_child_step = 0
    best_child_proxy = -1.0
    for step, rows in sorted(rows_by_step.items()):
        hope_count = sum(1 for row in rows if row.get("emotion") == "希望")
        child_proxy = sum(
            1
            for row in rows
            if row.get("layer") in {"家族形成", "若者", "次世代"}
            and row.get("evaluation") == "良好"
            and row.get("emotion") in {"希望", "安心", "連帯感"}
        )
        if hope_count > best_hope_count:
            best_hope_step = step
            best_hope_count = hope_count
        if child_proxy > best_child_proxy:
            best_child_step = step
            best_child_proxy = child_proxy

    print(f"run_dir\t{args.run_dir}")
    print(f"steps\t{min(rows_by_step)}-{max(rows_by_step)}")
    print(f"best_hope_step\t{best_hope_step}")
    print(f"best_hope_count\t{best_hope_count}")
    print(f"best_family_positive_step\t{best_child_step}")
    print(f"best_family_positive_proxy\t{int(best_child_proxy)}")


if __name__ == "__main__":
    main()
