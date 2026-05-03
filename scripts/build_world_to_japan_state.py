#!/usr/bin/env python3
"""Build Japan social-state and auto-event inputs from country LLM turns."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "docs" / "構造持続理論ベースの新しい文明OSシミュレーション" / "国家モデル"
DEFAULT_COUNTRY_TURNS = ROOT / "outputs" / "runs" / "country_llm_smoke" / "turns.tsv"
DEFAULT_COUNTRIES = COUNTRY_DIR / "国家エージェント初期値.tsv"
DEFAULT_OUTPUT = ROOT / "outputs" / "runs" / "country_llm_smoke"

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

STATE_FIELD_LABELS = {
    "geopolitical_risk": "地政学リスク",
    "energy_price_pressure": "エネルギー価格圧力",
    "labor_market_uncertainty": "雇用不確実性",
    "compute_supply_constraint": "計算資源制約",
    "fiscal_pressure": "財政圧力",
    "supply_chain_fragility": "供給網不安",
    "sns_anxiety_amplification": "SNS不安増幅",
    "japan_policy_buffer": "日本の緩衝政策余力",
}

STAGE_SEVERITY = {
    "平時": 0,
    "圧力上昇": 1,
    "境界的圧力": 2,
    "間接衝突": 3,
    "限定戦争": 4,
}


def read_tsv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: Iterable[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def to_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def rows_by_step(rows: List[Dict[str, str]]) -> Dict[int, List[Dict[str, str]]]:
    grouped: Dict[int, List[Dict[str, str]]] = {}
    for row in rows:
        step = int(to_float(row.get("step"), 0))
        grouped.setdefault(step, []).append(row)
    return grouped


def country_weights(country_rows: List[Dict[str, str]]) -> Dict[str, float]:
    weights = {}
    for row in country_rows:
        weights[row["国家コード"]] = max(0.0, to_float(row.get("日本波及係数"), 0.0))
    return weights


def weighted_average(rows: List[Dict[str, str]], weights: Dict[str, float], field: str) -> float:
    weighted_sum = 0.0
    weight_sum = 0.0
    for row in rows:
        weight = weights.get(row.get("country_code", ""), 50.0)
        weighted_sum += to_float(row.get(field), 0.0) * weight
        weight_sum += weight
    if not weight_sum:
        return 0.0
    return round(clamp(weighted_sum / weight_sum), 1)


def top_pressure_field(state: Dict[str, Any]) -> str:
    negative_fields = [field for field in PRESSURE_FIELDS if field != "japan_policy_buffer"]
    return max(negative_fields, key=lambda field: to_float(state.get(field), 0.0))


def top_pressure_fields(state: Dict[str, Any], limit: int = 2) -> set[str]:
    negative_fields = [field for field in PRESSURE_FIELDS if field != "japan_policy_buffer"]
    ranked = sorted(negative_fields, key=lambda field: to_float(state.get(field), 0.0), reverse=True)
    return set(ranked[:limit])


def high_risk_countries(rows: List[Dict[str, str]]) -> str:
    filtered = [
        row for row in rows
        if STAGE_SEVERITY.get(row.get("risk_stage", ""), 0) >= 3
    ]
    filtered.sort(
        key=lambda row: (
            STAGE_SEVERITY.get(row.get("risk_stage", ""), 0),
            to_float(row.get("geopolitical_risk"), 0.0),
        ),
        reverse=True,
    )
    return "、".join(f"{row.get('country_name')}({row.get('risk_stage')})" for row in filtered[:5])


def summarize_world_context(step: int, rows: List[Dict[str, str]], state: Dict[str, Any]) -> str:
    top_field = top_pressure_field(state)
    risk_text = high_risk_countries(rows) or "大きな衝突国なし"
    return (
        f"ステップ{step}: {STATE_FIELD_LABELS[top_field]}が{state[top_field]}。"
        f"高リスク国: {risk_text}。"
        f"日本の緩衝政策余力は{state['japan_policy_buffer']}。"
    )


def build_japan_state_rows(country_turns: List[Dict[str, str]], weights: Dict[str, float]) -> List[Dict[str, Any]]:
    grouped = rows_by_step(country_turns)
    state_rows = []
    for step in sorted(grouped):
        rows = grouped[step]
        state: Dict[str, Any] = {"step": step}
        for field in PRESSURE_FIELDS:
            state[field] = weighted_average(rows, weights, field)

        top_field = top_pressure_field(state)
        state["dominant_world_pressure"] = STATE_FIELD_LABELS[top_field]
        state["high_risk_countries"] = high_risk_countries(rows)
        state["world_context_for_agents"] = summarize_world_context(step, rows, state)
        state_rows.append(state)
    return state_rows


def event_intensity(value: float, threshold: float, scale: float = 35.0) -> float:
    return round(clamp((value - threshold) / scale, 0.20, 1.0), 2)


def should_emit_pressure_event(
    step: int,
    value: float,
    previous_value: float | None,
    threshold: float,
    worsening_delta: float = 4.0,
) -> tuple[bool, str]:
    if value < threshold:
        if previous_value is not None and previous_value >= threshold and value <= threshold - 3.0:
            return True, "緩和"
        return False, ""
    if previous_value is None or previous_value < threshold:
        return True, "新規発生"
    if value - previous_value >= worsening_delta:
        return True, "悪化"
    if step % 6 == 0:
        return True, "高止まり"
    return False, ""


def event_name_for_trend(base_name: str, trend: str) -> str:
    if trend == "悪化":
        return f"{base_name}の悪化"
    if trend == "高止まり":
        return f"{base_name}の高止まり"
    if trend == "緩和":
        return f"{base_name}の緩和"
    return base_name


def direction_for_trend(direction: str, trend: str) -> str:
    if trend == "緩和":
        return "不安↓ 生活予見性↑"
    if trend == "高止まり":
        return f"{direction} 慢性負荷↑"
    return direction


def youth_input_for_trend(youth_input: str, trend: str) -> str:
    if trend == "悪化":
        return f"{youth_input} 直近で悪化しており、前よりも日常の判断に入り込みやすい。"
    if trend == "高止まり":
        return f"{youth_input} 新しい事件というより、高い不安が続いて疲労感を生む。"
    if trend == "緩和":
        return "一部の圧力は和らいでいるが、すぐ安心できるほどの回復かは判断が分かれる。"
    return youth_input


def make_event(
    event_id: str,
    step: int,
    category: str,
    name: str,
    intensity: float,
    target: str,
    direction: str,
    source: str,
    countries: str,
    state_summary: str,
    youth_input: str,
) -> Dict[str, Any]:
    return {
        "イベントID": event_id,
        "step": step,
        "区分": category,
        "イベント名": name,
        "強度_0to1": f"{clamp(intensity, 0.0, 1.0):.2f}",
        "対象": target,
        "主な影響方向": direction,
        "発生源": source,
        "関連国": countries,
        "日本社会状態": state_summary,
        "若者への入力文": youth_input,
    }


def build_auto_events(country_turns: List[Dict[str, str]], state_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped = rows_by_step(country_turns)
    state_by_step = {int(row["step"]): row for row in state_rows}
    event_rows: List[Dict[str, Any]] = []
    running_id = 1

    for step in sorted(grouped):
        rows = grouped[step]
        previous_rows = grouped.get(step - 1, [])
        previous_stages = {row.get("country_code"): row.get("risk_stage") for row in previous_rows}
        state = state_by_step[step]
        previous_state = state_by_step.get(step - 1)
        state_summary = state["world_context_for_agents"]

        new_wars = [
            row for row in rows
            if row.get("risk_stage") == "限定戦争" and previous_stages.get(row.get("country_code")) != "限定戦争"
        ]
        if new_wars:
            countries = "、".join(row.get("country_name", "") for row in new_wars)
            event_rows.append(make_event(
                f"WE{running_id:03d}",
                step,
                "戦争",
                "世界限定戦争発生",
                0.95,
                "全体",
                "将来予見性↓ 生活防衛↑ 制度信頼↓",
                "国家LLMリスク段階",
                countries,
                state_summary,
                f"{countries}が限定戦争段階に入り、長期計画と生活安心感が揺らぐ。",
            ))
            running_id += 1

        new_proxy = [
            row for row in rows
            if row.get("risk_stage") == "間接衝突" and previous_stages.get(row.get("country_code")) not in {"間接衝突", "限定戦争"}
        ]
        if new_proxy:
            countries = "、".join(row.get("country_name", "") for row in new_proxy[:4])
            event_rows.append(make_event(
                f"WE{running_id:03d}",
                step,
                "世界イベント",
                "間接衝突拡大",
                0.72,
                "全体",
                "地政学リスク↑ SNS不安↑",
                "国家LLMリスク段階",
                countries,
                state_summary,
                f"{countries}の間接衝突化により、SNS上の不安と将来予見性の低下が強まる。",
            ))
            running_id += 1

        thresholds = [
            ("energy_price_pressure", 60.0, "エネルギー価格ショック", "生活コスト↑ 子ども意向↓", "エネルギー圧力が高く、家計と移動・電気代への不安が増える。"),
            ("compute_supply_constraint", 55.0, "半導体・計算資源制約", "学習機会格差↑ 雇用不安↑", "計算資源と半導体制約により、AI利用格差と進路不安が広がる。"),
            ("supply_chain_fragility", 56.0, "供給網不安拡大", "物価不安↑ 雇用安定↓", "供給網の不安定化により、物価と企業採用への不安が残る。"),
            ("labor_market_uncertainty", 55.0, "AI雇用不安増幅", "希望経路↓ 自己効力感↓", "AIと景気の不確実性により、努力が報われる経路が見えにくくなる。"),
            ("sns_anxiety_amplification", 58.0, "地政学SNS不安拡散", "不安↑ 怒り↑ 逃避行動↑", "危機情報がSNSで増幅し、不安と怒りが日常会話に入り込む。"),
        ]
        high_stop_fields = top_pressure_fields(state, limit=2)
        for field, threshold, name, direction, youth_input in thresholds:
            value = to_float(state.get(field), 0.0)
            previous_value = to_float(previous_state.get(field), 0.0) if previous_state else None
            emit, trend = should_emit_pressure_event(step, value, previous_value, threshold)
            if trend == "高止まり" and field not in high_stop_fields:
                emit = False
            if emit:
                intensity = event_intensity(value, threshold) if trend != "緩和" else 0.32
                event_rows.append(make_event(
                    f"WE{running_id:03d}",
                    step,
                    "世界イベント" if trend != "緩和" else "緩和",
                    event_name_for_trend(name, trend),
                    intensity,
                    "全体",
                    direction_for_trend(direction, trend),
                    STATE_FIELD_LABELS[field],
                    state.get("high_risk_countries", ""),
                    state_summary,
                    youth_input_for_trend(youth_input, trend),
                ))
                running_id += 1

        fiscal = to_float(state.get("fiscal_pressure"), 0.0)
        buffer = to_float(state.get("japan_policy_buffer"), 0.0)
        previous_fiscal = to_float(previous_state.get("fiscal_pressure"), 0.0) if previous_state else None
        previous_buffer = to_float(previous_state.get("japan_policy_buffer"), 100.0) if previous_state else None
        fiscal_condition = fiscal >= 55.0 and buffer <= 52.0
        previous_condition = (
            previous_fiscal is not None
            and previous_buffer is not None
            and previous_fiscal >= 55.0
            and previous_buffer <= 52.0
        )
        fiscal_worsened = (
            previous_fiscal is not None
            and previous_buffer is not None
            and (fiscal - previous_fiscal >= 4.0 or previous_buffer - buffer >= 4.0)
        )
        fiscal_chronic = step % 6 == 0
        if fiscal_condition and (not previous_condition or fiscal_worsened or fiscal_chronic):
            trend = "新規発生" if not previous_condition else "悪化" if fiscal_worsened else "高止まり"
            event_rows.append(make_event(
                f"WE{running_id:03d}",
                step,
                "制度制約",
                event_name_for_trend("財政制約による支援遅れ", trend),
                event_intensity(fiscal + (52.0 - buffer), 55.0, 45.0),
                "全体",
                direction_for_trend("制度信頼↓ 裏切られ感↑", trend),
                "日本社会状態",
                "日本",
                state_summary,
                youth_input_for_trend("財政圧力により若者支援や生活支援が遅れ、制度への失望が出やすい。", trend),
            ))
            running_id += 1

    return event_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--country-turns", type=Path, default=DEFAULT_COUNTRY_TURNS)
    parser.add_argument("--countries-tsv", type=Path, default=DEFAULT_COUNTRIES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    country_turns = read_tsv(args.country_turns)
    countries = read_tsv(args.countries_tsv)
    weights = country_weights(countries)

    japan_state_rows = build_japan_state_rows(country_turns, weights)
    auto_event_rows = build_auto_events(country_turns, japan_state_rows)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_tsv(
        args.output_dir / "japan_state.tsv",
        japan_state_rows,
        [
            "step",
            *PRESSURE_FIELDS,
            "dominant_world_pressure",
            "high_risk_countries",
            "world_context_for_agents",
        ],
    )
    write_tsv(
        args.output_dir / "auto_events.tsv",
        auto_event_rows,
        [
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
        ],
    )
    (args.output_dir / "world_to_japan_manifest.json").write_text(
        json.dumps(
            {
                "kind": "world_to_japan_state",
                "country_turns": str(args.country_turns),
                "countries_tsv": str(args.countries_tsv),
                "outputs": ["japan_state.tsv", "auto_events.tsv"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {len(japan_state_rows)} Japan state rows and {len(auto_event_rows)} auto events to {args.output_dir}")


if __name__ == "__main__":
    main()
