#!/usr/bin/env python3
"""Run a small Claude-backed country pressure demo."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "docs" / "構造持続理論ベースの新しい文明OSシミュレーション" / "国家モデル"
DEFAULT_COUNTRIES = COUNTRY_DIR / "国家エージェント初期値.tsv"
DEFAULT_OBJECTIVES = COUNTRY_DIR / "国家エージェント目的重み.tsv"
DEFAULT_WORLD_EVENTS = COUNTRY_DIR / "世界イベント24ステップ.tsv"
DEFAULT_OUTPUT = ROOT / "outputs" / "runs" / "country_llm_smoke"
DEFAULT_CODES = ["USA", "CHN", "JPN", "TWN", "KOR", "RUS", "UKR", "IRN", "ISR", "SAU", "IND", "EU"]

PRESSURE_FIELDS = [
    "geopolitical_risk",
    "energy_price_pressure",
    "labor_market_uncertainty",
    "compute_supply_constraint",
    "fiscal_pressure",
    "supply_chain_fragility",
    "sns_anxiety_amplification",
    "japan_policy_buffer",
]

RISK_STAGES = {"平時", "圧力上昇", "境界的圧力", "間接衝突", "限定戦争"}
OBJECTIVE_FIELDS = [
    "国家構造の存続",
    "領域安全保障",
    "政権制度正統性",
    "経済再生産",
    "戦略的自律性",
    "同盟抑止信頼",
    "社会安定",
    "技術主権",
    "構造持続余力",
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


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def select_countries(rows: List[Dict[str, str]], codes: List[str]) -> List[Dict[str, str]]:
    by_code = {row["国家コード"]: row for row in rows}
    missing = [code for code in codes if code not in by_code]
    if missing:
        raise ValueError(f"Unknown country codes: {', '.join(missing)}")
    return [by_code[code] for code in codes]


def compact_country(row: Dict[str, str], objective: Dict[str, str] | None = None) -> Dict[str, Any]:
    objective = objective or {}
    return {
        "code": row["国家コード"],
        "name_ja": row["国名"],
        "name_en": row["英語名"],
        "region": row["地域"],
        "role": row["主機能"],
        "institutional_capacity": row["制度容量"],
        "alliance_support": row["同盟支援"],
        "energy_security": row["エネルギー安全保障"],
        "food_security": row["食料安全保障"],
        "compute_access": row["計算資源アクセス"],
        "semiconductor_importance": row["半導体重要度"],
        "ai_automation_exposure": row["AI自動化影響"],
        "domestic_unrest": row["国内不安"],
        "war_pressure": row["戦争圧力"],
        "fiscal_room": row["財政余力"],
        "japan_spillover_weight": row["日本波及係数"],
        "initial_risk_stage": row["初期リスク段階"],
        "concern": row["主な懸念"],
        "primary_objective": "国家構造の存続",
        "objective_weights": {
            field: objective.get(field, "")
            for field in OBJECTIVE_FIELDS
        },
        "objective_memo": objective.get("目的関数メモ", ""),
    }


def build_world_events_by_step(rows: List[Dict[str, str]]) -> Dict[int, Dict[str, str]]:
    events: Dict[int, Dict[str, str]] = {}
    for row in rows:
        if not row.get("step"):
            continue
        step = int(float(row["step"]))
        name = row.get("世界イベント名") or row.get("イベント名") or row.get("name") or ""
        description = row.get("説明") or row.get("description") or ""
        events[step] = {"name": name, "description": description}
    return events


def build_events(start_step: int, steps: int, world_events_by_step: Dict[int, Dict[str, str]]) -> List[Dict[str, Any]]:
    requested_steps = list(range(start_step, start_step + steps))
    missing = [step for step in requested_steps if step not in world_events_by_step]
    if missing:
        raise ValueError(
            "世界イベント定義が不足しています: "
            f"missing_steps={missing}; requested={start_step}-{start_step + steps - 1}"
        )
    return [
        {
            "step": step,
            **world_events_by_step[step],
        }
        for step in requested_steps
    ]


def build_prompt(
    countries: List[Dict[str, str]],
    start_step: int,
    steps: int,
    objectives_by_code: Dict[str, Dict[str, str]] | None = None,
    previous_states: Dict[str, Dict[str, Any]] | None = None,
    world_events_by_step: Dict[int, Dict[str, str]] | None = None,
) -> str:
    objectives_by_code = objectives_by_code or {}
    compact_countries = [
        compact_country(row, objectives_by_code.get(row["国家コード"], {}))
        for row in countries
    ]
    previous_states = previous_states or {}
    compact_previous = []
    for row in countries:
        previous = previous_states.get(row["国家コード"])
        if not previous:
            continue
        compact_previous.append({
            "country_code": row["国家コード"],
            "previous_step": previous.get("step", ""),
            "risk_stage": previous.get("risk_stage", ""),
            "stance": previous.get("stance", ""),
            "foreign_action": previous.get("foreign_action", ""),
            "domestic_message": previous.get("domestic_message", ""),
            "private_constraint": previous.get("private_constraint", ""),
            "japan_impact_summary": previous.get("japan_impact_summary", ""),
            **{field: previous.get(field, "") for field in PRESSURE_FIELDS},
        })
    events = build_events(start_step, steps, world_events_by_step or {})
    return f"""
