#!/usr/bin/env python3
"""Build a GitHub Pages-ready static demo site.

The development viewer reads local paths under ``outputs/runs``. This builder
copies only the publishable demo artifacts into ``public/`` and rewrites the
copied HTML to read from ``public/data/runs``.
"""

from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
REQUIRED_RUN_IDS = (
    "no_intervention_71steps_panel48",
    "structure_intervention_100years_panel48_midprompt",
)
OPTIONAL_RUN_IDS = (
    "policy_search_no_sustain_12steps_panel48",
    "policy_search_with_sustain_12steps_panel48",
    "birth_grant_only_83steps_panel48",
    "structure_birth_grant_package_83steps_panel48",
    "structure_hope_family_package_83steps_panel48",
)
RUN_FILES = (
    "agent_turns.tsv",
    "country_turns.tsv",
    "auto_events_with_feedback.tsv",
    "agent_feedback.tsv",
    "japan_state.tsv",
    "manifest.json",
)
OPTIONAL_RUN_FILES_WITH_EMPTY_FALLBACK = {
    "scheduled_events_used.tsv": "step\tscenario_mode\tevent_id\tevent_type\tevent_name\tstart_step\tend_step\tintensity_0to1\tprobability_0to1\ttarget\tdirection\tdescription\n",
}
OPTIONAL_RUN_FILE_MAPPINGS = {
    "interesting_observations.md": "interesting_observations.md",
    "logs/outcome_summary.tsv": "outcome_summary.tsv",
    "policy_planner_turns.tsv": "policy_planner_turns.tsv",
    "policy_events.tsv": "policy_events.tsv",
    "auto_events_with_policy.tsv": "auto_events_with_policy.tsv",
}
DOMAIN_DATA_FILES = (
    "youth_agents.tsv",
    "working_agents.tsv",
    "time_schedule.tsv",
    "world_events.tsv",
)
TEXT_SUFFIXES = {".html", ".json", ".md", ".tsv", ".txt", ".yaml", ".yml"}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def copy_text(source: Path, target: Path) -> None:
    text = source.read_text(encoding="utf-8").replace("\r\n", "\n")
    write_text(target, text)


def copy_binary_or_text(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.suffix in TEXT_SUFFIXES:
        copy_text(source, target)
    else:
        shutil.copy2(source, target)


def clean_public() -> None:
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    PUBLIC.mkdir(parents=True, exist_ok=True)


def build_public_site() -> None:
    clean_public()

    source_html = ROOT / "visualization" / "future_emotion_map.html"
    if not source_html.exists():
        raise SystemExit(f"Missing UI source: {source_html}")

    html = source_html.read_text(encoding="utf-8")
    html = html.replace("../outputs/runs/", "../data/runs/")
    write_text(PUBLIC / "visualization" / "future_emotion_map.html", html)

    studio_html = ROOT / "visualization" / "simulation_studio_mock.html"
    if studio_html.exists():
        copy_text(studio_html, PUBLIC / "visualization" / "simulation_studio_mock.html")

    for asset_dir_name in ("map_backgrounds", "avatars"):
        asset_source = ROOT / "visualization" / "assets" / asset_dir_name
        if asset_source.exists():
            shutil.copytree(asset_source, PUBLIC / "visualization" / "assets" / asset_dir_name, dirs_exist_ok=True)

    published_run_ids = []
    for run_id in [*REQUIRED_RUN_IDS, *OPTIONAL_RUN_IDS]:
        run_source = ROOT / "outputs" / "runs" / run_id
        required = run_id in REQUIRED_RUN_IDS
        if not run_source.exists():
            if required:
                raise SystemExit(f"Missing run output: {run_source}")
            continue
        missing_required = [file_name for file_name in RUN_FILES if not (run_source / file_name).exists()]
        if missing_required:
            if required:
                raise SystemExit(f"Missing run files in {run_source}: {', '.join(missing_required)}")
            continue
        for file_name in RUN_FILES:
            source = run_source / file_name
            copy_binary_or_text(source, PUBLIC / "data" / "runs" / run_id / file_name)
        for file_name, empty_fallback in OPTIONAL_RUN_FILES_WITH_EMPTY_FALLBACK.items():
            source = run_source / file_name
            target = PUBLIC / "data" / "runs" / run_id / file_name
            if source.exists():
                copy_binary_or_text(source, target)
            else:
                write_text(target, empty_fallback)
        for source_name, target_name in OPTIONAL_RUN_FILE_MAPPINGS.items():
            source = run_source / source_name
            if source.exists():
                copy_binary_or_text(source, PUBLIC / "data" / "runs" / run_id / target_name)
        published_run_ids.append(run_id)

    domain_data_source = ROOT / "domain_packs" / "agi_youth_japan" / "data"
    for file_name in DOMAIN_DATA_FILES:
        source = domain_data_source / file_name
        if not source.exists():
            raise SystemExit(f"Missing domain data file: {source}")
        copy_text(source, PUBLIC / "domain_packs" / "agi_youth_japan" / "data" / file_name)

    write_text(
        PUBLIC / "index.html",
        """<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>文明OSシミュレーション デモ</title>
  <meta http-equiv="refresh" content="0; url=visualization/future_emotion_map.html">
  <link rel="canonical" href="visualization/future_emotion_map.html">
</head>
<body>
  <p><a href="visualization/future_emotion_map.html">文明OSシミュレーション デモ</a></p>
  <p><a href="visualization/simulation_studio_mock.html">シミュレーション作成スタジオ モック</a></p>
</body>
</html>
""",
    )
    write_text(
        PUBLIC / "README.md",
        f"""# 文明OSシミュレーション デモ

GitHub Pages公開用の静的サイトです。

- Demo URL: `https://karesansui-u.github.io/hackathon-singulab/visualization/future_emotion_map.html`
- Main UI: `visualization/future_emotion_map.html`
- Studio mock: `visualization/simulation_studio_mock.html`
- 実行結果データ: {", ".join(f"`data/runs/{run_id}/`" for run_id in published_run_ids)}
- Domain data: `domain_packs/agi_youth_japan/data/`

Source files live outside this directory. Rebuild this folder with:

```bash
python3 scripts/build_pages_site.py
```
""",
    )
    write_text(PUBLIC / ".nojekyll", "")
    print(f"Wrote GitHub Pages site to {PUBLIC}")


def main() -> None:
    build_public_site()


if __name__ == "__main__":
    main()
