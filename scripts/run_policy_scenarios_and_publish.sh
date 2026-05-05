#!/bin/zsh
set -euo pipefail

cd "$(dirname "$0")/.."

run_scenario() {
  local mode="$1"
  local run_id="$2"
  local log_dir="outputs/runs/${run_id}/logs"
  mkdir -p "$log_dir"

  echo "=== Running ${mode} -> ${run_id} ==="
  /usr/bin/caffeinate -dimsu /opt/homebrew/bin/python3 scripts/run_closed_loop_llm_demo.py \
    --start-step 1 \
    --steps 83 \
    --scenario-mode "$mode" \
    --model gpt-5.2 \
    --parallel-by-country \
    --parallel-by-organization \
    --parallel-by-agent \
    --workers 8 \
    --timeout 420 \
    --output-dir "outputs/runs/${run_id}" \
    > "${log_dir}/background_stdout.log" \
    2> "${log_dir}/background_stderr.log"
  /opt/homebrew/bin/python3 scripts/summarize_run_outcomes.py "outputs/runs/${run_id}" \
    > "${log_dir}/outcome_summary.tsv"
}

publish_pages() {
  local label="$1"
  echo "=== Building Pages for ${label} ==="
  /opt/homebrew/bin/python3 scripts/build_pages_site.py

  /opt/homebrew/bin/python3 -m py_compile \
    scripts/build_pages_site.py \
    scripts/run_civilization_os_llm_demo.py \
    scripts/run_closed_loop_llm_demo.py

  git diff --check
  git add public
  if ! git diff --cached --quiet; then
    git commit -m "Publish ${label} scenario data"
    git push origin main
  else
    echo "No public changes to publish for ${label}."
  fi
}

run_scenario "structure_birth_grant_package" "structure_birth_grant_package_83steps_panel48"
publish_pages "birth grant package"

run_scenario "structure_hope_family_package" "structure_hope_family_package_83steps_panel48"
publish_pages "hope family package"