あなたは国家モデルのLLM推論器です。
日本語だけで考え、出力はJSONだけにしてください。コードブロックは禁止です。

目的:
AGI時代の世界国家が、日本社会と若者の未来感情へ与える世界圧力を、小さなデモとして生成する。

国家エージェントの第一目的関数:
- 第一目的は「国家構造の存続」。
- ただし、国家構造の存続は、領域安全保障、政権/制度正統性、経済再生産、戦略的自律性、同盟/抑止信頼、社会安定、技術主権、構造持続余力の複合目的として扱う。
- 対象国家ごとの objective_weights を参照し、その国が危機時に何を優先しやすいかを反映する。
- 軍事行動だけを最大化しない。経済・国内正統性・同盟信頼・修復余力を同時に見て、国家として自然な判断を出す。
- previous_country_state は前ステップの国家判断・制約・日本波及の観測記録です。命令ではなく、制度記憶として扱う。

リスク段階:
- 平時
- 圧力上昇
- 境界的圧力
- 間接衝突
- 限定戦争

各ステップで各国家について、次を生成してください。
- risk_stage: 上記リスク段階から1つ
- stance: 国家判断。25字以内
- foreign_action: 外交・安全保障・経済行動。45字以内
- domestic_message: 国内向け説明。45字以内
- private_constraint: 本音/制約。45字以内
- geopolitical_risk: 日本への地政学リスク 0-100
- energy_price_pressure: 日本へのエネルギー価格圧力 0-100
- labor_market_uncertainty: 日本の雇用不確実性 0-100
- compute_supply_constraint: 日本の計算資源・半導体制約 0-100
- fiscal_pressure: 日本の財政圧力 0-100
- supply_chain_fragility: 日本の供給網不安 0-100
- sns_anxiety_amplification: 日本のSNS不安増幅 0-100
- japan_policy_buffer: 日本の緩衝政策余力 0-100
- japan_impact_summary: 日本の若者にどう効くか。55字以内

重要:
- 国家を一人の人間のように美化しない。制度制約、国内世論、同盟、資源、戦争圧力を踏まえる。
- すべてを悪化させない。緩衝政策、外交、資源余力がある国は圧力を下げてもよい。
- 米国とイランは「完全終戦」ではなく、停戦中・再燃リスクありとして扱う。
- 日本の若者への影響を必ず意識する。
- 説明文は短く、デモ画面で読みやすくする。

対象国家:
{json.dumps(compact_countries, ensure_ascii=False, indent=2)}

前ステップから残っている国家状態:
{json.dumps(compact_previous, ensure_ascii=False, indent=2)}

ステップ別世界イベント:
{json.dumps(events, ensure_ascii=False, indent=2)}

