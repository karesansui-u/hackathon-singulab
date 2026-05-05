#!/usr/bin/env python3
"""Generate policy-search interventions from feedback and scenario constraints."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "outputs" / "runs" / "policy_planner_smoke"
DEFAULT_JAPAN_STATE = ROOT / "outputs" / "runs" / "no_intervention_71steps_panel48" / "japan_state.tsv"
DEFAULT_AGENT_FEEDBACK = ROOT / "outputs" / "runs" / "no_intervention_71steps_panel48" / "agent_feedback.tsv"
DEFAULT_AUTO_EVENTS = ROOT / "outputs" / "runs" / "no_intervention_71steps_panel48" / "auto_events_with_feedback.tsv"

AUTO_EVENT_FIELDNAMES = [
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

POLICY_TURN_FIELDNAMES = [
    "step",
    "planner_id",
    "scenario_mode",
    "model",
    "diagnosis",
    "policy_count",
    "total_budget_cost_0to1",
    "dominant_issue",
    "adjustment_strategy",
]

POLICY_EVENT_FIELDNAMES = [
    *AUTO_EVENT_FIELDNAMES,
    "planner_action",
    "delivery_channel",
    "budget_cost_0to1",
    "implementation_lag_steps",
    "duration_steps",
    "expected_effect",
    "side_effect_watchpoints",
    "adjustment_reason",
]

PLANNER_ID = "POLICY_PLANNER"
SUSTAIN_TERMS = ("構造持続", "持続通貨", "nat", "Nat", "NAT", "社会持続活動")


def read_optional_tsv(path: Path) -> List[Dict[str, str]]:
    if not path or not path.exists() or not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: Iterable[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def to_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def latest_row_at_or_before(rows: List[Dict[str, str]], step: int) -> Dict[str, str]:
    candidates = [
        row for row in rows
        if int(to_float(row.get("step"), 0)) <= step
    ]
    if not candidates:
        return {}
    return max(candidates, key=lambda row: int(to_float(row.get("step"), 0)))


def rows_near_step(rows: List[Dict[str, str]], step: int, window: int = 4) -> List[Dict[str, str]]:
    return [
        row for row in rows
        if step - window <= int(to_float(row.get("step"), 0)) <= step
    ]


def scenario_policy_context(scenario_mode: str) -> Dict[str, Any]:
    if scenario_mode == "policy_search_with_sustain":
        return {
            "search_space": "構造持続あり",
            "allowed": [
                "構造持続通貨/nat報酬",
                "社会維持活動の報酬化",
                "住居・ケア・学び直し・地域更新の束ね直し",
                "副作用監査、異議申立、非強制説明",
                "既存制度の簡素化・対象条件修正",
            ],
            "not_allowed": [
                "出生や家族形成の強制",
                "短期人気取りだけの給付",
                "副作用や財源説明を省いた拡大",
            ],
            "core_hypothesis": "探索空間に構造持続の概念があると、政策は給付追加だけでなく、役割・報酬・ケア・地域維持の再設計へ向かえる。",
        }
    if scenario_mode == "policy_search_no_sustain":
        return {
            "search_space": "構造持続なし",
            "allowed": [
                "既存財政の範囲での補助金・税控除",
                "規制緩和",
                "相談窓口",
                "説明強化",
                "企業・自治体への通常補助",
                "手続き簡素化",
            ],
            "not_allowed": [
                "構造持続通貨",
                "nat報酬",
                "社会維持活動を新しい通貨・価値発行として扱う施策",
                "構造持続という概念名の利用",
                "出生や家族形成の強制",
            ],
            "core_hypothesis": "構造持続なしでは、LLMが多くの現実的施策を打っても、補助金・説明・窓口追加に寄り、政策疲労や財政不安が増えやすいかを見る。",
        }
    return {
        "search_space": scenario_mode or "generic",
        "allowed": ["既存シナリオの範囲での調整"],
        "not_allowed": ["比較条件を壊す新概念の追加"],
        "core_hypothesis": "悪化指標を見て施策を調整できるかを見る。",
    }


def compact_feedback(row: Dict[str, str]) -> Dict[str, Any]:
    fields = [
        "step",
        "feedback_summary",
        "良好_share",
        "中立_share",
        "注意_share",
        "危険_share",
        "average_pathway",
        "average_support",
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
    ]
    return {field: row.get(field, "") for field in fields if row.get(field, "") != ""}


def compact_japan_state(row: Dict[str, str]) -> Dict[str, Any]:
    fields = [
        "step",
        "dominant_world_pressure",
        "geopolitical_risk",
        "energy_price_pressure",
        "labor_market_uncertainty",
        "compute_supply_constraint",
        "fiscal_pressure",
        "supply_chain_fragility",
        "sns_anxiety_amplification",
        "japan_policy_buffer",
        "world_context_for_agents",
    ]
    return {field: row.get(field, "") for field in fields if row.get(field, "") != ""}


def compact_recent_policies(rows: List[Dict[str, str]], step: int) -> List[Dict[str, Any]]:
    compact = []
    for row in rows_near_step(rows, step, 6)[-12:]:
        compact.append({
            "step": row.get("step", ""),
            "id": row.get("イベントID", ""),
            "name": row.get("イベント名", ""),
            "target": row.get("対象", ""),
            "direction": row.get("主な影響方向", ""),
            "action": row.get("planner_action", ""),
            "budget": row.get("budget_cost_0to1", ""),
            "watch": row.get("side_effect_watchpoints", ""),
        })
    return compact


def build_prompt(
    step: int,
    scenario_mode: str,
    japan_state: Dict[str, str],
    feedback: Dict[str, str],
    recent_policy_events: List[Dict[str, str]],
    max_policies: int,
) -> str:
    context = scenario_policy_context(scenario_mode)
    return f"""
