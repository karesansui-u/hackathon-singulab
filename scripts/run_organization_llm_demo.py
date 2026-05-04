#!/usr/bin/env python3
"""Run organization decision LLM rows for the AGI youth domain pack."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
DOMAIN_PACK_DATA = ROOT / "domain_packs" / "agi_youth_japan" / "data"
DEFAULT_ORGANIZATIONS = DOMAIN_PACK_DATA / "organization_agents.tsv"
DEFAULT_OUTPUT = ROOT / "outputs" / "runs" / "organization_llm_smoke"
DEFAULT_JAPAN_STATE = ROOT / "outputs" / "runs" / "country_llm_smoke" / "japan_state.tsv"
DEFAULT_AUTO_EVENTS = ROOT / "outputs" / "runs" / "country_llm_smoke" / "auto_events.tsv"
DEFAULT_ORG_IDS = ("O02", "O04", "O07", "O10", "O11", "O12", "O14", "O15")

OUTPUT_FIELDS = [
    "step",
    "organization_id",
    "organization_name",
    "decision_maker",
    "organization_type",
    "industry",
    "region",
    "hiring_policy",
    "youth_training_policy",
    "ai_adoption_policy",
    "robotics_adoption_policy",
    "employment_retention_policy",
    "business_shift_policy",
    "expected_youth_impact",
    "expected_working_generation_impact",
    "reasoning_basis",
    "memory_update",
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


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def parse_ids(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def select_organizations(rows: List[Dict[str, str]], wanted_ids: List[str]) -> List[Dict[str, str]]:
    wanted = set(wanted_ids)
    order = {org_id: index for index, org_id in enumerate(wanted_ids)}
    selected = [row for row in rows if row.get("組織ID") in wanted]
    missing = [org_id for org_id in wanted_ids if org_id not in {row.get("組織ID") for row in selected}]
    if missing:
        raise ValueError(f"Unknown organization ids: {', '.join(missing)}")
    return sorted(selected, key=lambda row: order.get(row["組織ID"], 999))


def compact_japan_state(row: Dict[str, str]) -> Dict[str, Any]:
    if not row:
        return {}
    fields = [
        "geopolitical_risk",
        "energy_price_pressure",
        "labor_market_uncertainty",
        "compute_supply_constraint",
        "fiscal_pressure",
        "supply_chain_fragility",
        "sns_anxiety_amplification",
        "japan_policy_buffer",
    ]
    compact: Dict[str, Any] = {
        "dominant_world_pressure": row.get("dominant_world_pressure", ""),
        "high_risk_countries": row.get("high_risk_countries", ""),
        "context": row.get("world_context_for_agents", ""),
    }
    for field in fields:
        if row.get(field, "") != "":
            compact[field] = row[field]
    return compact


def build_rows_by_step(rows: List[Dict[str, str]]) -> Dict[int, List[Dict[str, str]]]:
    grouped: Dict[int, List[Dict[str, str]]] = {}
    for row in rows:
        if not row.get("step"):
            continue
        grouped.setdefault(int(float(row["step"])), []).append(row)
    return grouped


def latest_org_states(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
    latest: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        org_id = row.get("organization_id", "")
        if not org_id:
            continue
        step = int(float(row.get("step") or 0))
        current_step = int(float(latest.get(org_id, {}).get("step") or -1))
        if step >= current_step:
            latest[org_id] = dict(row)
    return latest


def build_prompt(
    organizations: List[Dict[str, str]],
    start_step: int,
    steps: int,
    japan_state_rows: List[Dict[str, str]] | None = None,
    auto_event_rows: List[Dict[str, str]] | None = None,
    previous_states: Dict[str, Dict[str, Any]] | None = None,
) -> str:
    compact_organizations = []
    for row in organizations:
        compact_organizations.append({
            "id": row["組織ID"],
            "organization_name": row["組織名"],
            "decision_maker": row["意思決定者氏名"],
            "persona": row["組織ペルソナ名"],
            "organization_type": row["組織種別"],
            "industry": row["業種"],
            "scale": row["規模区分"],
            "region": row["地域区分"],
            "employment_size": row["雇用人数規模"],
            "new_grad_hiring_dependency": row["新卒一括採用依存度"],
            "midcareer_dependency": row["中途即戦力依存度"],
            "nonregular_outsource_dependency": row["非正規外注依存度"],
            "membership_employment": row["メンバーシップ雇用度"],
            "youth_training_capacity": row["若手育成余力"],
            "ai_adoption_capacity": row["AI導入余力"],
            "robotics_adoption_capacity": row["ロボ導入余力"],
            "cash_room": row["資金余力"],
            "labor_shortage_pressure": row["人手不足圧力"],
            "short_term_profit_pressure": row["短期利益圧力"],
            "wage_increase_room": row["賃上げ余力"],
            "price_pass_through_room": row["価格転嫁余力"],
            "regional_responsibility": row["地域責任意識"],
            "structure_sustain_investment": row["構造持続投資姿勢"],
            "decision_speed": row["意思決定速度"],
            "initial_hiring_policy": row["採用方針_初期"],
            "initial_youth_training_policy": row["若手育成方針_初期"],
            "initial_ai_policy": row["AI導入方針_初期"],
            "initial_robotics_policy": row["ロボ導入方針_初期"],
            "initial_employment_retention": row["雇用維持姿勢_初期"],
            "initial_business_shift": row["事業転換方針_初期"],
        })

    previous_states = previous_states or {}
    compact_previous = []
    for row in organizations:
        previous = previous_states.get(row["組織ID"])
        if not previous:
            continue
        compact_previous.append({
            "id": row["組織ID"],
            "previous_step": previous.get("step", ""),
            "hiring_policy": previous.get("hiring_policy", ""),
            "youth_training_policy": previous.get("youth_training_policy", ""),
            "ai_adoption_policy": previous.get("ai_adoption_policy", ""),
            "robotics_adoption_policy": previous.get("robotics_adoption_policy", ""),
            "employment_retention_policy": previous.get("employment_retention_policy", ""),
            "business_shift_policy": previous.get("business_shift_policy", ""),
            "memory_update": previous.get("memory_update", ""),
        })

    japan_state_by_step = {
        int(float(row["step"])): row
        for row in japan_state_rows or []
        if row.get("step")
    }
    auto_events_by_step = build_rows_by_step(auto_event_rows or [])
    compact_steps = []
    for step in range(start_step, start_step + steps):
        compact_steps.append({
            "step": step,
            "world_state": compact_japan_state(japan_state_by_step.get(step, {})),
            "auto_events": [
                {
                    "id": event.get("イベントID", ""),
                    "type": event.get("区分", ""),
                    "name": event.get("イベント名", ""),
                    "intensity": event.get("強度_0to1", ""),
                    "direction": event.get("主な影響方向", ""),
                    "description": event.get("若者への入力文", ""),
                }
                for event in auto_events_by_step.get(step, [])
            ],
        })

    return f"""
