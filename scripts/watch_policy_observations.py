#!/usr/bin/env python3
"""Watch policy scenario runs and append GPT-5.2/Codex observations.

This is intentionally read-only toward generated TSVs. It creates observation
notes under each run's logs/ and interesting_observations.md.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import tempfile
import time
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_IDS = (
    "structure_birth_grant_package_83steps_panel48",
    "structure_hope_family_package_83steps_panel48",
)
IMPORTANT_STEPS = {1, 8, 12, 15, 18, 20, 22, 24, 30, 45, 60, 65, 71, 83}


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def step_number(row: dict[str, str]) -> int:
    try:
        return int(float(row.get("step", "")))
    except ValueError:
        return 0


def rows_for_step(path: Path, step: int) -> list[dict[str, str]]:
    return [row for row in read_tsv(path) if step_number(row) == step]


def available_steps(run_dir: Path) -> list[int]:
    steps = sorted({step_number(row) for row in read_tsv(run_dir / "agent_turns.tsv")})
    return [step for step in steps if step > 0]


def observed_steps(path: Path) -> set[int]:
    if not path.exists():
        return set()
    result: set[int] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            result.add(int(line.strip()))
        except ValueError:
            continue
    return result


def mark_observed(path: Path, step: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = observed_steps(path)
    existing.add(step)
    path.write_text("\n".join(str(item) for item in sorted(existing)) + "\n", encoding="utf-8")


def should_observe(step: int) -> bool:
    return step in IMPORTANT_STEPS or step % 5 == 0


def compact_counter(rows: list[dict[str, str]], field: str) -> str:
    counter = Counter(row.get(field, "") or "未記入" for row in rows)
    return ", ".join(f"{key}:{value}" for key, value in counter.most_common())


def trim(value: str, limit: int = 140) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def build_prompt(run_id: str, run_dir: Path, step: int) -> str:
    agent_rows = rows_for_step(run_dir / "agent_turns.tsv", step)
    prev_rows = rows_for_step(run_dir / "agent_turns.tsv", step - 1) if step > 1 else []
    event_rows = rows_for_step(run_dir / "scheduled_events_used.tsv", step)
    japan_rows = rows_for_step(run_dir / "japan_state.tsv", step)
    feedback_rows = rows_for_step(run_dir / "agent_feedback.tsv", step)

    hope_count = sum(1 for row in agent_rows if row.get("emotion") == "希望")
    positive_family_proxy = sum(
        1
        for row in agent_rows
        if row.get("layer") in {"若者", "家族形成", "次世代"}
        and row.get("evaluation") == "良好"
        and row.get("emotion") in {"希望", "安心", "連帯感"}
    )
    prev_hope_count = sum(1 for row in prev_rows if row.get("emotion") == "希望")

    interesting_rows = [
        row
        for row in agent_rows
        if row.get("emotion") in {"希望", "安心", "連帯感", "怒り", "裏切られ感", "喪失感", "絶望", "諦念"}
    ][:14]
    row_lines = []
    for row in interesting_rows:
        row_lines.append(
            "\t".join([
                row.get("agent_id", ""),
                row.get("name", ""),
                row.get("layer", ""),
                row.get("current_age", ""),
                row.get("evaluation", ""),
                row.get("emotion", ""),
                row.get("action_category", ""),
                trim(row.get("thought", "")),
                trim(row.get("reasoning_basis", "")),
            ])
        )

    event_lines = [
        "\t".join([
            row.get("event_id", ""),
            row.get("event_type", ""),
            row.get("event_name", ""),
            row.get("direction", ""),
            trim(row.get("description", ""), 110),
        ])
        for row in event_rows[:18]
    ]

    japan_summary = ""
    if japan_rows:
        row = japan_rows[-1]
        japan_summary = ", ".join(
            f"{key}={row.get(key, '')}"
            for key in [
                "geopolitical_risk",
                "labor_market_uncertainty",
                "fiscal_pressure",
                "sns_anxiety_amplification",
                "japan_policy_buffer",
                "dominant_world_pressure",
            ]
            if key in row
        )

    feedback_summary = ""
    if feedback_rows:
        feedback_summary = " / ".join(
            trim(" ".join(row.values()), 180)
            for row in feedback_rows[:4]
        )

    return f"""