あなたは制度設計シミュレーション内の政策探索プランナーです。
日本語だけで考え、出力はJSONだけにしてください。コードブロックは禁止です。

目的:
- 平均値を良く見せるのではなく、悪化している層、副作用、二極化、政策疲労を見て、次の政策アクションを提案します。
- 新規施策だけでなく、既存施策の修正、順序変更、説明強化、一時停止、補完策も選べます。
- 1ステップで採択できる施策は最大{max_policies}件です。総予算コストは1.0以内にしてください。

比較条件:
{json.dumps(context, ensure_ascii=False, indent=2)}

現在ステップ: {step}

日本社会状態:
{json.dumps(compact_japan_state(japan_state), ensure_ascii=False, indent=2)}

直近の個人/社会フィードバック:
{json.dumps(compact_feedback(feedback), ensure_ascii=False, indent=2)}

直近の政策探索イベント:
{json.dumps(compact_recent_policies(recent_policy_events, step), ensure_ascii=False, indent=2)}

政策アクション語彙:
maintain / amend / sequence / explain / localize / simplify / pause / rollback / compensate / add

診断観点:
- 危険/注意が高い層はどこか
- 子ども希望や家族形成の前に詰まっている条件は何か
- 対象外反発、強制感、財政不安、手続き疲れ、政策疲労は出ているか
- 施策を増やすべきか、減らすべきか、説明や順序を変えるべきか
- 構造持続なし/ありの比較条件を破っていないか

