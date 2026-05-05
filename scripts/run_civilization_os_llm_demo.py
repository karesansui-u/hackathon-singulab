#!/usr/bin/env python3
"""Run a tiny Claude-backed Civilization OS agent demo.

This is intentionally small: it asks Claude to simulate a handful of agents
for a handful of steps, then writes viewer-friendly artifacts.
"""

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
DEFAULT_OUTPUT = ROOT / "outputs" / "runs" / "civilization_os_llm_smoke"
DEFAULT_JAPAN_STATE = ROOT / "outputs" / "runs" / "country_llm_smoke" / "japan_state.tsv"
DEFAULT_AUTO_EVENTS = ROOT / "outputs" / "runs" / "country_llm_smoke" / "auto_events.tsv"
DEFAULT_AGENT_PANEL = DOMAIN_PACK_DATA / "demo_panel_48.tsv"
DEFAULT_TIME_SCHEDULE = DOMAIN_PACK_DATA / "time_schedule.tsv"
DEFAULT_CHILD_COHORTS = DOMAIN_PACK_DATA / "child_cohorts.tsv"
DEFAULT_GENERATION_INFLOW_TEMPLATES = DOMAIN_PACK_DATA / "generation_inflow_templates.tsv"
DEFAULT_AGENT_IDS = (
    "A01", "A02", "A03", "A04", "A05", "A06",
    "A07", "A08", "A09", "A10", "A11", "A14",
    "A12", "A13", "A15", "A17", "A18", "A27",
    "W02", "W22",
)
ACTION_CATEGORIES = {
    "静観",
    "情報収集",
    "相談",
    "生活防衛",
    "回避・縮小",
    "学習・就活",
    "制度利用",
    "参加・連帯",
    "抗議・発信",
    "ケア継続",
    "撤退",
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


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def parse_agent_ids(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def select_agents(
    youth_rows: List[Dict[str, str]],
    working_rows: List[Dict[str, str]],
    wanted_ids: List[str],
) -> List[Dict[str, str]]:
    # Pick a small but varied panel: good/caution/danger youth and caution/danger working adults.
    wanted = set(wanted_ids)
    order = {agent_id: index for index, agent_id in enumerate(wanted_ids)}
    rows = [row for row in [*youth_rows, *working_rows] if row.get("エージェントID") in wanted]
    return sorted(rows, key=lambda row: order.get(row["エージェントID"], 999))


def to_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def read_agent_panel_overrides(path: Path | None) -> Dict[str, Dict[str, str]]:
    rows = read_optional_tsv(path)
    return {
        row["ID"]: row
        for row in rows
        if row.get("ID", "").startswith(("A", "W", "YG_")) and row.get("本番対象", "1") != "0"
    }


def apply_agent_panel_overrides(
    agents: List[Dict[str, str]],
    overrides_by_id: Dict[str, Dict[str, str]],
) -> List[Dict[str, str]]:
    if not overrides_by_id:
        return agents
    patched = []
    for row in agents:
        override = overrides_by_id.get(row["エージェントID"])
        if not override:
            patched.append(row)
            continue
        merged = dict(row)
        population_weight = (
            override.get("全体代表重み_パーセント")
            or override.get("代表重み_パーセント")
        )
        if population_weight:
            merged["人口重み_パーセント"] = population_weight
        merged["パネル層内代表重み"] = override.get("代表重み_パーセント", "")
        merged["パネル表示重み"] = override.get("UI表示重み", "")
        merged["パネル選抜理由"] = override.get("選抜理由", "")
        patched.append(merged)
    return patched


def is_birth_grant_package_event(event: Dict[str, str]) -> bool:
    event_id = event.get("イベントID", "")
    return event_id.startswith("BP")


def is_hope_family_package_event(event: Dict[str, str]) -> bool:
    event_id = event.get("イベントID", "")
    return event_id.startswith("HP")


def is_direct_birth_support_event(event: Dict[str, str]) -> bool:
    event_id = event.get("イベントID", "")
    return event_id == "P04" or is_birth_grant_package_event(event)


def is_base_pressure_event(event: Dict[str, str]) -> bool:
    event_id = event.get("イベントID", "")
    return (
        event.get("区分") != "政策"
        and not event_id.startswith("P")
        and not is_birth_grant_package_event(event)
        and not is_hope_family_package_event(event)
    )


def filter_events_for_scenario(events: List[Dict[str, str]], scenario_mode: str) -> List[Dict[str, str]]:
    if scenario_mode == "no_intervention":
        return [event for event in events if is_base_pressure_event(event)]
    if scenario_mode == "birth_grant_only":
        return [
            event for event in events
            if is_base_pressure_event(event) or is_direct_birth_support_event(event)
        ]
    if scenario_mode == "structure_intervention":
        return [
            event for event in events
            if not is_direct_birth_support_event(event)
            and not is_hope_family_package_event(event)
        ]
    if scenario_mode == "structure_birth_grant_package":
        return [event for event in events if not is_hope_family_package_event(event)]
    if scenario_mode == "structure_hope_family_package":
        return events
    return events


def active_events(events: List[Dict[str, str]], step: int) -> List[Dict[str, str]]:
    active: List[Dict[str, str]] = []
    for event in events:
        try:
            start = int(event["開始ステップ"])
            end = int(event["終了ステップ"])
        except (KeyError, ValueError):
            continue
        if start <= step <= end:
            active.append(event)
    return active


def event_prompt_rank(event: Dict[str, str], step: int) -> tuple[int, float, str]:
    try:
        start_step = int(event.get("開始ステップ", "0"))
    except ValueError:
        start_step = 0
    try:
        intensity = float(event.get("強度_0to1", "0"))
    except ValueError:
        intensity = 0.0
    freshness = 1 if start_step and step - start_step <= 2 else 0
    return freshness, intensity, event.get("イベントID", "")


def active_events_for_prompt(
    events: List[Dict[str, str]],
    step: int,
    max_policy_events: int = 12,
) -> List[Dict[str, str]]:
    active = active_events(events, step)
    policy_events = [event for event in active if event.get("区分") == "政策"]
    if len(policy_events) <= max_policy_events:
        return active

    selected_policy_events = sorted(
        policy_events,
        key=lambda event: event_prompt_rank(event, step),
        reverse=True,
    )[:max_policy_events]
    omitted_policy_events = [event for event in policy_events if event not in selected_policy_events]
    omitted_names = "、".join(event.get("イベント名", "") for event in omitted_policy_events[:6] if event.get("イベント名"))
    summary_event = {
        "イベントID": "POLICY_SUMMARY",
        "区分": "政策要約",
        "イベント名": f"その他の継続施策 {len(omitted_policy_events)}件",
        "開始ステップ": str(step),
        "終了ステップ": str(step),
        "強度_0to1": "",
        "発生確率_0to1": "",
        "対象": "複数対象",
        "主な影響方向": "施策量↑ 実装負荷↑ 対象外反発/政策疲労の監査が必要",
        "説明": (
            "比較公平性のため、同時に本人へ見せる政策イベント数を制限している。"
            f"省略された継続施策例: {omitted_names or '複数の既存施策'}。"
            "施策が多いこと自体は、情報過多、申請疲れ、対象外感、実装負荷として知覚され得る。"
        ),
    }
    selected_ids = {event.get("イベントID", "") for event in selected_policy_events}
    selected_in_original_order = [
        event
        for event in active
        if event.get("区分") != "政策" or event.get("イベントID", "") in selected_ids
    ]
    return [*selected_in_original_order, summary_event]


def scheduled_event_usage_rows(
    events: List[Dict[str, str]],
    start_step: int,
    steps: int,
    scenario_mode: str,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for step in range(start_step, start_step + steps):
        for event in active_events(events, step):
            rows.append({
                "step": step,
                "scenario_mode": scenario_mode,
                "event_id": event.get("イベントID", ""),
                "event_type": event.get("区分", ""),
                "event_name": event.get("イベント名", ""),
                "start_step": event.get("開始ステップ", ""),
                "end_step": event.get("終了ステップ", ""),
                "intensity_0to1": event.get("強度_0to1", ""),
                "probability_0to1": event.get("発生確率_0to1", ""),
                "target": event.get("対象", ""),
                "direction": event.get("主な影響方向", ""),
                "description": event.get("説明", ""),
            })
    return rows


def scenario_context_for_mode(scenario_mode: str, step: int) -> Dict[str, Any]:
    context: Dict[str, Any] = {
        "scenario_mode": scenario_mode,
        "note": "これは希望や行動を指定する命令ではなく、この比較シナリオで本人が知覚しやすい社会状況の補足情報です。",
        "available_policy_channels": [],
        "delivery_channels": [],
        "known_constraints": [],
        "what_is_not_available": [],
        "side_effect_watchpoints": [
            "対象外感",
            "政策疲労",
            "財政不安",
            "手続き負担",
            "地域差",
            "所得差",
            "制度を使える人だけが有利になる分断",
        ],
    }
    if scenario_mode == "no_intervention":
        context.update({
            "available_policy_channels": ["既存制度の範囲内"],
            "delivery_channels": ["ニュース", "SNS", "学校/職場の一般情報"],
            "known_constraints": [
                "新しい制度介入は置かれない",
                "生活コスト、AI雇用不安、ケア負担、地政学不安は緩衝されにくい",
            ],
            "what_is_not_available": [
                "構造持続通貨",
                "社会持続活動への報酬",
                "追加の出生・家族形成パッケージ",
                "個別資格通知や即時予約",
            ],
        })
    elif scenario_mode == "birth_grant_only":
        context.update({
            "available_policy_channels": [
                "出産・初期育児費用の緩衝",
                "産後休息",
                "代替ケア",
                "復帰キャリア支援",
                "非強制監査",
            ],
            "delivery_channels": ["自治体/職場/医療・保育窓口", "一般広報", "対象者向け通知"],
            "known_constraints": [
                "構造持続通貨や社会維持活動の報酬化はない",
                "仕事・住居・学び直し・地域役割の再設計は弱い",
                "非対象者は不公平感や『産ませたいだけ』という強制感を持ち得る",
            ],
            "what_is_not_available": [
                "nat報酬",
                "地域更新やケアの役割報酬",
                "若者全体の役割再設計",
                "構造持続の長期財源説明",
            ],
        })
    elif scenario_mode == "structure_intervention":
        context.update({
            "available_policy_channels": [
                "住居安定",
                "学び直し・移行雇用",
                "ケア支援",
                "地域更新",
                "社会持続活動へのnat報酬",
                "財政・副作用監査",
            ],
            "delivery_channels": ["学校", "職場", "自治体", "地域プロジェクト", "制度窓口"],
            "known_constraints": [
                "直接の出産一時金や家族形成パッケージは置かれない",
                "制度名だけでは希望化せず、本人が使える経路や実績が必要",
                "制度利用が増えるほど情報過多や窓口負荷が出得る",
            ],
            "what_is_not_available": [
                "出産・初期育児の大型一時金",
                "家族形成の個別面談・即時予約",
                "出生支援を中心にした直接介入",
            ],
        })
    elif scenario_mode == "structure_birth_grant_package":
        context.update({
            "available_policy_channels": [
                "構造持続通貨",
                "住居・学び直し・ケア・地域更新",
                "出産・初期育児費用の緩衝",
                "産後休息",
                "代替ケア",
                "復帰キャリア支援",
                "財政・非強制監査",
            ],
            "delivery_channels": ["学校", "職場", "自治体", "医療・保育窓口", "地域プロジェクト"],
            "known_constraints": [
                "支援が存在しても、本人に届く/予約できる/使い切れるとは限らない",
                "対象外反発、財政不安、申請疲れ、企業実装負荷は観測対象に残る",
                "子どもを迎える/迎えない/待つ自由を残す必要がある",
            ],
            "what_is_not_available": [
                "希望を直接増やす命令",
                "全員に同じ反応を求める設計",
            ],
        })
    elif scenario_mode == "structure_hope_family_package":
        context.update({
            "available_policy_channels": [
                "構造持続通貨",
                "個別資格通知",
                "即時予約",
                "nat初回着金",
                "若者メンター",
                "地域成功ケース共有",
                "家族形成面談",
                "異議申立・副作用監査",
            ],
            "delivery_channels": ["スマホ通知", "学校", "職場", "自治体窓口", "地域の伴走者"],
            "known_constraints": [
                "本人に届く情報が増えるほど、情報過多・申請疲れ・期待外れも起こり得る",
                "希望が増えても、非対象者や制度不信層の反発が同時に出る可能性がある",
                "制度が止まる不安、財政不安、地域差は残る",
            ],
            "what_is_not_available": [
                "希望感情の直接命令",
                "出生や家族形成の強制",
                "副作用の無視",
            ],
        })
    elif scenario_mode in {"policy_search_no_sustain", "policy_search_with_sustain"}:
        has_sustain = scenario_mode == "policy_search_with_sustain"
        context.update({
            "available_policy_channels": [
                "LLM政策プランナーが予算・実装制約内で提案した施策",
                *(
                    ["構造持続通貨", "社会維持活動への報酬化"]
                    if has_sustain
                    else ["既存の財政・補助金・規制・説明施策"]
                ),
            ],
            "delivery_channels": ["政策発表", "自治体/企業の運用", "対象者通知", "相談窓口"],
            "known_constraints": [
                "施策を増やすほど政策疲労、対象外反発、実装負荷が増え得る",
                "悪化集団を見て、修正、一時停止、説明強化、補完策を選ぶ必要がある",
            ],
            "what_is_not_available": [] if has_sustain else ["構造持続通貨", "nat報酬", "社会維持活動を制度上の価値として扱う探索空間"],
        })
    else:
        context.update({
            "available_policy_channels": ["シナリオ定義に含まれる政策イベント"],
            "delivery_channels": ["ニュース", "SNS", "学校/職場", "自治体/企業窓口"],
            "known_constraints": ["比較シナリオの範囲外の制度は勝手に補わない"],
            "what_is_not_available": [],
        })

    if scenario_mode != "structure_hope_family_package":
        return context

    if step >= 18:
        context["direct_notice_condition"] = (
            "個別資格通知、即時予約、初職・復帰の先行契約枠は、対象者本人のスマホ、学校、職場、自治体窓口に届くため、"
            "単なるニュースより本人が知覚しやすい。本人は使う/使わない/疑う/相談する/安心するなど自然に反応する。"
        )
    if step >= 20:
        context["experienced_effect_condition"] = (
            "SNS希望反転、財政持続監査の初回クリア、nat報酬の初回着金は、制度が実際に動いたという社会的事実として観測される。"
            "ただし全員が信じる必要はなく、所得、ケア責任、制度信頼、過去記憶に応じて反応は分岐する。"
        )
    if step >= 22:
        context["family_formation_condition"] = (
            "家族形成シミュレーション結果通知は、子どもを迎えたい人に対して、自分の場合の可能条件と不足条件を可視化する。"
            "出生を促す命令ではなく、望む/望まない/まだ無理/条件付きで考えるなどの判断材料として扱う。"
        )
    return context


def build_time_schedule_by_step(rows: List[Dict[str, str]]) -> Dict[int, Dict[str, str]]:
    schedule: Dict[int, Dict[str, str]] = {}
    for row in rows:
        try:
            step = int(float(row.get("step", "")))
        except ValueError:
            continue
        schedule[step] = row
    return schedule


def relative_year_for_step(step: int, schedule_by_step: Dict[int, Dict[str, str]]) -> float:
    row = schedule_by_step.get(step, {})
    try:
        return float(row.get("相対年", ""))
    except ValueError:
        pass
    if step <= 0:
        return 0.0
    if step <= 60:
        return step / 12
    if step <= 65:
        return float(step - 55)
    return float(10 + (step - 65) * 5)


def to_int(value: str, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def age_band_for_step(
    lower_age: str,
    upper_age: str,
    step: int,
    schedule_by_step: Dict[int, Dict[str, str]],
) -> str:
    lower = to_int(lower_age)
    upper = to_int(upper_age)
    relative_year = int(relative_year_for_step(step, schedule_by_step))
    return f"{lower + relative_year}-{upper + relative_year}"


def midpoint_age(lower_age: str, upper_age: str) -> str:
    lower = to_float(lower_age)
    upper = to_float(upper_age, lower)
    return str(int((lower + upper) / 2 + 0.5))


def current_age_for_step(base_age: str, step: int, schedule_by_step: Dict[int, Dict[str, str]]) -> str:
    try:
        age = float(base_age)
    except ValueError:
        return ""
    return str(int(age + relative_year_for_step(step, schedule_by_step)))


def representative_age_from_text(value: str) -> str:
    numbers = [float(item) for item in re.findall(r"\d+(?:\.\d+)?", value or "")]
    if not numbers:
        return ""
    return str(int(sum(numbers) / len(numbers) + 0.5))


def current_age_for_agent(
    agent: Dict[str, str],
    step: int,
    schedule_by_step: Dict[int, Dict[str, str]],
) -> str:
    inflow_age = agent.get("流入時代表年齢", "")
    inflow_year = agent.get("流入時相対年", "")
    if inflow_age and inflow_year:
        age = to_float(inflow_age, -1.0)
        year = to_float(inflow_year, 0.0)
        if age >= 0:
            return str(int(age + relative_year_for_step(step, schedule_by_step) - year))
    return current_age_for_step(agent.get("年齢", ""), step, schedule_by_step)


def compact_child_cohorts(
    child_rows: List[Dict[str, str]] | None,
    inflow_rows: List[Dict[str, str]] | None,
    start_step: int,
    steps: int,
    schedule_by_step: Dict[int, Dict[str, str]],
) -> Dict[str, Any]:
    if not child_rows:
        return {}

    step_range = range(start_step, start_step + steps)
    cohorts = []
    for row in child_rows:
        cohorts.append({
            "cohort_id": row.get("コホートID", ""),
            "label": row.get("表示名", ""),
            "initial_age_band": f'{row.get("初期年齢下限", "")}-{row.get("初期年齢上限", "")}',
            "representative_initial_age": row.get("代表初期年齢", ""),
            "represented_weight_percent": row.get("代表重み_パーセント", ""),
            "context": row.get("主な生活文脈", ""),
            "parent_environment": row.get("親世代環境", ""),
            "memory_reception": row.get("制度記憶の受け取り方", ""),
            "hope_inheritance": row.get("初期希望継承係数", ""),
            "distrust_inheritance": row.get("初期不信継承係数", ""),
            "solidarity_inheritance": row.get("初期連帯継承係数", ""),
            "future_age_by_step": {
                str(step): age_band_for_step(
                    row.get("初期年齢下限", ""),
                    row.get("初期年齢上限", ""),
                    step,
                    schedule_by_step,
                )
                for step in step_range
            },
            "llm_policy": row.get("個人LLM化方針", ""),
            "future_inflow_policy": row.get("将来流入方針", ""),
        })

    inflows = []
    for row in inflow_rows or []:
        inflows.append({
            "template_id": row.get("テンプレートID", ""),
            "source_cohort_id": row.get("流入元コホートID", ""),
            "trigger_step": row.get("発火ステップ", ""),
            "relative_year": row.get("相対年", ""),
            "inflow_age_band": row.get("流入時年齢帯", ""),
            "representative_inflow_age": row.get("流入時代表年齢", ""),
            "inflow_relative_year": row.get("流入時相対年", ""),
            "generation_lineage": row.get("世代系統", ""),
            "target_layer": row.get("流入先レイヤー", ""),
            "display_policy": row.get("表示名方針", ""),
            "emotion_initialization": row.get("初期感情初期化", ""),
            "weight_policy": row.get("代表重み方針", ""),
            "llm_input_policy": row.get("LLM入力方針", ""),
            "ui_policy": row.get("UI方針", ""),
        })

    return {
        "policy": "0-14歳は名前付き個人ではなく次世代コホートとして扱い、15歳以上に到達した時点で若者/家族形成層へ接続する。",
        "cohorts": cohorts,
        "inflow_templates": inflows,
    }


def child_cohorts_by_id(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    return {row.get("コホートID", ""): row for row in rows if row.get("コホートID")}


def evaluation_from_scores(pathway: float, support: float, trust: float) -> tuple[str, str]:
    if pathway >= 60 and support >= 56 and trust >= 50:
        return "良好", "希望"
    if pathway <= 38 and support <= 38:
        return "危険", "諦念"
    if trust <= 38 or pathway <= 48 or support <= 45:
        return "注意", "不安"
    return "中立", "平静"


def build_generation_agents(
    child_rows: List[Dict[str, str]],
    inflow_rows: List[Dict[str, str]],
    start_step: int,
    steps: int,
) -> List[Dict[str, str]]:
    if not child_rows or not inflow_rows:
        return []
    cohorts = child_cohorts_by_id(child_rows)
    agents: List[Dict[str, str]] = []
    end_step = start_step + steps - 1
    for template in inflow_rows:
        trigger_step = to_int(template.get("発火ステップ", ""), 9999)
        if end_step < trigger_step:
            continue
        cohort = cohorts.get(template.get("流入元コホートID", ""))
        if not cohort:
            continue

        hope_inheritance = to_float(cohort.get("初期希望継承係数"), 0.55)
        distrust_inheritance = to_float(cohort.get("初期不信継承係数"), 0.40)
        solidarity_inheritance = to_float(cohort.get("初期連帯継承係数"), 0.50)
        pathway = round(clamp(48 + hope_inheritance * 24 - distrust_inheritance * 13))
        support = round(clamp(46 + solidarity_inheritance * 22 - distrust_inheritance * 10))
        trust = round(clamp(44 + hope_inheritance * 18 - distrust_inheritance * 16))
        hope = round(clamp(46 + hope_inheritance * 26 - distrust_inheritance * 12))
        child_intent = round(clamp(24 + hope_inheritance * 18 + solidarity_inheritance * 10 - distrust_inheritance * 10))
        evaluation, emotion = evaluation_from_scores(pathway, support, trust)
        inflow_age = (
            template.get("流入時代表年齢", "")
            or representative_age_from_text(template.get("流入時年齢帯", ""))
            or cohort.get("代表初期年齢")
            or midpoint_age(cohort.get("初期年齢下限", "0"), cohort.get("初期年齢上限", "0"))
        )
        inflow_year = template.get("流入時相対年", "") or template.get("相対年", "")

        agents.append({
            "代表初期年齢": cohort.get("代表初期年齢", ""),
            "エージェントID": template.get("生成ID接頭辞", ""),
            "氏名": template.get("表示名方針") or cohort.get("表示名", ""),
            "分類コード": "次世代コホート",
            "ペルソナ名": template.get("表示名方針") or cohort.get("表示名", ""),
            "年齢": inflow_age,
            "性別": "世代代表",
            "地域区分": "全国",
            "世帯所得階層": "混合",
            "在学就業区分": template.get("流入先レイヤー", "若者前期"),
            "雇用安定度": "中",
            "住居形態": "家族または同居",
            "奨学金等負債_百万円": "0.0",
            "ケア責任": "なし",
            "SNS影響感受性": str(round(clamp(54 + distrust_inheritance * 28))),
            "リスク回避度": str(round(clamp(50 + distrust_inheritance * 26))),
            "時間割引率": str(round(clamp(50 + distrust_inheritance * 22))),
            "自己効力感": str(pathway),
            "制度信頼": str(trust),
            "希望指数": str(hope),
            "子ども意向スコア": str(child_intent),
            "初期評価分類": evaluation,
            "主感情": emotion,
            "未来経路開放度": str(pathway),
            "構造支援度": str(support),
            "感情強度": str(round(clamp(42 + distrust_inheritance * 32))),
            "人口重み_パーセント": cohort.get("代表重み_パーセント", "1.0"),
            "発信影響重み": "0.8",
            "出典種別": "コホート設計+仮定",
            "根拠_歴史と国家特性": (
                f"{cohort.get('表示名', '')}を、{template.get('流入時年齢帯', '')}の"
                "世代代表として流入させる。"
            ),
            "experience_employment_shock": "0",
            "experience_policy_success": "0",
            "experience_policy_failure": "0",
            "experience_care_burden": "0",
            "experience_housing_instability": "0",
            "experience_confidence_weight": "0.85",
            "過去経験メモ": template.get("初期感情初期化", ""),
            "世代代表フラグ": "1",
            "流入元コホートID": cohort.get("コホートID", ""),
            "流入テンプレートID": template.get("テンプレートID", ""),
            "流入発火ステップ": str(trigger_step),
            "流入時代表年齢": inflow_age,
            "流入時相対年": inflow_year,
            "世代系統": template.get("世代系統", ""),
        })
    return [agent for agent in agents if agent.get("エージェントID")]


def agent_layer(agent_id: str) -> str:
    if agent_id.startswith("A"):
        return "若者"
    if agent_id.startswith("W"):
        return "現役世代"
    if agent_id.startswith("YG_"):
        return "次世代コホート"
    return "世代代表"


def agent_layer_for_age(agent_id: str, age_value: str) -> str:
    age = to_float(age_value, -1.0)
    if 0 <= age < 15:
        return "次世代コホート"
    if 15 <= age <= 22:
        return "若者"
    if 23 <= age <= 40:
        return "家族形成"
    if age >= 41:
        return "補助観測"
    if agent_id.startswith("YG_"):
        return "次世代コホート"
    return agent_layer(agent_id)


def compact_time_context(step: int, schedule_by_step: Dict[int, Dict[str, str]]) -> Dict[str, Any]:
    row = schedule_by_step.get(step, {})
    return {
        "step": step,
        "label": row.get("表示期間", ""),
        "relative_year": row.get("相対年", relative_year_for_step(step, schedule_by_step)),
        "unit": row.get("単位", ""),
        "phase": row.get("本番フェーズ", ""),
        "description": row.get("説明", ""),
    }


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


def build_prompt(
    agents: List[Dict[str, str]],
    events: List[Dict[str, str]],
    start_step: int,
    steps: int,
    japan_state_rows: List[Dict[str, str]] | None = None,
    auto_event_rows: List[Dict[str, str]] | None = None,
    previous_states: Dict[str, Dict[str, Any]] | None = None,
    time_schedule_rows: List[Dict[str, str]] | None = None,
    child_cohort_rows: List[Dict[str, str]] | None = None,
    generation_inflow_rows: List[Dict[str, str]] | None = None,
    scenario_mode: str = "",
) -> str:
    schedule_by_step = build_time_schedule_by_step(time_schedule_rows or [])
    child_cohort_context = compact_child_cohorts(
        child_cohort_rows,
        generation_inflow_rows,
        start_step,
        steps,
        schedule_by_step,
    )
    compact_agents = []
    for row in agents:
        current_age = current_age_for_agent(row, start_step, schedule_by_step)
        age_by_step = {
            str(step): current_age_for_agent(row, step, schedule_by_step)
            for step in range(start_step, start_step + steps)
        }
        compact_agents.append({
            "id": row["エージェントID"],
            "name": row["氏名"],
            "layer": agent_layer_for_age(row["エージェントID"], current_age or row["年齢"]),
            "persona": row["ペルソナ名"],
            "age": current_age or row["年齢"],
            "base_age": row["年齢"],
            "current_age": current_age or row["年齢"],
            "age_by_step": age_by_step,
            "gender": row["性別"],
            "region": row["地域区分"],
            "income": row["世帯所得階層"],
            "work_school": row["在学就業区分"],
            "employment_stability": row["雇用安定度"],
            "housing": row["住居形態"],
            "debt_million_yen": row["奨学金等負債_百万円"],
            "care": row["ケア責任"],
            "self_efficacy": row["自己効力感"],
            "institutional_trust": row["制度信頼"],
            "hope": row["希望指数"],
            "child_intent": row["子ども意向スコア"],
            "represented_population_weight_percent": row.get("人口重み_パーセント", ""),
            "layer_internal_weight_percent": row.get("パネル層内代表重み", ""),
            "panel_display_weight": row.get("パネル表示重み", ""),
            "panel_selection_reason": row.get("パネル選抜理由", ""),
            "initial_evaluation": row["初期評価分類"],
            "initial_emotion": row["主感情"],
            "pathway": row["未来経路開放度"],
            "support": row["構造支援度"],
            "intensity": row["感情強度"],
            "generation_representative": row.get("世代代表フラグ", "0"),
            "source_child_cohort": row.get("流入元コホートID", ""),
            "inflow_template": row.get("流入テンプレートID", ""),
            "inflow_age": row.get("流入時代表年齢", ""),
            "inflow_relative_year": row.get("流入時相対年", ""),
            "generation_lineage": row.get("世代系統", ""),
        })

    compact_previous = []
    previous_states = previous_states or {}
    for row in agents:
        previous = previous_states.get(row["エージェントID"])
        if not previous:
            continue
        compact_previous.append({
            "id": row["エージェントID"],
            "previous_step": previous.get("step", ""),
            "evaluation": previous.get("evaluation", ""),
            "emotion": previous.get("emotion", ""),
            "pathway": previous.get("pathway", ""),
            "support": previous.get("support", ""),
            "intensity": previous.get("intensity", ""),
            "action": previous.get("action", ""),
            "action_category": previous.get("action_category", ""),
            "action_detail": previous.get("action_detail", ""),
            "memory_update": previous.get("memory_update", ""),
            "carryover_concern": previous.get("carryover_concern", ""),
            "side_effect": previous.get("side_effect", ""),
            "adjustment_request": previous.get("adjustment_request", ""),
            "fairness_perception": previous.get("fairness_perception", ""),
            "policy_fatigue": previous.get("policy_fatigue", ""),
        })

    japan_state_by_step = {
        int(row["step"]): row
        for row in japan_state_rows or []
        if row.get("step")
    }
    auto_events_by_step: Dict[int, List[Dict[str, str]]] = {}
    for row in auto_event_rows or []:
        if not row.get("step"):
            continue
        auto_events_by_step.setdefault(int(row["step"]), []).append(row)

    compact_events = []
    for step in range(start_step, start_step + steps):
        compact_events.append({
            "step": step,
            "time": compact_time_context(step, schedule_by_step),
            "scheduled_events": [
                {
                    "id": event["イベントID"],
                    "type": event["区分"],
                    "name": event["イベント名"],
                    "intensity": event["強度_0to1"],
                    "target": event["対象"],
                    "direction": event["主な影響方向"],
                    "description": event["説明"],
                }
                for event in active_events_for_prompt(events, step)
            ],
            "world_state": compact_japan_state(japan_state_by_step.get(step, {})),
            "auto_events": [
                {
                    "id": event["イベントID"],
                    "type": event["区分"],
                    "name": event["イベント名"],
                    "intensity": event["強度_0to1"],
                    "target": event["対象"],
                    "direction": event["主な影響方向"],
                    "source": event["発生源"],
                    "countries": event["関連国"],
                    "description": event["若者への入力文"],
                }
                for event in auto_events_by_step.get(step, [])
            ],
        })
    scenario_context = scenario_context_for_mode(scenario_mode, start_step)

    return f"""
あなたは社会シミュレーションの観測器です。
日本語だけで考え、出力はJSONだけにしてください。コードブロックは禁止です。

このプロンプトのレイヤー:
- 出力契約: JSON形式、観測項目、分類語彙、短さは実装上の制約として固定する。
- 世界条件: エージェント属性、世界状態、日本社会状態、制度シナリオ、前ステップ記憶は観測条件として固定する。
- 人間反応: その条件で本人がどう知覚し、どう感じ、どう動くかは固定しない。

この実行で行うこと:
エージェント本人へ命令するのではなく、固定属性・現在状態・世界状態・日本社会状態・情報環境を観測条件として渡します。
その条件に置かれた人物モデルが、次のステップで自然にどう知覚し、どう感じ、どう考え、どう動いたかをrowデータとして記録します。

入力情報の扱い:
- world_state、scheduled_events、auto_events は、本人が置かれている社会状況です。本人への命令ではありません。
- event.direction は「こう変化させろ」という指示ではなく、社会状態の説明ラベルです。
- previous_agent_state は、前ステップから残っている本人の記憶・状態です。これも命令ではありません。
- scenario_context は、この比較シナリオで本人が知覚しやすい追加の社会状況です。これも命令ではありません。
- age/current_age は開始ステップ時点の年齢です。base_age は開始時点の年齢です。複数ステップを観測する場合は age_by_step を優先してください。
- 10年後、20年後の判断では、現在年齢に応じて進学・就職・家族形成・ケア責任・子ども意向の現実性が変わります。
- child_cohort_context は0-14歳の次世代コホート設計です。子ども本人の内心やSNS発信を生成する命令ではありません。15歳以上に到達したステップ以降、若者/家族形成層へ入る初期条件として扱ってください。
- 対象エージェントに `YG_` で始まるIDが含まれる場合、それは個人名を持たない世代代表rowです。子ども本人ではなく、15歳以上に到達した世代代表として、同世代の集合的な知覚・感情・行動を1rowで観測してください。
- その人が情報を見ない、見ても反応しない、別の生活課題を優先する、矛盾した反応をすることも自然なら許容します。
- 同じ情報でも、所得、住居、雇用、ケア責任、制度信頼、SNS感受性、過去の記憶によって反応は分岐します。

分類語彙:
- 良好: 安心・希望・連帯感
- 中立: 平静
- 注意: 不安・怒り
- 危険: 裏切られ感・喪失感・絶望・諦念

	分類の目安:
	- 未来経路と構造支援がどちらも高く、本人が具体的な次の一手を確認できている場合は、社会リスクが残っていても良好（安心・希望・連帯感）になり得ます。
	- 不安が少し残るだけで自動的に注意へ固定しないでください。本人の主感情が「それでも動ける」「自分にも経路がある」「一人ではない」に近い場合は希望・安心・連帯感を選べます。
	- 逆に、経路や支援が高く見えても、本人が対象外感、遅延、不信、ケア拘束を強く感じる場合は注意や危険のままで構いません。
	- 具体的な支援や経路が存在しても、本人が知らない、対象外だと思う、手続きが重い、過去の制度不信が強い、家族ケアや住居制約で動けない、財政不安で持続しないと感じる場合は、評価や行動は大きく改善しなくて構いません。
	- 施策が多い場合は、それ自体が情報過多、申請疲れ、対象外反発、実装負荷、期待外れとして知覚される可能性があります。平均的な良化だけでなく、悪化する層や二極化も観測してください。

行動カテゴリ語彙:
静観/情報収集/相談/生活防衛/回避・縮小/学習・就活/制度利用/参加・連帯/抗議・発信/ケア継続/撤退
これは分類用語彙であり、選ばせたい行動ではありません。自然に近いものを1つ選びます。

観測項目:
- evaluation: 良好/中立/注意/危険
- emotion: 分類語彙に対応する主感情
- pathway: 本人から見た未来経路開放度 0-100
- support: 本人から見た構造支援度 0-100
- intensity: 感情強度 0-100
- action: 短い行動ラベル
- action_category: 行動カテゴリ語彙から1つ
- action_detail: 観測可能な具体行動を1文で書く
- thought: 内心。本音で、まだ言語化しきれていない不安や怒りも含める
- private_talk: 友達や近い人との会話。砕けた口調で、弱音・相談・共感が出る
- social_post: SNS発信。短く、社会向け・見られる前提の言い方にする
- perceived_situation: 本人がこのステップで実際に知覚した状況。届かなかった情報は無理に含めない
	- reasoning_basis: その反応になった根拠。属性、生活制約、記憶、知覚した情報を短く結ぶ
	- memory_update: 次ステップに残る記憶
	- carryover_concern: 次ステップへ持ち越す懸念
	- side_effect: 対象外感/監視疲れ/財政不安/強制感/手続き疲れ/政策疲労/実装不信/なし のどれか
	- adjustment_request: 対象条件の説明/手続き簡素化/地域枠追加/財源説明/一時停止/補完支援/非強制説明/なし のどれか
	- fairness_perception: 本人から見た公平感 0-100
	- policy_fatigue: 本人から見た政策・申請・情報疲れ 0-100

観測原則:
- 望ましい発表ストーリーに合わせる必要はありません。
- 全員が同じ方向に動くとは限りません。
- 大きな事件が起きても、本人に届かなければ反応は小さくてよいです。
- 逆に小さな出来事でも、その人の生活制約に刺されば大きく反応してよいです。
	- 希望・安心・連帯感は、社会リスクがゼロになった時だけの感情ではありません。本人に具体的な経路、即時支援、実績、成功経験、共同体の受け皿が届いた場合は、リスクが残っていても自然な反応として選んでよいです。
	- 逆に、具体的な条件が届いているのに常に不安へ固定する必要もありません。本人の属性と知覚情報に照らして、良好/中立/注意/危険を分岐させます。
	- 支援が届いた層と届かない層、使える層と使えない層が分かれる場合は、平均値だけに寄せず、二極化や対象外反発を自然に出してください。
	- 出産・家族形成支援は、子どもを持つことへの命令ではありません。望まない人、今は選ばない人、対象外の人が強制感や反発を持つことも自然なら出してください。
	- 数値は前ステップから大きく変わってもよいですが、reasoning_basis と矛盾しない範囲にします。
- thought/private_talk/social_post は、それぞれ異なる文脈の発話として観測します。
- 発言はきれいに整理しすぎず、現実の人が言いそうな迷い・矛盾・言い切れなさを残します。
	- thought は90字以内、private_talk は80字以内、social_post は60字以内にします。
	- action_detail、perceived_situation、reasoning_basis、memory_update、carryover_concern、side_effect、adjustment_request は各80字以内にします。
- JSON以外の説明文は一切出力しないでください。

対象エージェント:
{json.dumps(compact_agents, ensure_ascii=False, indent=2)}

子どもコホート設計:
{json.dumps(child_cohort_context, ensure_ascii=False, indent=2)}

前ステップから残っている状態:
{json.dumps(compact_previous, ensure_ascii=False, indent=2)}

シナリオ補足:
{json.dumps(scenario_context, ensure_ascii=False, indent=2)}

ステップ別の観測条件:
{json.dumps(compact_events, ensure_ascii=False, indent=2)}

JSON形式:
{{
  "turns": [
    {{
      "step": {start_step},
      "agents": [
        {{
          "agent_id": "A04",
          "evaluation": "注意",
          "emotion": "不安",
          "pathway": 40,
          "support": 36,
          "intensity": 70,
          "action": "警戒",
          "action_category": "情報収集",
          "action_detail": "進路とバイトへの影響を先生とSNSで調べる",
          "thought": "...",
          "private_talk": "...",
          "social_post": "...",
	          "perceived_situation": "...",
	          "reasoning_basis": "...",
	          "memory_update": "...",
	          "carryover_concern": "...",
	          "side_effect": "対象外感",
	          "adjustment_request": "対象条件の説明",
	          "fairness_perception": 42,
	          "policy_fatigue": 58
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
    except json.JSONDecodeError as original_error:
        decoder = json.JSONDecoder()
        candidates = [text]
        candidates.extend(
            match.group(1).strip()
            for match in re.finditer(r"```(?:json)?\s*(.*?)```", text, flags=re.S | re.I)
        )
        for candidate in candidates:
            for start in [0, *[match.start() for match in re.finditer(r"\{", candidate)]]:
                try:
                    parsed, _ = decoder.raw_decode(candidate[start:].strip())
                except json.JSONDecodeError:
                    continue
                if isinstance(parsed, dict):
                    return parsed
        raise original_error


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
    last_error: Exception | None = None
    for attempt in range(1, 4):
        completed = subprocess.run(
            cmd,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if completed.returncode != 0:
            last_error = RuntimeError(completed.stderr or completed.stdout)
            continue
        try:
            return extract_json_from_claude(completed.stdout)
        except json.JSONDecodeError as exc:
            # Claude CLI occasionally returns valid outer JSON whose textual result
            # contains a small JSON formatting error. Retrying the same isolated
            # agent turn is cheaper and safer than failing the whole closed loop.
            last_error = exc
            if attempt < 3:
                continue
            break
    raise RuntimeError(f"Claude JSON extraction failed after retries: {last_error}")


def combine_payloads_by_step(payloads_by_agent: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    turns_by_step: Dict[int, Dict[str, Dict[str, Any]]] = {}
    for expected_agent_id, payload in payloads_by_agent.items():
        found_expected_agent = False
        for turn in payload.get("turns", []):
            step = int(turn["step"])
            turns_by_step.setdefault(step, {})
            for agent_row in turn.get("agents", []):
                if agent_row.get("agent_id") != expected_agent_id:
                    continue
                found_expected_agent = True
                # Single-agent prompts can occasionally echo the same row twice.
                # Keep the final row deterministically so downstream feedback is
                # counted once per agent per step.
                turns_by_step[step][expected_agent_id] = agent_row
        if not found_expected_agent:
            raise RuntimeError(f"Missing expected agent row in LLM output: {expected_agent_id}")
    return {
        "turns": [
            {
                "step": step,
                "agents": sorted(turns_by_step[step].values(), key=lambda item: item.get("agent_id", "")),
            }
            for step in sorted(turns_by_step)
        ],
        "raw_by_agent": payloads_by_agent,
    }


def flatten_turns(
    payload: Dict[str, Any],
    agents_by_id: Dict[str, Dict[str, str]],
    time_schedule_rows: List[Dict[str, str]] | None = None,
) -> List[Dict[str, Any]]:
    schedule_by_step = build_time_schedule_by_step(time_schedule_rows or [])
    rows: List[Dict[str, Any]] = []
    deduped: Dict[tuple[int, str], Dict[str, Any]] = {}
    order: List[tuple[int, str]] = []
    for turn in payload.get("turns", []):
        step = int(turn["step"])
        for item in turn.get("agents", []):
            agent_id = item.get("agent_id", "")
            if agent_id not in agents_by_id:
                continue
            agent = agents_by_id[agent_id]
            current_age = current_age_for_agent(agent, step, schedule_by_step)
            key = (step, agent_id)
            if key not in deduped:
                order.append(key)
            deduped[key] = {
                "step": step,
                "agent_id": agent_id,
                "name": agent.get("氏名", ""),
                "layer": agent_layer_for_age(agent_id, current_age or agent.get("年齢", "")),
                "base_age": agent.get("年齢", ""),
                "current_age": current_age or agent.get("年齢", ""),
                "evaluation": normalize_evaluation(item.get("evaluation", "")),
                "emotion": normalize_emotion(item.get("evaluation", ""), item.get("emotion", "")),
                "pathway": round(clamp(float(item.get("pathway", 0))), 1),
                "support": round(clamp(float(item.get("support", 0))), 1),
                "intensity": round(clamp(float(item.get("intensity", 0))), 1),
                "action": item.get("action", ""),
                "action_category": normalize_action_category(
                    item.get("action_category", ""),
                    item.get("action", ""),
                ),
                "action_detail": item.get("action_detail", "") or action_detail_fallback(item.get("action", "")),
                "thought": item.get("thought", ""),
                "private_talk": item.get("private_talk", ""),
                "social_post": item.get("social_post", ""),
                "perceived_situation": item.get("perceived_situation", ""),
                "reasoning_basis": item.get("reasoning_basis", ""),
                "memory_update": item.get("memory_update", ""),
                "carryover_concern": item.get("carryover_concern", ""),
                "side_effect": normalize_side_effect(item.get("side_effect", "")),
                "adjustment_request": normalize_adjustment_request(item.get("adjustment_request", "")),
                "fairness_perception": optional_score(item.get("fairness_perception", "")),
                "policy_fatigue": optional_score(item.get("policy_fatigue", "")),
            }
    return [deduped[key] for key in order]


def optional_score(value: Any) -> str:
    if value in {None, ""}:
        return ""
    try:
        return str(round(clamp(float(value)), 1))
    except (TypeError, ValueError):
        return ""


def normalize_evaluation(value: str) -> str:
    if value in {"良好", "中立", "注意", "危険"}:
        return value
    return "中立"


def normalize_emotion(evaluation: str, emotion: str) -> str:
    normalized_evaluation = normalize_evaluation(evaluation)
    allowed = {
        "良好": {"安心", "希望", "連帯感"},
        "中立": {"平静"},
        "注意": {"不安", "怒り"},
        "危険": {"裏切られ感", "喪失感", "絶望", "諦念"},
    }
    if emotion in allowed[normalized_evaluation]:
        return emotion
    if normalized_evaluation == "良好":
        return "希望"
    if normalized_evaluation == "中立":
        return "平静"
    if normalized_evaluation == "注意":
        return "不安" if emotion in {"焦り", "疲労感"} else "怒り"
    if emotion == "怒り":
        return "裏切られ感"
    if emotion in {"焦り", "疲労感"}:
        return "喪失感"
    return "喪失感"


def normalize_action_category(value: str, action: str) -> str:
    if value in ACTION_CATEGORIES:
        return value
    return infer_action_category(action)


def normalize_side_effect(value: str) -> str:
    allowed = {
        "対象外感",
        "監視疲れ",
        "財政不安",
        "強制感",
        "手続き疲れ",
        "政策疲労",
        "実装不信",
        "なし",
    }
    return value if value in allowed else (str(value)[:40] if value else "")


def normalize_adjustment_request(value: str) -> str:
    allowed = {
        "対象条件の説明",
        "手続き簡素化",
        "地域枠追加",
        "財源説明",
        "一時停止",
        "補完支援",
        "非強制説明",
        "なし",
    }
    return value if value in allowed else (str(value)[:40] if value else "")


def infer_action_category(action: str) -> str:
    if any(word in action for word in ("相談", "窓口")):
        return "相談"
    if any(word in action for word in ("確認", "検索", "情報", "観察", "注視")):
        return "情報収集"
    if any(word in action for word in ("節約", "防衛", "耐える", "耐久", "維持")):
        return "生活防衛"
    if any(word in action for word in ("回避", "縮小", "停滞", "麻痺", "消耗", "巣ごもり")):
        return "回避・縮小"
    if any(word in action for word in ("就活", "応募", "学習", "スキル", "内省")):
        return "学習・就活"
    if any(word in action for word in ("申請", "制度", "支援", "問い合わせ")):
        return "制度利用"
    if any(word in action for word in ("参加", "連帯", "関与", "地域")):
        return "参加・連帯"
    if any(word in action for word in ("抗議", "発信", "不満", "批判", "憤慨", "怒り")):
        return "抗議・発信"
    if any(word in action for word in ("ケア", "介護")):
        return "ケア継続"
    if any(word in action for word in ("撤退", "諦", "孤立")):
        return "撤退"
    return "静観"


def action_detail_fallback(action: str) -> str:
    return f"{action or '様子見'}を続けながら次の判断材料を探す"


def latest_agent_states(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
    latest: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        agent_id = row.get("agent_id", "")
        if not agent_id:
            continue
        step = int(float(row.get("step") or 0))
        current_step = int(float(latest.get(agent_id, {}).get("step") or -1))
        if step >= current_step:
            latest[agent_id] = dict(row)
    return latest


def run_stateful_generation(
    agents: List[Dict[str, str]],
    agents_by_id: Dict[str, Dict[str, str]],
    event_rows: List[Dict[str, str]],
    start_step: int,
    steps: int,
    japan_state_rows: List[Dict[str, str]],
    auto_event_rows: List[Dict[str, str]],
    time_schedule_rows: List[Dict[str, str]],
    child_cohort_rows: List[Dict[str, str]],
    generation_inflow_rows: List[Dict[str, str]],
    initial_previous_states: Dict[str, Dict[str, Any]],
    model: str,
    budget: float,
    timeout: int,
    parallel_by_agent: bool,
    workers: int,
    scenario_mode: str,
) -> Dict[str, Any]:
    previous_states: Dict[str, Dict[str, Any]] = dict(initial_previous_states)
    all_turns: List[Dict[str, Any]] = []
    raw_by_step: List[Dict[str, Any]] = []

    for step in range(start_step, start_step + steps):
        active_agents = [
            agent for agent in agents
            if to_int(agent.get("流入発火ステップ", str(start_step)), start_step) <= step
        ]
        if parallel_by_agent:
            payloads_by_agent: Dict[str, Dict[str, Any]] = {}
            with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
                futures = {
                    executor.submit(
                        run_claude,
                        build_prompt(
                            [agent],
                            event_rows,
                            step,
                            1,
                            japan_state_rows,
                            auto_event_rows,
                            previous_states,
                            time_schedule_rows,
                            child_cohort_rows,
                            generation_inflow_rows,
                            scenario_mode,
                        ),
                        model,
                        budget,
                        timeout,
                    ): agent["エージェントID"]
                    for agent in active_agents
                }
                for future in as_completed(futures):
                    agent_id = futures[future]
                    payloads_by_agent[agent_id] = future.result()
                    print(f"Finished {agent_id} step {step}", flush=True)
            step_payload = combine_payloads_by_step(payloads_by_agent)
        else:
            prompt = build_prompt(
                active_agents,
                event_rows,
                step,
                1,
                japan_state_rows,
                auto_event_rows,
                previous_states,
                time_schedule_rows,
                child_cohort_rows,
                generation_inflow_rows,
                scenario_mode,
            )
            step_payload = run_claude(prompt, model, budget, timeout)
            print(f"Finished step {step}", flush=True)

        flat_rows = flatten_turns(step_payload, agents_by_id, time_schedule_rows)
        for row in flat_rows:
            previous_states[row["agent_id"]] = row

        all_turns.extend(step_payload.get("turns", []))
        raw_by_step.append({"step": step, "payload": step_payload})

    return {
        "turns": sorted(all_turns, key=lambda turn: int(turn["step"])),
        "raw_by_step": raw_by_step,
    }


def read_optional_tsv(path: Path | None) -> List[Dict[str, str]]:
    if not path or not path.exists():
        return []
    return read_tsv(path)


def max_schedule_step(rows: List[Dict[str, str]]) -> int | None:
    steps = []
    for row in rows:
        try:
            steps.append(int(float(row.get("step", ""))))
        except ValueError:
            continue
    return max(steps) if steps else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-step", type=int, default=4)
    parser.add_argument("--steps", type=int, default=3)
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--budget", type=float, default=0.50)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--japan-state-tsv", type=Path, default=DEFAULT_JAPAN_STATE)
    parser.add_argument("--auto-events-tsv", type=Path, default=DEFAULT_AUTO_EVENTS)
    parser.add_argument("--agent-panel-tsv", type=Path, default=DEFAULT_AGENT_PANEL)
    parser.add_argument("--time-schedule-tsv", type=Path, default=DEFAULT_TIME_SCHEDULE)
    parser.add_argument("--child-cohorts-tsv", type=Path, default=DEFAULT_CHILD_COHORTS)
    parser.add_argument(
        "--generation-inflow-templates-tsv",
        type=Path,
        default=DEFAULT_GENERATION_INFLOW_TEMPLATES,
    )
    parser.add_argument("--agent-ids", default=",".join(DEFAULT_AGENT_IDS))
    parser.add_argument("--parallel-by-agent", action="store_true")
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--stateful", action="store_true")
    parser.add_argument("--previous-agent-turns-tsv", type=Path)
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
        help="Filter scheduled events for comparison runs.",
    )
    args = parser.parse_args()

    youth_rows = read_tsv(DOMAIN_PACK_DATA / "youth_agents.tsv")
    working_rows = read_tsv(DOMAIN_PACK_DATA / "working_agents.tsv")
    event_rows = filter_events_for_scenario(
        read_tsv(DOMAIN_PACK_DATA / "events.tsv"),
        args.scenario_mode,
    )
    japan_state_rows = read_optional_tsv(args.japan_state_tsv)
    auto_event_rows = read_optional_tsv(args.auto_events_tsv)
    time_schedule_rows = read_optional_tsv(args.time_schedule_tsv)
    max_step = max_schedule_step(time_schedule_rows)
    if max_step is not None and args.start_step + args.steps - 1 > max_step:
        raise SystemExit(
            f"Requested steps exceed time schedule: "
            f"start_step={args.start_step}, steps={args.steps}, max_step={max_step}"
        )
    child_cohort_rows = read_optional_tsv(args.child_cohorts_tsv)
    generation_inflow_rows = read_optional_tsv(args.generation_inflow_templates_tsv)
    agent_ids = parse_agent_ids(args.agent_ids)
    agents = select_agents(youth_rows, working_rows, agent_ids)
    generation_agents = build_generation_agents(
        child_cohort_rows,
        generation_inflow_rows,
        args.start_step,
        args.steps,
    )
    agents.extend(generation_agents)
    if not args.stateful:
        agents = [
            agent for agent in agents
            if to_int(agent.get("流入発火ステップ", str(args.start_step)), args.start_step) <= args.start_step
        ]
    panel_overrides = read_agent_panel_overrides(args.agent_panel_tsv)
    agents = apply_agent_panel_overrides(agents, panel_overrides)
    agents_by_id = {row["エージェントID"]: row for row in agents}
    previous_agent_rows = read_optional_tsv(args.previous_agent_turns_tsv)
    previous_states = latest_agent_states(previous_agent_rows)

    if args.stateful:
        payload = run_stateful_generation(
            agents,
            agents_by_id,
            event_rows,
            args.start_step,
            args.steps,
            japan_state_rows,
            auto_event_rows,
            time_schedule_rows,
            child_cohort_rows,
            generation_inflow_rows,
            previous_states,
            args.model,
            args.budget,
            args.timeout,
            args.parallel_by_agent,
            args.workers,
            args.scenario_mode,
        )
    elif args.parallel_by_agent:
        payloads_by_agent: Dict[str, Dict[str, Any]] = {}
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
            futures = {
                executor.submit(
                    run_claude,
                    build_prompt(
                        [agent],
                        event_rows,
                        args.start_step,
                        args.steps,
                        japan_state_rows,
                        auto_event_rows,
                        None,
                        time_schedule_rows,
                        child_cohort_rows,
                        generation_inflow_rows,
                        args.scenario_mode,
                    ),
                    args.model,
                    args.budget,
                    args.timeout,
                ): agent["エージェントID"]
                for agent in agents
            }
            for future in as_completed(futures):
                agent_id = futures[future]
                payloads_by_agent[agent_id] = future.result()
                print(f"Finished {agent_id}", flush=True)
        payload = combine_payloads_by_step(payloads_by_agent)
    else:
        prompt = build_prompt(
            agents,
            event_rows,
            args.start_step,
            args.steps,
            japan_state_rows,
            auto_event_rows,
            None,
            time_schedule_rows,
            child_cohort_rows,
            generation_inflow_rows,
            args.scenario_mode,
        )
        payload = run_claude(prompt, args.model, args.budget, args.timeout)
    rows = flatten_turns(payload, agents_by_id, time_schedule_rows)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "raw_claude_response.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_jsonl(args.output_dir / "agent_states.jsonl", rows)
    write_tsv(
        args.output_dir / "turns.tsv",
        rows,
        [
            "step",
            "agent_id",
            "name",
            "layer",
            "base_age",
            "current_age",
            "evaluation",
            "emotion",
            "pathway",
            "support",
            "intensity",
            "action",
            "action_category",
            "action_detail",
            "thought",
            "private_talk",
            "social_post",
            "perceived_situation",
            "reasoning_basis",
            "memory_update",
            "carryover_concern",
            "side_effect",
            "adjustment_request",
            "fairness_perception",
            "policy_fatigue",
        ],
    )
    scheduled_events_used_path = args.output_dir / "scheduled_events_used.tsv"
    write_tsv(
        scheduled_events_used_path,
        scheduled_event_usage_rows(
            event_rows,
            args.start_step,
            args.steps,
            args.scenario_mode,
        ),
        [
            "step",
            "scenario_mode",
            "event_id",
            "event_type",
            "event_name",
            "start_step",
            "end_step",
            "intensity_0to1",
            "probability_0to1",
            "target",
            "direction",
            "description",
        ],
    )
    manifest = {
        "kind": "civilization_os_llm_smoke",
        "model": args.model,
        "start_step": args.start_step,
        "steps": args.steps,
        "stateful": args.stateful,
        "scenario_mode": args.scenario_mode,
        "parallel_by_agent": args.parallel_by_agent,
        "japan_state_tsv": str(args.japan_state_tsv) if japan_state_rows else "",
        "auto_events_tsv": str(args.auto_events_tsv) if auto_event_rows else "",
        "agent_panel_tsv": str(args.agent_panel_tsv) if panel_overrides else "",
        "time_schedule_tsv": str(args.time_schedule_tsv) if time_schedule_rows else "",
        "child_cohorts_tsv": str(args.child_cohorts_tsv) if child_cohort_rows else "",
        "generation_inflow_templates_tsv": (
            str(args.generation_inflow_templates_tsv) if generation_inflow_rows else ""
        ),
        "previous_agent_turns_tsv": str(args.previous_agent_turns_tsv or ""),
        "agents": list(agents_by_id),
        "generation_agents": [row["エージェントID"] for row in generation_agents],
        "outputs": [
            "turns.tsv",
            "scheduled_events_used.tsv",
            "agent_states.jsonl",
            "raw_claude_response.json",
        ],
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Wrote {len(rows)} rows to {args.output_dir}")


if __name__ == "__main__":
    main()