あなたは日本の組織運営シミュレーションの観測器です。
日本語だけで考え、出力はJSONだけにしてください。コードブロックは禁止です。

目的:
AGI・生成AI・汎用ロボティクス普及下で、企業・自治体・教育機関が、採用・若手育成・AI導入・ロボ導入・雇用維持・事業転換をどう判断するかを観測する。

重要:
- 組織に命令しない。組織属性、制約、世界状態、前ステップ記憶を情報として扱う。
- 日本型雇用の制約を考える。新卒一括採用、長期雇用、OJT、非正規調整、稟議、現場抵抗、地域責任。
- 利益最大化だけでなく、採用市場、若手育成、地域雇用、ケア、制度信頼、構造持続投資を考慮する。
- 短期合理性と長期の構造持続が衝突する場合は、その葛藤を判断根拠に出す。
- すべての組織を同じ方向に動かさない。資金余力、業種、地域責任、導入余力で分岐させる。
- 各項目は60字以内。reasoning_basis と memory_update は90字以内。

出力項目:
- hiring_policy
- youth_training_policy
- ai_adoption_policy
- robotics_adoption_policy
- employment_retention_policy
- business_shift_policy
- expected_youth_impact
- expected_working_generation_impact
- reasoning_basis
- memory_update

対象組織:
{json.dumps(compact_organizations, ensure_ascii=False, indent=2)}

前ステップから残っている組織状態:
{json.dumps(compact_previous, ensure_ascii=False, indent=2)}

ステップ別の観測条件:
{json.dumps(compact_steps, ensure_ascii=False, indent=2)}

