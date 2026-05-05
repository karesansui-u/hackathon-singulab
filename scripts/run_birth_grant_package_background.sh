#!/bin/zsh
set -euo pipefail

cd "$(dirname "$0")/.."

RUN_ID="structure_birth_grant_package_83steps_panel48"
OUT_DIR="outputs/runs/${RUN_ID}"
LOG_DIR="${OUT_DIR}/logs"
mkdir -p "$LOG_DIR"

exec /usr/bin/caffeinate -dimsu /opt/homebrew/bin/python3 scripts/run_closed_loop_llm_demo.py \
  --start-step 1 \
  --steps 83 \
  --scenario-mode structure_birth_grant_package \
  --model gpt-5.2 \
  --parallel-by-country \
  --parallel-by-organization \
  --parallel-by-agent \
  --workers 8 \
  --timeout 420 \
  --output-dir "$OUT_DIR"