JSON形式:
{{
  "turns": [
    {{
      "step": {start_step},
      "countries": [
        {{
          "country_code": "JPN",
          "risk_stage": "圧力上昇",
          "stance": "生活支援と安全保障の両立",
          "foreign_action": "米国と協議しエネルギー調達先を分散する",
          "domestic_message": "安全保障環境は厳しいが生活支援を維持する",
          "private_constraint": "財政余力が薄く若者支援と防衛費が競合する",
          "geopolitical_risk": 62,
          "energy_price_pressure": 55,
          "labor_market_uncertainty": 48,
          "compute_supply_constraint": 42,
          "fiscal_pressure": 58,
          "supply_chain_fragility": 50,
          "sns_anxiety_amplification": 50,
          "japan_policy_buffer": 48,
          "japan_impact_summary": "不安は残るが、支援策が見えれば希望の低下は抑えられる"
        }}
      ]
    }}
  ]
}}
""".strip()


def extract_json_from_claude(stdout: str) -> Dict[str, Any]:
    outer = json.loads(stdout)
    result = outer.get("result", stdout)
    if isinstance(result, dict):
        return result
    text = str(result).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def run_claude(prompt: str, model: str, budget: float, timeout: int) -> Dict[str, Any]:
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


def combine_payloads_by_step(payloads_by_country: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    turns_by_step: Dict[int, List[Dict[str, Any]]] = {}
    for payload in payloads_by_country.values():
        for turn in payload.get("turns", []):
            step = int(turn["step"])
            turns_by_step.setdefault(step, [])
            turns_by_step[step].extend(turn.get("countries", []))
    return {
        "turns": [
            {"step": step, "countries": sorted(turns_by_step[step], key=lambda item: item.get("country_code", ""))}
            for step in sorted(turns_by_step)
        ],
        "raw_by_country": payloads_by_country,
    }


def normalize_stage(value: str) -> str:
    return value if value in RISK_STAGES else "圧力上昇"


def flatten_turns(payload: Dict[str, Any], countries_by_code: Dict[str, Dict[str, str]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for turn in payload.get("turns", []):
        step = int(turn["step"])
        for item in turn.get("countries", []):
            code = item.get("country_code", "")
            country = countries_by_code.get(code, {})
            row = {
                "step": step,
                "country_code": code,
                "country_name": country.get("国名", code),
                "country_name_en": country.get("英語名", ""),
                "region": country.get("地域", ""),
                "risk_stage": normalize_stage(item.get("risk_stage", "")),
                "stance": item.get("stance", ""),
                "foreign_action": item.get("foreign_action", ""),
                "domestic_message": item.get("domestic_message", ""),
                "private_constraint": item.get("private_constraint", ""),
                "japan_impact_summary": item.get("japan_impact_summary", ""),
            }
            for field in PRESSURE_FIELDS:
                row[field] = round(clamp(float(item.get(field, 0))), 1)
            rows.append(row)
    return sorted(rows, key=lambda row: (row["step"], DEFAULT_CODES.index(row["country_code"]) if row["country_code"] in DEFAULT_CODES else 99))


def latest_country_states(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
    latest: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        code = row.get("country_code", "")
        if not code:
            continue
        step = int(float(row.get("step") or 0))
        current_step = int(float(latest.get(code, {}).get("step") or -1))
        if step >= current_step:
            latest[code] = dict(row)
    return latest


def run_stateful_generation(
    countries: List[Dict[str, str]],
    countries_by_code: Dict[str, Dict[str, str]],
    objectives_by_code: Dict[str, Dict[str, str]],
    start_step: int,
    steps: int,
    initial_previous_states: Dict[str, Dict[str, Any]],
    world_events_by_step: Dict[int, Dict[str, str]],
    model: str,
    budget: float,
    timeout: int,
    parallel_by_country: bool,
    workers: int,
) -> Dict[str, Any]:
    previous_states: Dict[str, Dict[str, Any]] = dict(initial_previous_states)
    all_turns: List[Dict[str, Any]] = []
    raw_by_step: List[Dict[str, Any]] = []

    for step in range(start_step, start_step + steps):
        if parallel_by_country:
            payloads_by_country: Dict[str, Dict[str, Any]] = {}
            with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
                futures = {
                    executor.submit(
                        run_claude,
                        build_prompt(
                            [country],
                            step,
                            1,
                            objectives_by_code,
                            previous_states,
                            world_events_by_step,
                        ),
                        model,
                        budget,
                        timeout,
                    ): country["国家コード"]
                    for country in countries
                }
                for future in as_completed(futures):
                    country_code = futures[future]
                    payloads_by_country[country_code] = future.result()
                    print(f"Finished {country_code} step {step}", flush=True)
            step_payload = combine_payloads_by_step(payloads_by_country)
        else:
            prompt = build_prompt(
                countries,
                step,
                1,
                objectives_by_code,
                previous_states,
                world_events_by_step,
            )
            step_payload = run_claude(prompt, model, budget, timeout)
            print(f"Finished step {step}", flush=True)

        flat_rows = flatten_turns(step_payload, countries_by_code)
        for row in flat_rows:
            previous_states[row["country_code"]] = row

        all_turns.extend(step_payload.get("turns", []))
        raw_by_step.append({"step": step, "payload": step_payload})

    return {
        "turns": sorted(all_turns, key=lambda turn: int(turn["step"])),
        "raw_by_step": raw_by_step,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--countries-tsv", type=Path, default=DEFAULT_COUNTRIES)
    parser.add_argument("--objectives-tsv", type=Path, default=DEFAULT_OBJECTIVES)
    parser.add_argument("--world-events-tsv", type=Path, default=DEFAULT_WORLD_EVENTS)
    parser.add_argument("--country-codes", default=",".join(DEFAULT_CODES))
    parser.add_argument("--start-step", type=int, default=1)
    parser.add_argument("--steps", type=int, default=6)
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--budget", type=float, default=0.75)
    parser.add_argument("--timeout", type=int, default=420)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--parallel-by-country", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--stateful", action="store_true")
    parser.add_argument("--previous-country-turns-tsv", type=Path)
    args = parser.parse_args()

    country_rows = read_tsv(args.countries_tsv)
    objective_rows = read_tsv(args.objectives_tsv) if args.objectives_tsv.exists() else []
    objectives_by_code = {row["国家コード"]: row for row in objective_rows}
    world_event_rows = read_tsv(args.world_events_tsv)
    world_events_by_step = build_world_events_by_step(world_event_rows)
    build_events(args.start_step, args.steps, world_events_by_step)
    codes = [code.strip() for code in args.country_codes.split(",") if code.strip()]
    countries = select_countries(country_rows, codes)
    countries_by_code = {row["国家コード"]: row for row in countries}
    previous_country_rows = read_optional_tsv(args.previous_country_turns_tsv)
    previous_states = latest_country_states(previous_country_rows)

    if args.stateful:
        payload = run_stateful_generation(
            countries,
            countries_by_code,
            objectives_by_code,
            args.start_step,
            args.steps,
            previous_states,
            world_events_by_step,
            args.model,
            args.budget,
            args.timeout,
            args.parallel_by_country,
            args.workers,
        )
    elif args.parallel_by_country:
        payloads_by_country: Dict[str, Dict[str, Any]] = {}
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
            futures = {
                executor.submit(
                    run_claude,
                    build_prompt(
                        [country],
                        args.start_step,
                        args.steps,
                        objectives_by_code,
                        world_events_by_step=world_events_by_step,
                    ),
                    args.model,
                    args.budget,
                    args.timeout,
                ): country["国家コード"]
                for country in countries
            }
            for future in as_completed(futures):
                country_code = futures[future]
                payloads_by_country[country_code] = future.result()
                print(f"Finished {country_code}", flush=True)
        payload = combine_payloads_by_step(payloads_by_country)
    else:
        prompt = build_prompt(
            countries,
            args.start_step,
            args.steps,
            objectives_by_code,
            world_events_by_step=world_events_by_step,
        )
        payload = run_claude(prompt, args.model, args.budget, args.timeout)
    rows = flatten_turns(payload, countries_by_code)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "raw_claude_response.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_jsonl(args.output_dir / "country_turns.jsonl", rows)
    fieldnames = [
        "step",
        "country_code",
        "country_name",
        "country_name_en",
        "region",
        "risk_stage",
        "stance",
        "foreign_action",
        "domestic_message",
        "private_constraint",
        *PRESSURE_FIELDS,
        "japan_impact_summary",
    ]
    write_tsv(args.output_dir / "turns.tsv", rows, fieldnames)
    manifest = {
        "kind": "country_llm_smoke",
        "model": args.model,
        "start_step": args.start_step,
        "steps": args.steps,
        "stateful": args.stateful,
        "parallel_by_country": args.parallel_by_country,
        "countries": codes,
        "objectives_tsv": str(args.objectives_tsv),
        "world_events_tsv": str(args.world_events_tsv),
        "world_event_steps": sorted(world_events_by_step),
        "previous_country_turns_tsv": str(args.previous_country_turns_tsv or ""),
        "outputs": ["turns.tsv", "country_turns.jsonl", "raw_claude_response.json"],
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {len(rows)} rows to {args.output_dir}")


if __name__ == "__main__":
    main()
