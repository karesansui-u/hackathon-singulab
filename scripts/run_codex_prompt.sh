#!/usr/bin/env bash

set -euo pipefail

if ! command -v codex >/dev/null 2>&1; then
  echo "codex CLI was not found on PATH." >&2
  exit 127
fi

prompt="$(cat)"

if [[ -z "${prompt}" ]]; then
  echo "No prompt was provided to run_codex_prompt.sh" >&2
  exit 1
fi

tmp_output="$(mktemp "${TMPDIR:-/tmp}/codex-last.XXXXXX")"
tmp_log="$(mktemp "${TMPDIR:-/tmp}/codex-log.XXXXXX")"

cleanup() {
  rm -f "$tmp_output" "$tmp_log"
}
trap cleanup EXIT

sandbox_mode="${CODEX_SANDBOX:-read-only}"

composite_prompt=$(
  cat <<EOF
You are being used as a pure text generation backend inside a simulation loop.
Do not run commands, inspect files, edit the repository, or use tools.
Return only the final answer requested by the prompt below.

$prompt
EOF
)

codex_cmd=(codex -a never exec --color never -s "$sandbox_mode")
if [[ -n "${CODEX_MODEL:-}" ]]; then
  codex_cmd+=(--model "$CODEX_MODEL")
fi
codex_cmd+=(-o "$tmp_output" -)

if printf '%s' "$composite_prompt" | "${codex_cmd[@]}" >"$tmp_log" 2>&1; then
  if [[ ! -s "$tmp_output" ]]; then
    cat "$tmp_log" >&2
    echo "codex completed without producing a final message." >&2
    exit 1
  fi

  cat "$tmp_output"
  exit 0
fi

cat "$tmp_log" >&2
exit 1
