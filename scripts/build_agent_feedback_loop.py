#!/usr/bin/env python3
"""Convert agent actions into Japan social-state feedback."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
DOMAIN_PACK_DATA = ROOT / "domain_packs" / "agi_youth_japan" / "data"
DEFAULT_AGENT_TURNS = ROOT / "outputs" / "runs" / "civilization_os_llm_world_connected" / "turns.tsv"
DEFAULT_JAPAN_STATE = ROOT / "outputs" / "runs" / "country_llm_smoke" / "japan_state.tsv"
DEFAULT_AUTO_EVENTS = ROOT / "outputs" / "runs" / "country_llm_smoke" / "auto_events.tsv"
DEFAULT_OUTPUT = ROOT / "outputs" / "runs" / "civilization_os_llm_feedback"
DEFAULT_AGENT_PANEL = DOMAIN_PACK_DATA / "demo_panel_48.tsv"
DEFAULT_CHILD_COHORTS = DOMAIN_PACK_DATA / "child_cohorts.tsv"
DEFAULT_GENERATION_INFLOW_TEMPLATES = DOMAIN_PACK_DATA / "generation_inflow_templates.tsv"

STATE_FIELDS = [
    "geopolitical_risk",
    "energy_price_pressure",
    "labor_market_uncertainty",
    "compute_supply_constraint",
    "fiscal_pressure",
    "supply_chain_fragility",
    "sns_anxiety_amplification",
    "japan_policy_buffer",
]

STATE_LABELS = {
    "geopolitical_risk": "地政学リスク",
    "energy_price_pressure": "エネルギー価格圧力",
    "labor_market_uncertainty": "雇用不確実性",
    "compute_supply_constraint": "計算資源制約",
    "fiscal_pressure": "財政圧力",
    "supply_chain_fragility": "供給網不安",
    "sns_anxiety_amplification": "SNS不安増幅",
    "japan_policy_buffer": "日本の緩衝政策余力",
}


def read_tsv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_optional_tsv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    return read_tsv(path)


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


def read_agent_metadata(agent_panel_tsv: Path | None = None) -> Dict[str, Dict[str, str]]:
    rows = [
        *read_optional_tsv(DOMAIN_PACK_DATA / "youth_agents.tsv"),
        *read_optional_tsv(DOMAIN_PACK_DATA / "working_agents.tsv"),
    ]
    metadata = {row["エージェントID"]: row for row in rows if row.get("エージェントID")}
    metadata.update(read_generation_metadata())
    for panel_row in read_optional_tsv(agent_panel_tsv or DEFAULT_AGENT_PANEL):
        agent_id = panel_row.get("ID", "")
        if not agent_id.startswith(("A", "W", "YG_")) or agent_id not in metadata:
            continue
        patched = dict(metadata[agent_id])
        population_weight = (
            panel_row.get("全体代表重み_パーセント")
            or panel_row.get("代表重み_パーセント")
        )
        if population_weight:
            patched["人口重み_パーセント"] = population_weight
        metadata[agent_id] = patched
    return metadata


def read_generation_metadata() -> Dict[str, Dict[str, str]]:
    cohorts = {
        row.get("コホートID", ""): row
        for row in read_optional_tsv(DEFAULT_CHILD_COHORTS)
        if row.get("コホートID")
    }
    metadata: Dict[str, Dict[str, str]] = {}
    for template in read_optional_tsv(DEFAULT_GENERATION_INFLOW_TEMPLATES):
        agent_id = template.get("生成ID接頭辞", "")
        cohort = cohorts.get(template.get("流入元コホートID", ""))
        if not agent_id or not cohort:
            continue
        metadata[agent_id] = {
            "エージェントID": agent_id,
            "氏名": template.get("表示名方針", "") or cohort.get("表示名", ""),
            "人口重み_パーセント": cohort.get("代表重み_パーセント", "1.0"),
            "発信影響重み": "0.8",
            "ケア責任": "なし",
        }
    return metadata


def action_signal(row: Dict[str, str], metadata: Dict[str, str], key: str) -> float:
    category = row.get("action_category", "")
    emotion = row.get("emotion", "")
    evaluation = row.get("evaluation", "")
    intensity = clamp(to_float(row.get("intensity"), 0.0)) / 100.0
    care = metadata.get("ケア責任", "なし")

    signal = 0.0
    if key == "withdrawal_pressure":
        if category == "撤退":
            signal += 1.0
        if category == "回避・縮小":
            signal += 0.85
        if evaluation == "危険":
            signal += 0.24
        if emotion in {"絶望", "諦念", "喪失感"}:
            signal += 0.16
    elif key == "institution_demand_pressure":
        if category in {"抗議・発信", "制度利用"}:
            signal += 0.85
        if emotion in {"怒り", "裏切られ感"}:
            signal += 0.30
        if "支援" in row.get("social_post", "") or "制度" in row.get("social_post", ""):
            signal += 0.16
    elif key == "livelihood_defense_pressure":
        if category in {"生活防衛", "相談", "制度利用"}:
            signal += 0.82
        if any(word in row.get("action_detail", "") for word in ("家計", "光熱費", "支出", "生活")):
            signal += 0.18
    elif key == "learning_transition_pressure":
        if category == "学習・就活":
            signal += 0.88
        if any(word in row.get("action_detail", "") for word in ("学習", "資格", "スキル", "就活")):
            signal += 0.12
    elif key == "solidarity_pressure":
        if category == "参加・連帯":
            signal += 0.92
        if emotion == "連帯感":
            signal += 0.28
        if evaluation == "良好":
            signal += 0.12
    elif key == "information_overload_pressure":
        if category == "情報収集":
            signal += 0.72
        if any(word in row.get("action_detail", "") for word in ("SNS", "ニュース", "スレッド")):
            signal += 0.22
    elif key == "care_pressure":
        if category == "ケア継続":
            signal += 0.90
        if care in {"軽度", "中度", "重度"} and evaluation in {"注意", "危険"}:
            signal += {"軽度": 0.18, "中度": 0.26, "重度": 0.36}.get(care, 0.0)

    return clamp(signal * intensity * 100.0)


def build_feedback_rows(agent_turns: List[Dict[str, str]], metadata_by_id: Dict[str, Dict[str, str]]) -> List[Dict[str, Any]]:
    grouped = rows_by_step(agent_turns)
    rows = []
    signal_keys = [
        "withdrawal_pressure",
        "institution_demand_pressure",
        "livelihood_defense_pressure",
        "learning_transition_pressure",
        "solidarity_pressure",
        "information_overload_pressure",
        "care_pressure",
    ]

    for step in sorted(grouped):
        turns = grouped[step]
        weighted = {key: 0.0 for key in signal_keys}
        weight_sum = 0.0
        influence_weighted = {key: 0.0 for key in signal_keys}
        influence_sum = 0.0
        evaluation_counts = {"良好": 0.0, "中立": 0.0, "注意": 0.0, "危険": 0.0}
        pathway_sum = 0.0
        support_sum = 0.0
        intensity_sum = 0.0
        side_effect_weighted = 0.0
        policy_fatigue_weighted = 0.0
        fairness_gap_weighted = 0.0
        coercion_weighted = 0.0
        fiscal_anxiety_weighted = 0.0

        for turn in turns:
            metadata = metadata_by_id.get(turn.get("agent_id", ""), {})
            population_weight = max(0.1, to_float(metadata.get("人口重み_パーセント"), 1.0))
            influence_weight = population_weight * max(0.1, to_float(metadata.get("発信影響重み"), 1.0))
            weight_sum += population_weight
            influence_sum += influence_weight
            evaluation_counts[turn.get("evaluation", "中立")] = evaluation_counts.get(turn.get("evaluation", "中立"), 0.0) + population_weight
            pathway_sum += to_float(turn.get("pathway"), 0.0) * population_weight
            support_sum += to_float(turn.get("support"), 0.0) * population_weight
            intensity_sum += to_float(turn.get("intensity"), 0.0) * population_weight
            side_effect = turn.get("side_effect", "")
            if side_effect and side_effect != "なし":
                side_effect_weighted += population_weight * 100.0
            fatigue = to_float(turn.get("policy_fatigue"), 0.0)
            if fatigue:
                policy_fatigue_weighted += population_weight * fatigue
            fairness = to_float(turn.get("fairness_perception"), -1.0)
            if fairness >= 0:
                fairness_gap_weighted += population_weight * max(0.0, 100.0 - fairness)
            if side_effect == "強制感":
                coercion_weighted += population_weight * 100.0
            if side_effect == "財政不安":
                fiscal_anxiety_weighted += population_weight * 100.0

            for key in signal_keys:
                signal = action_signal(turn, metadata, key)
                weighted[key] += signal * population_weight
                influence_weighted[key] += signal * influence_weight

        if not weight_sum:
            continue

        row: Dict[str, Any] = {
            "step": step,
            "agent_count": len(turns),
            "population_weight_total": round(weight_sum, 2),
            "average_pathway": round(pathway_sum / weight_sum, 1),
            "average_support": round(support_sum / weight_sum, 1),
            "average_intensity": round(intensity_sum / weight_sum, 1),
        }
        for label in ["良好", "中立", "注意", "危険"]:
            row[f"{label}_share"] = round(evaluation_counts.get(label, 0.0) / weight_sum * 100.0, 1)
        for key in signal_keys:
            denominator = influence_sum if key in {"institution_demand_pressure", "information_overload_pressure"} else weight_sum
            source = influence_weighted if key in {"institution_demand_pressure", "information_overload_pressure"} else weighted
            row[key] = round(source[key] / max(denominator, 0.1), 1)
        row["side_effect_pressure"] = round(side_effect_weighted / max(weight_sum, 0.1), 1)
        row["policy_fatigue_pressure"] = round(policy_fatigue_weighted / max(weight_sum, 0.1), 1)
        row["fairness_gap_pressure"] = round(fairness_gap_weighted / max(weight_sum, 0.1), 1)
        row["coercion_pressure"] = round(coercion_weighted / max(weight_sum, 0.1), 1)
        row["fiscal_anxiety_pressure"] = round(fiscal_anxiety_weighted / max(weight_sum, 0.1), 1)

        row["feedback_summary"] = summarize_feedback(row)
        rows.append(row)
    return rows


def summarize_feedback(row: Dict[str, Any]) -> str:
    signals = [
        ("撤退", row["withdrawal_pressure"]),
        ("制度要求", row["institution_demand_pressure"]),
        ("生活防衛", row["livelihood_defense_pressure"]),
        ("学習移行", row["learning_transition_pressure"]),
        ("連帯", row["solidarity_pressure"]),
        ("情報過敏", row["information_overload_pressure"]),
        ("ケア", row["care_pressure"]),
        ("政策疲労", row.get("policy_fatigue_pressure", 0.0)),
        ("公平感欠損", row.get("fairness_gap_pressure", 0.0)),
    ]
    top = sorted(signals, key=lambda item: item[1], reverse=True)[:3]
    return "、".join(f"{label}{value:.1f}" for label, value in top)


def dominant_pressure(row: Dict[str, Any]) -> str:
    negative = [field for field in STATE_FIELDS if field != "japan_policy_buffer"]
    field = max(negative, key=lambda key: to_float(row.get(key), 0.0))
    return STATE_LABELS[field]


def feedback_deltas(feedback: Dict[str, Any] | None) -> Dict[str, float]:
    if not feedback:
        return {field: 0.0 for field in STATE_FIELDS}

    withdrawal = to_float(feedback.get("withdrawal_pressure"))
    institution = to_float(feedback.get("institution_demand_pressure"))
    livelihood = to_float(feedback.get("livelihood_defense_pressure"))
    learning = to_float(feedback.get("learning_transition_pressure"))
    solidarity = to_float(feedback.get("solidarity_pressure"))
    information = to_float(feedback.get("information_overload_pressure"))
    care = to_float(feedback.get("care_pressure"))

    return {
        "geopolitical_risk": 0.010 * information,
        "energy_price_pressure": 0.015 * livelihood,
        "labor_market_uncertainty": 0.035 * withdrawal - 0.040 * learning - 0.020 * solidarity,
        "compute_supply_constraint": -0.010 * learning,
        "fiscal_pressure": 0.025 * institution + 0.020 * care + 0.012 * livelihood,
        "supply_chain_fragility": 0.0,
        "sns_anxiety_amplification": 0.045 * institution + 0.035 * withdrawal + 0.025 * information - 0.035 * solidarity,
        "japan_policy_buffer": 0.040 * institution + 0.030 * learning + 0.055 * solidarity - 0.050 * withdrawal - 0.030 * care,
    }


def build_feedback_state_rows(japan_state_rows: List[Dict[str, str]], feedback_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    feedback_by_step = {int(row["step"]): row for row in feedback_rows}
    rows = []
    for state in japan_state_rows:
        step = int(to_float(state.get("step"), 0))
        source_feedback = feedback_by_step.get(step - 1)
        deltas = feedback_deltas(source_feedback)
        adjusted: Dict[str, Any] = {
            "step": step,
            "applied_feedback_from_step": source_feedback.get("step", "") if source_feedback else "",
        }
        for field in STATE_FIELDS:
            original = to_float(state.get(field), 0.0)
            delta = round(deltas[field], 2)
            adjusted[field] = round(clamp(original + delta), 1)
            adjusted[f"{field}_delta_from_agent_feedback"] = delta

        adjusted["dominant_world_pressure"] = dominant_pressure(adjusted)
        adjusted["high_risk_countries"] = state.get("high_risk_countries", "")
        feedback_text = source_feedback.get("feedback_summary", "なし") if source_feedback else "なし"
        adjusted["world_context_for_agents"] = (
            f"{state.get('world_context_for_agents', '')}"
            f" 国内フィードバック: {feedback_text}。"
        ).strip()
        rows.append(adjusted)
    return rows


def feedback_event(
    event_id: str,
    step: int,
    category: str,
    name: str,
    intensity: float,
    direction: str,
    source: str,
    summary: str,
    youth_input: str,
) -> Dict[str, Any]:
    return {
        "イベントID": event_id,
        "step": step,
        "区分": category,
        "イベント名": name,
        "強度_0to1": f"{clamp(intensity, 0.0, 1.0):.2f}",
        "対象": "全体",
        "主な影響方向": direction,
        "発生源": source,
        "関連国": "日本国内",
        "日本社会状態": summary,
        "若者への入力文": youth_input,
    }


def build_feedback_events(feedback_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    event_number = 1
    for feedback in feedback_rows:
        target_step = int(feedback["step"]) + 1
        summary = feedback["feedback_summary"]
        candidates = [
            (
                feedback["withdrawal_pressure"],
                30.0,
                "社会反応",
                "社会的撤退の拡大",
                "希望経路↓ 雇用不確実性↑",
                "撤退・回避が増え、学習や就労移行の経路が細く見えやすい。",
            ),
            (
                feedback["institution_demand_pressure"],
                24.0,
                "社会反応",
                "制度要求の可視化",
                "制度応答↑ SNS不安↑",
                "怒りや制度要求が可視化され、政策対応への期待と失望が同時に高まる。",
            ),
            (
                feedback["livelihood_defense_pressure"],
                18.0,
                "社会反応",
                "生活防衛シフト",
                "生活コスト不安↑ 子ども意向↓",
                "家計防衛が優先され、将来投資や子どもを迎える判断が後回しになる。",
            ),
            (
                feedback["learning_transition_pressure"],
                25.0,
                "社会反応",
                "移行学習の自走",
                "自己効力感↑ 雇用不確実性↓",
                "学び直しや就活行動が増え、AI時代の役割再設計に向かう人が出る。",
            ),
            (
                feedback["solidarity_pressure"],
                24.0,
                "社会反応",
                "連帯の芽",
                "連帯感↑ SNS不安↓",
                "一人で抱え込まず、友人・地域・職場で支え合う経路が見え始める。",
            ),
            (
                feedback["care_pressure"],
                18.0,
                "社会反応",
                "ケア負担の制度要求",
                "財政圧力↑ 制度信頼↓",
                "介護やケア負担が個人の限界を超え、制度対応を求める声が強まる。",
            ),
            (
                feedback["information_overload_pressure"],
                25.0,
                "社会反応",
                "情報過敏の拡大",
                "SNS不安↑ 地政学体感リスク↑",
                "ニュースやSNSの確認が増え、外圧が日常の不安として体感されやすくなる。",
            ),
        ]
        for value, threshold, category, name, direction, youth_input in candidates:
            if to_float(value) < threshold:
                continue
            rows.append(feedback_event(
                f"FB{event_number:03d}",
                target_step,
                category,
                name,
                round((to_float(value) - threshold) / 55.0 + 0.25, 2),
                direction,
                "若者・現役行動フィードバック",
                summary,
                youth_input,
            ))
            event_number += 1
    return rows


def write_combined_events(path: Path, auto_events: List[Dict[str, str]], feedback_events: List[Dict[str, Any]]) -> None:
    fieldnames = [
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
    rows = [*auto_events, *feedback_events]
    rows.sort(key=lambda row: (int(to_float(row.get("step"), 0)), str(row.get("イベントID", ""))))
    write_tsv(path, rows, fieldnames)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-turns", type=Path, default=DEFAULT_AGENT_TURNS)
    parser.add_argument("--japan-state-tsv", type=Path, default=DEFAULT_JAPAN_STATE)
    parser.add_argument("--auto-events-tsv", type=Path, default=DEFAULT_AUTO_EVENTS)
    parser.add_argument("--agent-panel-tsv", type=Path, default=DEFAULT_AGENT_PANEL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    agent_turns = read_tsv(args.agent_turns)
    japan_state_rows = read_tsv(args.japan_state_tsv)
    auto_events = read_optional_tsv(args.auto_events_tsv)
    metadata_by_id = read_agent_metadata(args.agent_panel_tsv)

    feedback_rows = build_feedback_rows(agent_turns, metadata_by_id)
    feedback_state_rows = build_feedback_state_rows(japan_state_rows, feedback_rows)
    feedback_events = build_feedback_events(feedback_rows)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    feedback_fieldnames = [
        "step",
        "agent_count",
        "population_weight_total",
        "average_pathway",
        "average_support",
        "average_intensity",
        "良好_share",
        "中立_share",
        "注意_share",
        "危険_share",
        "withdrawal_pressure",
        "institution_demand_pressure",
        "livelihood_defense_pressure",
        "learning_transition_pressure",
        "solidarity_pressure",
        "information_overload_pressure",
        "care_pressure",
        "side_effect_pressure",
        "policy_fatigue_pressure",
        "fairness_gap_pressure",
        "coercion_pressure",
        "fiscal_anxiety_pressure",
        "feedback_summary",
    ]
    write_tsv(args.output_dir / "agent_feedback.tsv", feedback_rows, feedback_fieldnames)

    state_fieldnames = [
        "step",
        "applied_feedback_from_step",
        *STATE_FIELDS,
        *[f"{field}_delta_from_agent_feedback" for field in STATE_FIELDS],
        "dominant_world_pressure",
        "high_risk_countries",
        "world_context_for_agents",
    ]
    write_tsv(args.output_dir / "japan_state_feedback.tsv", feedback_state_rows, state_fieldnames)

    event_fieldnames = [
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
    write_tsv(args.output_dir / "feedback_events.tsv", feedback_events, event_fieldnames)
    write_combined_events(args.output_dir / "auto_events_with_feedback.tsv", auto_events, feedback_events)

    (args.output_dir / "feedback_manifest.json").write_text(
        json.dumps(
            {
                "kind": "agent_feedback_loop",
                "agent_turns": str(args.agent_turns),
                "japan_state_tsv": str(args.japan_state_tsv),
                "auto_events_tsv": str(args.auto_events_tsv),
                "outputs": [
                    "agent_feedback.tsv",
                    "japan_state_feedback.tsv",
                    "feedback_events.tsv",
                    "auto_events_with_feedback.tsv",
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {len(feedback_rows)} feedback rows and {len(feedback_events)} feedback events to {args.output_dir}")


if __name__ == "__main__":
    main()
