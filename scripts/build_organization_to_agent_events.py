#!/usr/bin/env python3
"""Convert organization decisions into agent-facing auto events."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ORG_TURNS = ROOT / "outputs" / "runs" / "closed_loop_llm_24steps" / "organization_turns.tsv"
DEFAULT_AUTO_EVENTS = ROOT / "outputs" / "runs" / "closed_loop_llm_24steps" / "auto_events.tsv"
DEFAULT_OUTPUT = ROOT / "outputs" / "runs" / "closed_loop_llm_24steps"

EVENT_FIELDS = [
    "イベントID",
    "step",
    "区分",
    "イベント名",
    "強度_0to1",
    "対象",
    "主な影響方向",
    "発生源",
    "関連国",
    "日本社会状態",
    "若者への入力文",
]


def read_tsv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_optional_tsv(path: Path | None) -> List[Dict[str, str]]:
    if not path or not path.exists():
        return []
    return read_tsv(path)


def write_tsv(path: Path, rows: Iterable[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def to_int(value: Any, fallback: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return fallback


def grouped_by_step(rows: List[Dict[str, str]]) -> Dict[int, List[Dict[str, str]]]:
    grouped: Dict[int, List[Dict[str, str]]] = {}
    for row in rows:
        step = to_int(row.get("step"), 0)
        if step:
            grouped.setdefault(step, []).append(row)
    return grouped


def risk_score(row: Dict[str, str]) -> int:
    text = " ".join([
        row.get("hiring_policy", ""),
        row.get("youth_training_policy", ""),
        row.get("employment_retention_policy", ""),
        row.get("expected_youth_impact", ""),
    ])
    risk_words = ["縮小", "厳選", "削減", "外注", "非正規", "抑制", "不安", "選別"]
    positive_words = ["維持", "育成", "支援", "連携", "機会", "底上げ", "雇用維持"]
    return sum(word in text for word in risk_words) - sum(word in text for word in positive_words)


def summarize(rows: List[Dict[str, str]], field: str, limit: int = 3) -> str:
    parts = []
    for row in sorted(rows, key=risk_score, reverse=True)[:limit]:
        value = row.get(field, "")
        if value:
            parts.append(f"{row.get('organization_name', row.get('organization_id', ''))}: {value}")
    return " / ".join(parts)


def build_organization_events(org_turns: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    for step, rows in sorted(grouped_by_step(org_turns).items()):
        avg_risk = sum(risk_score(row) for row in rows) / max(1, len(rows))
        intensity = min(0.92, max(0.28, 0.48 + avg_risk * 0.08))
        hiring = summarize(rows, "hiring_policy")
        youth_impact = summarize(rows, "expected_youth_impact")
        working_impact = summarize(rows, "expected_working_generation_impact")
        direction = "採用不安↑ 若手育成経路↓" if avg_risk > 0 else "育成経路↑ 地域接続↑"
        events.append({
            "イベントID": f"OE{step:03d}",
            "step": step,
            "区分": "組織判断",
            "イベント名": "企業・組織の採用育成判断",
            "強度_0to1": f"{intensity:.2f}",
            "対象": "若者・現役世代",
            "主な影響方向": direction,
            "発生源": "組織運営LLM",
            "関連国": "日本",
            "日本社会状態": hiring,
            "若者への入力文": f"{youth_impact} 現役側には {working_impact}",
        })
    return events


def write_combined_events(path: Path, base_events: List[Dict[str, str]], org_events: List[Dict[str, Any]]) -> None:
    rows = [*base_events, *org_events]
    rows.sort(key=lambda row: (to_int(row.get("step"), 0), str(row.get("イベントID", ""))))
    write_tsv(path, rows, EVENT_FIELDS)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--organization-turns", type=Path, default=DEFAULT_ORG_TURNS)
    parser.add_argument("--auto-events-tsv", type=Path, default=DEFAULT_AUTO_EVENTS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    org_turns = read_tsv(args.organization_turns)
    base_events = read_optional_tsv(args.auto_events_tsv)
    org_events = build_organization_events(org_turns)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_tsv(args.output_dir / "organization_events.tsv", org_events, EVENT_FIELDS)
    write_combined_events(args.output_dir / "auto_events_with_organization.tsv", base_events, org_events)
    (args.output_dir / "organization_to_agent_manifest.json").write_text(
        json.dumps(
            {
                "kind": "organization_to_agent_events",
                "organization_turns": str(args.organization_turns),
                "auto_events_tsv": str(args.auto_events_tsv),
                "outputs": ["organization_events.tsv", "auto_events_with_organization.tsv"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {len(org_events)} organization events to {args.output_dir}")


if __name__ == "__main__":
    main()