JSON形式:
{{
  "turns": [
    {{
      "step": {start_step},
      "organizations": [
        {{
          "organization_id": "O02",
          "hiring_policy": "新卒をAI活用前提で厳選し、中途採用を増やす",
          "youth_training_policy": "若手研修をAIネイティブ型へ再設計する",
          "ai_adoption_policy": "全社基盤として導入する",
          "robotics_adoption_policy": "物理ロボは限定実験に留める",
          "employment_retention_policy": "雇用維持より職務転換を優先する",
          "business_shift_policy": "AI基盤投資へ集中する",
          "expected_youth_impact": "AI人材以外に選別不安が広がる",
          "expected_working_generation_impact": "現役IT職に再学習圧力が高まる",
          "reasoning_basis": "...",
          "memory_update": "..."
        }}
      ]
    }}
  ]
}}
""".strip()


def extract_json_from_text(text: str) -> Dict[str, Any]:
    text = str(text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def extract_json_from_claude(stdout: str) -> Dict[str, Any]:
    outer = json.loads(stdout)
    result = outer.get("result", stdout)
    if isinstance(result, dict):
        return result
    return extract_json_from_text(str(result))


def is_codex_model(model: str) -> bool:
    return model == "codex" or model.startswith("codex:") or model.startswith("gpt-")


def codex_model_name(model: str) -> str:
    if model == "codex":
        return "gpt-5.2"
    if model.startswith("codex:"):
        return model.split(":", 1)[1]
    return model


def run_codex(prompt: str, model: str, timeout: int) -> Dict[str, Any]:
    output_path = Path(tempfile.mkstemp(prefix="codex_llm_", suffix=".txt")[1])
    cmd = [
        "codex",
        "--ask-for-approval",
        "never",
        "exec",
        "--ignore-user-config",
        "--ignore-rules",
        "--ephemeral",
        "-m",
        codex_model_name(model),
        "-c",
        'model_reasoning_effort="low"',
        "--sandbox",
        "read-only",
        "--skip-git-repo-check",
        "--output-last-message",
        str(output_path),
        "-",
    ]
    try:
        completed = subprocess.run(
            cmd,
            cwd=ROOT,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr or completed.stdout)
        text = output_path.read_text(encoding="utf-8").strip() or completed.stdout
        return extract_json_from_text(text)
    finally:
        output_path.unlink(missing_ok=True)


def run_claude(prompt: str, model: str, budget: float, timeout: int) -> Dict[str, Any]:
    if is_codex_model(model):
        return run_codex(prompt, model, timeout)
    cmd = [
        "claude",
        "-p",
        "--model",
        model,
        "--max-budget-usd",
        str(budget),
        "--tools",
        "",
        "--output-format",
        "json",
        prompt,
    ]
    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr or completed.stdout)
    return extract_json_from_claude(completed.stdout)


def combine_payloads_by_step(payloads_by_org: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    turns_by_step: Dict[int, List[Dict[str, Any]]] = {}
    for payload in payloads_by_org.values():
        for turn in payload.get("turns", []):
            step = int(turn["step"])
            turns_by_step.setdefault(step, [])
            turns_by_step[step].extend(turn.get("organizations", []))
    return {
        "turns": [
            {"step": step, "organizations": sorted(turns_by_step[step], key=lambda item: item.get("organization_id", ""))}
            for step in sorted(turns_by_step)
        ],
        "raw_by_organization": payloads_by_org,
    }


def flatten_turns(payload: Dict[str, Any], organizations_by_id: Dict[str, Dict[str, str]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for turn in payload.get("turns", []):
        step = int(turn["step"])
        for item in turn.get("organizations", []):
            org_id = item.get("organization_id", "")
            org = organizations_by_id.get(org_id, {})
            row = {
                "step": step,
                "organization_id": org_id,
                "organization_name": org.get("組織名", org_id),
                "decision_maker": org.get("意思決定者氏名", ""),
                "organization_type": org.get("組織種別", ""),
                "industry": org.get("業種", ""),
                "region": org.get("地域区分", ""),
            }
            for field in OUTPUT_FIELDS:
                if field not in row:
                    row[field] = item.get(field, "")
            rows.append(row)
    return sorted(rows, key=lambda row: (row["step"], row["organization_id"]))


def run_stateful_generation(
    organizations: List[Dict[str, str]],
    organizations_by_id: Dict[str, Dict[str, str]],
    start_step: int,
    steps: int,
    japan_state_rows: List[Dict[str, str]],
    auto_event_rows: List[Dict[str, str]],
    initial_previous_states: Dict[str, Dict[str, Any]],
    model: str,
    budget: float,
    timeout: int,
    parallel_by_organization: bool,
    workers: int,
) -> Dict[str, Any]:
    previous_states: Dict[str, Dict[str, Any]] = dict(initial_previous_states)
    all_turns: List[Dict[str, Any]] = []
    raw_by_step: List[Dict[str, Any]] = []

    for step in range(start_step, start_step + steps):
        if parallel_by_organization:
            payloads_by_org: Dict[str, Dict[str, Any]] = {}
            with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
                futures = {
                    executor.submit(
                        run_claude,
                        build_prompt([org], step, 1, japan_state_rows, auto_event_rows, previous_states),
                        model,
                        budget,
                        timeout,
                    ): org["組織ID"]
                    for org in organizations
                }
                for future in as_completed(futures):
                    org_id = futures[future]
                    payloads_by_org[org_id] = future.result()
                    print(f"Finished {org_id} step {step}", flush=True)
            step_payload = combine_payloads_by_step(payloads_by_org)
        else:
            step_payload = run_claude(
                build_prompt(organizations, step, 1, japan_state_rows, auto_event_rows, previous_states),
                model,
                budget,
                timeout,
            )
            print(f"Finished organization step {step}", flush=True)

        flat_rows = flatten_turns(step_payload, organizations_by_id)
        for row in flat_rows:
            previous_states[row["organization_id"]] = row

        all_turns.extend(step_payload.get("turns", []))
        raw_by_step.append({"step": step, "payload": step_payload})

    return {
        "turns": sorted(all_turns, key=lambda turn: int(turn["step"])),
        "raw_by_step": raw_by_step,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--organizations-tsv", type=Path, default=DEFAULT_ORGANIZATIONS)
    parser.add_argument("--organization-ids", default=",".join(DEFAULT_ORG_IDS))
    parser.add_argument("--start-step", type=int, default=1)
    parser.add_argument("--steps", type=int, default=3)
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--budget", type=float, default=0.45)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--japan-state-tsv", type=Path, default=DEFAULT_JAPAN_STATE)
    parser.add_argument("--auto-events-tsv", type=Path, default=DEFAULT_AUTO_EVENTS)
    parser.add_argument("--parallel-by-organization", action="store_true")
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--stateful", action="store_true")
    parser.add_argument("--previous-organization-turns-tsv", type=Path)
    args = parser.parse_args()

    org_rows = read_tsv(args.organizations_tsv)
    org_ids = parse_ids(args.organization_ids)
    organizations = select_organizations(org_rows, org_ids)
    organizations_by_id = {row["組織ID"]: row for row in organizations}
    japan_state_rows = read_optional_tsv(args.japan_state_tsv)
    auto_event_rows = read_optional_tsv(args.auto_events_tsv)
    previous_rows = read_optional_tsv(args.previous_organization_turns_tsv)
    previous_states = latest_org_states(previous_rows)

    if args.stateful:
        payload = run_stateful_generation(
            organizations,
            organizations_by_id,
            args.start_step,
            args.steps,
            japan_state_rows,
            auto_event_rows,
            previous_states,
            args.model,
            args.budget,
            args.timeout,
            args.parallel_by_organization,
            args.workers,
        )
    elif args.parallel_by_organization:
        payloads_by_org: Dict[str, Dict[str, Any]] = {}
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
            futures = {
                executor.submit(
                    run_claude,
                    build_prompt([org], args.start_step, args.steps, japan_state_rows, auto_event_rows),
                    args.model,
                    args.budget,
                    args.timeout,
                ): org["組織ID"]
                for org in organizations
            }
            for future in as_completed(futures):
                org_id = futures[future]
                payloads_by_org[org_id] = future.result()
                print(f"Finished {org_id}", flush=True)
        payload = combine_payloads_by_step(payloads_by_org)
    else:
        payload = run_claude(
            build_prompt(organizations, args.start_step, args.steps, japan_state_rows, auto_event_rows),
            args.model,
            args.budget,
            args.timeout,
        )

    rows = flatten_turns(payload, organizations_by_id)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "raw_claude_response.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_jsonl(args.output_dir / "organization_states.jsonl", rows)
    write_tsv(args.output_dir / "turns.tsv", rows, OUTPUT_FIELDS)
    (args.output_dir / "manifest.json").write_text(
        json.dumps(
            {
                "kind": "organization_llm_demo",
                "model": args.model,
                "start_step": args.start_step,
                "steps": args.steps,
                "organizations": org_ids,
                "stateful": args.stateful,
                "parallel_by_organization": args.parallel_by_organization,
                "japan_state_tsv": str(args.japan_state_tsv) if japan_state_rows else "",
                "auto_events_tsv": str(args.auto_events_tsv) if auto_event_rows else "",
                "previous_organization_turns_tsv": str(args.previous_organization_turns_tsv or ""),
                "outputs": ["turns.tsv", "organization_states.jsonl", "raw_claude_response.json"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {len(rows)} organization rows to {args.output_dir}")


if __name__ == "__main__":
    main()