あなたはハッカソン発表の観測アナリストです。
以下はAGI社会移行シミュレーションの途中rowです。
誇張せず、発表で使える「面白い観測」を日本語で短くまとめてください。

run_id: {run_id}
step: {step}
希望人数: {hope_count}（前step {prev_hope_count}）
家族形成ポジティブ代理: {positive_family_proxy}
評価分布: {compact_counter(agent_rows, "evaluation")}
感情分布: {compact_counter(agent_rows, "emotion")}
行動分布: {compact_counter(agent_rows, "action_category")}
日本状態: {japan_summary or "なし"}
社会フィードバック: {feedback_summary or "なし"}

予定イベント:
event_id\ttype\tname\tdirection\tdescription
{chr(10).join(event_lines) if event_lines else "なし"}

注目エージェント:
agent_id\tname\tlayer\tage\tevaluation\temotion\taction_category\tthought\treasoning_basis
{chr(10).join(row_lines) if row_lines else "なし"}

出力形式:
## step {step}
- 観測:
- 創発/意外性:
- 勝ち筋:
- 副作用/注意:
- 発表で見せるなら:

特に「希望を持つ若者が3エージェント以上になるか」「子どもを迎えたい/迎えられる条件が増えたか」に注意してください。
""".strip()


def run_codex(prompt: str, model: str, timeout: int) -> str:
    output_path = Path(tempfile.mkstemp(prefix="policy_observation_", suffix=".md")[1])
    cmd = [
        "codex",
        "--ask-for-approval",
        "never",
        "exec",
        "--ignore-user-config",
        "--ignore-rules",
        "--ephemeral",
        "-m",
        model,
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
        return output_path.read_text(encoding="utf-8").strip() or completed.stdout.strip()
    finally:
        output_path.unlink(missing_ok=True)


def append_observation(run_dir: Path, step: int, text: str) -> None:
    path = run_dir / "interesting_observations.md"
    header = f"\n\n---\n\n<!-- observed_at={datetime.now().isoformat(timespec='seconds')} step={step} -->\n\n"
    if not path.exists():
        path.write_text(f"# Interesting Observations\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(header)
        handle.write(text.strip())
        handle.write("\n")


def observe_step(run_id: str, step: int, model: str, timeout: int) -> None:
    run_dir = ROOT / "outputs" / "runs" / run_id
    logs_dir = run_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    prompt = build_prompt(run_id, run_dir, step)
    try:
        text = run_codex(prompt, model, timeout)
    except Exception as error:
        text = f"## step {step}\n- 観測: Codex観測に失敗: `{error}`"
    append_observation(run_dir, step, text)
    mark_observed(logs_dir / "observed_steps.txt", step)
    print(f"Observed {run_id} step {step}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Watch scenario runs and collect Codex observations.")
    parser.add_argument("--run-ids", default=",".join(RUN_IDS))
    parser.add_argument("--max-step", type=int, default=83)
    parser.add_argument("--sleep", type=int, default=60)
    parser.add_argument("--model", default="gpt-5.2")
    parser.add_argument("--timeout", type=int, default=360)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    run_ids = [item.strip() for item in args.run_ids.split(",") if item.strip()]
    while True:
        all_done = True
        did_work = False
        for run_id in run_ids:
            run_dir = ROOT / "outputs" / "runs" / run_id
            steps = available_steps(run_dir)
            if not steps:
                all_done = False
                continue
            if max(steps) < args.max_step:
                all_done = False
            seen = observed_steps(run_dir / "logs" / "observed_steps.txt")
            pending = [step for step in steps if should_observe(step) and step not in seen]
            if pending:
                observe_step(run_id, pending[0], args.model, args.timeout)
                did_work = True
        if args.once:
            return
        if all_done and not did_work:
            return
        time.sleep(args.sleep)


if __name__ == "__main__":
    main()