JSON形式:
{{
  "step": {step},
  "diagnosis": "80字以内の診断",
  "dominant_issue": "二極化/対象外反発/政策疲労/財政不安/雇用不安/ケア負担/住居不安/希望不足",
  "adjustment_strategy": "短い戦略名",
  "policies": [
    {{
      "action": "add",
      "policy_name": "短い施策名",
      "target": "対象層",
      "delivery_channel": "学校/職場/自治体/スマホ通知/相談窓口/企業/地域",
      "budget_cost_0to1": 0.25,
      "implementation_lag_steps": 1,
      "duration_steps": 8,
      "event_intensity_0to1": 0.55,
      "expected_effect": "未来経路↑ 制度信頼↑ など",
      "side_effect_watchpoints": ["対象外感", "政策疲労"],
      "adjustment_reason": "なぜ今この調整か",
      "youth_input": "本人が知覚する社会状況を1文で"
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


def is_codex_model(model: str) -> bool:
    return model == "codex" or model.startswith("codex:") or model.startswith("gpt-")


def codex_model_name(model: str) -> str:
    if model == "codex":
        return "gpt-5.2"
    if model.startswith("codex:"):
        return model.split(":", 1)[1]
    return model


def run_codex(prompt: str, model: str, timeout: int) -> Dict[str, Any]:
    output_path = Path(tempfile.mkstemp(prefix="policy_planner_", suffix=".txt")[1])
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
    outer = json.loads(completed.stdout)
    result = outer.get("result", completed.stdout)
    return result if isinstance(result, dict) else extract_json_from_text(str(result))


def strongest_issue(feedback: Dict[str, str], japan_state: Dict[str, str]) -> str:
    candidates = [
        ("政策疲労", to_float(feedback.get("policy_fatigue_pressure"), 0.0)),
        ("対象外反発", to_float(feedback.get("fairness_gap_pressure"), 0.0)),
        ("撤退圧", to_float(feedback.get("withdrawal_pressure"), 0.0)),
        ("制度要求", to_float(feedback.get("institution_demand_pressure"), 0.0)),
        ("生活防衛", to_float(feedback.get("livelihood_defense_pressure"), 0.0)),
        ("情報過敏", to_float(feedback.get("information_overload_pressure"), 0.0)),
        ("ケア負担", to_float(feedback.get("care_pressure"), 0.0)),
        ("財政不安", to_float(japan_state.get("fiscal_pressure"), 0.0) / 2),
        ("雇用不安", to_float(japan_state.get("labor_market_uncertainty"), 0.0) / 2),
    ]
    return max(candidates, key=lambda item: item[1])[0]


def deterministic_payload(
    step: int,
    scenario_mode: str,
    japan_state: Dict[str, str],
    feedback: Dict[str, str],
) -> Dict[str, Any]:
    issue = strongest_issue(feedback, japan_state)
    with_sustain = scenario_mode == "policy_search_with_sustain"
    if issue in {"政策疲労", "対象外反発", "制度要求"}:
        first = {
            "action": "simplify" if issue == "政策疲労" else "explain",
            "policy_name": "申請一本化と対象外説明" if not with_sustain else "持続通貨申請一本化と異議申立",
            "target": "低中所得層・ケア責任層・対象外不安層",
            "delivery_channel": "自治体/スマホ通知/相談窓口",
            "budget_cost_0to1": 0.18 if not with_sustain else 0.22,
            "implementation_lag_steps": 1,
            "duration_steps": 8,
            "event_intensity_0to1": 0.52,
            "expected_effect": "手続き疲れ↓ 対象外反発↓ 制度信頼↑",
            "side_effect_watchpoints": ["政策疲労", "対象外感", "財政不安"],
            "adjustment_reason": f"{issue}が強く、施策追加より説明と簡素化が先に必要。",
            "youth_input": "支援窓口と申請が一本化され、対象外の場合の理由と補完策も通知される。",
        }
    elif issue in {"撤退圧", "雇用不安"}:
        first = {
            "action": "add",
            "policy_name": "移行雇用の短期保証" if not with_sustain else "社会維持活動nat付き移行雇用",
            "target": "若者・非正規・無業就活中",
            "delivery_channel": "学校/職場/自治体",
            "budget_cost_0to1": 0.30 if not with_sustain else 0.36,
            "implementation_lag_steps": 1,
            "duration_steps": 10,
            "event_intensity_0to1": 0.60,
            "expected_effect": "未来経路↑ 雇用不安↓ 自己効力感↑",
            "side_effect_watchpoints": ["低賃金固定", "対象外感", "実装負荷"],
            "adjustment_reason": "撤退圧を減らすには、情報提供ではなく短期の役割経路が必要。",
            "youth_input": "AI移行期の短期雇用枠と学び直し枠が接続され、自分の次の役割を試せる。",
        }
    elif issue == "ケア負担":
        first = {
            "action": "localize",
            "policy_name": "地域代替ケア即時枠" if not with_sustain else "nat報酬付き地域代替ケア",
            "target": "家族ケア責任層・子育て初期",
            "delivery_channel": "自治体/地域/職場",
            "budget_cost_0to1": 0.28 if not with_sustain else 0.34,
            "implementation_lag_steps": 1,
            "duration_steps": 10,
            "event_intensity_0to1": 0.58,
            "expected_effect": "ケア負担↓ 時間余力↑ 家族形成条件↑",
            "side_effect_watchpoints": ["地域格差", "担い手不足", "財政不安"],
            "adjustment_reason": "ケア負担が未来経路と子ども希望を同時に削っている。",
            "youth_input": "家族ケアを一人で抱えないための地域代替枠が予約できるようになる。",
        }
    else:
        first = {
            "action": "sequence",
            "policy_name": "家計防衛から未来投資への順序変更" if not with_sustain else "家計防衛と構造持続報酬の接続",
            "target": "低中所得層・家族形成層",
            "delivery_channel": "自治体/企業/スマホ通知",
            "budget_cost_0to1": 0.26 if not with_sustain else 0.32,
            "implementation_lag_steps": 1,
            "duration_steps": 8,
            "event_intensity_0to1": 0.55,
            "expected_effect": "生活防衛↓ 将来予見性↑ 子ども希望条件↑",
            "side_effect_watchpoints": ["財政不安", "申請疲れ", "対象外感"],
            "adjustment_reason": "生活防衛が強く、家族形成支援の前に家計の床を作る必要がある。",
            "youth_input": "家計の下支えと次の学び・住居・ケア支援が同じ導線で提示される。",
        }

    policies = [first]
    if with_sustain and first["budget_cost_0to1"] <= 0.70:
        policies.append({
            "action": "compensate",
            "policy_name": "非対象者の構造維持参加枠",
            "target": "非婚非出産層・対象外若者",
            "delivery_channel": "地域/学校/職場",
            "budget_cost_0to1": 0.20,
            "implementation_lag_steps": 2,
            "duration_steps": 10,
            "event_intensity_0to1": 0.46,
            "expected_effect": "対象外反発↓ 連帯感↑ 制度信頼↑",
            "side_effect_watchpoints": ["名目参加", "低賃金固定", "監査疲れ"],
            "adjustment_reason": "家族形成支援だけに見えると分断が出るため、社会維持への別経路を残す。",
            "youth_input": "子どもを持つ/持たないに関係なく、地域やケアを支える活動が評価される枠ができる。",
        })

    return {
        "step": step,
        "diagnosis": f"{issue}が強く、施策追加より副作用を見ながら順序と届き方を調整する局面。",
        "dominant_issue": issue,
        "adjustment_strategy": "構造持続探索" if with_sustain else "既存制度内探索",
        "policies": policies[:2],
    }


def contains_sustain_terms(policy: Dict[str, Any]) -> bool:
    text = json.dumps(policy, ensure_ascii=False)
    return any(term in text for term in SUSTAIN_TERMS)


def normalize_policy(policy: Dict[str, Any], scenario_mode: str, index: int) -> Dict[str, Any] | None:
    if scenario_mode == "policy_search_no_sustain" and contains_sustain_terms(policy):
        return None
    normalized = {
        "action": str(policy.get("action") or "add")[:24],
        "policy_name": str(policy.get("policy_name") or f"政策探索施策{index + 1}")[:48],
        "target": str(policy.get("target") or "若者・家族形成層")[:80],
        "delivery_channel": str(policy.get("delivery_channel") or "自治体/職場")[:80],
        "budget_cost_0to1": clamp(to_float(policy.get("budget_cost_0to1"), 0.25)),
        "implementation_lag_steps": max(0, min(6, int(to_float(policy.get("implementation_lag_steps"), 1)))),
        "duration_steps": max(2, min(24, int(to_float(policy.get("duration_steps"), 8)))),
        "event_intensity_0to1": clamp(to_float(policy.get("event_intensity_0to1"), 0.50)),
        "expected_effect": str(policy.get("expected_effect") or "制度信頼↑")[:120],
        "side_effect_watchpoints": policy.get("side_effect_watchpoints") or ["対象外感", "政策疲労"],
        "adjustment_reason": str(policy.get("adjustment_reason") or "悪化指標を見て調整する。")[:120],
        "youth_input": str(policy.get("youth_input") or "新しい政策調整が提示される。")[:160],
    }
    if isinstance(normalized["side_effect_watchpoints"], list):
        normalized["side_effect_watchpoints"] = "、".join(map(str, normalized["side_effect_watchpoints"][:4]))
    else:
        normalized["side_effect_watchpoints"] = str(normalized["side_effect_watchpoints"])[:80]
    return normalized


def normalize_payload(payload: Dict[str, Any], step: int, scenario_mode: str, max_policies: int) -> Dict[str, Any]:
    policies = []
    total_budget = 0.0
    for index, policy in enumerate(payload.get("policies", [])[:max_policies * 2]):
        normalized = normalize_policy(policy, scenario_mode, index)
        if not normalized:
            continue
        if total_budget + normalized["budget_cost_0to1"] > 1.0 and policies:
            continue
        total_budget += normalized["budget_cost_0to1"]
        policies.append(normalized)
        if len(policies) >= max_policies:
            break
    return {
        "step": step,
        "diagnosis": str(payload.get("diagnosis") or "")[:120],
        "dominant_issue": str(payload.get("dominant_issue") or "")[:40],
        "adjustment_strategy": str(payload.get("adjustment_strategy") or "")[:60],
        "policies": policies,
    }


def policy_turn_row(payload: Dict[str, Any], scenario_mode: str, model: str) -> Dict[str, Any]:
    policies = payload.get("policies", [])
    return {
        "step": payload["step"],
        "planner_id": PLANNER_ID,
        "scenario_mode": scenario_mode,
        "model": model,
        "diagnosis": payload.get("diagnosis", ""),
        "policy_count": len(policies),
        "total_budget_cost_0to1": f"{sum(to_float(policy.get('budget_cost_0to1'), 0.0) for policy in policies):.2f}",
        "dominant_issue": payload.get("dominant_issue", ""),
        "adjustment_strategy": payload.get("adjustment_strategy", ""),
    }


def policy_event_rows(payload: Dict[str, Any], scenario_mode: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    step = int(payload["step"])
    mode_label = "構造持続あり" if scenario_mode == "policy_search_with_sustain" else "通常政策のみ"
    for index, policy in enumerate(payload.get("policies", []), start=1):
        lag = int(policy.get("implementation_lag_steps", 1))
        event_step = step + lag
        rows.append({
            "イベントID": f"PL{step:03d}_{index:02d}",
            "step": event_step,
            "区分": "政策探索",
            "イベント名": policy["policy_name"],
            "強度_0to1": f"{policy['event_intensity_0to1']:.2f}",
            "対象": policy["target"],
            "主な影響方向": policy["expected_effect"],
            "発生源": f"LLM政策探索/{mode_label}",
            "関連国": "日本",
            "日本社会状態": payload.get("diagnosis", ""),
            "若者への入力文": policy["youth_input"],
            "planner_action": policy["action"],
            "delivery_channel": policy["delivery_channel"],
            "budget_cost_0to1": f"{policy['budget_cost_0to1']:.2f}",
            "implementation_lag_steps": lag,
            "duration_steps": policy["duration_steps"],
            "expected_effect": policy["expected_effect"],
            "side_effect_watchpoints": policy["side_effect_watchpoints"],
            "adjustment_reason": policy["adjustment_reason"],
        })
    return rows


def combined_auto_events(auto_events: List[Dict[str, str]], policy_events: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    for row in [*auto_events, *policy_events]:
        event_key = row.get("イベントID", "") or f"{row.get('イベント名', '')}|{row.get('発生源', '')}"
        key = (event_key, int(to_float(row.get("step"), 0)))
        if key in seen:
            continue
        seen.add(key)
        rows.append({field: row.get(field, "") for field in AUTO_EVENT_FIELDNAMES})
    rows.sort(key=lambda row: (int(to_float(row.get("step"), 0)), str(row.get("イベントID", ""))))
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run policy-search planner for one simulation step.")
    parser.add_argument("--start-step", type=int, default=1)
    parser.add_argument(
        "--scenario-mode",
        choices=["policy_search_no_sustain", "policy_search_with_sustain"],
        default="policy_search_no_sustain",
    )
    parser.add_argument("--model", default="fixture")
    parser.add_argument("--budget", type=float, default=0.20)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--max-policies", type=int, default=2)
    parser.add_argument("--japan-state-tsv", type=Path, default=DEFAULT_JAPAN_STATE)
    parser.add_argument("--agent-feedback-tsv", type=Path, default=DEFAULT_AGENT_FEEDBACK)
    parser.add_argument("--auto-events-tsv", type=Path, default=DEFAULT_AUTO_EVENTS)
    parser.add_argument("--previous-policy-events-tsv", type=Path, default=Path(""))
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    step = args.start_step
    japan_rows = read_optional_tsv(args.japan_state_tsv)
    feedback_rows = read_optional_tsv(args.agent_feedback_tsv)
    auto_events = read_optional_tsv(args.auto_events_tsv)
    previous_policy_events = read_optional_tsv(args.previous_policy_events_tsv)
    japan_state = latest_row_at_or_before(japan_rows, step)
    feedback = latest_row_at_or_before(feedback_rows, step - 1) or latest_row_at_or_before(feedback_rows, step)
    prompt = build_prompt(
        step,
        args.scenario_mode,
        japan_state,
        feedback,
        previous_policy_events,
        args.max_policies,
    )
    if args.model == "fixture":
        raw_payload = deterministic_payload(step, args.scenario_mode, japan_state, feedback)
    else:
        raw_payload = run_claude(prompt, args.model, args.budget, args.timeout)
    payload = normalize_payload(raw_payload, step, args.scenario_mode, args.max_policies)
    if not payload["policies"]:
        payload = normalize_payload(
            deterministic_payload(step, args.scenario_mode, japan_state, feedback),
            step,
            args.scenario_mode,
            args.max_policies,
        )

    new_policy_events = policy_event_rows(payload, args.scenario_mode)
    all_policy_events = [*previous_policy_events, *new_policy_events]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "policy_planner_prompt.txt").write_text(prompt, encoding="utf-8")
    (args.output_dir / "raw_policy_planner_response.json").write_text(
        json.dumps(raw_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (args.output_dir / "policy_planner_payload.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_tsv(args.output_dir / "policy_planner_turns.tsv", [policy_turn_row(payload, args.scenario_mode, args.model)], POLICY_TURN_FIELDNAMES)
    write_tsv(args.output_dir / "policy_events.tsv", new_policy_events, POLICY_EVENT_FIELDNAMES)
    write_tsv(args.output_dir / "policy_events_cumulative.tsv", all_policy_events, POLICY_EVENT_FIELDNAMES)
    write_tsv(args.output_dir / "auto_events_with_policy.tsv", combined_auto_events(auto_events, all_policy_events), AUTO_EVENT_FIELDNAMES)
    (args.output_dir / "policy_planner_manifest.json").write_text(
        json.dumps(
            {
                "kind": "policy_planner_llm_demo",
                "step": step,
                "scenario_mode": args.scenario_mode,
                "model": args.model,
                "japan_state_tsv": str(args.japan_state_tsv),
                "agent_feedback_tsv": str(args.agent_feedback_tsv),
                "auto_events_tsv": str(args.auto_events_tsv),
                "previous_policy_events_tsv": str(args.previous_policy_events_tsv),
                "outputs": [
                    "policy_planner_turns.tsv",
                    "policy_events.tsv",
                    "policy_events_cumulative.tsv",
                    "auto_events_with_policy.tsv",
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {len(new_policy_events)} policy events for step {step} to {args.output_dir}")


if __name__ == "__main__":
    main()
