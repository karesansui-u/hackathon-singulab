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
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "docs" / "構造持続理論ベースの新しい文明OSシミュレーション"
DEFAULT_OUTPUT = ROOT / "outputs" / "runs" / "civilization_os_llm_smoke"
DEFAULT_JAPAN_STATE = ROOT / "outputs" / "runs" / "country_llm_smoke" / "japan_state.tsv"
DEFAULT_AUTO_EVENTS = ROOT / "outputs" / "runs" / "country_llm_smoke" / "auto_events.tsv"
DEFAULT_AGENT_IDS = ("A04", "A13", "A16", "W12", "W25")
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
) -> str:
    compact_agents = []
    for row in agents:
        compact_agents.append({
            "id": row["エージェントID"],
            "name": row["氏名"],
            "layer": "若者" if row["エージェントID"].startswith("A") else "現役世代",
            "persona": row["ペルソナ名"],
            "age": row["年齢"],
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
            "initial_evaluation": row["初期評価分類"],
            "initial_emotion": row["主感情"],
            "pathway": row["未来経路開放度"],
            "support": row["構造支援度"],
            "intensity": row["感情強度"],
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
                for event in active_events(events, step)
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

    return f"""
あなたは社会シミュレーションの観測器です。
日本語だけで考え、出力はJSONだけにしてください。コードブロックは禁止です。

この実行で行うこと:
エージェント本人へ命令するのではなく、固定属性・現在状態・世界状態・日本社会状態・情報環境を観測条件として渡します。
その条件に置かれた人物モデルが、次のステップで自然にどう知覚し、どう感じ、どう考え、どう動いたかをrowデータとして記録します。

入力情報の扱い:
- world_state、scheduled_events、auto_events は、本人が置かれている社会状況です。本人への命令ではありません。
- event.direction は「こう変化させろ」という指示ではなく、社会状態の説明ラベルです。
- previous_agent_state は、前ステップから残っている本人の記憶・状態です。これも命令ではありません。
- その人が情報を見ない、見ても反応しない、別の生活課題を優先する、矛盾した反応をすることも自然なら許容します。
- 同じ情報でも、所得、住居、雇用、ケア責任、制度信頼、SNS感受性、過去の記憶によって反応は分岐します。

分類語彙:
- 良好: 安心・希望・連帯感
- 中立: 平静
- 注意: 不安・怒り
- 危険: 裏切られ感・喪失感・絶望・諦念

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

観測原則:
- 望ましい発表ストーリーに合わせる必要はありません。
- 全員を同じ方向に動かさないでください。
- 大きな事件が起きても、本人に届かなければ反応は小さくてよいです。
- 逆に小さな出来事でも、その人の生活制約に刺されば大きく反応してよいです。
- 数値は前ステップから大きく変わってもよいですが、reasoning_basis と矛盾しない範囲にします。
- thought/private_talk/social_post は同じ内容の言い換えにしないでください。
- 発言はきれいに整理しすぎず、現実の人が言いそうな迷い・矛盾・言い切れなさを残します。
- thought は90字以内、private_talk は80字以内、social_post は60字以内にします。
- action_detail、perceived_situation、reasoning_basis、memory_update、carryover_concern は各80字以内にします。
- JSON以外の説明文は一切出力しないでください。

対象エージェント:
{json.dumps(compact_agents, ensure_ascii=False, indent=2)}

前ステップから残っている状態:
{json.dumps(compact_previous, ensure_ascii=False, indent=2)}

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
          "carryover_concern": "..."
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


def combine_payloads_by_step(payloads_by_agent: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    turns_by_step: Dict[int, List[Dict[str, Any]]] = {}
    for payload in payloads_by_agent.values():
        for turn in payload.get("turns", []):
            step = int(turn["step"])
            turns_by_step.setdefault(step, [])
            turns_by_step[step].extend(turn.get("agents", []))
    return {
        "turns": [
            {"step": step, "agents": sorted(turns_by_step[step], key=lambda item: item.get("agent_id", ""))}
            for step in sorted(turns_by_step)
        ],
        "raw_by_agent": payloads_by_agent,
    }


def flatten_turns(payload: Dict[str, Any], agents_by_id: Dict[str, Dict[str, str]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for turn in payload.get("turns", []):
        step = int(turn["step"])
        for item in turn.get("agents", []):
            agent = agents_by_id.get(item["agent_id"], {})
            rows.append({
                "step": step,
                "agent_id": item["agent_id"],
                "name": agent.get("氏名", ""),
                "layer": "若者" if item["agent_id"].startswith("A") else "現役世代",
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
            })
    return rows


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
    initial_previous_states: Dict[str, Dict[str, Any]],
    model: str,
    budget: float,
    timeout: int,
    parallel_by_agent: bool,
    workers: int,
) -> Dict[str, Any]:
    previous_states: Dict[str, Dict[str, Any]] = dict(initial_previous_states)
    all_turns: List[Dict[str, Any]] = []
    raw_by_step: List[Dict[str, Any]] = []

    for step in range(start_step, start_step + steps):
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
                        ),
                        model,
                        budget,
                        timeout,
                    ): agent["エージェントID"]
                    for agent in agents
                }
                for future in as_completed(futures):
                    agent_id = futures[future]
                    payloads_by_agent[agent_id] = future.result()
                    print(f"Finished {agent_id} step {step}", flush=True)
            step_payload = combine_payloads_by_step(payloads_by_agent)
        else:
            prompt = build_prompt(
                agents,
                event_rows,
                step,
                1,
                japan_state_rows,
                auto_event_rows,
                previous_states,
            )
            step_payload = run_claude(prompt, model, budget, timeout)
            print(f"Finished step {step}", flush=True)

        flat_rows = flatten_turns(step_payload, agents_by_id)
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
    parser.add_argument("--agent-ids", default=",".join(DEFAULT_AGENT_IDS))
    parser.add_argument("--parallel-by-agent", action="store_true")
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--stateful", action="store_true")
    parser.add_argument("--previous-agent-turns-tsv", type=Path)
    args = parser.parse_args()

    youth_rows = read_tsv(DATA_DIR / "若者エージェント.tsv")
    working_rows = read_tsv(DATA_DIR / "現役世代エージェント.tsv")
    event_rows = read_tsv(DATA_DIR / "イベント定義.tsv")
    japan_state_rows = read_optional_tsv(args.japan_state_tsv)
    auto_event_rows = read_optional_tsv(args.auto_events_tsv)
    agent_ids = parse_agent_ids(args.agent_ids)
    agents = select_agents(youth_rows, working_rows, agent_ids)
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
            previous_states,
            args.model,
            args.budget,
            args.timeout,
            args.parallel_by_agent,
            args.workers,
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
        prompt = build_prompt(agents, event_rows, args.start_step, args.steps, japan_state_rows, auto_event_rows)
        payload = run_claude(prompt, args.model, args.budget, args.timeout)
    rows = flatten_turns(payload, agents_by_id)

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
        ],
    )
    manifest = {
        "kind": "civilization_os_llm_smoke",
        "model": args.model,
        "start_step": args.start_step,
        "steps": args.steps,
        "stateful": args.stateful,
        "parallel_by_agent": args.parallel_by_agent,
        "japan_state_tsv": str(args.japan_state_tsv) if japan_state_rows else "",
        "auto_events_tsv": str(args.auto_events_tsv) if auto_event_rows else "",
        "previous_agent_turns_tsv": str(args.previous_agent_turns_tsv or ""),
        "agents": list(agents_by_id),
        "outputs": ["turns.tsv", "agent_states.jsonl", "raw_claude_response.json"],
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Wrote {len(rows)} rows to {args.output_dir}")


if __name__ == "__main__":
    main()
